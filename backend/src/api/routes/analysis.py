"""Analysis routes - POST /api/v1/analysis/run."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/run")
async def run_analysis():
    """Trigger anomaly analysis."""
    # TODO: Implement in Phase 4
    return {"analysis_id": "mock-id", "status": "completed", "anomaly_count": 0}
