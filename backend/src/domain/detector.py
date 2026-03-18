"""Anomaly detection engine — pure functions, no I/O dependencies.

Constitution I: This module has zero imports from infrastructure/, api/, or ui/.
All six anomaly types: SPIKE, TREND_BREAK, ZERO_NEG, MISSING, RATIO, MISSING_DATA.
"""

import calendar
from collections import defaultdict
from datetime import date
from statistics import mean, stdev
from typing import Any

from src.domain.models import Anomaly, DataPoint, ThresholdRules


def detect_anomalies(
    data_points: list[DataPoint],
    threshold_rules: ThresholdRules,
    source_id: str,
    run_id: str,
    date_from: date,
    date_to: date,
) -> list[Anomaly]:
    """Detect anomalies in a list of DataPoints.

    Runs all enabled detection algorithms and returns the combined results.
    Order: MISSING_DATA → ZERO_NEG → SPIKE → TREND_BREAK → MISSING → RATIO.
    """
    anomalies: list[Anomaly] = []

    # Group by dimension combination and sort chronologically
    by_combo: dict[str, list[DataPoint]] = defaultdict(list)
    for dp in data_points:
        by_combo[_dim_key(dp.dimensions)].append(dp)
    for pts in by_combo.values():
        pts.sort(key=lambda p: p.period)

    # MISSING_DATA — qty == 0 (always checked, not behind a flag)
    for dp in data_points:
        if dp.raw_qty == 0:
            anomalies.append(
                Anomaly(
                    source_id=source_id,
                    run_id=run_id,
                    dimensions=dp.dimensions,
                    period=dp.period,
                    anomaly_type="MISSING_DATA",
                    current_value=None,
                    previous_value=None,
                    pct_change=None,
                    zscore=None,
                    threshold_triggered={"missing_data": True},
                )
            )

    # ZERO_NEG — value <= 0 for valid (non-missing-data) points
    if threshold_rules.zero_neg_enabled:
        for dp in data_points:
            if dp.raw_qty != 0 and dp.value <= 0:
                anomalies.append(
                    Anomaly(
                        source_id=source_id,
                        run_id=run_id,
                        dimensions=dp.dimensions,
                        period=dp.period,
                        anomaly_type="ZERO_NEG",
                        current_value=dp.value,
                        previous_value=None,
                        pct_change=None,
                        zscore=None,
                        threshold_triggered={"zero_neg": True},
                    )
                )

    # SPIKE — sudden jump or drop vs moving average
    for combo_pts in by_combo.values():
        anomalies.extend(_detect_spike(combo_pts, threshold_rules, source_id, run_id))

    # TREND_BREAK — reversal after consistent directional movement
    for combo_pts in by_combo.values():
        anomalies.extend(_detect_trend_break(combo_pts, threshold_rules, source_id, run_id))

    # MISSING — expected month-end periods absent for a combination
    if threshold_rules.missing_enabled:
        expected = _expected_month_ends(date_from, date_to)
        for combo_pts in by_combo.values():
            actual = {dp.period for dp in combo_pts}
            dims = combo_pts[0].dimensions
            for exp_period in expected:
                if exp_period not in actual:
                    prev = next(
                        (p.value for p in reversed(combo_pts) if p.period < exp_period),
                        None,
                    )
                    anomalies.append(
                        Anomaly(
                            source_id=source_id,
                            run_id=run_id,
                            dimensions=dims,
                            period=exp_period,
                            anomaly_type="MISSING",
                            current_value=None,
                            previous_value=prev,
                            pct_change=None,
                            zscore=None,
                            threshold_triggered={"missing": True},
                        )
                    )

    # RATIO — value outside configured bounds
    if threshold_rules.ratio_enabled:
        for dp in data_points:
            if dp.raw_qty == 0:
                continue
            triggered: dict[str, Any] = {}
            if threshold_rules.ratio_min is not None and dp.value < threshold_rules.ratio_min:
                triggered["ratio_min"] = threshold_rules.ratio_min
            if threshold_rules.ratio_max is not None and dp.value > threshold_rules.ratio_max:
                triggered["ratio_max"] = threshold_rules.ratio_max
            if triggered:
                anomalies.append(
                    Anomaly(
                        source_id=source_id,
                        run_id=run_id,
                        dimensions=dp.dimensions,
                        period=dp.period,
                        anomaly_type="RATIO",
                        current_value=dp.value,
                        previous_value=None,
                        pct_change=None,
                        zscore=None,
                        threshold_triggered=triggered,
                    )
                )

    return anomalies


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _dim_key(dimensions: dict[str, str]) -> str:
    """Stable hashable key for a dimension combination."""
    return "|".join(f"{k}={v}" for k, v in sorted(dimensions.items()))


