"""Anomalies routes - GET /api/v1/anomalies."""

from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from src.api.schemas import AnomalyListResponse, AnomalyResponse
from src.infrastructure.persistence.sqlite import SQLiteAnomalyRepository

router = APIRouter()

_DB_PATH = str(Path(__file__).parents[3] / "data" / "anomaly_detection.db")
anomaly_repo = SQLiteAnomalyRepository(_DB_PATH)


@router.get(
    "",
    response_model=AnomalyListResponse,
    summary="List anomalies",
    description=(
        "Retrieve detected anomalies with optional filters. "
        "When no filters are supplied all stored anomalies are returned."
    ),
)
async def get_anomalies(
    run_id: str | None = None,
    type: str | None = None,
    period_from: date | None = None,
    period_to: date | None = None,
) -> AnomalyListResponse:
    """Get anomalies with optional filtering.

    Query parameters:
    - **run_id**: filter by analysis run ID
    - **type**: filter by anomaly type (SPIKE, ZERO_NEG, TREND_BREAK, MISSING, RATIO, MISSING_DATA)
    - **period_from**: include only anomalies on or after this date
    - **period_to**: include only anomalies on or before this date
    """
    if run_id:
        anomalies = anomaly_repo.get_by_run_id(run_id)
        if type:
            anomalies = [a for a in anomalies if a.anomaly_type == type]
    else:
        anomalies = anomaly_repo.get_by_filters(
            anomaly_type=type,
            period_from=period_from,
            period_to=period_to,
        )

    items: list[AnomalyResponse] = [
        AnomalyResponse(
            id=a.id,
            run_id=a.run_id or "",
            source_id=a.source_id,
            type=a.anomaly_type,
            dimensions=a.dimensions,
            period=a.period,
            current_value=a.current_value,
            previous_value=a.previous_value,
            pct_change=a.pct_change,
            zscore=a.zscore,
            threshold_triggered=a.threshold_triggered or None,
        )
        for a in anomalies
    ]

    pagination: dict[str, Any] = {"total": len(items), "page": 1, "page_size": len(items)}
    return AnomalyListResponse(anomalies=items, pagination=pagination)
