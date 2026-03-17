# Research: Financial Anomaly Detection Service MVP

**Created**: 2026-03-17
**Feature**: 001-anomaly-detection-mvp
**Purpose**: Resolve technical unknowns before design phase

---

## Decision 1: FastAPI + Jinja2 SSR Pattern

**Question**: How to structure server-rendered HTML with FastAPI?

**Decision**: Use `Jinja2Templates` with `TemplateResponse` for HTML rendering; `StaticFiles` for Chart.js and CSS.

**Rationale**:
- Constitution-mandated team standard
- No build step required (unlike React/Vue)
- Direct data passing from backend to templates
- Simple deployment (single backend container)

**Implementation Pattern**:
```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="ui/templates")
app.mount("/static", StaticFiles(directory="ui/static"), name="static")

@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "sources": sources,
        "last_analysis": last_analysis
    })
```

**Alternatives Considered**:
- **React SPA**: Overkill for internal tool; requires build pipeline
- **HTMX**: Adds complexity; team less familiar
- **Pure HTML forms**: Too limited for dynamic heat map interactions

---

## Decision 2: Chart.js Integration in Jinja2 Templates

**Question**: How to embed Chart.js in server-rendered templates with dynamic data?

**Decision**: Pass chart data as JSON in template context; render via inline `<script>` tag with JSON-safe serialization.

**Rationale**:
- No AJAX calls needed (data embedded in initial HTML)
- Works with SSR pattern
- Chart.js is lightweight and CDN-hostable

**Implementation Pattern**:
```python
# Backend
@app.get("/drilldown/{combination_id}")
async def drilldown(request: Request, combination_id: str):
    timeseries_data = get_timeseries(combination_id)  # List[dict]
    return templates.TemplateResponse("drilldown.html", {
        "request": request,
        "chart_data": json.dumps(timeseries_data),  # JSON string
        "anomalies": anomalies
    })
```

```html
{# Template: drilldown.html #}
<canvas id="timeseries-chart"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  const ctx = document.getElementById('timeseries_chart');
  const data = {{ chart_data | safe }};  {# Jinja2 safe filter #}
  
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.period),
      datasets: [{
        label: 'Value',
        data: data.map(d => d.value),
        borderColor: 'rgb(75, 192, 192)'
      }]
    }
  });
</script>
```

**Alternatives Considered**:
- **Fetch API + AJAX**: Adds latency; requires loading states
- **Server-side chart rendering (e.g., matplotlib)**: Produces static images, not interactive

---

## Decision 3: SQLite Schema for Multi-Dimensional Anomaly Data

**Question**: How to store anomaly data with varying dimension counts (4-5 dimensions per register)?

**Decision**: Use separate tables for `DataSource`, `AnalysisRun`, `Anomaly`; store dimension values as JSON blob.

**Rationale**:
- Flexibility: Different registers have different dimension sets
- Query performance acceptable for MVP scale (100 combinations max)
- SQLite has native JSON functions for filtering

**Schema**:
```sql
-- Data Sources (configuration)
CREATE TABLE data_sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    register_name TEXT NOT NULL,
    dimensions TEXT NOT NULL,  -- JSON array: ["Период", "Номенклатура", ...]
    metric_fields TEXT NOT NULL,  -- JSON: {"sum": "Сумма", "qty": "Количество"}
    threshold_rules TEXT NOT NULL,  -- JSON: {spike_pct, spike_zscore, ...}
    auth_config TEXT NOT NULL,  -- JSON: {type, user, pass}
    enabled BOOLEAN DEFAULT 1
);

-- Analysis Runs (execution history)
CREATE TABLE analysis_runs (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    triggered_by TEXT DEFAULT 'user',
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    anomaly_count INTEGER,
    error_message TEXT,
    FOREIGN KEY (source_id) REFERENCES data_sources(id)
);

-- Anomalies (results)
CREATE TABLE anomalies (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    dimensions TEXT NOT NULL,  -- JSON object: {"Номенклатура": "Продукт А", ...}
    period DATE NOT NULL,
    anomaly_type TEXT CHECK(anomaly_type IN ('SPIKE', 'TREND_BREAK', 'ZERO_NEG', 'MISSING', 'RATIO', 'MISSING_DATA')),
    current_value REAL,
    previous_value REAL,
    pct_change REAL,
    zscore REAL,
    threshold_triggered TEXT,  -- JSON: which rules fired
    FOREIGN KEY (run_id) REFERENCES analysis_runs(id),
    FOREIGN KEY (source_id) REFERENCES data_sources(id)
);

-- Indexes for common queries
CREATE INDEX idx_anomalies_run_id ON anomalies(run_id);
CREATE INDEX idx_anomalies_type ON anomalies(anomaly_type);
CREATE INDEX idx_anomalies_period ON anomalies(period);
```

