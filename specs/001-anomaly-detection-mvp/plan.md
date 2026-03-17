# Implementation Plan: Financial Anomaly Detection Service MVP

**Branch**: `001-anomaly-detection-mvp` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification for Financial Anomaly Detection Service

---

## Summary

**Primary Requirement**: Build an internal tool for financial analysts to manually trigger anomaly detection on 1C register data and visualize results via heat map and drill-down views.

**Technical Approach**: Walking skeleton delivery - each phase produces a runnable, demonstrable UI increment:
1. Phase 1: Static UI with mock data → clickable prototype
2. Phase 2: Real API with mock detector → live data flow
3. Phase 3: Full detector → end-to-end anomaly detection

---

## Technical Context

**Language/Version**: Python 3.12 (constitution-mandated team standard)

**Primary Dependencies**: 
- Backend: FastAPI (API framework)
- Frontend: Jinja2 + Chart.js (SSR templates)
- Database: SQLite (MVP), pandas + scipy (analytics)
- HTTP Client: httpx (async 1C requests)

**Storage**: SQLite for DataSource configs, AnalysisRun history, Anomaly results

**Testing**: pytest (unit), httpx.AsyncClient (API contract tests)

**Target Platform**: Linux server (Docker Compose on-premise)

**Project Type**: Web application (backend API + server-rendered frontend)

**Performance Goals**: 
- Analysis execution: <30 seconds per register (up to 100 dimension combinations)
- UI render time: <2 seconds for heat map load

**Constraints**: 
- No authentication in MVP (internal network)
- Synchronous analysis only (no background jobs)
- Single manual trigger endpoint

**Scale/Scope**: 
- MVP: 1-2 registers, 100 combinations max
- Target: 10-15 registers

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| **I. Detector Purity** | Detector has no DB/HTTP/UI dependencies | ✅ PASS (planned as pure functions) |
| **II. Manual Trigger Only** | No cron/scheduler in MVP | ✅ PASS (only `POST /api/v1/analysis/run`) |
| **III. Computed Metrics** | Sum/Qty computed at analysis time | ✅ PASS (Transformer layer) |
| **IV. DataSource as Config** | Registers added via UI, not code | ✅ PASS (DataSource entity + CRUD) |
| **V. Repository Pattern** | Abstract persistence layer | ✅ PASS (RepositoryBase interface) |
| **VI. Observability via Text I/O** | JSON APIs, structured logs | ✅ PASS (JSON responses, error schemas) |

**Architecture Standards Compliance**:
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

---

## Project Structure

### Documentation (this feature)

