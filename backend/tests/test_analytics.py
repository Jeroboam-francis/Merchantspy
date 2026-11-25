import unittest

import numpy as np
import pandas as pd

from app.ml.detection import detect_spikes_and_drops
from app.ml.forecasting import forecast
from app.ml.segmentation import segment_merchants
from app.services.scoring import grade_for


class AnalyticsTests(unittest.TestCase):
    def test_grade_thresholds(self):
        self.assertEqual(grade_for(90), "A+")
        self.assertEqual(grade_for(80), "A")
        self.assertEqual(grade_for(70), "B+")
        self.assertEqual(grade_for(60), "B")
        self.assertEqual(grade_for(45), "C")
        self.assertEqual(grade_for(44.9), "D")

    def test_rolling_signal_detects_positive_spike_and_drop(self):
        values = [10.0] * 8 + [100.0] + [10.0] * 8 + [0.0]
        dates = pd.date_range("2026-01-01", periods=len(values), freq="D")
        findings = detect_spikes_and_drops(pd.Series(values, index=dates), window=7, z_threshold=2.0)
        self.assertEqual([finding["type"] for finding in findings], ["spike", "drop"])

    def test_random_forest_forecast_has_requested_dates_and_nonnegative_bounds(self):
        dates = pd.date_range("2025-01-01", periods=45, freq="D")
        values = pd.Series(100 + np.arange(45) + np.sin(np.arange(45)), index=dates)
        result = forecast(values, periods=3, model_name="random_forest")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["target_date"], (dates[-1] + pd.Timedelta(days=1)).date())
        self.assertTrue(all(row["lower_bound"] <= row["predicted_revenue"] <= row["upper_bound"] for row in result))

    def test_ml_segmentation_assigns_supported_merchants_to_segments(self):
        metrics = [
            {"id": 1, "revenue": 100, "transactions": 2, "subscribers": 5, "growth_rate": -10, "grade": "D", "score": 20},
            {"id": 2, "revenue": 1000, "transactions": 20, "subscribers": 50, "growth_rate": 5, "grade": "C", "score": 45},
            {"id": 3, "revenue": 50000, "transactions": 500, "subscribers": 500, "growth_rate": 18, "grade": "B+", "score": 75},
        ]
        result = segment_merchants(metrics)
        self.assertEqual({row["merchant_id"] for row in result}, {1, 2, 3})
        self.assertEqual(len(result), 3)
        self.assertTrue(all(row["segment"] in {"developing", "emerging", "leading"} for row in result))


if __name__ == "__main__":
    unittest.main()
