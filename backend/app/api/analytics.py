from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_roles
from app.database.session import get_db
from app.ml.detection import detect_anomalies, detect_spikes_and_drops
from app.ml.forecasting import revenue_series
from app.ml.segmentation import segment_merchants
from app.models import AnomalyResult, Collection, Disbursement, Merchant, Region, Subscriber, Transaction, User
from app.services.scoring import ranked_merchants

router = APIRouter(prefix="/analytics", tags=["analytics"], dependencies=[Depends(current_user)])


def _sum(db: Session, model, date_column, start: date | None, end: date | None) -> float:
    query = db.query(func.coalesce(func.sum(model.amount), 0))
    query = query.filter(model.status == "successful")
    if start:
        query = query.filter(date_column >= datetime.combine(start, datetime.min.time()))
    if end:
        query = query.filter(date_column < datetime.combine(end + timedelta(days=1), datetime.min.time()))
    return float(query.scalar() or 0)


@router.get("/overview")
def overview(start: date | None = None, end: date | None = None, db: Session = Depends(get_db)):
    revenue = _sum(db, Transaction, Transaction.occurred_at, start, end)
    collections = _sum(db, Collection, Collection.collected_at, start, end)
    disbursements = _sum(db, Disbursement, Disbursement.disbursed_at, start, end)
    active = db.query(func.count(Merchant.id)).filter(Merchant.status == "active").scalar() or 0
    total = db.query(func.count(Merchant.id)).scalar() or 0
    subscribers = db.query(func.count(Subscriber.id)).filter(Subscriber.status == "active").scalar() or 0
    return {
        "total_revenue": revenue, "total_collections": collections, "total_disbursements": disbursements,
        "revenue_to_collection_ratio": round(revenue / collections, 4) if collections else None,
        "revenue_to_disbursement_ratio": round(revenue / disbursements, 4) if disbursements else None,
        "active_merchants": active, "dormant_merchants": max(0, total - active), "unique_subscribers": subscribers,
        "period": {"start": start, "end": end},
    }


@router.get("/trends")
def trends(days: int = Query(30, ge=7, le=730), db: Session = Depends(get_db)):
    start = datetime.utcnow().date() - timedelta(days=days - 1)
    def grouped(model, column, status_filter=None):
        day = func.date(column) if db.bind.dialect.name == "sqlite" else func.trunc(column)
        query = db.query(day.label("day"), func.sum(model.amount).label("total")).filter(column >= start)
        if status_filter is not None:
            query = query.filter(model.status == status_filter)
        return {str(row.day): float(row.total or 0) for row in query.group_by(day).order_by(day).all()}
    tx_day = func.date(Transaction.occurred_at) if db.bind.dialect.name == "sqlite" else func.trunc(Transaction.occurred_at)
    return {
        "revenue": grouped(Transaction, Transaction.occurred_at, "successful"),
        "collections": grouped(Collection, Collection.collected_at, "successful"),
        "disbursements": grouped(Disbursement, Disbursement.disbursed_at, "successful"),
        "merchant_activity": {str(row.day): int(row.count) for row in db.query(
            tx_day.label("day"), func.count(func.distinct(Transaction.merchant_id)).label("count")
        ).filter(Transaction.occurred_at >= start).group_by(tx_day).all()},
    }


@router.get("/geography")
def geography(db: Session = Depends(get_db)):
    rows = db.query(Region.name, func.coalesce(func.sum(Transaction.amount), 0)).join(
        Merchant, Merchant.region_id == Region.id
    ).join(Transaction, and_(Transaction.merchant_id == Merchant.id, Transaction.status == "successful"),
           isouter=True).group_by(Region.id, Region.name).all()
    return [{"region": name, "revenue": float(amount or 0)} for name, amount in
            sorted(rows, key=lambda row: float(row[1] or 0), reverse=True)]


@router.get("/ranking")
def ranking(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    return {"top": ranked_merchants(db, limit), "lowest": ranked_merchants(db, limit, descending=False)}


@router.get("/segments")
def segments(db: Session = Depends(get_db)):
    merchants = ranked_merchants(db, limit=10000)
    grades: dict[str, int] = {}
    for merchant in merchants:
        grades[merchant["grade"]] = grades.get(merchant["grade"], 0) + 1
    return {"total": len(merchants), "segments": [{"grade": grade, "count": count}
            for grade, count in sorted(grades.items())]}


@router.get("/segments/ml")
def ml_segments(db: Session = Depends(get_db)):
    merchants = ranked_merchants(db, limit=10000)
    try:
        return {"total": len(merchants), "assignments": segment_merchants(merchants)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/signals")
def signals(merchant_id: int | None = None, db: Session = Depends(get_db)):
    series = revenue_series(db, merchant_id)
    try:
        return {"anomalies": detect_anomalies(series), "spikes_and_drops": detect_spikes_and_drops(series)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/anomalies")
def list_anomalies(merchant_id: int | None = None, limit: int = Query(100, ge=1, le=1000),
                   db: Session = Depends(get_db)):
    query = db.query(AnomalyResult)
    if merchant_id is not None:
        query = query.filter(AnomalyResult.merchant_id == merchant_id)
    return [
        {"id": row.id, "merchant_id": row.merchant_id, "detected_at": row.detected_at,
         "metric": row.metric, "observed_value": row.observed_value, "severity": row.severity,
         "method": row.method, "details": row.details}
        for row in query.order_by(AnomalyResult.detected_at.desc()).limit(limit).all()
    ]


@router.post("/anomalies/detect")
def detect_and_store_anomalies(merchant_id: int | None = None, db: Session = Depends(get_db),
                               user: User = Depends(require_roles("admin", "manager", "analyst"))):
    merchant_ids = [merchant_id] if merchant_id is not None else [row[0] for row in db.query(Merchant.id).all()]
    created = 0
    skipped = []
    try:
        for selected_id in merchant_ids:
            series = revenue_series(db, selected_id)
            if len(series) < 14:
                skipped.append({"merchant_id": selected_id, "reason": "At least 14 daily observations are required"})
                continue
            detections = [
                {"detected_at": datetime.combine(row["date"], datetime.min.time()), "metric": "revenue",
                 "observed_value": row["value"], "severity": row["severity"],
                 "method": row["method"], "details": "Isolation Forest flagged daily revenue as anomalous."}
                for row in detect_anomalies(series)
            ]
            detections.extend(
                {"detected_at": datetime.combine(row["date"], datetime.min.time()), "metric": "revenue",
                 "observed_value": row["value"], "severity": "high" if abs(row["z_score"]) >= 4 else "medium",
                 "method": row["method"], "details": f'{row["type"].capitalize()} detected against a rolling 7-day baseline.'}
                for row in detect_spikes_and_drops(series)
            )
            for item in detections:
                exists = db.query(AnomalyResult.id).filter(
                    AnomalyResult.merchant_id == selected_id,
                    AnomalyResult.detected_at == item["detected_at"],
                    AnomalyResult.metric == item["metric"],
                    AnomalyResult.method == item["method"],
                ).first()
                if exists is None:
                    db.add(AnomalyResult(merchant_id=selected_id, **item))
                    created += 1
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"merchant_ids_analyzed": len(merchant_ids) - len(skipped), "new_anomalies": created, "skipped": skipped}


@router.get("/regions")
def regions(db: Session = Depends(get_db)):
    return [{"id": row.id, "name": row.name} for row in db.query(Region).order_by(Region.name).all()]
