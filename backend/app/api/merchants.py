from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import current_user
from app.database.session import get_db
from app.models import Collection, Disbursement, Merchant, Region, Subscriber, Transaction
from app.services.scoring import merchant_score, merchant_scores, ranked_merchants
from app.utils.db_time import period_expression

router = APIRouter(prefix="/merchants", tags=["merchants"], dependencies=[Depends(current_user)])


@router.get("")
def list_merchants(search: str | None = None, region_id: int | None = None,
                   region: str | None = None, status: str | None = None, limit: int = Query(50, ge=1, le=200),
                   offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    query = db.query(Merchant).options(joinedload(Merchant.region))
    if search:
        query = query.filter(Merchant.name.ilike(f"%{search}%") | Merchant.code.ilike(f"%{search}%"))
    if region_id:
        query = query.filter(Merchant.region_id == region_id)
    if region:
        query = query.join(Merchant.region).filter(Region.name == region)
    if status:
        query = query.filter(Merchant.status == status)
    total = query.count()
    rows = query.order_by(Merchant.name).offset(offset).limit(limit).all()
    scores = merchant_scores(db)
    output = []
    for merchant in rows:
        output.append({"id": merchant.id, "code": merchant.code, "name": merchant.name,
                       "category": merchant.category, "status": merchant.status,
                       "region": merchant.region.name if merchant.region else "Unknown",
                       **scores.get(merchant.id, {"revenue": 0, "transactions": 0, "subscribers": 0,
                                                  "growth_rate": 0, "score": 0, "grade": "D"})})
    return {"items": output, "total": total, "limit": limit, "offset": offset}


@router.get("/{merchant_id}")
def merchant_detail(merchant_id: int, period: str = Query("monthly", pattern="^(daily|monthly|yearly)$"),
                    db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if merchant is None:
        raise HTTPException(status_code=404, detail="Merchant not found")
    score = merchant_score(db, merchant_id)
    portfolio = ranked_merchants(db, limit=10000)
    rank = next((index for index, row in enumerate(portfolio, start=1) if row["id"] == merchant_id), None)
    tx_count = db.query(func.count(Transaction.id)).filter(Transaction.merchant_id == merchant_id).scalar() or 0
    revenue = float(db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.merchant_id == merchant_id, Transaction.status == "successful"
    ).scalar() or 0)
    collections = float(db.query(func.coalesce(func.sum(Collection.amount), 0)).filter(
        Collection.merchant_id == merchant_id, Collection.status == "successful"
    ).scalar() or 0)
    disbursements = float(db.query(func.coalesce(func.sum(Disbursement.amount), 0)).filter(
        Disbursement.merchant_id == merchant_id, Disbursement.status == "successful"
    ).scalar() or 0)
    def grouped_amount(model, date_column):
        expression = period_expression(db, date_column, period)
        return db.query(expression.label("period"), func.sum(model.amount).label("amount"),
                        func.count(model.id).label("count")).filter(
            model.merchant_id == merchant_id, model.status == "successful"
        ).group_by(expression).order_by(expression).all()

    periods = {}
    for row in grouped_amount(Transaction, Transaction.occurred_at):
        periods[row.period] = {"period": row.period, "revenue": float(row.amount or 0),
                               "transactions": int(row.count or 0), "collections": 0.0,
                               "disbursements": 0.0}
    for row in grouped_amount(Collection, Collection.collected_at):
        periods.setdefault(row.period, {"period": row.period, "revenue": 0.0,
                                        "transactions": 0, "collections": 0.0,
                                        "disbursements": 0.0})["collections"] = float(row.amount or 0)
    for row in grouped_amount(Disbursement, Disbursement.disbursed_at):
        periods.setdefault(row.period, {"period": row.period, "revenue": 0.0,
                                        "transactions": 0, "collections": 0.0,
                                        "disbursements": 0.0})["disbursements"] = float(row.amount or 0)
    subscribers = db.query(func.count(Subscriber.id)).filter(
        Subscriber.merchant_id == merchant_id, Subscriber.status == "active"
    ).scalar() or 0
    tx_rows = db.query(Transaction).filter(Transaction.merchant_id == merchant_id).order_by(
        Transaction.occurred_at.desc()).limit(100).all()
    return {
        "profile": {"id": merchant.id, "code": merchant.code, "name": merchant.name,
                    "category": merchant.category, "status": merchant.status,
                    "region": merchant.region.name if merchant.region else "Unknown"},
        "revenue": revenue, "transactions": tx_count, "collections": collections,
        "disbursements": disbursements, "subscribers": subscribers, **score,
        "ranking": rank, "portfolio_size": len(portfolio),
        "period": period, "period_analysis": [periods[key] for key in sorted(periods)],
        "recent_transactions": [
            {"id": row.id, "reference": row.transaction_ref, "date": row.occurred_at,
             "amount": float(row.amount), "status": row.status, "channel": row.channel}
            for row in tx_rows
        ],
    }
