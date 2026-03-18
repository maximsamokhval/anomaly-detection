"""Unit tests for MISSING period detection (T045)."""

from datetime import date

import pytest

from src.domain.detector import detect_anomalies
from src.domain.models import DataPoint, ThresholdRules


def _point(product: str, period: date, value: float = 1000.0) -> DataPoint:
    return DataPoint(
        source_id="src",
        dimensions={"Номенклатура": product},
        period=period,
        value=value,
        raw_sum=value * 10.0,
        raw_qty=10.0,
        run_id="run1",
    )


class TestMissingDetection:
    def test_missing_period_creates_anomaly(self) -> None:
        rules = ThresholdRules(zero_neg_enabled=False, missing_enabled=True)
        points = [
            _point("A", date(2026, 1, 31)),
            # February missing
            _point("A", date(2026, 3, 31)),
        ]
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2026, 1, 1), date_to=date(2026, 3, 31)
        )
        missing = [a for a in anomalies if a.anomaly_type == "MISSING"]
        assert len(missing) == 1
        assert missing[0].period == date(2026, 2, 28)
        assert missing[0].dimensions == {"Номенклатура": "A"}

    def test_all_periods_present_no_missing(self) -> None:
        rules = ThresholdRules(zero_neg_enabled=False, missing_enabled=True)
        points = [
            _point("A", date(2026, 1, 31)),
            _point("A", date(2026, 2, 28)),
            _point("A", date(2026, 3, 31)),
        ]
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2026, 1, 1), date_to=date(2026, 3, 31)
        )
        missing = [a for a in anomalies if a.anomaly_type == "MISSING"]
        assert len(missing) == 0

    def test_disabled_missing_skips_detection(self) -> None:
        rules = ThresholdRules(zero_neg_enabled=False, missing_enabled=False)
        points = [
            _point("A", date(2026, 1, 31)),
            # February missing
            _point("A", date(2026, 3, 31)),
        ]
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2026, 1, 1), date_to=date(2026, 3, 31)
        )
        missing = [a for a in anomalies if a.anomaly_type == "MISSING"]
        assert len(missing) == 0

    def test_missing_anomaly_sets_previous_value(self) -> None:
        rules = ThresholdRules(zero_neg_enabled=False, missing_enabled=True)
        points = [
            _point("A", date(2026, 1, 31), value=900.0),
            _point("A", date(2026, 3, 31), value=950.0),
        ]
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2026, 1, 1), date_to=date(2026, 3, 31)
        )
        missing = [a for a in anomalies if a.anomaly_type == "MISSING"]
        assert missing[0].previous_value == pytest.approx(900.0)
        assert missing[0].current_value is None

    def test_multiple_missing_periods(self) -> None:
        rules = ThresholdRules(zero_neg_enabled=False, missing_enabled=True)
        points = [
            _point("A", date(2026, 1, 31)),
            # Feb, Mar missing
            _point("A", date(2026, 4, 30)),
        ]
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2026, 1, 1), date_to=date(2026, 4, 30)
        )
        missing = [a for a in anomalies if a.anomaly_type == "MISSING"]
        assert len(missing) == 2
        periods = {a.period for a in missing}
        assert date(2026, 2, 28) in periods
        assert date(2026, 3, 31) in periods

    def test_independent_combinations_tracked_separately(self) -> None:
        """Missing detection should be per dimension combination."""
        rules = ThresholdRules(zero_neg_enabled=False, missing_enabled=True)
        points = [
            _point("A", date(2026, 1, 31)),
            _point("A", date(2026, 3, 31)),
            _point("B", date(2026, 1, 31)),
            _point("B", date(2026, 2, 28)),
            _point("B", date(2026, 3, 31)),
        ]
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2026, 1, 1), date_to=date(2026, 3, 31)
        )
        missing = [a for a in anomalies if a.anomaly_type == "MISSING"]
        assert len(missing) == 1
        assert missing[0].dimensions == {"Номенклатура": "A"}
