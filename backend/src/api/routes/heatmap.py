"""Heat map routes - GET /api/v1/heatmap."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_heatmap():
    """Get heat map data."""
    # TODO: Implement in Phase 4
    return {"rows": [], "columns": [], "cells": []}
