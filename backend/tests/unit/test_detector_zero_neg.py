"""Unit tests for ZERO_NEG detection (T044)."""

from datetime import date

import pytest

from src.domain.detector import detect_anomalies
from src.domain.models import DataPoint, ThresholdRules


def _point(value: float, period: date = date(2026, 1, 31)) -> DataPoint:
    raw_sum = value * 10.0
    return DataPoint(
        source_id="src",
        dimensions={"Номенклатура": "A"},
        period=period,
        value=value,
        raw_sum=raw_sum,
        raw_qty=10.0,
        run_id="run1",
    )


class TestZeroNegDetection:
    def test_negative_value_triggers_zero_neg(self) -> None:
        rules = ThresholdRules(zero_neg_enabled=True, missing_enabled=False)
        point = _point(-100.0)
        anomalies = detect_anomalies(
            [point], rules, "src", "run1",
            date_from=date(2026, 1, 1), date_to=date(2026, 1, 31)
        )
        zn = [a for a in anomalies if a.anomaly_type == "ZERO_NEG"]
        assert len(zn) == 1
        assert zn[0].current_value == -100.0

    def test_zero_value_triggers_zero_neg(self) -> None:
        rules = ThresholdRules(zero_neg_enabled=True, missing_enabled=False)
        # Create point with value=0, raw_qty != 0 (raw_sum=0)
        point = DataPoint(
            source_id="src",
            dimensions={"Номенклатура": "A"},
            period=date(2026, 1, 31),
            value=0.0,
            raw_sum=0.0,
            raw_qty=10.0,
            run_id="run1",
        )
        anomalies = detect_anomalies(
            [point], rules, "src", "run1",
            date_from=date(2026, 1, 1), date_to=date(2026, 1, 31)
        )
        zn = [a for a in anomalies if a.anomaly_type == "ZERO_NEG"]
        assert len(zn) == 1

    def test_positive_value_no_zero_neg(self) -> None:
        rules = ThresholdRules(zero_neg_enabled=True, missing_enabled=False)
        point = _point(500.0)
        anomalies = detect_anomalies(
            [point], rules, "src", "run1",
            date_from=date(2026, 1, 1), date_to=date(2026, 1, 31)
        )
        zn = [a for a in anomalies if a.anomaly_type == "ZERO_NEG"]
        assert len(zn) == 0

    def test_disabled_zero_neg_skips_detection(self) -> None:
        rules = ThresholdRules(zero_neg_enabled=False, missing_enabled=False)
        point = _point(-100.0)
        anomalies = detect_anomalies(
            [point], rules, "src", "run1",
            date_from=date(2026, 1, 1), date_to=date(2026, 1, 31)
        )
        zn = [a for a in anomalies if a.anomaly_type == "ZERO_NEG"]
        assert len(zn) == 0

    def test_qty_zero_does_not_trigger_zero_neg(self) -> None:
        """A MISSING_DATA point (qty=0) should NOT also produce ZERO_NEG."""
        rules = ThresholdRules(zero_neg_enabled=True, missing_enabled=False)
        point = DataPoint(
            source_id="src",
            dimensions={"Номенклатура": "A"},
            period=date(2026, 1, 31),
            value=0.0,
            raw_sum=5000.0,
            raw_qty=0.0,
            run_id="run1",
        )
        anomalies = detect_anomalies(
            [point], rules, "src", "run1",
            date_from=date(2026, 1, 1), date_to=date(2026, 1, 31)
        )
        zn = [a for a in anomalies if a.anomaly_type == "ZERO_NEG"]
        assert len(zn) == 0
