"""Pytest fixtures for contract tests."""

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
def client():
    """Create test client for synchronous tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client():
    """Create async client for asynchronous tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def app():
    """Provide the FastAPI app for testing."""
    return app
