# Quickstart: Financial Anomaly Detection Service MVP

**Created**: 2026-03-17
**Feature**: 001-anomaly-detection-mvp

---

## Prerequisites

- Docker + Docker Compose
- Access to 1C HTTP service (for Phase 4; optional for Phases 1-3)

---

## Local Development

### 1. Start the Service

```bash
docker-compose up --build
```

The service will be available at `http://localhost:8000`.

### 2. Open the UI

Navigate to `http://localhost:8000` in your browser.

---

## Configure a Data Source

### Step 1: Navigate to Sources

Click **"Sources"** in the navigation menu.

### Step 2: Add New Source

Click **"Add Source"** button.

### Step 3: Fill in the Form

| Field | Value |
|-------|-------|
| **ID** | `partii_tovarov` |
| **Name** | `ПартииТоваровНаСкладахПоПроизводителям` |
| **Endpoint** | `http://1c-server/base/hs/analytics/v1` |
| **Register Name** | `ПартииТоваровНаСкладахПоПроизводителям` |
| **Dimensions** | `Период`, `Номенклатура`, `Склад`, `Организация`, `Производитель` (click "Add Dimension" for each) |
| **Sum Field** | `Сумма` |
| **Quantity Field** | `Количество` |

### Step 4: Configure Authentication

| Field | Value |
|-------|-------|
| **Auth Type** | `basic` (or `none` for internal network without auth) |
| **Username** | `service_user` |
| **Password** | (provided by IT team) |

### Step 5: Configure Thresholds (Optional)

Default thresholds are suitable for MVP:

| Threshold | Default |
|-----------|---------|
| Spike % | 20 |
| Spike Z-Score | 3.0 |
| Spike Logic | OR |
| Moving Avg Window | 6 |
| Trend Window | 3 |
| Trend Min Points | 5 |
| Zero/Neg Enabled | ✓ |
| Missing Enabled | ✓ |
| Ratio Enabled | ✗ (disabled by default) |

### Step 6: Test Connection

Click **"Test Connection"** to verify connectivity to 1C.

**Expected Response**:
- ✅ "Connection successful" (green)
- Response time: < 1 second

### Step 7: Save

Click **"Save"** to persist the data source configuration.

---

## Run Analysis

### Step 1: Go to Dashboard

Click **"Dashboard"** in the navigation menu.

### Step 2: Select Source

Choose the data source you just configured from the dropdown.

### Step 3: Choose Date Range

Select a period for analysis:
- **From**: `2026-01-01`
- **To**: `2026-03-31`

Recommendation: Start with last 3 months for pilot testing.

### Step 4: Run Analysis

Click **"Run Analysis"** button.

**Expected Behavior**:
- Progress bar appears
- Analysis completes in < 30 seconds
- Results display automatically

---

## View Results

### Heat Map View

The heat map displays:
- **Rows**: Unique combinations of dimensions (e.g., Product + Warehouse + Organization + Manufacturer)
- **Columns**: Time periods (month-end dates)
- **Cell Color**: Anomaly type and severity

**Legend**:
| Color | Anomaly Type | Priority |
|-------|--------------|----------|
| 🔴 Red | Zero/Negative | Highest |
| 🟠 Orange | Spike | High |
| 🟣 Purple | Ratio | Medium |
| 🔵 Blue | Trend Break | Low |
| ⚫ Gray | Missing | Low |

### Drill-Down

**Click a colored cell** to view:
- Time series chart (Chart.js line chart)
- Anomaly markers on the chart
- Metadata panel:
  - Current value
  - Previous value
  - % change
  - Z-score
  - Triggered thresholds

### Table View

Click **"Table"** tab to see:
- Sortable columns (click header to sort)
- Filterable by anomaly type, period, dimension values
- Click a row to navigate to drill-down

---

## Compare Products (Optional)

### Step 1: Go to Compare

Click **"Compare"** in the navigation menu.

### Step 2: Select Products

Use multi-select to choose up to 5 products (Nomenclatures).

### Step 3: View Overlaid Charts

Time series for all selected products display on the same chart.

---

## Troubleshooting

### "Connection failed" when testing source

**Possible Causes**:
1. 1C HTTP service not running
2. Incorrect endpoint URL
3. Invalid credentials

**Resolution**:
- Verify 1C service is accessible from the anomaly detection server
- Check endpoint URL matches 1C publication
- Confirm credentials with IT team

### "No data found" after running analysis

**Possible Causes**:
1. No data exists in 1C for selected period
2. Incorrect register name
3. Dimension names don't match 1C metadata

**Resolution**:
- Use **"Preview"** button in source configuration to verify data exists
- Confirm register name exactly matches 1C metadata (Cyrillic spelling)
- Verify dimension names match 1C metadata

### Analysis takes > 30 seconds

**Possible Causes**:
1. Too many dimension combinations (> 100)
2. Slow 1C HTTP service response
3. Network latency

**Resolution**:
- Reduce date range
- Add filters (organization, warehouse) to limit data volume
- Check network connectivity to 1C server

---

## Next Steps

After successful pilot:
1. Configure additional registers (up to 10-15 target)
2. Calibrate thresholds based on false positive rate
3. Enable RATIO detection if price data source is identified
4. Consider Post-MVP features: scheduling, notifications, YouTrack integration

---

## API Access (Optional)

For programmatic access, use the REST API:

```bash
# List sources
curl http://localhost:8000/api/v1/sources

# Run analysis
curl -X POST http://localhost:8000/api/v1/analysis/run \
  -H "Content-Type: application/json" \
  -d '{"source_id": "partii_tovarov", "date_from": "2026-01-01", "date_to": "2026-03-31"}'

# Get anomalies
curl "http://localhost:8000/api/v1/anomalies?run_id=<analysis_id>"
```

See `contracts/api.md` for full API documentation.
