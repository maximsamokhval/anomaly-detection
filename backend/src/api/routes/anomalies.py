"""Anomalies routes - GET /api/v1/anomalies."""

from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query, Request

from src.api.schemas import AnomalyListResponse, AnomalyResponse
from src.infrastructure.persistence.sqlite import SQLiteAnomalyRepository

router = APIRouter()

_DB_PATH = str(Path(__file__).parents[3] / "data" / "anomaly_detection.db")
anomaly_repo = SQLiteAnomalyRepository(_DB_PATH)

_SORTABLE_FIELDS = {"pct_change", "zscore", "period", "current_value"}


@router.get(
    "",
    response_model=AnomalyListResponse,
    summary="List anomalies",
    description=(
        "Retrieve detected anomalies with optional filters, sorting, and pagination. "
        "Dimension filters use the `dimension.{name}=value` query parameter syntax. "
        "When no filters are supplied all stored anomalies are returned."
    ),
)
async def get_anomalies(
    request: Request,
    run_id: str | None = None,
    type: str | None = None,
    period_from: date | None = None,
    period_to: date | None = None,
    sort_by: str | None = Query(
        None,
        description="Sort field: pct_change, zscore, period, current_value",
    ),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=500, description="Records per page"),
) -> AnomalyListResponse:
    """Get anomalies with optional filtering, sorting and pagination.

    Query parameters:
    - **run_id**: filter by analysis run ID
    - **type**: filter by anomaly type (SPIKE, ZERO_NEG, TREND_BREAK, MISSING, RATIO, MISSING_DATA)
    - **period_from**: include only anomalies on or after this date
    - **period_to**: include only anomalies on or before this date
    - **dimension.{name}**: filter by dimension value, e.g. `dimension.product=Widget`
    - **sort_by**: pct_change | zscore | period | current_value
    - **sort_order**: asc | desc (default: desc)
    - **page**: page number, 1-based
    - **page_size**: records per page (1–500, default 50)
    """
    # Parse dimension.{name} query parameters
    dimension_filters: dict[str, str] = {}
    for key, value in request.query_params.items():
        if key.startswith("dimension."):
            dimension_filters[key[len("dimension.") :]] = value

    if run_id:
        anomalies = anomaly_repo.get_by_run_id(run_id)
        if type:
            anomalies = [a for a in anomalies if a.anomaly_type == type]
        if dimension_filters:
            anomalies = [
                a
                for a in anomalies
                if all(a.dimensions.get(k) == v for k, v in dimension_filters.items())
            ]
    else:
        anomalies = anomaly_repo.get_by_filters(
            anomaly_type=type,
            period_from=period_from,
            period_to=period_to,
            dimension_filters=dimension_filters or None,
        )

    # Sorting
    if sort_by and sort_by in _SORTABLE_FIELDS:
        reverse = sort_order.lower() != "asc"
        if sort_by == "pct_change":
            anomalies.sort(
                key=lambda a: (a.pct_change is None, a.pct_change or 0.0), reverse=reverse
            )
        elif sort_by == "zscore":
            anomalies.sort(key=lambda a: (a.zscore is None, a.zscore or 0.0), reverse=reverse)
        elif sort_by == "current_value":
            anomalies.sort(
                key=lambda a: (a.current_value is None, a.current_value or 0.0), reverse=reverse
            )
        elif sort_by == "period":
            anomalies.sort(key=lambda a: (a.period is None, a.period or date.min), reverse=reverse)

    # Pagination
    total = len(anomalies)
    start = (page - 1) * page_size
    page_anomalies = anomalies[start : start + page_size]
    has_next = start + page_size < total

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
        for a in page_anomalies
    ]

    pagination: dict[str, Any] = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": has_next,
    }
    return AnomalyListResponse(anomalies=items, pagination=pagination)
