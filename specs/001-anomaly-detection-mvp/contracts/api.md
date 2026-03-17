# API Contract: Financial Anomaly Detection Service

**Created**: 2026-03-17
**Feature**: 001-anomaly-detection-mvp

---

## Analysis Endpoints

### POST /api/v1/analysis/run

**Purpose**: Trigger anomaly detection for a data source and date range.

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
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
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

**Response (400 Bad Request - Invalid Date Range)**:
```json
{
  "error": "invalid_date_range",
  "message": "date_from must be <= date_to"
}
```

**Response (500 Internal Error)**:
```json
{
  "error": "analysis_failed",
  "message": "1C service unavailable: connection timeout"
}
```

---

### GET /api/v1/analysis/{id}

**Purpose**: Get status and results of a specific analysis run.

**Response (200 OK)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source_id": "reg_cost_price",
  "source_name": "Себестоимость производства",
  "date_from": "2026-01-01",
  "date_to": "2026-03-31",
  "triggered_by": "user",
  "started_at": "2026-03-17T10:00:00Z",
  "completed_at": "2026-03-17T10:00:05Z",
  "status": "completed",
  "anomaly_count": 5
}
```

**Response (404 Not Found)**:
```json
{
  "error": "not_found",
  "message": "Analysis run '550e8400-e29b-41d4-a716-446655440000' not found"
}
```

---

## Anomaly Endpoints

### GET /api/v1/anomalies

**Purpose**: List anomalies with filtering and sorting.

**Query Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | str | No | Filter by analysis run |
| `source_id` | str | No | Filter by data source |
| `type` | str | No | Filter by anomaly type (SPIKE, TREND_BREAK, etc.) |
| `period_from` | date | No | Filter by period start (YYYY-MM-DD) |
| `period_to` | date | No | Filter by period end (YYYY-MM-DD) |
| `dimension.{name}` | str | No | Filter by dimension value (e.g., `dimension.Номенклатура=Продукт А`) |
| `sort_by` | str | No | Sort field: `pct_change`, `zscore`, `period` (default: `pct_change`) |
| `sort_order` | "asc" \| "desc" | No | Sort order (default: "desc") |
| `page` | int | No | Page number (default: 1) |
| `page_size` | int | No | Items per page (default: 50, max: 200) |

**Response (200 OK)**:
```json
{
  "anomalies": [
    {
      "id": "anomaly-uuid-1",
      "run_id": "550e8400-e29b-41d4-a716-446655440000",
      "source_id": "reg_cost_price",
      "type": "SPIKE",
      "dimensions": {
        "Номенклатура": "Продукт А",
        "Склад": "Центральный",
        "Организация": "ООО Компания",
        "Производитель": "Завод №1"
      },
      "period": "2026-02-28",
      "current_value": 3100.0,
      "previous_value": 1250.0,
      "pct_change": 148.0,
      "zscore": 3.5,
      "threshold_triggered": {
        "spike_pct": true,
        "spike_zscore": true
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 5,
    "has_next": false
  }
}
```

---

### GET /api/v1/anomalies/{id}

**Purpose**: Get details of a specific anomaly.

**Response (200 OK)**:
```json
{
  "id": "anomaly-uuid-1",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_id": "reg_cost_price",
  "type": "SPIKE",
  "dimensions": {...},
  "period": "2026-02-28",
  "current_value": 3100.0,
  "previous_value": 1250.0,
  "pct_change": 148.0,
  "zscore": 3.5,
  "threshold_triggered": {...}
}
```

---

## Heat Map Endpoint

### GET /api/v1/heatmap

**Purpose**: Get data for heat map visualization.

**Query Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | str | Yes | Analysis run ID |
| `dimension_filters` | str | No | JSON object with dimension filters |

**Response (200 OK)**:
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "row_dimensions": ["Номенклатура", "Склад", "Организация", "Производитель"],
  "rows": [
    {
      "idx": 0,
      "values": {"Номенклатура": "Продукт А", "Склад": "Центральный", "Организация": "ООО Компания", "Производитель": "Завод №1"}
    },
    {
      "idx": 1,
      "values": {"Номенклатура": "Продукт Б", "Склад": "Центральный", "Организация": "ООО Компания", "Производитель": "Завод №1"}
    }
  ],
  "columns": [
    {"idx": 0, "period": "2026-01-31"},
    {"idx": 1, "period": "2026-02-28"},
    {"idx": 2, "period": "2026-03-31"}
  ],
  "cells": [
    {
      "row_idx": 0,
      "col_idx": 1,
      "type": "SPIKE",
      "intensity": 0.8,
      "anomaly_id": "anomaly-uuid-1"
    },
    {
      "row_idx": 1,
      "col_idx": 0,
      "type": "ZERO_NEG",
      "intensity": 1.0,
      "anomaly_id": "anomaly-uuid-2"
    }
  ],
  "legend": {
    "ZERO_NEG": {"color": "#DC2626", "label": "Zero/Negative", "priority": 1},
    "SPIKE": {"color": "#F59E0B", "label": "Spike", "priority": 2},
    "RATIO": {"color": "#8B5CF6", "label": "Ratio", "priority": 3},
    "TREND_BREAK": {"color": "#3B82F6", "label": "Trend Break", "priority": 4},
    "MISSING": {"color": "#6B7280", "label": "Missing", "priority": 5}
  }
}
```

---

## Time Series Endpoint

### GET /api/v1/timeseries

**Purpose**: Get time series data for drill-down view.

**Query Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | str | Yes | Analysis run ID |
| `dimensions` | str | Yes | JSON object with dimension values to filter |

**Example Request**:
```
GET /api/v1/timeseries?run_id=550e8400-e29b-41d4-a716-446655440000&dimensions={"Номенклатура":"Продукт А","Склад":"Центральный"}
```

**Response (200 OK)**:
```json
{
  "dimensions": {
    "Номенклатура": "Продукт А",
    "Склад": "Центральный",
    "Организация": "ООО Компания",
    "Производитель": "Завод №1"
  },
  "data": [
    {
      "period": "2026-01-31",
      "value": 1250.0,
      "raw_sum": 125000.0,
      "raw_qty": 100.0,
      "anomaly_type": null
    },
    {
      "period": "2026-02-28",
      "value": 3100.0,
      "raw_sum": 310000.0,
      "raw_qty": 100.0,
      "anomaly_type": "SPIKE"
    },
    {
      "period": "2026-03-31",
      "value": 1100.0,
      "raw_sum": 110000.0,
      "raw_qty": 100.0,
      "anomaly_type": null
    }
  ]
}
```

**Response (404 Not Found)**:
```json
{
  "error": "not_found",
  "message": "No data found for specified dimensions"
}
```

---

## Data Source Endpoints

### GET /api/v1/sources

**Purpose**: List all configured data sources.

**Response (200 OK)**:
```json
{
  "sources": [
    {
      "id": "reg_cost_price",
      "name": "Себестоимость производства",
      "endpoint": "http://1c-server/base/hs/analytics/v1",
      "register_name": "ПартииТоваровНаСкладахПоПроизводителям",
      "enabled": true,
      "last_analysis": {
        "run_id": "550e8400-e29b-41d4-a716-446655440000",
        "date": "2026-03-17T10:00:00Z",
        "anomaly_count": 5
      }
    }
  ]
}
```

---

### POST /api/v1/sources

**Purpose**: Create a new data source.

**Request**:
```json
{
  "id": "reg_cost_price",
  "name": "Себестоимость производства",
  "endpoint": "http://1c-server/base/hs/analytics/v1",
  "register_name": "ПартииТоваровНаСкладахПоПроизводителям",
  "dimensions": ["Период", "Номенклатура", "Склад", "Организация", "Производитель"],
  "metric_fields": {
    "sum": "Сумма",
    "qty": "Количество"
  },
  "threshold_rules": {
    "spike_pct": 20.0,
    "spike_zscore": 3.0,
    "spike_logic": "OR",
    "moving_avg_window": 6,
    "trend_window": 3,
    "trend_min_points": 5,
    "ratio_min": null,
    "ratio_max": null,
    "zero_neg_enabled": true,
    "missing_enabled": true,
    "ratio_enabled": false
  },
  "auth": {
    "type": "basic",
    "user": "service_user",
    "pass": "secret_password"
  },
  "enabled": true
}
```

**Response (201 Created)**:
```json
{
  "id": "reg_cost_price",
  "name": "Себестоимость производства",
  "enabled": true
}
```

**Response (400 Bad Request)**:
```json
{
  "error": "validation_error",
  "message": "Field 'metric_fields.qty' is required",
  "details": {
    "field": "metric_fields.qty",
    "reason": "required"
  }
}
```

**Response (409 Conflict)**:
```json
{
  "error": "duplicate_id",
  "message": "Source with id 'reg_cost_price' already exists"
}
```

---

### PUT /api/v1/sources/{id}

**Purpose**: Update an existing data source.

**Request**: Same as POST

**Response (200 OK)**:
```json
{
  "id": "reg_cost_price",
  "name": "Себестоимость производства",
  "enabled": true
}
```

**Response (404 Not Found)**:
```json
{
  "error": "not_found",
  "message": "Source 'reg_cost_price' not found"
}
```

---

### DELETE /api/v1/sources/{id}

**Purpose**: Delete a data source.

**Response (204 No Content)**

**Response (404 Not Found)**:
```json
{
  "error": "not_found",
  "message": "Source 'reg_cost_price' not found"
}
```

---

### POST /api/v1/sources/{id}/test

**Purpose**: Test connectivity to 1C HTTP service.

**Response (200 OK)**:
```json
{
  "status": "ok",
  "message": "Connection successful",
  "response_time_ms": 45
}
```

**Response (401 Unauthorized)**:
```json
{
  "status": "error",
  "message": "Authentication failed: invalid credentials"
}
```

**Response (404 Not Found)**:
```json
{
  "status": "error",
  "message": "Register 'ПартииТоваровНаСкладахПоПроизводителям' not found in 1C configuration"
}
```

**Response (500 Internal Error)**:
```json
{
  "status": "error",
  "message": "1C service unavailable: connection timeout"
}
```

---

### GET /api/v1/sources/{id}/preview

**Purpose**: Preview raw data from 1C before running analysis.

**Query Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `date_from` | date | Yes | Start date |
| `date_to` | date | Yes | End date |
| `limit` | int | No | Max records to return (default: 10, max: 100) |

**Response (200 OK)**:
```json
{
  "source_id": "reg_cost_price",
  "register_name": "ПартииТоваровНаСкладахПоПроизводителям",
  "date_from": "2026-01-01",
  "date_to": "2026-03-31",
  "record_count": 87,
  "data": [
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
      "Сумма": 310000.00,
      "Количество": 100.0
    }
  ]
}
```

**Response (400 Bad Request)**:
```json
{
  "error": "missing_parameter",
  "message": "Parameter 'date_from' is required"
}
```

---

## Error Response Format

All error responses follow this schema:

```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "details": {...}  // Optional: additional context
}
```

**Standard Error Codes**:
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `validation_error` | 400 | Request validation failed |
| `invalid_source` | 400 | Data source not found |
| `invalid_date_range` | 400 | date_from > date_to |
| `missing_parameter` | 400 | Required query param missing |
| `unauthorized` | 401 | Authentication failed |
| `not_found` | 404 | Resource not found |
| `duplicate_id` | 409 | Resource already exists |
| `analysis_failed` | 500 | Analysis execution failed |
| `internal_error` | 500 | Unexpected server error |

---

## Pagination Format

All list endpoints use this pagination schema:

```json
{
  "page": 1,
  "page_size": 50,
  "total_count": 123,
  "has_next": true
}
```

---

## Versioning

API version is included in the path: `/api/v1/...`

Breaking changes require a new major version (`/api/v2/...`).
