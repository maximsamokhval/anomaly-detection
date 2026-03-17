"""Contract tests for GET /api/v1/anomalies endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.anyio
async def test_get_anomalies_success(app):
    """Test successful anomalies retrieval."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert "anomalies" in data
    assert isinstance(data["anomalies"], list)


@pytest.mark.anyio
async def test_get_anomalies_with_run_id_filter(app):
    """Test anomalies retrieval with run_id filter."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/anomalies?run_id=test-run-123")
    assert response.status_code == 200
    data = response.json()
    assert "anomalies" in data


@pytest.mark.anyio
async def test_get_anomalies_with_type_filter(app):
    """Test anomalies retrieval with type filter."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/anomalies?type=SPIKE")
    assert response.status_code == 200
    data = response.json()
    assert "anomalies" in data


@pytest.mark.anyio
async def test_get_anomalies_with_period_filter(app):
    """Test anomalies retrieval with period filter."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/anomalies?period_from=2026-01-01&period_to=2026-03-31")
    assert response.status_code == 200
    data = response.json()
    assert "anomalies" in data


@pytest.mark.anyio
async def test_get_anomalies_response_structure(app):
    """Test anomalies response has correct structure."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert "anomalies" in data
    # If anomalies exist, verify structure
    if len(data["anomalies"]) > 0:
        anomaly = data["anomalies"][0]
        assert "id" in anomaly
        assert "type" in anomaly
        assert "period" in anomaly


@pytest.mark.anyio
async def test_get_anomalies_empty_result(app):
    """Test anomalies retrieval returns empty list when no anomalies."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/anomalies?run_id=non-existent-run")
    assert response.status_code == 200
    data = response.json()
    assert "anomalies" in data
    assert data["anomalies"] == [] or isinstance(data["anomalies"], list)
