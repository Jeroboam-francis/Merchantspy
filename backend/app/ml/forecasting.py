from datetime import date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.repositories.transactions import daily_successful_revenue


def revenue_series(db: Session, merchant_id: int | None = None) -> pd.Series:
    rows = daily_successful_revenue(db, merchant_id)
    if not rows:
        return pd.Series(dtype=float)
    values = pd.Series({pd.Timestamp(row.day): float(row.revenue) for row in rows}, dtype=float)
    values.index = pd.to_datetime(values.index)
    return values.asfreq("D", fill_value=0)


def forecast(series: pd.Series, periods: int, model_name: str) -> list[dict]:
    if periods < 1 or periods > 365:
        raise ValueError("periods must be between 1 and 365")
    clean = series.astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < 14:
        raise ValueError("At least 14 daily observations are required to forecast")
    name = model_name.lower()
    if name == "arima":
        from statsmodels.tsa.arima.model import ARIMA
        predictions = ARIMA(clean, order=(1, 1, 1)).fit().get_forecast(steps=periods)
        means = np.maximum(0, np.asarray(predictions.predicted_mean))
        intervals = np.asarray(predictions.conf_int(alpha=0.05))
        lows, highs = np.maximum(0, intervals[:, 0]), np.maximum(0, intervals[:, 1])
        selected = "arima"
    elif name in ("random_forest", "random-forest"):
        from sklearn.ensemble import RandomForestRegressor
        frame = pd.DataFrame({"value": clean})
        frame["lag1"] = frame.value.shift(1)
        frame["lag7"] = frame.value.shift(7)
        frame["lag14"] = frame.value.shift(14)
        frame["dow"] = frame.index.dayofweek
        frame["month"] = frame.index.month
        frame = frame.dropna()
        if len(frame) < 5:
            raise ValueError("Not enough lagged observations for Random Forest")
        model = RandomForestRegressor(n_estimators=150, random_state=17, min_samples_leaf=2)
        model.fit(frame.drop(columns="value"), frame.value)
        history = clean.tolist()
        means = []
        for offset in range(periods):
            target = clean.index[-1] + timedelta(days=offset + 1)
            features = [[history[-1], history[-7], history[-14], target.dayofweek, target.month]]
            prediction = max(0.0, float(model.predict(features)[0]))
            means.append(prediction)
            history.append(prediction)
        means = np.asarray(means)
        residual = np.asarray(model.predict(frame.drop(columns="value"))) - frame.value.to_numpy()
        width = max(float(np.std(residual)), 0.0) * 1.96
        lows, highs, selected = np.maximum(0, means - width), means + width, "random_forest"
    elif name == "prophet":
        try:
            from prophet import Prophet
        except ImportError as exc:
            raise ValueError("Prophet model requested but optional package 'prophet' is not installed") from exc
        model = Prophet()
        model.fit(pd.DataFrame({"ds": clean.index, "y": clean.values}))
        result = model.predict(model.make_future_dataframe(periods=periods))
        future = result.tail(periods)
        means = np.maximum(0, future["yhat"].to_numpy())
        lows, highs, selected = np.maximum(0, future["yhat_lower"].to_numpy()), np.maximum(0, future["yhat_upper"].to_numpy()), "prophet"
    else:
        raise ValueError("model must be one of: arima, random_forest, prophet")
    start = clean.index[-1].date()
    return [
        {"target_date": start + timedelta(days=i + 1), "model_name": selected,
         "predicted_revenue": round(float(means[i]), 2), "lower_bound": round(float(lows[i]), 2),
         "upper_bound": round(float(highs[i]), 2)}
        for i in range(periods)
    ]
