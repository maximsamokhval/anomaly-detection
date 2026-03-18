# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands run from the `backend/` directory using **uv**.

```bash
# Install dependencies
uv sync --extra dev

# Run the application
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/contract/test_sources.py -v

# Type checking
uv run pyright src/      # fast, standard mode
uv run mypy src/         # strict mode

# Lint / format
uv run ruff check src/
uv run ruff format src/

# Initialize database
uv run python scripts/init_db.py
```

## Architecture

The project is a **Financial Anomaly Detection Service** — a FastAPI backend with Jinja2 server-rendered UI that detects anomalies in financial data from 1C accumulation registers.

### Layer Structure (`backend/src/`)

```
domain/           # Pure business logic — no DB, HTTP, or UI imports
  models.py       # Pydantic v2 domain entities (ThresholdRules, DataSource, AnalysisRun, Anomaly, DataPoint)
  detector.py     # Real anomaly detection: SPIKE, TREND_BREAK, ZERO_NEG, MISSING, MISSING_DATA, RATIO
  transformer.py  # Converts raw 1C rows → DataPoint (value = raw_sum / raw_qty, qty=0 guard)

api/              # HTTP interface
  middleware.py   # LoggingMiddleware: request/response timing via Loguru
  schemas.py      # OpenAPI request/response models (separate from domain models)
  routes/         # analysis.py, anomalies.py, sources.py, heatmap.py, timeseries.py

infrastructure/   # External adapters
  persistence/
    base.py       # Abstract repository interfaces (DataSourceRepository, AnomalyRepository, DataPointRepository)
    sqlite.py     # SQLite implementation with JSON serialization for nested fields
  http_client.py  # Real async httpx 1C client: fetch_1c_data (pagination), test_connection, BasicAuth
  mock_1c_adapter.py  # Retained for reference; no longer used in production code
  logging.py      # Loguru structured logging

ui/
  templates/      # Jinja2 HTML templates (dynamic, API-driven)
  static/         # CSS and JS assets

main.py           # FastAPI app, lifespan DB init, router registration, LoggingMiddleware
```

### Key Design Decisions

- **Clean Architecture**: Domain layer has zero dependencies on infrastructure/UI. Repository pattern abstracts all persistence.
- **Real detection**: `detector.py` implements all 6 anomaly types as pure functions (Constitution I — no I/O).
- **Analysis is synchronous**: `POST /api/v1/analysis/run` runs detection inline and returns when complete. No background tasks.
- **Computed metrics**: `DataPoint.value` is always `raw_sum / raw_qty`, computed at analysis time.
- **DB location**: Auto-created at `backend/data/anomaly_detection.db` on startup.
- **1C integration**: `http_client.py` auto-paginates using `has_next` from response. Falls back to 504 on timeout/connect error.
- **run_id propagation**: Dashboard stores `lastRunId` in localStorage; heatmap/table/drilldown read from URL `?run_id=` or localStorage.

### API Routes (prefix: `/api/v1/`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/analysis/run` | Trigger anomaly detection (calls real 1C HTTP client) |
| GET | `/analysis/{run_id}` | Get run status |
| GET | `/anomalies` | List anomalies — filters: run_id, type, period_from/to, dimension.{name}; sort_by, sort_order; page, page_size |
| GET/POST/PUT/DELETE | `/sources` | Data source CRUD |
| POST | `/sources/{id}/test` | Test 1C connection (real HTTP, returns status/message/response_time_ms) |
| GET | `/sources/{id}/preview` | Preview placeholder (stub) |
| GET | `/heatmap` | Heat map grid: rows × columns × cells with anomaly type + intensity |
| GET | `/timeseries` | Time series for one dimension combo with per-period anomaly markers |

UI pages served at: `/`, `/heatmap`, `/table`, `/drilldown`, `/sources`

### Testing

Contract tests use `httpx.AsyncClient` with ASGI transport — no external server needed. `tests/contract/conftest.py` patches `fetch_1c_data` with mock rows so tests run without a live 1C service. The test suite runs with `asyncio_mode = auto`.

Unit tests cover all 6 detector functions + transformer (57 tests, ~73% coverage).

### Implementation Status

All MVP phases complete (Phases 1–8):
- Real detector with all 6 anomaly types
- Real 1C HTTP client with auth + pagination
- Full SQLite persistence (DataSource, AnalysisRun, Anomaly, DataPoint)
- Dynamic UI: heatmap, drilldown (Chart.js), anomaly table (sortable, filterable, paginated)
- Request/response logging middleware
- Docker + docker-compose deployment
- 57 tests passing, 73% coverage

### Specifications

Detailed specs, API contracts, and phase plans live in `specs/001-anomaly-detection-mvp/`. The `contracts/api.md` is the authoritative API specification.
