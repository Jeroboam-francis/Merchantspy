from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.database.session import get_db
from app.ml.forecasting import forecast, revenue_series
from app.models import ForecastResult

router = APIRouter(prefix="/forecasts", tags=["forecasts"], dependencies=[Depends(current_user)])


@router.post("/revenue")
def revenue_forecast(merchant_id: int | None = None, periods: int = Query(30, ge=1, le=365),
                     model: str = Query("arima"), db: Session = Depends(get_db)):
    try:
        results = forecast(revenue_series(db, merchant_id), periods, model)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not results:
        raise HTTPException(status_code=422, detail="No forecast results generated")
    for row in results:
        db.add(ForecastResult(merchant_id=merchant_id, **row))
    db.commit()
    return {"merchant_id": merchant_id, "model": results[0]["model_name"], "forecast": results}


@router.get("")
def list_forecasts(merchant_id: int | None = None, limit: int = Query(100, ge=1, le=500),
                   db: Session = Depends(get_db)):
    query = db.query(ForecastResult)
    if merchant_id is not None:
        query = query.filter(ForecastResult.merchant_id == merchant_id)
    return [
        {"id": row.id, "merchant_id": row.merchant_id, "target_date": row.target_date,
         "model_name": row.model_name, "predicted_revenue": row.predicted_revenue,
         "lower_bound": row.lower_bound, "upper_bound": row.upper_bound, "created_at": row.created_at}
        for row in query.order_by(ForecastResult.target_date.desc()).limit(limit).all()
    ]
