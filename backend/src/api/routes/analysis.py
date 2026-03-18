"""Analysis routes - POST /api/v1/analysis/run."""

import time
from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.api.schemas import AnalysisRunRequest, AnalysisRunShortResponse
from src.domain.mock_detector import detect_anomalies_mock
from src.domain.models import AnalysisRun
from src.infrastructure.persistence.sqlite import (
    SQLiteAnalysisRunRepository,
    SQLiteAnomalyRepository,
    SQLiteDataSourceRepository,
)

router = APIRouter()

# Resolve DB path relative to the project root (backend/)
_DB_PATH = str(Path(__file__).parents[3] / "data" / "anomaly_detection.db")

analysis_run_repo = SQLiteAnalysisRunRepository(_DB_PATH)
anomaly_repo = SQLiteAnomalyRepository(_DB_PATH)
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
        422: {"model": dict, "description": "Validation error (missing fields or invalid date range)"},
    },
)
async def run_analysis(request: AnalysisRunRequest) -> AnalysisRunShortResponse:
    """Trigger anomaly analysis for a data source."""
    source = data_source_repo.get_by_id(request.source_id)
    if not source:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_source", "message": f"Source '{request.source_id}' not found"},
        )

    start_time = time.time()

    # Build AnalysisRun domain object
    run = AnalysisRun(
        source_id=request.source_id,
        date_from=request.date_from,
        date_to=request.date_to,
        triggered_by="user",
    )

    # Run mock detector (Phase 2 – no real 1C data fetching yet)
    anomalies = detect_anomalies_mock(
        data_points=[],
        threshold_rules=source.threshold_rules,
        source_id=request.source_id,
        run_id=run.id,
    )

    run.mark_completed(anomaly_count=len(anomalies))

    # Persist run and anomalies
    analysis_run_repo.create(run)
    if anomalies:
        anomaly_repo.save_batch(anomalies)

    duration_ms = int((time.time() - start_time) * 1000)

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
