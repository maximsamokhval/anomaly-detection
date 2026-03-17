# Data Model: Financial Anomaly Detection Service MVP

**Created**: 2026-03-17
**Feature**: 001-anomaly-detection-mvp

---

## Entities

### DataSource

**Purpose**: Configuration for a single 1C register.

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | str | Yes | Unique identifier (user-provided slug, e.g., `reg_cost_price`) |
| `name` | str | Yes | Display name (e.g., "Себестоимость производства") |
| `endpoint` | str | Yes | Base URL of 1C HTTP service (e.g., `http://1c-server/base/hs/analytics/v1`) |
| `register_name` | str | Yes | 1C register name (e.g., `ПартииТоваровНаСкладахПоПроизводителям`) |
| `dimensions` | list[str] | Yes | Ordered list of dimension names (e.g., `["Период", "Номенклатура", "Склад", "Организация", "Производитель"]`) |
| `metric_fields` | dict | Yes | `{"sum": "Сумма", "qty": "Количество"}` |
| `threshold_rules` | ThresholdRules | Yes | Detection thresholds (see below) |
| `auth` | AuthConfig | Yes | Authentication configuration |
| `enabled` | bool | Yes | Whether source is active |

**Validation Rules**:
- `id`: Alphanumeric + underscores only; max 50 chars
- `register_name`: Non-empty
- `dimensions`: At least 1 dimension
- `metric_fields`: Must have both `sum` and `qty` keys

---

### ThresholdRules (Embedded in DataSource)

**Purpose**: Configurable detection thresholds per data source.

**Fields**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `spike_pct` | float | 20.0 | Minimum % change for SPIKE anomaly |
| `spike_zscore` | float | 3.0 | Z-score threshold for SPIKE |
| `spike_logic` | "AND" \| "OR" | "OR" | Logic for combining % and z-score |
| `moving_avg_window` | int | 6 | Window size for rolling mean/std |
| `trend_window` | int | 3 | Minimum periods for trend detection |
| `trend_min_points` | int | 5 | Minimum history points for TREND_BREAK |
| `ratio_min` | float \| null | null | Lower bound for RATIO anomaly |
| `ratio_max` | float \| null | null | Upper bound for RATIO anomaly |
| `zero_neg_enabled` | bool | true | Enable ZERO_NEG detection |
| `missing_enabled` | bool | true | Enable MISSING detection |
| `ratio_enabled` | bool | false | Enable RATIO detection (requires min/max) |

---

### AuthConfig (Embedded in DataSource)

**Purpose**: Authentication for 1C HTTP service.

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | "none" \| "basic" | Yes | Authentication type |
| `user` | str | Conditional | Username (required if type=basic) |
| `pass` | str | Conditional | Password (required if type=basic) |

---

### AnalysisRun

**Purpose**: Execution history of anomaly detection runs.

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | str (UUID) | Yes | Unique run identifier |
| `source_id` | str | Yes | FK to DataSource.id |
| `date_from` | date | Yes | Start of analysis period |
| `date_to` | date | Yes | End of analysis period |
| `triggered_by` | str | Yes | "user" (MVP); reserved for future auth |
| `started_at` | datetime | Yes | When analysis began |
| `completed_at` | datetime \| null | No | When analysis finished |
| `status` | str | Yes | `pending` \| `running` \| `completed` \| `failed` |
| `anomaly_count` | int | No | Total anomalies detected |
| `error_message` | str \| null | No | Error details if failed |

**Validation Rules**:
- `date_from <= date_to`
- `completed_at >= started_at` (if set)
- `anomaly_count >= 0` (if set)

**State Transitions**:
```
pending → running → completed
                     ↘ failed
```

---

### DataPoint (Optional Persistence)

**Purpose**: Computed metric values for analysis (may be ephemeral or persisted for debugging).

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | str | Yes | FK to AnalysisRun.id |
| `source_id` | str | Yes | FK to DataSource.id |
| `dimensions` | dict[str, str] | Yes | JSON: `{"Номенклатура": "Продукт А", ...}` |
| `period` | date | Yes | Time period (e.g., month-end date) |
| `value` | float | Yes | Computed: `raw_sum / raw_qty` |
| `raw_sum` | float | Yes | Raw sum from 1C |
| `raw_qty` | float | Yes | Raw quantity from 1C |

**Validation Rules**:
- `value = raw_sum / raw_qty` (invariant)
- If `raw_qty == 0`, DataPoint should not be created; instead emit MISSING_DATA anomaly

---

### Anomaly

**Purpose**: Detected deviation from expected behavior.

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | str (UUID) | Yes | Unique identifier |
| `run_id` | str | Yes | FK to AnalysisRun.id |
| `source_id` | str | Yes | FK to DataSource.id |
| `dimensions` | dict[str, str] | Yes | JSON: dimension values |
| `period` | date | Yes | Period when anomaly occurred |
| `anomaly_type` | str | Yes | `SPIKE` \| `TREND_BREAK` \| `ZERO_NEG` \| `MISSING` \| `RATIO` \| `MISSING_DATA` |
| `current_value` | float \| null | No | Value at anomaly period |
| `previous_value` | float \| null | No | Value at previous period (for SPIKE/TREND_BREAK) |
| `pct_change` | float \| null | No | Percentage change (for SPIKE) |
| `zscore` | float \| null | No | Z-score (for SPIKE) |
| `threshold_triggered` | dict | No | JSON: which rules fired (e.g., `{"spike_pct": true, "spike_zscore": false}`) |