**Query Example** (filter by dimension value):
```sql
SELECT * FROM anomalies
WHERE run_id = ?
  AND json_extract(dimensions, '$.Номенклатура') = 'Продукт А';
```

**Alternatives Considered**:
- **One column per dimension**: Breaks with varying dimension counts
- **Separate table for each dimension**: Over-normalized; complex queries
- **PostgreSQL from start**: Violates MVP simplicity; SQLite sufficient for 100 combinations

---

## Decision 4: Pure Detector Architecture

**Question**: How to structure detector as pure functions with no external dependencies?

**Decision**: Detector accepts `List[DataPoint]` and `ThresholdRules`, returns `List[Anomaly]`. No imports from `infrastructure/`, `api/`, or `ui/`.

**Rationale**:
- Constitution Principle I (Detector Purity)
- Testable in isolation (no mocks needed)
- Swappable algorithm (can replace detector without touching other layers)

**Implementation Pattern**:
```python
# domain/models.py
@dataclass
class DataPoint:
    source_id: str
    dimensions: dict[str, str]
    period: date
    value: float
    raw_sum: float
    raw_qty: float

@dataclass
class Anomaly:
    source_id: str
    dimensions: dict[str, str]
    period: date
    anomaly_type: str
    current_value: float | None
    previous_value: float | None
    pct_change: float | None
    zscore: float | None
    threshold_triggered: dict

@dataclass
class ThresholdRules:
    spike_pct: float = 20.0
    spike_zscore: float = 3.0
    spike_logic: Literal["AND", "OR"] = "OR"
    moving_avg_window: int = 6
    trend_window: int = 3
    trend_min_points: int = 5
    ratio_min: float | None = None
    ratio_max: float | None = None
    zero_neg_enabled: bool = True
    missing_enabled: bool = True
    ratio_enabled: bool = False

# domain/detector.py
def detect_anomalies(
    data_points: list[DataPoint],
    threshold_rules: ThresholdRules
) -> list[Anomaly]:
    """Pure function: no I/O, no side effects."""
    anomalies = []
    
    # Group by dimension combination
    grouped = defaultdict(list)
    for dp in data_points:
        key = tuple(sorted(dp.dimensions.items()))
        grouped[key].append(dp)
    
    # Detect anomalies per combination
    for dim_key, points in grouped.items():
        sorted_points = sorted(points, key=lambda p: p.period)
        anomalies.extend(_detect_for_combination(sorted_points, threshold_rules))
    
    return anomalies

def _detect_for_combination(
    points: list[DataPoint],
    rules: ThresholdRules
) -> list[Anomaly]:
    """Detect all anomaly types for a single dimension combination."""
    anomalies = []
    
    for i, point in enumerate(points):
        # Guard: MISSING_DATA (qty=0)
        if point.raw_qty == 0:
            anomalies.append(Anomaly(
                source_id=point.source_id,
                dimensions=point.dimensions,
                period=point.period,
                anomaly_type="MISSING_DATA",
                current_value=None,
                previous_value=None,
                pct_change=None,
                zscore=None,
                threshold_triggered={"qty": 0}
            ))
            continue
        
        # ZERO_NEG detection
        if rules.zero_neg_enabled and point.value <= 0:
            anomalies.append(...anomaly_type="ZERO_NEG"...)
        
        # SPIKE detection (requires previous point)
        if i > 0:
            prev = points[i - 1]
            pct_change = ((point.value - prev.value) / prev.value) * 100
            
            # Z-score calculation (requires moving window)
            window = points[max(0, i - rules.moving_avg_window):i]
            if len(window) >= 2:
                mean = sum(p.value for p in window) / len(window)
                std = (sum((p.value - mean) ** 2 for p in window) / len(window)) ** 0.5
                zscore = (point.value - mean) / std if std > 0 else 0
                
                # SPIKE logic (AND/OR)
                if rules.spike_logic == "OR":
                    if pct_change > rules.spike_pct or zscore > rules.spike_zscore:
                        anomalies.append(...anomaly_type="SPIKE"...)
                else:  # AND
                    if pct_change > rules.spike_pct and zscore > rules.spike_zscore:
                        anomalies.append(...anomaly_type="SPIKE"...)
        
        # TREND_BREAK, MISSING, RATIO detection...
    
    return anomalies
```

