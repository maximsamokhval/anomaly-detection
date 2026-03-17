"""Anomalies routes - GET /api/v1/anomalies."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_anomalies():
    """Get anomalies with filtering."""
    # TODO: Implement in Phase 4
    return {"anomalies": []}
