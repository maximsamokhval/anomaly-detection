# qwen_dq Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-17

## Active Technologies

- ✅ Python 3.12 + FastAPI
- ✅ uv venv + uv sync
- ✅ ruff + mypy + pytest
- ✅ pytest-cov for coverage
- ✅ loguru for logging in debug mode
- ✅ pytest-asyncio for async tests
- ✅ Jinja2 + Chart.js for frontend
- ✅ SQLite for MVP
- ✅ Manual trigger only
- ✅ Heat map as primary UI

**Development Workflow Compliance**:
- ✅ Detector unit tests mandatory
- ✅ API contract tests mandatory
- ✅ Manual UI testing for MVP

**GATE RESULT**: ✅ ALL PASS - Proceed to Phase 0

## Project Structure

### Source Code (repository root)

```text
backend/
├── src/
│   ├── domain/                  # Pure business logic (Constitution I, III)
│   │   ├── detector.py          # Anomaly detection engine (pure functions)
│   │   ├── transformer.py       # DataPoint computation (Sum/Qty)
│   │   └── models.py            # Domain entities (DataSource, Anomaly, etc.)
│   ├── infrastructure/          # External concerns (Constitution V)
│   │   ├── persistence/
│   │   │   ├── base.py          # RepositoryBase interface
│   │   │   └── sqlite.py        # SQLite implementations
│   │   ├── http_client.py       # 1C HTTP client
│   │   └── config.py            # App configuration
│   ├── api/                     # FastAPI routes (Constitution VI)
│   │   ├── routes/
│   │   │   ├── analysis.py      # POST /api/v1/analysis/run
│   │   │   ├── sources.py       # CRUD /api/v1/sources
│   │   │   └── anomalies.py     # GET /api/v1/anomalies
│   │   └── schemas.py           # Pydantic request/response models
│   └── ui/                      # Jinja2 templates (Constitution VI)
│       ├── templates/
│       │   ├── dashboard.html   # Screen 1: Dashboard
│       │   ├── heatmap.html     # Screen 2: Heat Map
│       │   ├── table.html       # Screen 3: Anomaly Table
│       │   ├── drilldown.html   # Screen 4: Drill-down
│       │   └── sources.html     # Screen 6: Source Configurator
│       └── static/
│           └── chart.js         # Chart.js library
└── tests/
    ├── unit/
    │   ├── test_detector.py     # Detector purity tests
    │   └── test_transformer.py  # Guard clause tests
    ├── contract/
    │   └── test_api.py          # API contract tests
    └── integration/
        └── test_sqlite.py       # Repository tests

frontend/
# Note: Frontend is server-rendered via Jinja2 in backend/ui/templates/
# No separate frontend project needed (constitution: SSR without extra deps)

docker-compose.yml                 # Docker Compose deployment
Dockerfile.backend                 # Backend container
```

**Structure Decision**: Single backend project with server-rendered frontend (Jinja2). No separate frontend project - aligns with constitution "SSR without extra dependencies" rationale.

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.12 (constitution-mandated team standard): Follow standard conventions

## Recent Changes

- 001-anomaly-detection-mvp: Added Python 3.12 (constitution-mandated team standard)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
