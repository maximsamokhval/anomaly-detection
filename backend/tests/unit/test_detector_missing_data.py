"""Unit tests for MISSING_DATA detection (T046) — qty == 0 guard."""

from datetime import date

import pytest

from src.domain.detector import detect_anomalies
from src.domain.models import DataPoint, ThresholdRules


def _make_point(
    product: str,
    period: date,
    raw_sum: float,
    raw_qty: float,
    source_id: str = "src",
    run_id: str = "run1",
) -> DataPoint:
    value = raw_sum / raw_qty if raw_qty != 0 else 0.0
    return DataPoint(
        source_id=source_id,
        dimensions={"Номенклатура": product},
        period=period,
        value=value,
        raw_sum=raw_sum,
        raw_qty=raw_qty,
        run_id=run_id,
    )


class TestMissingDataDetection:
    def test_qty_zero_creates_missing_data_anomaly(self) -> None:
        rules = ThresholdRules()
        point = _make_point("A", date(2026, 1, 31), 5000.0, 0.0)
        anomalies = detect_anomalies(
            [point], rules, "src", "run1",
            date_from=date(2026, 1, 1), date_to=date(2026, 1, 31)
        )
        missing_data = [a for a in anomalies if a.anomaly_type == "MISSING_DATA"]
        assert len(missing_data) == 1
        assert missing_data[0].period == date(2026, 1, 31)
        assert missing_data[0].dimensions == {"Номенклатура": "A"}

    def test_qty_nonzero_no_missing_data(self) -> None:
        rules = ThresholdRules(zero_neg_enabled=False, missing_enabled=False)
        point = _make_point("A", date(2026, 1, 31), 5000.0, 10.0)
        anomalies = detect_anomalies(
            [point], rules, "src", "run1",
            date_from=date(2026, 1, 1), date_to=date(2026, 1, 31)
        )
        missing_data = [a for a in anomalies if a.anomaly_type == "MISSING_DATA"]
        assert len(missing_data) == 0

    def test_missing_data_threshold_triggered(self) -> None:
        rules = ThresholdRules()
        point = _make_point("A", date(2026, 1, 31), 0.0, 0.0)
        anomalies = detect_anomalies(
            [point], rules, "src", "run1",
            date_from=date(2026, 1, 1), date_to=date(2026, 1, 31)
        )
        missing_data = [a for a in anomalies if a.anomaly_type == "MISSING_DATA"]
        assert missing_data[0].threshold_triggered == {"missing_data": True}
