"""Unit tests for SPIKE detection (T042)."""

from datetime import date, timedelta

import pytest

from src.domain.detector import detect_anomalies
from src.domain.models import DataPoint, ThresholdRules


def _point(value: float, period: date, product: str = "A") -> DataPoint:
    return DataPoint(
        source_id="src",
        dimensions={"Номенклатура": product},
        period=period,
        value=value,
        raw_sum=value * 10.0,
        raw_qty=10.0,
        run_id="run1",
    )


def _monthly(values: list[float], product: str = "A") -> list[DataPoint]:
    """Create monthly data points starting from 2025-01-31."""
    months = [
        date(2025, 1, 31), date(2025, 2, 28), date(2025, 3, 31),
        date(2025, 4, 30), date(2025, 5, 31), date(2025, 6, 30),
        date(2025, 7, 31), date(2025, 8, 31), date(2025, 9, 30),
        date(2025, 10, 31), date(2025, 11, 30), date(2025, 12, 31),
    ]
    return [_point(v, months[i], product) for i, v in enumerate(values)]


class TestSpikeDetection:
    def test_large_pct_increase_triggers_spike(self) -> None:
        # Baseline ~100, then spike to 300 (+200%)
        rules = ThresholdRules(
            spike_pct=20.0, spike_zscore=99.0, spike_logic="OR",
            zero_neg_enabled=False, missing_enabled=False,
        )
        points = _monthly([100, 100, 100, 100, 100, 100, 300])
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2025, 1, 1), date_to=date(2025, 12, 31)
        )
        spikes = [a for a in anomalies if a.anomaly_type == "SPIKE"]
        assert len(spikes) == 1
        assert spikes[0].period == date(2025, 7, 31)
        assert spikes[0].current_value == pytest.approx(300.0)

    def test_high_zscore_triggers_spike(self) -> None:
        # Stable data, then extreme outlier
        rules = ThresholdRules(
            spike_pct=999.0, spike_zscore=2.0, spike_logic="OR",
            zero_neg_enabled=False, missing_enabled=False,
        )
        points = _monthly([100, 102, 98, 101, 99, 103, 500])
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2025, 1, 1), date_to=date(2025, 12, 31)
        )
        spikes = [a for a in anomalies if a.anomaly_type == "SPIKE"]
        assert any(a.period == date(2025, 7, 31) for a in spikes)

    def test_normal_variation_no_spike(self) -> None:
        rules = ThresholdRules(
            spike_pct=50.0, spike_zscore=3.0, spike_logic="OR",
            zero_neg_enabled=False, missing_enabled=False,
        )
        points = _monthly([100, 105, 102, 108, 103, 107, 110])
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2025, 1, 1), date_to=date(2025, 12, 31)
        )
        spikes = [a for a in anomalies if a.anomaly_type == "SPIKE"]
        assert len(spikes) == 0

    def test_first_point_no_baseline_no_spike(self) -> None:
        rules = ThresholdRules(
            spike_pct=0.0, spike_zscore=0.0, spike_logic="OR",
            zero_neg_enabled=False, missing_enabled=False,
        )
        points = [_point(1000.0, date(2025, 1, 31))]
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2025, 1, 1), date_to=date(2025, 1, 31)
        )
        spikes = [a for a in anomalies if a.anomaly_type == "SPIKE"]
        assert len(spikes) == 0

    def test_and_logic_requires_both_conditions(self) -> None:
        # High pct but low zscore (only 2 baseline points, low variance)
        rules = ThresholdRules(
            spike_pct=20.0, spike_zscore=99.0, spike_logic="AND",
            zero_neg_enabled=False, missing_enabled=False,
        )
        points = _monthly([100, 100, 100, 100, 100, 100, 300])
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2025, 1, 1), date_to=date(2025, 12, 31)
        )
        spikes = [a for a in anomalies if a.anomaly_type == "SPIKE"]
        assert len(spikes) == 0

    def test_or_logic_triggers_on_either_condition(self) -> None:
        rules = ThresholdRules(
            spike_pct=20.0, spike_zscore=99.0, spike_logic="OR",
            zero_neg_enabled=False, missing_enabled=False,
        )
        points = _monthly([100, 100, 100, 100, 100, 100, 300])
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2025, 1, 1), date_to=date(2025, 12, 31)
        )
        spikes = [a for a in anomalies if a.anomaly_type == "SPIKE"]
        assert len(spikes) == 1

    def test_spike_records_pct_change_and_zscore(self) -> None:
        rules = ThresholdRules(
            spike_pct=20.0, spike_zscore=99.0, spike_logic="OR",
            zero_neg_enabled=False, missing_enabled=False,
        )
        points = _monthly([100, 100, 100, 100, 100, 100, 300])
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2025, 1, 1), date_to=date(2025, 12, 31)
        )
        spikes = [a for a in anomalies if a.anomaly_type == "SPIKE"]
        assert spikes[0].pct_change is not None
        assert spikes[0].pct_change > 0
        assert spikes[0].zscore is not None

    def test_large_drop_also_triggers_spike(self) -> None:
        rules = ThresholdRules(
            spike_pct=50.0, spike_zscore=99.0, spike_logic="OR",
            zero_neg_enabled=False, missing_enabled=False,
        )
        # Drop by 90%
        points = _monthly([1000, 1000, 1000, 1000, 1000, 1000, 50])
        anomalies = detect_anomalies(
            points, rules, "src", "run1",
            date_from=date(2025, 1, 1), date_to=date(2025, 12, 31)
        )
        spikes = [a for a in anomalies if a.anomaly_type == "SPIKE"]
        assert len(spikes) == 1
