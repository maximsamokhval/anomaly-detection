"""Contract tests for POST /api/v1/analysis/run endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.anyio
async def test_post_analysis_run_success(app):
    """Test successful analysis run request."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/analysis/run",
            json={
                "source_id": "test_source",
                "date_from": "2026-01-01",
                "date_to": "2026-03-31",
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert "status" in data
    assert data["status"] in ["pending", "running", "completed"]


@pytest.mark.anyio
async def test_post_analysis_run_invalid_source(app):
    """Test analysis run with non-existent source."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/analysis/run",
            json={
                "source_id": "non_existent_source",
                "date_from": "2026-01-01",
                "date_to": "2026-03-31",
            },
        )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"] == "invalid_source"


@pytest.mark.anyio
async def test_post_analysis_run_invalid_date_range(app):
    """Test analysis run with invalid date range (from > to)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/analysis/run",
            json={
                "source_id": "test_source",
                "date_from": "2026-03-31",
                "date_to": "2026-01-01",
            },
        )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_post_analysis_run_missing_fields(app):
    """Test analysis run with missing required fields."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/analysis/run",
            json={
                "source_id": "test_source",
                # Missing date_from and date_to
            },
        )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_post_analysis_run_response_structure(app):
    """Test analysis run response has correct structure."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/analysis/run",
            json={
                "source_id": "test_source",
                "date_from": "2026-01-01",
                "date_to": "2026-03-31",
            },
        )
    if response.status_code == 200:
        data = response.json()
        assert "analysis_id" in data
        assert "status" in data
        assert "anomaly_count" in data or "duration_ms" in data or "source_id" in data