```text
specs/001-anomaly-detection-mvp/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── api.md           # API endpoint contracts
│   └── 1c-http.md       # 1C HTTP service contract
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

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

---

## Walking Skeleton Delivery Strategy

**Goal**: Each phase produces a runnable, demonstrable UI that users can interact with.

### Phase 1: Static UI Skeleton (Mock Data)

**Deliverable**: Fully clickable UI with hardcoded mock data

**What works**:
- Dashboard screen with static source list
- Heat map renders with sample anomaly data
- Click heat map cell → navigate to drill-down
- Drill-down shows Chart.js time series with mock data
- Anomaly table with static rows, filters, sorting
- Source configurator form (saves to in-memory list, not DB)

**What doesn't work**:
- No real API calls (data is hardcoded in templates)
- No database persistence
- No 1C integration
- No anomaly detection

**User Demo**: "This is how the UI will look and behave. Click through screens."

---

### Phase 2: Live API Skeleton (Mock Detector)

**Deliverable**: Real API + database, detector returns mock anomalies

**What works**:
- Dashboard loads sources from SQLite database
- "Run Analysis" button → `POST /api/v1/analysis/run` → real API call
- API fetches mock data (hardcoded in API layer), calls mock detector
- Mock detector returns pre-canned anomalies (no real algorithm)
- Results persisted to SQLite
- Heat map renders from real API response
- Source configurator saves to database, test connection returns mock status

**What doesn't work**:
- No real 1C HTTP integration (mock data only)
- No real anomaly detection (returns fixed anomalies)
- No real threshold logic

**User Demo**: "The system now connects to a real backend. Data is still simulated, but the flow is end-to-end."

---

### Phase 3: Full Detector (Real Algorithms)

**Deliverable**: Complete anomaly detection engine

**What works**:
- Real detector implements all 6 anomaly types
- SPIKE: % change + z-score logic
- TREND_BREAK: trend reversal detection
- ZERO_NEG: zero/negative value detection
- MISSING: missing period detection
- RATIO: out-of-range ratio (disabled by default)
- MISSING_DATA: division by zero guard

**What doesn't work**:
- No real 1C integration (still mock data)
- Post-MVP features: scheduling, notifications, YouTrack integration

**User Demo**: "Full anomaly detection is live. Upload real data to test."

---

### Phase 4: 1C Integration (Real Data)

**Deliverable**: HTTP client integration with 1C service

**What works**:
- Real `GET /hs/analytics/v1/data` calls to 1C
- Pagination handling
- Error handling (401, 404, 500)
- Test connection validates real 1C endpoint

**Prerequisites**: 1C HTTP service developed in parallel

**User Demo**: "End-to-end with real 1C data."

---

## Complexity Tracking

> **No violations** - All constitution principles followed.

---

## Phase 0: Research & Technical Decisions

**Purpose**: Resolve all technical unknowns before design.

### Research Tasks

1. **FastAPI + Jinja2 SSR Pattern**
   - Research: Best practices for server-rendered HTML with FastAPI
   - Decision: Use `Jinja2Templates` with `TemplateResponse`, static files via `StaticFiles`
   - Rationale: Constitution-mandated, team standard

2. **Chart.js Integration Pattern**
   - Research: How to embed Chart.js in Jinja2 templates with dynamic data
   - Decision: Pass chart data as JSON in template context, render via inline `<script>`
   - Rationale: No build step, SSR-friendly

3. **SQLite Schema Design for Anomaly Storage**
   - Research: Optimal schema for storing multi-dimensional anomaly data
   - Decision: Separate tables for `DataSource`, `AnalysisRun`, `Anomaly`; JSON for dimension values
   - Rationale: Flexibility for varying dimension counts, query performance acceptable for MVP scale

4. **Pure Detector Architecture Pattern**
   - Research: How to structure pure detector with no external dependencies
   - Decision: Detector accepts `List[DataPoint]`, returns `List[Anomaly]`; threshold rules passed as dataclass
   - Rationale**: Constitution Principle I (Detector Purity)

5. **1C HTTP Service Contract**
   - Research: Confirm JSON schema, field names (Cyrillic), pagination format
   - Decision**: Use BRD-specified schema with Cyrillic field names, pagination via `page`/`page_size`
   - Rationale: Matches 1C metadata naming conventions

**Output**: `research.md` with all decisions documented

---

## Phase 1: Design & Contracts

**Prerequisites**: `research.md` complete

### 1. Data Model (`data-model.md`)

**Entities** (from spec Key Entities):

**DataSource**:
- `id: str` (unique identifier, user-provided slug)
- `name: str` (display name)
- `endpoint: str` (base URL, e.g., `http://1c-server/hs/analytics/v1`)
- `register_name: str` (1C register name)
- `dimensions: list[str]` (e.g., `["Период", "Номенклатура", "Склад"]`)
- `metric_fields: dict` (`{"sum": "Сумма", "qty": "Количество"}`)
- `threshold_rules: dict` (spike_pct, spike_zscore, etc.)
- `auth: dict` (`{"type": "basic", "user": "...", "pass": "..."}`)
- `enabled: bool`

**AnalysisRun**:
- `id: str` (UUID)
- `source_id: str` (FK to DataSource)
- `date_from: date`, `date_to: date`
- `triggered_by: str` ("user" in MVP)
- `started_at: datetime`, `completed_at: datetime | null`
- `status: str` (pending | running | completed | failed)
- `anomaly_count: int`
- `error_message: str | null`

