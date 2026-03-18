"""Time series routes - GET /api/v1/timeseries."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from src.api.schemas import TimeSeriesDataPoint, TimeSeriesResponse
from src.domain.models import Anomaly
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
    response_model=TimeSeriesResponse,
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
) -> TimeSeriesResponse:
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

    # Build anomaly lookup: period -> anomaly (highest priority)
    _TYPE_PRIORITY: dict[str, int] = {
        "ZERO_NEG": 1,
        "MISSING_DATA": 1,
        "SPIKE": 2,
        "RATIO": 3,
        "TREND_BREAK": 4,
        "MISSING": 5,
    }
    anomalies = _anomaly_repo.get_by_run_id(run_id)
    period_to_anomaly: dict[str, Anomaly] = {}
    for anomaly in anomalies:
        if anomaly.dimensions != dims:
            continue
        if not anomaly.period:
            continue
        period_str = anomaly.period.isoformat()
        existing = period_to_anomaly.get(period_str)
        if existing is None or _TYPE_PRIORITY.get(anomaly.anomaly_type, 99) < _TYPE_PRIORITY.get(
            existing.anomaly_type,
            99,
        ):
            period_to_anomaly[period_str] = anomaly

    series = []
    for dp in data_points:
        period_str = dp.period.isoformat()
        anom = period_to_anomaly.get(period_str)
        series.append(
            TimeSeriesDataPoint(
                period=dp.period,
                value=dp.value,
                raw_sum=dp.raw_sum,
                raw_qty=dp.raw_qty,
                anomaly_type=anom.anomaly_type if anom else None,
                pct_change=anom.pct_change if anom else None,
                zscore=anom.zscore if anom else None,
            )
        )

    return TimeSeriesResponse(
        dimensions=data_points[0].dimensions,
        data=series,
    )
