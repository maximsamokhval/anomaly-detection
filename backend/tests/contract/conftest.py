"""Pytest fixtures for contract tests."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from src.domain.models import AuthConfig, DataSource, ThresholdRules
from src.infrastructure.persistence.sqlite import SQLiteDataSourceRepository
from src.main import app as fastapi_app

_DB_PATH = "data/anomaly_detection.db"

# Minimal mock rows matching the test_source metric fields (AmountTurnover, QuantityTurnover)
_MOCK_ROWS = [
    {"Период": "2026-01-31", "Product": "A", "AmountTurnover": 100.0, "QuantityTurnover": 2.0},
    {"Период": "2026-02-28", "Product": "A", "AmountTurnover": 300.0, "QuantityTurnover": 2.0},
    {"Период": "2026-03-31", "Product": "A", "AmountTurnover": 110.0, "QuantityTurnover": 2.0},
]


@pytest.fixture(autouse=True)
def mock_1c_http_client():
    """Patch real 1C HTTP client so contract tests don't need a live 1C service."""
    with patch(
        "src.api.routes.analysis.fetch_1c_data",
        new=AsyncMock(return_value=_MOCK_ROWS),
    ):
        yield


@pytest.fixture(autouse=True, scope="session")
def seed_test_source() -> None:
    """Ensure a 'test_source' data source exists for analysis contract tests."""
    repo = SQLiteDataSourceRepository(_DB_PATH)
    if not repo.exists("test_source"):
        source = DataSource(
            id="test_source",
            name="Test Source",
            endpoint="http://localhost/hs/analytics/v1",
            register_name="TestRegister",
            dimensions=["Period", "Product"],
            metric_fields={"sum": "AmountTurnover", "qty": "QuantityTurnover"},
            threshold_rules=ThresholdRules(),
            auth=AuthConfig(),
        )
        repo.save(source)


@pytest.fixture
def client():
    """Create test client for synchronous tests."""
    with TestClient(fastapi_app) as test_client:
        yield test_client


@pytest.fixture
async def async_client():
    """Create async client for asynchronous tests."""
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def app():
    """Provide the FastAPI app for testing."""
    return fastapi_app