**DataPoint** (optional persistence):
- `run_id: str` (FK to AnalysisRun)
- `source_id: str`
- `dimensions: dict[str, str]` (JSON: `{"Номенклатура": "Продукт А", ...}`)
- `period: date`
- `value: float` (computed: sum/qty)
- `raw_sum: float`, `raw_qty: float`

**Anomaly**:
- `id: str` (UUID)
- `run_id: str` (FK to AnalysisRun)
- `source_id: str`
- `dimensions: dict[str, str]` (JSON)
- `period: date`
- `anomaly_type: str` (SPIKE | TREND_BREAK | ZERO_NEG | MISSING | RATIO | MISSING_DATA)
- `current_value: float | null`
- `previous_value: float | null`
- `pct_change: float | null`
- `zscore: float | null`
- `threshold_triggered: dict` (JSON: which rules fired)

**Validation Rules**:
- DataSource: `register_name` required, `dimensions` non-empty, `metric_fields` has both sum/qty
- AnalysisRun: `date_from <= date_to`
- Anomaly: `anomaly_type` in allowed set

---

### 2. API Contracts (`contracts/api.md`)

**Endpoints** (from spec):

```markdown
# API Contract: Financial Anomaly Detection Service

## Analysis

### POST /api/v1/analysis/run
**Request**:
```json
{
  "source_id": "reg_cost_price",
  "date_from": "2026-01-01",
  "date_to": "2026-03-31"
}
```

**Response (200 OK)**:
```json
{
  "analysis_id": "uuid",
  "status": "completed",
  "anomaly_count": 5,
  "duration_ms": 1234
}
```

**Response (400 Bad Request)**:
```json
{
  "error": "invalid_source",
  "message": "Source 'reg_cost_price' not found"
}
```

### GET /api/v1/analysis/{id}
**Response (200 OK)**:
```json
{
  "id": "uuid",
  "source_id": "reg_cost_price",
  "date_from": "2026-01-01",
  "date_to": "2026-03-31",
  "status": "completed",
  "anomaly_count": 5,
  "started_at": "2026-03-17T10:00:00Z",
  "completed_at": "2026-03-17T10:00:05Z"
}
```

## Anomalies

### GET /api/v1/anomalies
**Query Params**: `run_id`, `type`, `period`, dimension filters

**Response (200 OK)**:
```json
{
  "anomalies": [
    {
      "id": "uuid",
      "type": "SPIKE",
      "dimensions": {"Номенклатура": "Продукт А", "Склад": "Центральный"},
      "period": "2026-02-28",
      "current_value": 3100.0,
      "previous_value": 1250.0,
      "pct_change": 148.0,
      "zscore": 3.5
    }
  ]
}
```

## Data Sources

### GET /api/v1/sources
**Response (200 OK)**:
```json
{
  "sources": [
    {
      "id": "reg_cost_price",
      "name": "Себестоимость производства",
      "enabled": true
    }
  ]
}
```

### POST /api/v1/sources
**Request**: Full DataSource object (see data-model.md)

### PUT /api/v1/sources/{id}
**Request**: Full DataSource object (update)

### DELETE /api/v1/sources/{id}
**Response (204 No Content)**

### POST /api/v1/sources/{id}/test
**Response (200 OK)**:
```json
{
  "status": "ok",
  "message": "Connection successful"
}
```

### GET /api/v1/sources/{id}/preview
**Query Params**: `date_from`, `date_to`
**Response (200 OK)**: Raw data table (JSON array of objects)

## Heat Map

### GET /api/v1/heatmap
**Query Params**: `run_id`

**Response (200 OK)**:
```json
{
  "rows": [
    {"Номенклатура": "Продукт А", "Склад": "Центральный", "Организация": "ООО Компания"}
  ],
  "columns": ["2026-01-31", "2026-02-28", "2026-03-31"],
  "cells": [
    {"row_idx": 0, "col_idx": 1, "type": "SPIKE", "intensity": 0.8}
  ]
}
```

## Time Series

### GET /api/v1/timeseries
**Query Params**: `run_id`, dimension filters (e.g., `Номенклатура=Продукт А`)

**Response (200 OK)**:
```json
{
  "dimensions": {"Номенклатура": "Продукт А", "Склад": "Центральный"},
  "data": [
    {"period": "2026-01-31", "value": 1250.0, "anomaly_type": null},
    {"period": "2026-02-28", "value": 3100.0, "anomaly_type": "SPIKE"}
  ]
}
```
```

