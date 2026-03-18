"""Time series routes - GET /api/v1/timeseries."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from src.infrastructure.persistence.sqlite import (
    SQLiteAnomalyRepository,
    SQLiteDataPointRepository,
)

router = APIRouter()

_DB_PATH = str(Path(__file__).parents[3] / "data" / "anomaly_detection.db")

_data_point_repo = SQLiteDataPointRepository(_DB_PATH)
_anomaly_repo = SQLiteAnomalyRepository(_DB_PATH)


@router.get(
    "",
    summary="Get time series data for drill-down",
    description=(
        "Returns the full time series for a specific dimension combination within a run, "
        "with anomaly type markers per period."
    ),
    responses={
        400: {"model": dict, "description": "run_id or dimensions parameter missing/invalid"},
        404: {"model": dict, "description": "No data found for specified dimensions"},
    },
)
async def get_timeseries(
    run_id: str = Query(..., description="Analysis run ID"),
    dimensions: str = Query(..., description="JSON object with dimension key-value pairs"),
) -> dict:
    """Return time series data points for a dimension combination with anomaly markers."""
    try:
        dims: dict[str, str] = json.loads(dimensions)
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_parameter",
                "message": "'dimensions' must be a valid JSON object",
            },
        ) from None

    data_points = _data_point_repo.get_by_run_and_dimensions(run_id, dims)

    if not data_points:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": "No data found for specified dimensions"},
        )

    # Build anomaly type lookup: period -> anomaly_type (highest priority)
    _TYPE_PRIORITY: dict[str, int] = {
        "ZERO_NEG": 1,
        "MISSING_DATA": 1,
        "SPIKE": 2,
        "RATIO": 3,
        "TREND_BREAK": 4,
        "MISSING": 5,
    }
    anomalies = _anomaly_repo.get_by_run_id(run_id)
    period_to_type: dict[str, str] = {}
    for anomaly in anomalies:
        # Match only anomalies for this dimension combination
        if anomaly.dimensions != dims:
            continue
        if not anomaly.period:
            continue
        period_str = anomaly.period.isoformat()
        existing = period_to_type.get(period_str)
        if existing is None or _TYPE_PRIORITY.get(anomaly.anomaly_type, 99) < _TYPE_PRIORITY.get(
            existing, 99
        ):
            period_to_type[period_str] = anomaly.anomaly_type

    series = [
        {
            "period": dp.period.isoformat(),
            "value": dp.value,
            "raw_sum": dp.raw_sum,
            "raw_qty": dp.raw_qty,
            "anomaly_type": period_to_type.get(dp.period.isoformat()),
        }
        for dp in data_points
    ]

    return {
        "dimensions": data_points[0].dimensions,
        "data": series,
    }
