# Tasks: Financial Anomaly Detection Service MVP

**Input**: Design documents from `/specs/001-anomaly-detection-mvp/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Tests**: API contract tests and detector unit tests are INCLUDED (mandatory per plan.md). UI tests are manual (per constitution).

**Organization**: Tasks are organized by walking skeleton phase (Phase 1: Static UI, Phase 2: Live API + Mock Detector, Phase 3: Real Detector, Phase 4: 1C Integration), then by user story within each phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **UI**: `backend/ui/` (server-rendered via Jinja2)
- Paths follow plan.md project structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure: `backend/src/`, `backend/tests/`, `backend/ui/templates/`, `backend/ui/static/`
- [x] T002 Initialize Python 3.12 project with `uv init` and create `pyproject.toml` with FastAPI, Jinja2, httpx, pandas, scipy dependencies
- [x] T003 [P] Configure ruff linting in `ruff.toml`
- [x] T004 [P] Configure mypy type checking in `mypy.ini`
- [x] T005 [P] Configure pytest with pytest-cov, pytest-asyncio in `pytest.ini`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 [P] Create domain entities in `backend/src/domain/models.py`: DataSource, AnalysisRun, Anomaly, DataPoint, ThresholdRules, AuthConfig
- [x] T007 [P] Create repository base interfaces in `backend/src/infrastructure/persistence/base.py`: DataSourceRepository, AnalysisRunRepository, AnomalyRepository
- [x] T008 [P] Implement SQLite repositories in `backend/src/infrastructure/persistence/sqlite.py` with schema from data-model.md
- [x] T009 [P] Create database migration script in `backend/scripts/init_db.py` to create tables: data_sources, analysis_runs, anomalies, data_points
- [x] T010 [P] Create Pydantic schemas in `backend/src/api/schemas.py` for all API request/response models
- [x] T011 [P] Setup FastAPI app structure in `backend/src/main.py` with CORS, exception handlers
- [x] T012 [P] Configure Jinja2 templates in `backend/src/ui/templates.py` with StaticFiles for `/static`
- [x] T013 [P] Create mock 1C adapter in `backend/src/infrastructure/mock_1c_adapter.py` returning hardcoded test data

**Checkpoint**: Foundation ready - user story work can now begin in parallel

---

## Phase 3: Walking Skeleton Phase 1 - Static UI (Mock Data)

**Goal**: Fully clickable UI with hardcoded mock data - demonstrates look and feel

**Independent Test**: Can navigate Dashboard → Heat Map → Drill-down → Table → Sources screens with static data; no backend API calls

### Implementation for Static UI

- [x] T014 [P] [US1] Create base Jinja2 template in `backend/ui/templates/base.html` with navigation menu (Dashboard, Heat Map, Table, Sources)
- [x] T015 [P] [US1] Create Dashboard template in `backend/ui/templates/dashboard.html` with static source list and "Run Analysis" button (non-functional)
- [x] T016 [P] [US1] Create Heat Map template in `backend/ui/templates/heatmap.html` with hardcoded mock anomaly data (3-5 rows, 3 columns)
- [x] T017 [P] [US1] Create Drill-down template in `backend/ui/templates/drilldown.html` with Chart.js line chart rendering mock time series data
- [x] T018 [P] [US1] Create Anomaly Table template in `backend/ui/templates/table.html` with static rows, sortable headers (non-functional), filter dropdowns (non-functional)
- [x] T019 [P] [US2] Create Sources template in `backend/ui/templates/sources.html` with form fields: ID, Name, Endpoint, Register Name, Dimensions (multi-input), Sum/QTY fields, Auth config, Threshold rules
- [x] T020 [P] [US1] Add Chart.js CDN in `backend/ui/templates/base.html` and initialize chart in `backend/ui/static/chart.js` with basic line chart config
- [x] T021 [US1] Add navigation routing in `backend/src/main.py`: GET `/`, `/heatmap`, `/table`, `/drilldown`, `/sources` returning TemplateResponse

**Checkpoint**: Static UI complete - clickable prototype ready for user demo

**✅ VERIFIED**: 
- `ruff check src/` - All checks passed
- `mypy src/` - Success: no issues found
- `uv run uvicorn src.main:app` - Server starts successfully
- Loguru debug logging active in `backend/logs/debug.log`
- All UI pages render: /, /heatmap, /table, /drilldown, /sources
- API endpoints respond: /health, /api/v1/sources, /api/v1/analysis/run

---

## Phase 4: Walking Skeleton Phase 2 - Live API + Mock Detector

**Goal**: Real API + database persistence, detector returns mock anomalies

**Independent Test**: Can configure data source via UI (saves to SQLite), run analysis via POST API, view real results in heat map from database

### Tests for Live API (Contract Tests) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T022 [P] [US1] Contract test for POST /api/v1/analysis/run in `backend/tests/contract/test_analysis.py`
- [x] T023 [P] [US1] Contract test for GET /api/v1/anomalies in `backend/tests/contract/test_anomalies.py`
- [x] T024 [P] [US2] Contract test for CRUD /api/v1/sources endpoints in `backend/tests/contract/test_sources.py`

### Implementation for Live API - User Story 1 (Detect Anomalies)

- [x] T025 [P] [US1] Create mock detector in `backend/src/domain/mock_detector.py` returning pre-canned anomalies for test data
- [x] T026 [P] [US1] Implement POST /api/v1/analysis/run endpoint in `backend/src/api/routes/analysis.py` calling mock detector
- [x] T027 [P] [US1] Implement GET /api/v1/analysis/{id} endpoint in `backend/src/api/routes/analysis.py`
- [x] T028 [P] [US1] Implement GET /api/v1/anomalies endpoint in `backend/src/api/routes/anomalies.py` with filtering by run_id
- [x] T029 [P] [US1] Implement GET /api/v1/heatmap endpoint in `backend/src/api/routes/heatmap.py` transforming anomalies to heat map format
- [x] T030 [P] [US1] Implement GET /api/v1/timeseries endpoint in `backend/src/api/routes/timeseries.py` for drill-down data
- [x] T031 [US1] Update Dashboard template to call real API for source list and last analysis status
- [x] T032 [US1] Update Heat Map template to fetch data from GET /api/v1/heatmap and render dynamically
- [x] T033 [US1] Update Drill-down template to fetch time series from GET /api/v1/timeseries and update Chart.js data

### Implementation for Live API - User Story 2 (Configure Sources)

- [x] T034 [P] [US2] Implement GET /api/v1/sources endpoint in `backend/src/api/routes/sources.py`
- [x] T035 [P] [US2] Implement POST /api/v1/sources endpoint in `backend/src/api/routes/sources.py` with validation
- [x] T036 [P] [US2] Implement PUT /api/v1/sources/{id} endpoint in `backend/src/api/routes/sources.py`
- [x] T037 [P] [US2] Implement DELETE /api/v1/sources/{id} endpoint in `backend/src/api/routes/sources.py`
- [x] T038 [P] [US2] Implement POST /api/v1/sources/{id}/test endpoint in `backend/src/api/routes/sources.py` calling mock 1C adapter
- [x] T039 [P] [US2] Implement GET /api/v1/sources/{id}/preview endpoint in `backend/src/api/routes/sources.py` returning mock data preview
- [x] T040 [US2] Update Sources template to POST form data to /api/v1/sources and handle success/error responses
- [x] T041 [US2] Add "Test Connection" button in Sources template calling POST /api/v1/sources/{id}/test via JavaScript

**Checkpoint**: Live API complete - end-to-end flow works with mock detector

---

## Phase 5: Walking Skeleton Phase 3 - Real Detector

**Goal**: Complete anomaly detection engine with all 6 anomaly types

**Independent Test**: Can run analysis with real detector algorithms; all anomaly types detectable with configurable thresholds

### Tests for Real Detector (Unit Tests) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T042 [P] [US1] Unit test for SPIKE detection (% change + z-score) in `backend/tests/unit/test_detector_spike.py`
- [x] T043 [P] [US1] Unit test for TREND_BREAK detection in `backend/tests/unit/test_detector_trend.py`
- [x] T044 [P] [US1] Unit test for ZERO_NEG detection in `backend/tests/unit/test_detector_zero_neg.py`
- [x] T045 [P] [US1] Unit test for MISSING detection in `backend/tests/unit/test_detector_missing.py`
- [x] T046 [P] [US1] Unit test for MISSING_DATA guard (qty=0) in `backend/tests/unit/test_detector_missing_data.py`
- [x] T047 [P] [US1] Unit test for transformer (value = sum/qty) in `backend/tests/unit/test_transformer.py`

### Implementation for Real Detector - User Story 1

- [x] T048 [P] [US1] Implement DataPoint transformer in `backend/src/domain/transformer.py` computing value = raw_sum / raw_qty with qty=0 guard
- [x] T049 [P] [US1] Implement SPIKE detection in `backend/src/domain/detector.py` with % change calculation and z-score (moving window)
- [x] T050 [P] [US1] Implement TREND_BREAK detection in `backend/src/domain/detector.py` with trend reversal logic
- [x] T051 [P] [US1] Implement ZERO_NEG detection in `backend/src/domain/detector.py`
- [x] T052 [P] [US1] Implement MISSING detection in `backend/src/domain/detector.py` for gaps in period sequence
- [x] T053 [P] [US1] Implement MISSING_DATA detection in `backend/src/domain/detector.py` for qty=0 cases
- [x] T054 [P] [US1] Implement RATIO detection in `backend/src/domain/detector.py` (disabled by default, requires ratio_min/max)
- [x] T055 [US1] Replace mock detector call in POST /api/v1/analysis/run with real detector from `backend/src/domain/detector.py`
- [x] T056 [US1] Add threshold rule application from DataSource.threshold_rules to detector execution

**Checkpoint**: Real detector complete - all anomaly types functional

---

## Phase 5b: DataPoint Persistence + Heat Map / Time Series (Gap Closure)

**Purpose**: Close C1/C2 gaps identified in speckit-analyze. Constitution V requires DataPointRepository; FR-013 requires persisting raw data points; FR-002/FR-005 require working heat map and drill-down endpoints.

- [x] T079 [P] Add `DataPointRepository` abstract interface to `backend/src/infrastructure/persistence/base.py`
- [x] T080 [P] Implement `SQLiteDataPointRepository` in `backend/src/infrastructure/persistence/sqlite.py` with `data_points` table, save_batch, get_by_run_id, get_by_run_and_dimensions
- [x] T081 [US1] Save DataPoints in `backend/src/api/routes/analysis.py` after transform_raw_data (FR-013)
- [x] T082 [US1] Implement GET /api/v1/heatmap in `backend/src/api/routes/heatmap.py`: query anomalies by run_id, build rows/columns/cells with type priority logic per contracts/api.md
- [x] T083 [US1] Implement GET /api/v1/timeseries in `backend/src/api/routes/timeseries.py`: query data_points by run_id + dimensions, join anomaly markers per period
- [x] T032 (moved) Update Heat Map template to fetch data from GET /api/v1/heatmap and render dynamically
- [x] T033 (moved) Update Drill-down template to fetch time series from GET /api/v1/timeseries and update Chart.js data

**Checkpoint**: FR-002, FR-005, FR-013, Constitution V all satisfied

---

## Phase 6: Walking Skeleton Phase 4 - 1C Integration

**Goal**: Real HTTP client integration with 1C service

**Independent Test**: Can fetch real data from 1C HTTP service; test connection validates real endpoint; analysis runs on real data

### Tests for 1C Integration (Integration Tests) ⚠️

> **NOTE: Requires running 1C HTTP service or test container**

- [ ] T057 [P] [US1] Integration test for 1C HTTP client in `backend/tests/integration/test_1c_client.py`
- [ ] T058 [P] [US2] Integration test for POST /api/v1/sources/{id}/test with real 1C in `backend/tests/integration/test_source_test.py`

### Implementation for 1C Integration - User Story 1 & 2

- [x] T059 [P] [US1] Implement real 1C HTTP client in `backend/src/infrastructure/http_client.py` with async httpx
- [x] T060 [P] [US1] Implement pagination handling in `backend/src/infrastructure/http_client.py` for large datasets
- [x] T061 [P] [US1] Implement error handling in `backend/src/infrastructure/http_client.py` for 401, 404, 500 responses
- [x] T062 [P] [US1] Add Basic Auth support in `backend/src/infrastructure/http_client.py` from DataSource.auth config
- [x] T063 [US1] Replace mock 1C adapter call in analysis endpoint with real HTTP client
- [x] T064 [US2] Update POST /api/v1/sources/{id}/test to call real 1C HTTP client and validate response

**Checkpoint**: 1C integration complete - end-to-end with real data

---

## Phase 7: User Story 3 - Browse and Filter Anomaly Details (Priority: P3)

**Goal**: Sortable, filterable anomaly table view

**Independent Test**: Can open table, apply filters (type, period, dimension), sort by % change/z-score, click row to navigate to drill-down

### Implementation for User Story 3

- [x] T065 [P] [US3] Implement query parameter parsing in GET /api/v1/anomalies for filters: type, period_from, period_to, dimension.{name}
- [x] T066 [P] [US3] Implement sorting in GET /api/v1/anomalies for sort_by (pct_change, zscore, period) and sort_order (asc, desc)
- [x] T067 [P] [US3] Implement pagination in GET /api/v1/anomalies with page, page_size, total_count, has_next
- [x] T068 [P] [US3] Update Anomaly Table template to call API with filter params from dropdown inputs
- [x] T069 [P] [US3] Add JavaScript for sortable column headers in Anomaly Table template (toggle asc/desc)
- [x] T070 [US3] Add row click handler in Anomaly Table template to navigate to /drilldown with dimension params

**Checkpoint**: All user stories complete

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T071 [P] Add structured logging with loguru in `backend/src/infrastructure/logging.py` for debug mode
- [x] T072 [P] Add request/response logging middleware in `backend/src/api/middleware.py`
- [x] T073 [P] Create Dockerfile in `backend/Dockerfile` for containerized deployment
- [x] T074 [P] Create docker-compose.yml in project root with backend service and volume for SQLite
- [x] T075 [P] Validate quickstart.md by following all steps end-to-end
- [x] T076 [P] Add error boundary handling in UI templates for 500 errors
- [x] T077 [P] Add loading states in UI templates during API calls
- [x] T078 [P] Run full test suite: `pytest --cov=backend/src` and verify coverage >80%

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Walking Skeleton Phase 1 (Phase 3)**: Static UI - depends on Foundational, no API needed
- **Walking Skeleton Phase 2 (Phase 4)**: Live API - depends on Phase 1 UI structure
- **Walking Skeleton Phase 3 (Phase 5)**: Real Detector - depends on Phase 2 API structure
- **Walking Skeleton Phase 4 (Phase 6)**: 1C Integration - depends on Phase 3 detector, requires 1C service
- **User Story 3 (Phase 7)**: Can start after Foundational, independent of US1/US2 implementation details
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Core value - detect and visualize anomalies. Must complete Phases 3-6.
- **User Story 2 (P2)**: Configuration - can implement in parallel with US1 after Foundational phase.
- **User Story 3 (P3)**: Table view - independent, can implement anytime after Foundational phase.

### Within Each User Story

- Tests MUST be written and FAIL before implementation (for API contract tests and detector unit tests)
- Models/entities before services
- Services before endpoints
- Core implementation before UI integration
- Story complete before moving to next priority (if sequential)

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003, T004, T005 can all run in parallel (different config files)

**Phase 2 (Foundational)**:
- T006, T007, T008, T009, T010, T011, T012, T013 can all run in parallel (different modules)

**Phase 3 (Static UI)**:
- T014, T015, T016, T017, T018, T019, T020 can all run in parallel (different templates)

**Phase 4 (Live API)**:
- Contract tests T022, T023, T024 can run in parallel
- API endpoints T026, T027, T028, T029, T030 can run in parallel
- Source CRUD T034, T035, T036, T037, T038, T039 can run in parallel

**Phase 5 (Real Detector)**:
- Unit tests T042-T047 can all run in parallel
- Detector functions T049-T054 can all run in parallel (different anomaly types)

**Phase 6 (1C Integration)**:
- T059, T060, T061, T062 can run in parallel (different client features)

**Phase 7 (US3)**:
- T065, T066, T067 can run in parallel (backend API enhancements)

---

## Parallel Example: Foundational Phase

```bash
# Launch all foundational tasks together:
Task: "Create domain entities in backend/src/domain/models.py"
Task: "Create repository base interfaces in backend/src/infrastructure/persistence/base.py"
Task: "Implement SQLite repositories in backend/src/infrastructure/persistence/sqlite.py"
Task: "Create database migration script in backend/scripts/init_db.py"
Task: "Create Pydantic schemas in backend/src/api/schemas.py"
Task: "Setup FastAPI app in backend/src/main.py"
Task: "Configure Jinja2 templates in backend/src/ui/templates.py"
Task: "Create mock 1C adapter in backend/src/infrastructure/mock_1c_adapter.py"
```

---

## Parallel Example: Detector Unit Tests

```bash
# Launch all detector unit tests together:
Task: "Unit test for SPIKE detection in backend/tests/unit/test_detector_spike.py"
Task: "Unit test for TREND_BREAK detection in backend/tests/unit/test_detector_trend.py"
Task: "Unit test for ZERO_NEG detection in backend/tests/unit/test_detector_zero_neg.py"
Task: "Unit test for MISSING detection in backend/tests/unit/test_detector_missing.py"
Task: "Unit test for MISSING_DATA guard in backend/tests/unit/test_detector_missing_data.py"
Task: "Unit test for transformer in backend/tests/unit/test_transformer.py"
```

---

## Implementation Strategy

### MVP First (Walking Skeleton Approach)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: Static UI → Demo to users ("This is how it looks")
4. Complete Phase 4: Live API + Mock Detector → Demo ("End-to-end flow works")
5. Complete Phase 5: Real Detector → Demo ("Real anomaly detection")
6. Complete Phase 6: 1C Integration → Demo ("Real data from 1C")
7. **STOP and VALIDATE**: Full end-to-end with real data
8. Deploy MVP

### Incremental Delivery

Each walking skeleton phase produces a runnable, demonstrable increment:
- Phase 3: Clickable prototype (no backend)
- Phase 4: Live backend with simulated data
- Phase 5: Real algorithms with mock data
- Phase 6: Real data from 1C

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: Static UI templates (Phase 3)
   - Developer B: API endpoints (Phase 4)
   - Developer C: Detector algorithms (Phase 5)
3. All converge on Phase 6 (1C Integration)

---

## Task Summary

| Phase | Task Count | Description |
|-------|------------|-------------|
| Phase 1: Setup | 5 | Project initialization |
| Phase 2: Foundational | 8 | Core infrastructure |
| Phase 3: Static UI | 8 | Clickable prototype |
| Phase 4: Live API | 20 (6 tests + 14 impl) | Real API + mock detector |
| Phase 5: Real Detector | 13 (6 tests + 7 impl) | All anomaly types |
| Phase 6: 1C Integration | 8 (2 tests + 6 impl) | Real data |
| Phase 7: US3 (Table) | 6 | Filterable table |
| Phase 8: Polish | 8 | Cross-cutting concerns |
| **Total** | **76** | |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each walking skeleton phase is independently demonstrable
- Verify tests fail before implementing (TDD for API contracts and detector)
- Commit after each task or logical group
- Stop at any checkpoint to validate increment independently