---

### 3. 1C HTTP Service Contract (`contracts/1c-http.md`)

**See BRD Section 7** - HTTP service specification copied here for reference.

**Key Points**:
- Endpoint: `GET /hs/analytics/v1/data`
- Required params: `register_name`, `date_from`, `date_to`
- Optional: `dimensions`, `organization`, `warehouse`, `page`, `page_size`
- Auth: Basic Auth (optional in MVP)
- Response: JSON with Cyrillic field names matching 1C metadata

---

### 4. Quickstart (`quickstart.md`)

```markdown
# Quickstart: Financial Anomaly Detection Service

## Prerequisites
- Docker + Docker Compose
- Access to 1C HTTP service (for Phase 4)

## Local Development

### 1. Start the service
```bash
docker-compose up --build
```

### 2. Open the UI
Navigate to `http://localhost:8000`

### 3. Configure a data source
1. Go to "Sources" screen
2. Click "Add Source"
3. Fill in:
   - Name: "ПартииТоваровНаСкладахПоПроизводителям"
   - Endpoint: `http://1c-server/base/hs/analytics/v1`
   - Register Name: `ПартииТоваровНаСкладахПоПроизводителям`
   - Dimensions: `Период`, `Номенклатура`, `Склад`, `Организация`, `Производитель`
   - Sum Field: `Сумма`
   - Qty Field: `Количество`
4. Click "Test Connection"
5. Click "Save"

### 4. Run analysis
1. Go to Dashboard
2. Select source
3. Choose date range (e.g., last 3 months)
4. Click "Run Analysis"
5. Wait for completion (<30 seconds)

### 5. View results
- Heat Map: Click colored cells to drill down
- Table: Filter/sort anomalies
- Drill-down: View time series with anomaly markers
```

---

### 5. Agent Context Update

Run `.specify/scripts/bash/update-agent-context.sh qwen` to add:
- FastAPI + Jinja2 SSR pattern
- Chart.js embedding in templates
- SQLite with JSON columns for dimensions

---

## Phase 2: Task Breakdown

**Next Command**: `/speckit.tasks`

Tasks will be organized by walking skeleton phase:
- Phase 1 tasks: Static UI (mock data)
- Phase 2 tasks: Live API + mock detector
- Phase 3 tasks: Real detector
- Phase 4 tasks: 1C integration

Each phase produces a runnable, demonstrable increment.

---

## Constitution Re-Check (Post-Design)

| Principle | Design Compliance | Status |
|-----------|-------------------|--------|
| **I. Detector Purity** | `domain/detector.py` has no imports from `infrastructure/` or `api/` | ✅ PASS |
| **II. Manual Trigger Only** | Only endpoint: `POST /api/v1/analysis/run` (no cron) | ✅ PASS |
| **III. Computed Metrics** | `domain/transformer.py` computes `value = raw_sum / raw_qty`; guard for qty=0 | ✅ PASS |
| **IV. DataSource as Config** | DataSource entity stored in SQLite; UI form for CRUD | ✅ PASS |
| **V. Repository Pattern** | `RepositoryBase` abstract class; `sqlite.py` implements | ✅ PASS |
| **VI. Observability via Text I/O** | All API responses are JSON; errors are JSON with `error` + `message` | ✅ PASS |

**GATE RESULT**: ✅ ALL PASS - Proceed to Phase 2 (Task Breakdown)

---

## Walking Skeleton Summary

| Phase | Deliverable | User Demo |
|-------|-------------|-----------|
| **Phase 1** | Static UI (mock data) | "This is how it looks" |
| **Phase 2** | Live API + mock detector | "End-to-end flow works" |
| **Phase 3** | Real detector | "Real anomaly detection" |
| **Phase 4** | 1C integration | "Real data from 1C" |

**Next Step**: Run `/speckit.tasks` to generate task breakdown.
