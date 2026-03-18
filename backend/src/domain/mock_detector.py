"""Mock detector for Walking Skeleton Phase 2.

Returns pre-canned anomalies for testing without real detection algorithms.
"""

from datetime import date
from uuid import uuid4

from src.domain.models import Anomaly, DataPoint, ThresholdRules


def detect_anomalies_mock(
    data_points: list[DataPoint],
    threshold_rules: ThresholdRules,
    source_id: str,
    run_id: str,
) -> list[Anomaly]:
    """Return pre-canned anomalies for mock testing.
    
    Args:
        data_points: List of data points to analyze (ignored in mock)
        threshold_rules: Threshold configuration (ignored in mock)
        source_id: Source identifier
        run_id: Analysis run identifier
    
    Returns:
        List of mock anomalies with predefined values
    """
    # Return 5 mock anomalies covering different types
    return [
        Anomaly(
            id=str(uuid4()),
            run_id=run_id,
            source_id=source_id,
            dimensions={
                "Номенклатура": "Продукт A",
                "Склад": "Центральний",
                "Організація": "ТОВ Компанія",
            },
            period=date(2026, 2, 28),
            anomaly_type="SPIKE",
            current_value=1240.0,
            previous_value=500.0,
            pct_change=148.0,
            zscore=3.5,
            threshold_triggered={"spike_pct": 20.0, "spike_zscore": 3.0},
        ),
        Anomaly(
            id=str(uuid4()),
            run_id=run_id,
            source_id=source_id,
            dimensions={
                "Номенклатура": "Продукт B",
                "Склад": "Центральний",
                "Організація": "ТОВ Компанія",
            },
            period=date(2026, 1, 31),
            anomaly_type="ZERO_NEG",
            current_value=-100.0,
            previous_value=1600.0,
            pct_change=None,
            zscore=None,
            threshold_triggered={"zero_neg": True},
        ),
        Anomaly(
            id=str(uuid4()),
            run_id=run_id,
            source_id=source_id,
            dimensions={
                "Номенклатура": "Продукт C",
                "Склад": "Центральний",
                "Організація": "ТОВ Компанія",
            },
            period=date(2026, 3, 31),
            anomaly_type="TREND_BREAK",
            current_value=450.0,
            previous_value=550.0,
            pct_change=-18.2,
            zscore=2.1,
            threshold_triggered={"trend_break": True},
        ),
        Anomaly(
            id=str(uuid4()),
            run_id=run_id,
            source_id=source_id,
            dimensions={
                "Номенклатура": "Продукт D",
                "Склад": "Центральний",
                "Організація": "ТОВ Компанія",
            },
            period=date(2026, 2, 28),
            anomaly_type="MISSING",
            current_value=None,
            previous_value=900.0,
            pct_change=None,
            zscore=None,
            threshold_triggered={"missing": True},
        ),
        Anomaly(
            id=str(uuid4()),
            run_id=run_id,
            source_id=source_id,
            dimensions={
                "Номенклатура": "Продукт A",
                "Склад": "Північний",
                "Організація": "ТОВ Компанія",
            },
            period=date(2026, 2, 28),
            anomaly_type="SPIKE",
            current_value=980.0,
            previous_value=400.0,
            pct_change=145.0,
            zscore=3.2,
            threshold_triggered={"spike_pct": 20.0, "spike_zscore": 3.0},
        ),
    ]
