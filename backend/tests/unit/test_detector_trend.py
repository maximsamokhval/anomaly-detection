"""Unit tests for TREND_BREAK detection (T043)."""

from datetime import date

import pytest

from src.domain.detector import detect_anomalies
from src.domain.models import DataPoint, ThresholdRules

_MONTHS = [
    date(2025, 1, 31), date(2025, 2, 28), date(2025, 3, 31),
    date(2025, 4, 30), date(2025, 5, 31), date(2025, 6, 30),
    date(2025, 7, 31),
]


def _monthly(values: list[float]) -> list[DataPoint]:
    return [
        DataPoint(
            source_id="src",
            dimensions={"Номенклатура": "A"},
            period=_MONTHS[i],
            value=v,
            raw_sum=v * 10.0,
            raw_qty=10.0,
            run_id="run1",
        )
        for i, v in enumerate(values)
    ]


def _rules(**kwargs) -> ThresholdRules:
    defaults = dict(zero_neg_enabled=False, missing_enabled=False)
    defaults.update(kwargs)
    return ThresholdRules(**defaults)


class TestTrendBreakDetection:
    def test_uptrend_reversal_detected(self) -> None:
        # Rising 4 periods (trend_min_points=5), then drops
        rules = _rules(trend_window=3, trend_min_points=5)
        points = _monthly([100, 110, 120, 130, 140, 90])
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2025, 1, 1), date_to=date(2025, 7, 31)
        )
        tb = [a for a in anomalies if a.anomaly_type == "TREND_BREAK"]
        assert len(tb) >= 1
        assert tb[-1].period == date(2025, 6, 30)

    def test_downtrend_reversal_detected(self) -> None:
        # Falling 4 periods, then rises
        rules = _rules(trend_window=3, trend_min_points=5)
        points = _monthly([200, 180, 160, 140, 120, 170])
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2025, 1, 1), date_to=date(2025, 7, 31)
        )
        tb = [a for a in anomalies if a.anomaly_type == "TREND_BREAK"]
        assert len(tb) >= 1

    def test_continuing_trend_no_break(self) -> None:
        rules = _rules(trend_window=3, trend_min_points=5)
        points = _monthly([100, 110, 120, 130, 140, 150])
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2025, 1, 1), date_to=date(2025, 7, 31)
        )
        tb = [a for a in anomalies if a.anomaly_type == "TREND_BREAK"]
        assert len(tb) == 0

    def test_insufficient_points_skips_trend_detection(self) -> None:
        rules = _rules(trend_window=3, trend_min_points=5)
        points = _monthly([100, 110, 120, 90])  # only 4 points
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2025, 1, 1), date_to=date(2025, 4, 30)
        )
        tb = [a for a in anomalies if a.anomaly_type == "TREND_BREAK"]
        assert len(tb) == 0

    def test_trend_break_has_current_and_previous_value(self) -> None:
        rules = _rules(trend_window=3, trend_min_points=5)
        points = _monthly([100, 110, 120, 130, 140, 90])
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2025, 1, 1), date_to=date(2025, 7, 31)
        )
        tb = [a for a in anomalies if a.anomaly_type == "TREND_BREAK"]
        assert tb[-1].current_value is not None
        assert tb[-1].previous_value is not None
        assert tb[-1].pct_change is not None
