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
    """
    Return anomalies optionally filtered by run_id and anomaly_type.
    
    Parameters:
        run_id (str | None): If provided, only anomalies from the specified analysis run are returned.
        anomaly_type (str | None): If provided, only anomalies whose `anomaly_type` equals this value are included.
        period_from (str | None): Accepted but not applied to filtering.
        period_to (str | None): Accepted but not applied to filtering.
    
    Returns:
        dict: A dictionary with key "anomalies" mapping to a list of serialized anomaly objects. Each anomaly object contains:
            - id
            - run_id
            - source_id
            - dimensions
            - period (ISO-formatted string when possible)
            - anomaly_type
            - current_value
            - previous_value
            - pct_change
            - zscore
            - threshold_triggered
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
