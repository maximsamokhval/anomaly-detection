"""Data sources routes - CRUD /api/v1/sources."""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from src.api.schemas import (
    DataSourceCreateRequest,
    DataSourceListResponse,
    DataSourceResponse,
    DataSourceShortResponse,
    DataSourceUpdateRequest,
    TestConnectionResponse,
    ThresholdRulesResponse,
)
from src.domain.models import AuthConfig, DataSource, ThresholdRules
from src.infrastructure.http_client import test_connection as _test_1c_connection
from src.infrastructure.persistence.sqlite import SQLiteDataSourceRepository

router = APIRouter()

_DB_PATH = str(Path(__file__).parents[3] / "data" / "anomaly_detection.db")
data_source_repo = SQLiteDataSourceRepository(_DB_PATH)


def _source_to_response(source: DataSource) -> DataSourceResponse:
    """Convert a DataSource domain object to its API response model."""
    rules = source.threshold_rules
    return DataSourceResponse(
        id=source.id,
        name=source.name,
        endpoint=source.endpoint,
        register_name=source.register_name,
        dimensions=source.dimensions,
        metric_fields=source.metric_fields,
        threshold_rules=ThresholdRulesResponse(
            spike_pct=rules.spike_pct,
            spike_zscore=rules.spike_zscore,
            spike_logic=rules.spike_logic,
            moving_avg_window=rules.moving_avg_window,
            trend_window=rules.trend_window,
            trend_min_points=rules.trend_min_points,
            ratio_min=rules.ratio_min,
            ratio_max=rules.ratio_max,
            zero_neg_enabled=rules.zero_neg_enabled,
            missing_enabled=rules.missing_enabled,
            ratio_enabled=rules.ratio_enabled,
        ),
        auth={"type": source.auth.type, "user": source.auth.user},
        enabled=source.enabled,
        last_analysis=None,
    )


@router.get(
    "",
    response_model=DataSourceListResponse,
    summary="List data sources",
    description="Return all configured data sources (abbreviated view).",
)
async def list_sources() -> DataSourceListResponse:
    """List all data sources."""
    sources = data_source_repo.get_all()
    return DataSourceListResponse(
        sources=[DataSourceShortResponse(id=s.id, name=s.name, enabled=s.enabled) for s in sources]
    )


@router.post(
    "",
    response_model=DataSourceResponse,
    status_code=201,
    summary="Create data source",
    description="Create a new data source configuration.",
    responses={
        409: {"model": dict, "description": "A data source with this ID already exists"},
        422: {"model": dict, "description": "Validation error"},
    },
)
async def create_source(request: DataSourceCreateRequest) -> DataSourceResponse:
    """Create a new data source."""
    if data_source_repo.exists(request.id):
        raise HTTPException(
            status_code=409,
            detail={
                "error": "conflict",
                "message": f"Data source '{request.id}' already exists",
            },
        )

    source = DataSource(
        id=request.id,
        name=request.name,
        endpoint=request.endpoint,
        register_name=request.register_name,
        dimensions=request.dimensions,
        metric_fields=request.metric_fields,
        threshold_rules=ThresholdRules(**request.threshold_rules),
        auth=AuthConfig(**request.auth),
        enabled=request.enabled,
    )

    errors = source.validate_config()
    if errors:
        raise HTTPException(
            status_code=422,
            detail={"error": "validation_error", "message": "; ".join(errors)},
        )

    data_source_repo.save(source)
    return _source_to_response(source)


@router.put(
    "/{source_id}",
    response_model=DataSourceResponse,
    summary="Update data source",
    description="Update an existing data source configuration. Returns 404 if not found.",
    responses={
        404: {"model": dict, "description": "Data source not found"},
        422: {"model": dict, "description": "Validation error"},
    },
)
async def update_source(source_id: str, request: DataSourceUpdateRequest) -> DataSourceResponse:
    """Update an existing data source."""
    existing = data_source_repo.get_by_id(source_id)
    if not existing:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Data source '{source_id}' not found"},
        )

    updated = DataSource(
        id=source_id,
        name=request.name,
        endpoint=request.endpoint,
        register_name=request.register_name,
        dimensions=request.dimensions,
        metric_fields=request.metric_fields,
        threshold_rules=ThresholdRules(**request.threshold_rules),
        auth=AuthConfig(**request.auth),
        enabled=request.enabled,
        created_at=existing.created_at,
        updated_at=datetime.now(),
    )

    errors = updated.validate_config()
    if errors:
        raise HTTPException(
            status_code=422,
            detail={"error": "validation_error", "message": "; ".join(errors)},
        )

    data_source_repo.save(updated)
    return _source_to_response(updated)


@router.delete(
    "/{source_id}",
    status_code=204,
    summary="Delete data source",
    description="Delete a data source by ID. Returns 204 on success, 404 if not found.",
    responses={
        204: {"description": "Successfully deleted"},
        404: {"model": dict, "description": "Data source not found"},
    },
)
async def delete_source(source_id: str) -> Response:
    """Delete a data source by ID."""
    if not data_source_repo.exists(source_id):
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Data source '{source_id}' not found"},
        )
    data_source_repo.delete(source_id)
    return Response(status_code=204)


@router.post(
    "/{source_id}/test",
    response_model=TestConnectionResponse,
    summary="Test data source connection",
    description="Check whether the 1C HTTP endpoint for a data source is reachable.",
    responses={
        404: {"model": dict, "description": "Data source not found"},
    },
)
async def test_connection(source_id: str) -> TestConnectionResponse:
    """Test connectivity to the 1C endpoint for a data source."""
    source = data_source_repo.get_by_id(source_id)
    if not source:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Data source '{source_id}' not found"},
        )

    result = await _test_1c_connection(
        endpoint=source.endpoint,
        register_name=source.register_name,
        auth_type=source.auth.type,
        auth_user=source.auth.user,
        auth_password=source.auth.password,
    )
    return TestConnectionResponse(
        status=result["status"],
        message=result["message"],
        response_time_ms=result["response_time_ms"],
    )


@router.get(
    "/{source_id}/preview",
    response_model=dict,
    summary="Preview data source data",
    description="Fetch a small sample of raw register data from 1C (mock in Phase 2).",
    responses={
        404: {"model": dict, "description": "Data source not found"},
    },
)
async def preview_source(source_id: str, limit: int = 10) -> dict:
    """Preview raw data for a data source."""
    source = data_source_repo.get_by_id(source_id)
    if not source:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Data source '{source_id}' not found"},
        )

    # Phase 2: return empty mock preview
    return {
        "source_id": source_id,
        "register_name": source.register_name,
        "record_count": 0,
        "data": [],
    }
