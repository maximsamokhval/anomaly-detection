<!--
SYNC IMPACT REPORT
==================
Version change: (none) → 1.0.0 (initial)
Modified principles: (none) → 6 new principles added
Added sections:
  - Core Principles (6 principles: Detector Purity, Manual Trigger, Computed Metrics,
    DataSource Configuration, Repository Pattern, Observability)
  - Architecture Standards
  - Development Workflow
Removed sections: (none)
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ (Constitution Check section compatible)
  - .specify/templates/spec-template.md ✅ (no conflicts)
  - .specify/templates/tasks-template.md ✅ (no conflicts)
Follow-up TODOs: None
-->

# Financial Anomaly Detection Service Constitution

## Core Principles

### I. Detector Purity (NON-NEGOTIABLE)

The anomaly detection engine MUST be pure and isolated from external concerns. It accepts
`List[DataPoint]` as input and returns `List[Anomaly]` as output. No dependencies on
databases, HTTP clients, or UI frameworks are permitted within the detector module.

**Rationale**: Enables isolated unit testing, algorithm swaps without side effects, and
clear separation between business logic and infrastructure.

**Rules**:
- Detector MUST NOT import database, HTTP, or UI modules
- Detector MUST be deterministic: same input → same output
- All 6 anomaly types (SPIKE, TREND_BREAK, ZERO_NEG, MISSING, RATIO, MISSING_DATA)
  MUST be implemented as pure functions
- Threshold rules MUST be passed as parameters, not read from global state

---

### II. Manual Trigger Only (MVP CONSTRAINT)

No automated scheduling, cron jobs, or background workers are permitted in MVP. All
analysis MUST be initiated explicitly by user action via `POST /api/v1/analysis/run`.

**Rationale**: MVP focuses on analytical exploration, not alerting. Manual trigger
reduces complexity and eliminates need for state management, retry logic, and
notification infrastructure.

**Rules**:
- No `cron`, `scheduler`, or `celery` dependencies in MVP
- No background task queues
- Analysis runs synchronously within request context (<30 sec timeout)
- Post-MVP automation requires constitution amendment

---

### III. Computed Metrics (NON-NEGOTIABLE)

Financial metrics are NEVER stored pre-computed. The value `Сумма / Количество` MUST be
calculated at analysis time by the Transformer component. Guard: `Количество = 0` →
emit `MISSING_DATA` anomaly, do NOT crash.

**Rationale**: Prevents stale data issues, ensures calculation logic is always applied
consistently, and makes division-by-zero an explicit anomaly type rather than error.

**Rules**:
- Transformer MUST compute `value = raw_sum / raw_qty` for each DataPoint
- Guard clause: if `raw_qty == 0` → anomaly type `MISSING_DATA`, skip calculation
- Raw values (`raw_sum`, `raw_qty`) MUST be preserved in DataPoint for audit
- No caching of computed values in MVP

---

### IV. DataSource as Configuration

Every 1C register is described by a declarative `DataSource` configuration stored in
the database. Adding a new register MUST NOT require code changes to the detector.

**Rationale**: Enables scaling from 2 to 15+ registers without code proliferation.
Configuration-driven architecture allows analysts to add registers via UI.

**Rules**:
- `DataSource` model MUST contain: id, name, endpoint, register_name, dimensions,
  metric_fields, threshold_rules, auth, enabled
- All fields except `threshold_rules` are mandatory
- New DataSource instances are created via `POST /api/v1/sources`, not code changes
- Detector MUST read configuration from database, not hardcoded values

---

### V. Repository Pattern

All data persistence MUST go through abstract repository interfaces. SQLite is the
MVP implementation; migration to PostgreSQL must be possible without rewriting
business logic.

**Rationale**: Enables database technology swap at scale without touching domain logic.
Clear separation between business entities and storage mechanics.

**Rules**:
- Define `RepositoryBase` abstract interface for each aggregate
- Entities: `DataSource`, `Anomaly`, `AnalysisRun`, `DataPoint` (optional persistence)
- SQLite implementation in `infrastructure.persistence.sqlite`
- No raw SQL in service or detector layers
- Migration to PostgreSQL requires only new repository implementation

---

### VI. Observability via Text I/O

All I/O operations MUST produce human-readable text output. JSON for API responses,
structured logs for debugging, plain text errors for CLI. Binary formats prohibited
except for database storage.

**Rationale**: Ensures debuggability in production without special tooling. Analysts
can inspect raw API responses; developers can grep logs.

**Rules**:
- API responses: JSON with consistent schema (see API spec)
- Logs: structured format with timestamp, level, context
- Errors: plain text with clear message, no stack traces in production
- Heat map and chart data: JSON arrays, not binary blobs

---

## Architecture Standards

**Technology Stack** (fixed for MVP):

| Layer | Technology | Change Policy |
|---|---|---|
| Backend | Python 3.12 + FastAPI | Requires amendment |
| Frontend | Jinja2 + Chart.js | Can swap framework, keep SSR |
| Database | SQLite → PostgreSQL | Repository pattern handles migration |
| Analytics | pandas + scipy | Can replace, keep interface |
| HTTP Client | httpx (async) | Can replace |
| Deployment | Docker Compose | Can replace with k8s post-MVP |

**Architectural Constraints**:

1. **Single Manual Entry Point**: `POST /api/v1/analysis/run` is the only trigger
2. **Synchronous Analysis**: Analysis completes within request cycle (<30 sec)
3. **No Authentication in MVP**: Internal network, open access
4. **One HTTP Service for 1C**: Single `/hs/analytics/v1/data` endpoint serves all
   registers via `register_name` parameter
5. **Heat Map First**: Primary UI is heat map; drill-down is secondary

---

## Development Workflow

**Test Strategy**:

| Layer | Test Type | Mandatory |
|---|---|---|
| Detector | Unit tests (pure functions) | YES |
| Transformer | Unit tests (guard clauses) | YES |
| Repository | Integration tests (SQLite) | YES |
| API | Contract tests (endpoints) | YES |
| UI | Manual testing | MVP only |

**Code Review Requirements**:

1. All detector changes require 2 reviewers (algorithm correctness)
2. API contract changes require updating `contracts/` directory
3. New DataSource fields require migration script
4. Threshold rule changes require test coverage for all 6 anomaly types

**Definition of Done**:

- [ ] Detector unit tests pass (100% coverage for anomaly types)
- [ ] API contract tests pass
- [ ] Manual test: heat map renders for pilot register
- [ ] Manual test: drill-down shows correct time series
- [ ] No TODO comments in detector or transformer code

---

## Governance

This constitution supersedes all other development practices. Amendments require:

1. **Proposal**: Document proposed change with rationale
2. **Impact Analysis**: List affected modules, migration needs
3. **Approval**: Team lead + tech lead sign-off
4. **Migration Plan**: For breaking changes, document upgrade path
5. **Version Bump**: Follow semantic versioning

**Versioning Policy**:

- MAJOR: Breaking changes to DataSource schema, anomaly type removal, architecture
  pattern changes
- MINOR: New anomaly types, new API endpoints, UI additions
- PATCH: Bug fixes, performance improvements, documentation

**Compliance Review**:

- All PRs MUST be checked against constitution before merge
- Monthly review of constitution adherence (tech debt audit)
- Use `.specify/memory/constitution.md` as single source of truth

---

**Version**: 1.0.0 | **Ratified**: 2026-03-17 | **Last Amended**: 2026-03-17
