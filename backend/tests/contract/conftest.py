"""Pytest fixtures for contract tests."""

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
def client():
    """
    Create a TestClient bound to the FastAPI app for synchronous tests.
    
    Returns:
        test_client (TestClient): A test client instance configured for the application; yielded for use in tests.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client():
    """
    Provide an AsyncClient connected to the FastAPI app for asynchronous tests.
    
    Returns:
        AsyncClient: An httpx AsyncClient using ASGITransport bound to the test app with base_url "http://test".
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def app():
    """
    Provide the FastAPI application instance for tests.
    
    Returns:
        FastAPI: The application instance used by test fixtures.
    """
    return app
