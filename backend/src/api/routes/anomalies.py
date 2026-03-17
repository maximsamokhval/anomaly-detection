"""Anomalies routes - GET /api/v1/anomalies."""

from fastapi import APIRouter

from infrastructure.persistence.sqlite import SQLiteAnomalyRepository

router = APIRouter()

# Initialize repository
db_path = "backend/data/anomaly_detection.db"
anomaly_repo = SQLiteAnomalyRepository(db_path)


@router.get("")
async def get_anomalies(
    run_id: str | None = None,
    anomaly_type: str | None = None,
    period_from: str | None = None,
    period_to: str | None = None,
) -> dict:
    """Get anomalies with optional filtering.

    Args:
        run_id: Filter by analysis run ID
        anomaly_type: Filter by anomaly type (SPIKE, ZERO_NEG, etc.)
        period_from: Filter by period start date
        period_to: Filter by period end date

    Returns:
        List of anomalies matching filters
    """
    # Get all anomalies from repository
    if run_id:
        anomalies = anomaly_repo.get_by_run_id(run_id)
    else:
        # For now, get all anomalies (last run)
        anomalies = anomaly_repo.get_all()

    # Apply additional filters
    if anomaly_type:
        anomalies = [a for a in anomalies if a.anomaly_type == anomaly_type]

    # Convert to response format
    return {
        "anomalies": [
            {
                "id": a.id,
                "run_id": a.run_id,
                "source_id": a.source_id,
                "dimensions": a.dimensions,
                "period": a.period.isoformat() if hasattr(a.period, "isoformat") else str(a.period),
                "anomaly_type": a.anomaly_type,
                "current_value": a.current_value,
                "previous_value": a.previous_value,
                "pct_change": a.pct_change,
                "zscore": a.zscore,
                "threshold_triggered": a.threshold_triggered,
            }
            for a in anomalies
        ]
    }