def _detect_spike(
    points: list[DataPoint],
    rules: ThresholdRules,
    source_id: str,
    run_id: str,
) -> list[Anomaly]:
    """Detect sudden spikes/drops relative to a rolling moving-average baseline."""
    anomalies: list[Anomaly] = []

    for i, dp in enumerate(points):
        if dp.raw_qty == 0:
            continue  # MISSING_DATA — skip from spike analysis

        # Build baseline: up to moving_avg_window valid prior points
        window_start = max(0, i - rules.moving_avg_window)
        baseline = [p for p in points[window_start:i] if p.raw_qty != 0]

        if not baseline:
            continue  # No history — cannot compute baseline

        values = [p.value for p in baseline]
        avg = mean(values)

        if avg == 0:
            continue  # Avoid division by zero in pct_change

        pct_change = (dp.value - avg) / abs(avg) * 100.0

        # Z-score requires at least 2 points for stdev
        if len(values) > 1:
            sd = stdev(values)
            z = (dp.value - avg) / sd if sd > 0 else 0.0
        else:
            z = 0.0

        pct_triggered = abs(pct_change) >= rules.spike_pct
        z_triggered = abs(z) >= rules.spike_zscore

        if rules.spike_logic == "AND":
            fire = pct_triggered and z_triggered
        else:  # OR
            fire = pct_triggered or z_triggered

        if fire:
            anomalies.append(
                Anomaly(
                    source_id=source_id,
                    run_id=run_id,
                    dimensions=dp.dimensions,
                    period=dp.period,
                    anomaly_type="SPIKE",
                    current_value=dp.value,
                    previous_value=round(avg, 4),
                    pct_change=round(pct_change, 2),
                    zscore=round(z, 2),
                    threshold_triggered={
                        "spike_pct": pct_triggered,
                        "spike_zscore": z_triggered,
                    },
                )
            )

    return anomalies


def _detect_trend_break(
    points: list[DataPoint],
    rules: ThresholdRules,
    source_id: str,
    run_id: str,
) -> list[Anomaly]:
    """Detect reversal after trend_window consecutive moves in one direction.

    Requires at least trend_min_points valid data points; otherwise skipped.
    """
    anomalies: list[Anomaly] = []

    # Work only with valid (non-missing-data) points
    valid = [p for p in points if p.raw_qty != 0]

    if len(valid) < rules.trend_min_points:
        return []

    # We need trend_window prior changes + the current change → trend_window+1 steps
    # → minimum index = trend_window (0-based)
    for i in range(rules.trend_window, len(valid)):
        # Collect trend_window+1 consecutive points ending at index i
        window = valid[i - rules.trend_window : i + 1]

        changes = [window[j].value - window[j - 1].value for j in range(1, len(window))]

        prior_changes = changes[:-1]  # trend_window - 1 changes confirming prior direction
        current_change = changes[-1]  # the change that may break the trend

        if not prior_changes or current_change == 0:
            continue

        prior_positive = all(c > 0 for c in prior_changes)
        prior_negative = all(c < 0 for c in prior_changes)

        if (prior_positive and current_change < 0) or (prior_negative and current_change > 0):
            dp = valid[i]
            prev_dp = valid[i - 1]
            pct = (
                (dp.value - prev_dp.value) / abs(prev_dp.value) * 100.0
                if prev_dp.value != 0
                else None
            )
            anomalies.append(
                Anomaly(
                    source_id=source_id,
                    run_id=run_id,
                    dimensions=dp.dimensions,
                    period=dp.period,
                    anomaly_type="TREND_BREAK",
                    current_value=dp.value,
                    previous_value=prev_dp.value,
                    pct_change=round(pct, 2) if pct is not None else None,
                    zscore=None,
                    threshold_triggered={"trend_break": True},
                )
            )

    return anomalies


def _expected_month_ends(date_from: date, date_to: date) -> list[date]:
    """Generate last-day-of-month dates in [date_from, date_to] range."""
    periods: list[date] = []
    year, month = date_from.year, date_from.month

    while (year, month) <= (date_to.year, date_to.month):
        last_day = calendar.monthrange(year, month)[1]
        period = date(year, month, last_day)
        if period <= date_to:
            periods.append(period)
        month += 1
        if month > 12:
            month = 1
            year += 1

    return periods
