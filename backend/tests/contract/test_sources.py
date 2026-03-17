"""Contract tests for /api/v1/sources CRUD endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_get_sources_success(app):
    """Test successful sources list retrieval."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/sources")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert isinstance(data["sources"], list)


@pytest.mark.asyncio
async def test_get_sources_response_structure(app):
    """Test sources response has correct structure."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/sources")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    # If sources exist, verify structure
    if len(data["sources"]) > 0:
        source = data["sources"][0]
        assert "id" in source
        assert "name" in source
        assert "enabled" in source


@pytest.mark.asyncio
async def test_post_sources_success(app):
    """Test successful source creation."""
    source_data = {
        "id": "test_source_123",
        "name": "Test Source",
        "endpoint": "http://1c-server/base/hs/analytics/v1",
        "register_name": "TestRegister",
        "dimensions": ["Period", "Product"],
        "metric_fields": {"sum": "Sum", "qty": "Qty"},
        "threshold_rules": {"spike_pct": 20.0, "spike_zscore": 3.0},
        "enabled": True,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/sources", json=source_data)
    assert response.status_code in [200, 201, 409]  # 409 if already exists


@pytest.mark.asyncio
async def test_post_sources_duplicate(app):
    """Test source creation with duplicate ID."""
    source_data = {
        "id": "duplicate_source",
        "name": "Duplicate Source",
        "endpoint": "http://1c-server/base/hs/analytics/v1",
        "register_name": "TestRegister",
        "dimensions": ["Period"],
        "metric_fields": {"sum": "Sum", "qty": "Qty"},
        "enabled": True,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # First creation
        response1 = await ac.post("/api/v1/sources", json=source_data)
        # Second creation should fail
        response2 = await ac.post("/api/v1/sources", json=source_data)
    assert response1.status_code in [200, 201, 409]
    assert response2.status_code == 409  # Conflict


@pytest.mark.asyncio
async def test_post_sources_missing_fields(app):
    """Test source creation with missing required fields."""
    source_data = {
        "id": "incomplete_source",
        # Missing required fields
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/sources", json=source_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_put_sources_success(app):
    """
    Send a PUT to /api/v1/sources/update_test_source to update (or create) a source and assert the API responds with an expected status code.
    
    Asserts that the response status code is one of: 200 (updated), 201 (created), or 404 (not found).
    """
    source_data = {
        "id": "update_test_source",
        "name": "Updated Source Name",
        "endpoint": "http://1c-server/base/hs/analytics/v1",
        "register_name": "UpdatedRegister",
        "dimensions": ["Period", "Warehouse"],
        "metric_fields": {"sum": "Sum", "qty": "Qty"},
        "enabled": True,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.put("/api/v1/sources/update_test_source", json=source_data)
    # May return 200, 201 (if created), or 404 (if not found)
    assert response.status_code in [200, 201, 404]


@pytest.mark.asyncio
async def test_delete_sources_success(app):
    """Test successful source deletion."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.delete("/api/v1/sources/non_existent_source")
    # May return 204 (deleted) or 404 (not found)
    assert response.status_code in [204, 404]


@pytest.mark.asyncio
async def test_post_sources_test_connection(app):
    """
    Verify the source connection test endpoint returns a valid response for an existing or missing source.
    
    Acceptable responses are 200 or 404. If the response is 200, the JSON body must include a "status" key.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/sources/test_source/test")
    assert response.status_code in [200, 404]  # 200 if source exists, 404 otherwise
    if response.status_code == 200:
        data = response.json()
        assert "status" in data


@pytest.mark.asyncio
async def test_get_sources_preview(app):
    """Test source data preview endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/sources/test_source/preview")
    assert response.status_code in [200, 404]  # 200 if source exists, 404 otherwise
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list) or "data" in data
