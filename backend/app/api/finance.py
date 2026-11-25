from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.database.session import get_db
from app.models import Collection, Disbursement, Transaction

router = APIRouter(tags=["financial activity"], dependencies=[Depends(current_user)])


def _list_records(db: Session, model, date_column, start: date | None, end: date | None,
                  merchant_id: int | None, status: str | None, limit: int, offset: int):
    query = db.query(model)
    if start:
        query = query.filter(date_column >= datetime.combine(start, time.min))
    if end:
        query = query.filter(date_column < datetime.combine(end + timedelta(days=1), time.min))
    if merchant_id is not None:
        query = query.filter(model.merchant_id == merchant_id)
    if status:
        query = query.filter(model.status == status)
    total = query.count()
    rows = query.order_by(date_column.desc()).offset(offset).limit(limit).all()
    if model is Transaction:
        items = [{"id": row.id, "merchant_id": row.merchant_id, "reference": row.transaction_ref,
                  "occurred_at": row.occurred_at, "amount": row.amount, "status": row.status,
                  "channel": row.channel} for row in rows]
    elif model is Collection:
        items = [{"id": row.id, "merchant_id": row.merchant_id, "transaction_id": row.transaction_id,
                  "occurred_at": row.collected_at, "amount": row.amount, "status": row.status} for row in rows]
    else:
        items = [{"id": row.id, "merchant_id": row.merchant_id, "reference": row.reference,
                  "occurred_at": row.disbursed_at, "amount": row.amount, "status": row.status} for row in rows]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/transactions", tags=["transactions"])
def list_transactions(start: date | None = None, end: date | None = None, merchant_id: int | None = None,
                      status: str | None = None, limit: int = Query(100, ge=1, le=1000),
                      offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return _list_records(db, Transaction, Transaction.occurred_at, start, end, merchant_id, status, limit, offset)


@router.get("/collections", tags=["collections"])
def list_collections(start: date | None = None, end: date | None = None, merchant_id: int | None = None,
                     status: str | None = None, limit: int = Query(100, ge=1, le=1000),
                     offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return _list_records(db, Collection, Collection.collected_at, start, end, merchant_id, status, limit, offset)


@router.get("/disbursements", tags=["disbursements"])
def list_disbursements(start: date | None = None, end: date | None = None, merchant_id: int | None = None,
                       status: str | None = None, limit: int = Query(100, ge=1, le=1000),
                       offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return _list_records(db, Disbursement, Disbursement.disbursed_at, start, end, merchant_id, status, limit, offset)
