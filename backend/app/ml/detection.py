import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_anomalies(series: pd.Series, contamination: float = 0.03) -> list[dict]:
    values = series.astype(float).dropna()
    if len(values) < 14:
        raise ValueError("At least 14 observations are required for anomaly detection")
    model = IsolationForest(contamination=contamination, random_state=17)
    labels = model.fit_predict(values.to_numpy().reshape(-1, 1))
    scores = model.decision_function(values.to_numpy().reshape(-1, 1))
    return [
        {"date": index.date(), "value": float(value), "severity": "high" if score < -0.15 else "medium",
         "method": "isolation_forest"}
        for (index, value), label, score in zip(values.items(), labels, scores) if label == -1
    ]


def detect_spikes_and_drops(series: pd.Series, window: int = 7, z_threshold: float = 3.0) -> list[dict]:
    values = series.astype(float).dropna()
    if len(values) < window + 1:
        return []
    prior = values.shift(1)
    mean = prior.rolling(window, min_periods=window).mean()
    std = prior.rolling(window, min_periods=window).std()
    std = std.where(std > 0, mean.abs().mul(0.1).clip(lower=1e-8))
    z_scores = (values - mean) / std
    findings = []
    for index in values.index[z_scores.abs() >= z_threshold]:
        spike = z_scores.loc[index] > 0
        findings.append({"date": index.date(), "value": float(values.loc[index]),
                         "expected": float(mean.loc[index]), "type": "spike" if spike else "drop",
                         "z_score": float(z_scores.loc[index]), "method": "rolling_z_score"})
    return findings