**Validation Rules**:
- `anomaly_type` in allowed set
- If `anomaly_type == SPIKE`: `pct_change` and `zscore` should be set
- If `anomaly_type == ZERO_NEG`: `current_value <= 0`
- If `anomaly_type == MISSING_DATA`: `current_value` is null

---

## Relationships

```
DataSource (1) ──< AnalysisRun (1) ──< Anomaly (N)
     │                                      │
     └──────────────────────────────────────┘
              (via source_id FK)

AnalysisRun (1) ──< DataPoint (N) [optional persistence]
```

---

## SQLite Schema

```sql
-- Data Sources
CREATE TABLE data_sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    register_name TEXT NOT NULL,
    dimensions TEXT NOT NULL,  -- JSON array
    metric_fields TEXT NOT NULL,  -- JSON object
    threshold_rules TEXT NOT NULL,  -- JSON object
    auth_config TEXT NOT NULL,  -- JSON object
    enabled INTEGER DEFAULT 1,  -- BOOLEAN
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- Analysis Runs
CREATE TABLE analysis_runs (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    triggered_by TEXT DEFAULT 'user',
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed')) NOT NULL,
    anomaly_count INTEGER,
    error_message TEXT,
    FOREIGN KEY (source_id) REFERENCES data_sources(id)
);

-- Anomalies
CREATE TABLE anomalies (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    dimensions TEXT NOT NULL,  -- JSON object
    period DATE NOT NULL,
    anomaly_type TEXT CHECK(anomaly_type IN (
        'SPIKE', 'TREND_BREAK', 'ZERO_NEG', 'MISSING', 'RATIO', 'MISSING_DATA'
    )) NOT NULL,
    current_value REAL,
    previous_value REAL,
    pct_change REAL,
    zscore REAL,
    threshold_triggered TEXT,  -- JSON object
    FOREIGN KEY (run_id) REFERENCES analysis_runs(id),
    FOREIGN KEY (source_id) REFERENCES data_sources(id)
);

-- Optional: DataPoints (for debugging/audit)
CREATE TABLE data_points (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    dimensions TEXT NOT NULL,  -- JSON object
    period DATE NOT NULL,
    value REAL NOT NULL,
    raw_sum REAL NOT NULL,
    raw_qty REAL NOT NULL,
    FOREIGN KEY (run_id) REFERENCES analysis_runs(id),
    FOREIGN KEY (source_id) REFERENCES data_sources(id)
);

-- Indexes
CREATE INDEX idx_runs_source ON analysis_runs(source_id);
CREATE INDEX idx_runs_status ON analysis_runs(status);
CREATE INDEX idx_anomalies_run ON anomalies(run_id);
CREATE INDEX idx_anomalies_source ON anomalies(source_id);
CREATE INDEX idx_anomalies_type ON anomalies(anomaly_type);
CREATE INDEX idx_anomalies_period ON anomalies(period);
CREATE INDEX idx_data_points_run ON data_points(run_id);
```

---

## Repository Interfaces

```python
# infrastructure/persistence/base.py
from abc import ABC, abstractmethod
from typing import Optional

class DataSourceRepository(ABC):
    @abstractmethod
    def get_all(self) -> list[DataSource]: ...
    
    @abstractmethod
    def get_by_id(self, id: str) -> Optional[DataSource]: ...
    
    @abstractmethod
    def save(self, source: DataSource) -> None: ...
    
    @abstractmethod
    def delete(self, id: str) -> None: ...

class AnalysisRunRepository(ABC):
    @abstractmethod
    def create(self, run: AnalysisRun) -> None: ...
    
    @abstractmethod
    def get_by_id(self, id: str) -> Optional[AnalysisRun]: ...
    
    @abstractmethod
    def update_status(self, id: str, status: str, error_message: str | None = None) -> None: ...
    
    @abstractmethod
    def get_latest(self, source_id: str) -> Optional[AnalysisRun]: ...

class AnomalyRepository(ABC):
    @abstractmethod
    def save_batch(self, anomalies: list[Anomaly]) -> None: ...
    
    @abstractmethod
    def get_by_run_id(self, run_id: str) -> list[Anomaly]: ...
    
    @abstractmethod
    def get_by_filters(
        self,
        source_id: str | None = None,
        anomaly_type: str | None = None,
        period_from: date | None = None,
        period_to: date | None = None,
        dimension_filters: dict[str, str] | None = None
    ) -> list[Anomaly]: ...
```

---

## Next Steps

1. Implement SQLite repositories in `infrastructure/persistence/sqlite.py`
2. Generate Pydantic schemas for API layer in `api/schemas.py`
3. Create domain entities in `domain/models.py`
