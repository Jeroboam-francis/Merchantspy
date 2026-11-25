from datetime import datetime, timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload

from app.models import Merchant, Subscriber, Transaction


def grade_for(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B+"
    if score >= 60:
        return "B"
    if score >= 45:
        return "C"
    return "D"


def merchant_score(db: Session, merchant_id: int) -> dict:
    return merchant_scores(db, merchant_id).get(merchant_id, _compose_score(0, 0, 0, 0, 0))


def _compose_score(revenue: float, count: int, subscribers: int, current_revenue: float, previous_revenue: float) -> dict:
    revenue_component = min(100.0, revenue / 10000)
    transaction_component = min(100.0, count / 10)
    subscriber_component = min(100.0, subscribers / 5)
    growth_rate = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue else 0.0
    growth_component = max(0.0, min(100.0, 50.0 + growth_rate))
    score = round(0.40 * revenue_component + 0.25 * transaction_component + 0.20 * subscriber_component + 0.15 * growth_component, 1)
    return {"revenue": revenue, "transactions": count, "subscribers": subscribers,
            "growth_rate": round(growth_rate, 1), "score": score, "grade": grade_for(score)}


def merchant_scores(db: Session, merchant_id: int | None = None) -> dict[int, dict]:
    now = datetime.utcnow()
    current_start = now - timedelta(days=30)
    previous_start = now - timedelta(days=60)
    tx_query = db.query(
        Transaction.merchant_id,
        func.sum(Transaction.amount).label("revenue"),
        func.count(Transaction.id).label("count"),
        func.sum(case((Transaction.occurred_at >= current_start, Transaction.amount), else_=0)).label("current"),
        func.sum(case((Transaction.occurred_at >= previous_start, Transaction.amount), else_=0)).label("last60"),
    ).filter(Transaction.status == "successful")
    subscriber_query = db.query(Subscriber.merchant_id, func.count(Subscriber.id).label("count"))
    if merchant_id is not None:
        tx_query = tx_query.filter(Transaction.merchant_id == merchant_id)
        subscriber_query = subscriber_query.filter(Subscriber.merchant_id == merchant_id)
    transaction_data = {row.merchant_id: row for row in tx_query.group_by(Transaction.merchant_id).all()}
    subscriber_data = {row.merchant_id: int(row.count or 0) for row in subscriber_query.group_by(Subscriber.merchant_id).all()}
    if merchant_id is not None:
        identifiers = [merchant_id]
    else:
        identifiers = [row[0] for row in db.query(Merchant.id).all()]
    result = {}
    for identifier in identifiers:
        tx = transaction_data.get(identifier)
        revenue = float(tx.revenue or 0) if tx else 0.0
        current_revenue = float(tx.current or 0) if tx else 0.0
        last60_revenue = float(tx.last60 or 0) if tx else 0.0
        previous_revenue = max(0.0, last60_revenue - current_revenue)
        result[identifier] = _compose_score(
            revenue, int(tx.count or 0) if tx else 0, subscriber_data.get(identifier, 0),
            current_revenue, previous_revenue,
        )
    return result


def ranked_merchants(db: Session, limit: int = 10, descending: bool = True) -> list[dict]:
    merchants = db.query(Merchant).options(joinedload(Merchant.region)).all()
    scores = merchant_scores(db)
    scored = []
    for merchant in merchants:
        score = scores[merchant.id]
        scored.append({
            "id": merchant.id, "code": merchant.code, "name": merchant.name,
            "category": merchant.category, "status": merchant.status,
            "region": merchant.region.name if merchant.region else "Unknown", **score,
        })
    scored.sort(key=lambda row: row["score"], reverse=descending)
    return scored[:limit]
