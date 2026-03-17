"""Mock detector for Walking Skeleton Phase 2.

Returns pre-canned anomalies for testing without real detection algorithms.
"""

from datetime import date, datetime
from uuid import uuid4

from domain.models import Anomaly, DataPoint, ThresholdRules


def detect_anomalies_mock(
    data_points: list[DataPoint],
    threshold_rules: ThresholdRules,
    source_id: str,
    run_id: str,
) -> list[Anomaly]:
    """
    Provide five pre-canned Anomaly objects used for testing the detector.
    
    Parameters:
        data_points (list[DataPoint]): Input data points (ignored by this mock).
        threshold_rules (ThresholdRules): Threshold configuration (ignored by this mock).
        source_id (str): Source identifier to embed in each returned anomaly.
        run_id (str): Analysis run identifier to embed in each returned anomaly.
    
    Returns:
        list[Anomaly]: Five predefined Anomaly instances covering SPIKE, ZERO_NEG, TREND_BREAK, and MISSING cases.
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
