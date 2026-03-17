"""Data sources routes - CRUD /api/v1/sources."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_sources():
    """List all data sources."""
    # TODO: Implement in Phase 4
    return {"sources": []}
