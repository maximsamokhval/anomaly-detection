"""Analysis routes - POST /api/v1/analysis/run."""

import time
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException
from loguru import logger

from src.api.schemas import AnalysisRunRequest, AnalysisRunShortResponse
from src.domain.detector import detect_anomalies
from src.domain.models import AnalysisRun
from src.domain.transformer import transform_raw_data
from src.infrastructure.http_client import fetch_1c_data
from src.infrastructure.persistence.sqlite import (
    SQLiteAnalysisRunRepository,
    SQLiteAnomalyRepository,
    SQLiteDataPointRepository,
    SQLiteDataSourceRepository,
)

router = APIRouter()

# Resolve DB path relative to the project root (backend/)
_DB_PATH = str(Path(__file__).parents[3] / "data" / "anomaly_detection.db")

analysis_run_repo = SQLiteAnalysisRunRepository(_DB_PATH)
anomaly_repo = SQLiteAnomalyRepository(_DB_PATH)
data_point_repo = SQLiteDataPointRepository(_DB_PATH)
data_source_repo = SQLiteDataSourceRepository(_DB_PATH)


@router.post(
    "/run",
    response_model=AnalysisRunShortResponse,
    summary="Trigger anomaly analysis",
    description=(
        "Run anomaly detection for the specified data source and date range. "
        "Returns immediately with the analysis result (synchronous execution)."
    ),
    responses={
        400: {"model": dict, "description": "Data source not found"},
        422: {
            "model": dict,
            "description": "Validation error (missing fields or invalid date range)",
        },
    },
)
async def run_analysis(request: AnalysisRunRequest) -> AnalysisRunShortResponse:
    """Trigger anomaly analysis for a data source."""
    source = data_source_repo.get_by_id(request.source_id)
    if not source:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_source",
                "message": f"Source '{request.source_id}' not found",
            },
        )

    start_time = time.time()

    # Build AnalysisRun domain object
    run = AnalysisRun(
        source_id=request.source_id,
        date_from=request.date_from,
        date_to=request.date_to,
        triggered_by="user",
    )

    logger.info(
        "[{rid}] Analysis start | source={src} | register={reg} | endpoint={ep} | {dfrom} → {dto} | auth={auth}",
        rid=run.id[:8],
        src=source.id,
        reg=source.register_name,
        ep=source.endpoint,
        dfrom=request.date_from,
        dto=request.date_to,
        auth=source.auth.type,
    )

    # Fetch raw data from 1C HTTP service
    try:
        raw_rows = await fetch_1c_data(
            endpoint=source.endpoint,
            register_name=source.register_name,
            date_from=request.date_from,
            date_to=request.date_to,
            auth_type=source.auth.type,
            auth_user=source.auth.user,
            auth_password=source.auth.password,
        )
    except httpx.HTTPStatusError as exc:
        logger.error(
            "[{rid}] 1C HTTP error {status} | url={url} | body={body}",
            rid=run.id[:8],
            status=exc.response.status_code,
            url=str(exc.request.url),
            body=exc.response.text[:500],
        )
        raise HTTPException(
            status_code=502,
            detail={
                "error": "upstream_error",
                "message": f"1C service returned HTTP {exc.response.status_code}",
            },
        ) from exc
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        logger.error("[{rid}] 1C unavailable | {exc}", rid=run.id[:8], exc=exc)
        raise HTTPException(
            status_code=504,
            detail={
                "error": "upstream_unavailable",
                "message": f"1C service unavailable: {exc}",
            },
        ) from exc

    logger.debug("[{rid}] 1C raw rows={n} | metric_fields={mf} | dimensions={dims}",
        rid=run.id[:8],
        n=len(raw_rows),
        mf=source.metric_fields,
        dims=source.dimensions,
    )
    if raw_rows:
        logger.debug("[{rid}] First row sample: {row}", rid=run.id[:8], row=raw_rows[0])

    # Transform raw rows into DataPoints (computes value = sum / qty)
    data_points = transform_raw_data(raw_rows, source, run_id=run.id)
    logger.debug("[{rid}] data_points={n}", rid=run.id[:8], n=len(data_points))

    # Detect anomalies using real detector with source threshold rules
    anomalies = detect_anomalies(
        data_points=data_points,
        threshold_rules=source.threshold_rules,
        source_id=request.source_id,
        run_id=run.id,
        date_from=request.date_from,
        date_to=request.date_to,
    )
    logger.info("[{rid}] anomalies={n}", rid=run.id[:8], n=len(anomalies))

    run.mark_completed(anomaly_count=len(anomalies))

    # Persist run, data points, and anomalies (FR-013: both raw data and results)
    analysis_run_repo.create(run)
    if data_points:
        data_point_repo.save_batch(data_points)
    if anomalies:
        anomaly_repo.save_batch(anomalies)

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("[{rid}] Analysis done | {ms}ms | anomalies={n}", rid=run.id[:8], ms=duration_ms, n=len(anomalies))

    return AnalysisRunShortResponse(
        analysis_id=run.id,
        status=run.status,
        anomaly_count=run.anomaly_count,
        duration_ms=duration_ms,
    )


@router.get(
    "/{run_id}",
    response_model=dict,
    summary="Get analysis run details",
    description="Retrieve the status and results of an analysis run by its UUID.",
    responses={
        404: {"model": dict, "description": "Analysis run not found"},
    },
)
async def get_analysis_run(run_id: str) -> dict:
    """Get analysis run by ID."""
    run = analysis_run_repo.get_by_id(run_id)
    if not run:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Analysis run '{run_id}' not found"},
        )

    return {
        "id": run.id,
        "source_id": run.source_id,
        "date_from": run.date_from.isoformat(),
        "date_to": run.date_to.isoformat(),
        "status": run.status,
        "anomaly_count": run.anomaly_count,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }
