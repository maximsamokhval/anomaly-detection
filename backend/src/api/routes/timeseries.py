"""Time series routes - GET /api/v1/timeseries."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_timeseries():
    """Get time series data for drill-down."""
    # TODO: Implement in Phase 4
    return {"dimensions": {}, "data": []}
