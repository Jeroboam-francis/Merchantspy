from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Transaction


def daily_successful_revenue(db: Session, merchant_id: int | None = None):
    day = func.date(Transaction.occurred_at) if db.bind.dialect.name == "sqlite" else func.trunc(Transaction.occurred_at)
    query = db.query(day.label("day"), func.sum(Transaction.amount).label("revenue")).filter(
        Transaction.status == "successful"
    )
    if merchant_id is not None:
        query = query.filter(Transaction.merchant_id == merchant_id)
    return query.group_by(day).order_by(day).all()
