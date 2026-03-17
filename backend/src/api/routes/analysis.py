"""Analysis routes - POST /api/v1/analysis/run."""

import time
from datetime import date, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from domain.mock_detector import detect_anomalies_mock
from domain.models import ThresholdRules
from infrastructure.persistence.sqlite import (
    SQLiteAnalysisRunRepository,
    SQLiteAnomalyRepository,
    SQLiteDataSourceRepository,
)

router = APIRouter()

# Initialize repositories
db_path = "backend/data/anomaly_detection.db"
analysis_run_repo = SQLiteAnalysisRunRepository(db_path)
anomaly_repo = SQLiteAnomalyRepository(db_path)
data_source_repo = SQLiteDataSourceRepository(db_path)


@router.post("/run")
async def run_analysis(request: dict) -> dict:
    """Trigger anomaly analysis for a data source.

    Args:
        request: JSON body with source_id, date_from, date_to

    Returns:
        Analysis run result with analysis_id, status, anomaly_count

    Raises:
        HTTPException: 400 if source not found
    """
    source_id = request.get("source_id")
    date_from = request.get("date_from")
    date_to = request.get("date_to")

    # Validate required fields
    if not source_id or not date_from or not date_to:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "missing_fields",
                "message": "source_id, date_from, and date_to are required",
            },
        )

    # Check if source exists
    try:
        source = data_source_repo.get_by_id(source_id)
    except Exception:
        source = None

    if not source:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_source", "message": f"Source '{source_id}' not found"},
        )

    # Create analysis run
    run_id = str(uuid4())
    start_time = time.time()

    # Create mock threshold rules if not configured
    threshold_rules = ThresholdRules(
        spike_pct=source.threshold_rules.get("spike_pct", 20.0) if source.threshold_rules else 20.0,
        spike_zscore=source.threshold_rules.get("spike_zscore", 3.0)
        if source.threshold_rules
        else 3.0,
        spike_logic=source.threshold_rules.get("spike_logic", "OR")
        if source.threshold_rules
        else "OR",
        moving_avg_window=source.threshold_rules.get("moving_avg_window", 6)
        if source.threshold_rules
        else 6,
        trend_window=source.threshold_rules.get("trend_window", 3) if source.threshold_rules else 3,
        zero_neg_enabled=source.threshold_rules.get("zero_neg_enabled", True)
        if source.threshold_rules
        else True,
        missing_enabled=source.threshold_rules.get("missing_enabled", True)
        if source.threshold_rules
        else True,
        ratio_enabled=source.threshold_rules.get("ratio_enabled", False)
        if source.threshold_rules
        else False,
        ratio_min=None,
        ratio_max=None,
    )

    # Run mock detector (Phase 2 - no real data fetching yet)
    mock_data_points = []  # Will be populated with real data in Phase 4
    anomalies = detect_anomalies_mock(
        data_points=mock_data_points,
        threshold_rules=threshold_rules,
        source_id=source_id,
        run_id=run_id,
    )

    # Save analysis run
    duration_ms = int((time.time() - start_time) * 1000)
    analysis_run_repo.create(
        id=run_id,
        source_id=source_id,
        date_from=date_from,
        date_to=date_to,
        triggered_by="user",
        status="completed",
        anomaly_count=len(anomalies),
        error_message=None,
    )

    # Save anomalies
    for anomaly in anomalies:
        anomaly_repo.create(anomaly)

    return {
        "analysis_id": run_id,
        "status": "completed",
        "anomaly_count": len(anomalies),
        "duration_ms": duration_ms,
        "source_id": source_id,
    }


@router.get("/{run_id}")
async def get_analysis_run(run_id: str) -> dict:
    """Get analysis run by ID.

    Args:
        run_id: Analysis run identifier

    Returns:
        Analysis run details

    Raises:
        HTTPException: 404 if run not found
    """
    try:
        run = analysis_run_repo.get_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Analysis run not found")

        return {
            "id": run.id,
            "source_id": run.source_id,
            "date_from": run.date_from.isoformat()
            if isinstance(run.date_from, (date, datetime))
            else run.date_from,
            "date_to": run.date_to.isoformat()
            if isinstance(run.date_to, (date, datetime))
            else run.date_to,
            "status": run.status,
            "anomaly_count": run.anomaly_count,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