**Test Example** (no mocks needed):
```python
def test_spike_detection():
    points = [
        DataPoint("src1", {}, date(2026, 1, 31), 100.0, 100.0, 1.0),
        DataPoint("src1", {}, date(2026, 2, 28), 150.0, 150.0, 1.0),  # 50% spike
        DataPoint("src1", {}, date(2026, 3, 31), 105.0, 105.0, 1.0),
    ]
    rules = ThresholdRules(spike_pct=20.0, spike_zscore=3.0)
    
    anomalies = detect_anomalies(points, rules)
    
    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == "SPIKE"
    assert anomalies[0].pct_change == 50.0
```

**Alternatives Considered**:
- **Detector reads from DB directly**: Violates purity; hard to test
- **Detector calls 1C HTTP service**: Violates purity; couples to external system

---

## Decision 5: 1C HTTP Service Contract

**Question**: Confirm JSON schema, field names (Cyrillic), pagination format for 1C integration.

**Decision**: Use BRD-specified schema with Cyrillic field names matching 1C metadata; pagination via `page`/`page_size` query params.

**Rationale**:
- BRD Section 7 provides complete specification
- Cyrillic field names match 1C metadata (avoiding translation errors)
- Pagination aligns with 1C `ПЕРВЫЕ N ПРОПУСТИТЬ M` pattern

**Request Format**:
```http
GET /hs/analytics/v1/data?register_name=ПартииТоваровНаСкладахПоПроизводителям&date_from=2026-01-01&date_to=2026-03-31&page=1&page_size=500
Authorization: Basic dXNlcjpwYXNz
```

**Response Format**:
```json
{
  "register_name": "ПартииТоваровНаСкладахПоПроизводителям",
  "date_from": "2026-01-01",
  "date_to": "2026-03-31",
  "page": 1,
  "page_size": 500,
  "total_count": 87,
  "has_next": false,
  "data": [
    {
      "Период": "2026-01-31",
      "Номенклатура": "Продукт А",
      "Склад": "Центральный",
      "Организация": "ООО Компания",
      "Производитель": "Завод №1",
      "Сумма": 125000.00,
      "Количество": 100.0
    }
  ]
}
```

**Error Handling**:
- `400 Bad Request`: Missing required param (`register_name`, `date_from`)
- `401 Unauthorized`: Invalid Basic Auth credentials
- `404 Not Found`: Register name not found in 1C configuration
- `500 Internal Server Error`: 1C internal error

**Mock Adapter** (for Phase 1-3 development before 1C service ready):
```python
# infrastructure/mock_1c_adapter.py
async def fetch_1c_data_mock(
    endpoint: str,
    register_name: str,
    date_from: date,
    date_to: date
) -> list[dict]:
    """Return mock data for development."""
    return [
        {
            "Период": "2026-01-31",
            "Номенклатура": "Продукт А",
            "Склад": "Центральный",
            "Организация": "ООО Компания",
            "Производитель": "Завод №1",
            "Сумма": 125000.00,
            "Количество": 100.0
        },
        {
            "Период": "2026-02-28",
            "Номенклатура": "Продукт А",
            "Склад": "Центральный",
            "Организация": "ООО Компания",
            "Производитель": "Завод №1",
            "Сумма": 310000.00,  # SPIKE: 148% increase
            "Количество": 100.0
        }
    ]
```

**Alternatives Considered**:
- **Transliterate field names to Latin**: Risk of mismatch with 1C metadata
- **Use numeric column indices**: Fragile; breaks if 1C schema changes

---

## Summary of Decisions

| # | Decision | Impact |
|---|----------|--------|
| 1 | FastAPI + Jinja2 SSR | Frontend architecture |
| 2 | Chart.js via JSON in templates | UI implementation pattern |
| 3 | SQLite with JSON for dimensions | Database schema |
| 4 | Pure detector (no I/O) | Code organization, testability |
| 5 | 1C contract with Cyrillic fields | Integration layer |

**All NEEDS CLARIFICATION items from Technical Context resolved.**

**Next Step**: Proceed to Phase 1 (Design & Contracts) with these decisions.
