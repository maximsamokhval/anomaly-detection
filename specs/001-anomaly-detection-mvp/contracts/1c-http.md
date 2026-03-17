# 1C HTTP Service Contract

**Created**: 2026-03-17
**Feature**: 001-anomaly-detection-mvp
**Source**: BRD Section 7

---

## Overview

The 1C HTTP service provides access to accumulation register data for anomaly detection.

**Status**: Needs to be developed in parallel with the anomaly detection service.

---

## General Parameters

| Parameter | Value |
|-----------|-------|
| Protocol | HTTP/HTTPS, REST |
| Format | JSON |
| Authentication | Basic Auth (optional in MVP for internal network) |
| Base URL | `http://<1c-server>/<base>/hs/analytics/v1` |

---

## Endpoints

### GET /health

**Purpose**: Health check for connectivity testing.

**Request**:
```http
GET /hs/analytics/v1/health
Authorization: Basic <base64(login:password)>
```

**Response (200 OK)**:
```json
{
  "status": "ok",
  "timestamp": "2026-03-17T08:00:00"
}
```

---

### GET /data

**Purpose**: Retrieve accumulation register data for a period.

**Request**:
```http
GET /hs/analytics/v1/data
  ?register_name=ПартииТоваровНаСкладахПоПроизводителям
  &date_from=2026-01-01
  &date_to=2026-03-31
  &dimensions=Номенклатура,Склад,Организация,Производитель
  &organization=ООО+Компания
  &warehouse=Центральный
  &page=1
  &page_size=500

Authorization: Basic <base64(login:password)>
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `register_name` | string | **Yes** | Accumulation register name in 1C |
| `date_from` | string (YYYY-MM-DD) | **Yes** | Period start (inclusive) |
| `date_to` | string (YYYY-MM-DD) | **Yes** | Period end (inclusive) |
| `dimensions` | string (comma-separated) | No | Dimension names for grouping. If omitted, returns all dimensions |
| `organization` | string | No | Filter by Organization dimension |
| `warehouse` | string | No | Filter by Warehouse dimension |
| `page` | int | No | Page number (default: 1) |
| `page_size` | int | No | Records per page (default: 500, max: 1000) |

**Response (200 OK)**:
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

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `register_name` | string | Echo of request parameter |
| `date_from` / `date_to` | string | Echo of request parameters |
| `page` / `page_size` | int | Current pagination |
| `total_count` | int | Total records for period (for pagination) |
| `has_next` | bool | Whether next page exists |
| `data` | array | Array of register records |
| `data[].Период` | string (YYYY-MM-DD) | Period date |
| `data[].<Dimension>` | string | Dimension value (Cyrillic field names) |
| `data[].Сумма` | float | Sum resource |
| `data[].Количество` | float | Quantity resource |

**Response Codes**:

| Code | Condition |
|------|-----------|
| `200 OK` | Success |
| `400 Bad Request` | Missing required parameter (`register_name`, `date_from`) |
| `401 Unauthorized` | Invalid Basic Auth credentials |
| `404 Not Found` | Register not found in 1C configuration |
| `500 Internal Server Error` | 1C internal error |

**Error Response (400 Bad Request)**:
```json
{
  "error": "missing_parameter",
  "message": "Parameter 'register_name' is required",
  "timestamp": "2026-03-17T08:00:00"
}
```

**Error Response (404 Not Found)**:
```json
{
  "error": "register_not_found",
  "message": "Register 'ПартииТоваровНаСкладахПоПроизводителям' not found in configuration",
  "timestamp": "2026-03-17T08:00:00"
}
```

---

## Implementation Recommendations (1C)

### Data Query

```bsl
// 1C:Enterprise query example
ВЫБРАТЬ
    Период,
    Номенклатура,
    Склад,
    Организация,
    Производитель,
    СУММА(Сумма) КАК Сумма,
    СУММА(Количество) КАК Количество
ИЗ
    РегистрНакопления.ПартииТоваровНаСкладахПоПроизводителям.Обороты(
        &ДатаНач,
        &ДатаКон,
        ,
        )
СГРУППИРОВАТЬ ПО
    Период,
    Номенклатура,
    Склад,
    Организация,
    Производитель
УПОРЯДОЧИТЬ ПО
    Период
```

### Pagination

```bsl
// Use ПЕРВЫЕ N ПРОПУСТИТЬ M for pagination
ВЫБРАТЬ ПЕРВЫЕ &PageSize ПРОПУСТИТЬ &Offset
    ...
```

### HTTP Service Handler (1C)

```bsl
// HTTP service handler example
&HTTPService
&URLTemplate("/data{?register_name,date_from,date_to,dimensions,page,page_size}")
Функция GetDataHTTP(ЗапросHTTP, register_name, date_from, date_to, dimensions, page, page_size)
    
    // Validate required parameters
    Если register_name = Неопределено Тогда
        Возврат СформироватьОшибка(400, "missing_parameter", "Parameter 'register_name' is required");
    КонецЕсли;
    
    // Execute query
    Данные = ВыполнитьЗапросРегистра(register_name, date_from, date_to, dimensions, page, page_size);
    
    // Return JSON response
    Возврат СформироватьJSONОтвет(Данные);
    
КонецФункции
```

---

## Field Names

**Important**: Field names in JSON response MUST match 1C metadata names exactly (Cyrillic).

**Pilot Register Fields**:
- Dimensions: `Период`, `Номенклатура`, `Склад`, `Организация`, `Производитель`
- Resources: `Сумма`, `Количество`

---

## Mock Adapter (for Development)

Until the 1C HTTP service is ready, use a mock adapter:

```python
# infrastructure/mock_1c_adapter.py
async def fetch_1c_data(
    endpoint: str,
    register_name: str,
    date_from: date,
    date_to: date,
    dimensions: list[str] | None = None,
    page: int = 1,
    page_size: int = 500
) -> dict:
    """Mock 1C HTTP service response."""
    return {
        "register_name": register_name,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "page": page,
        "page_size": page_size,
        "total_count": 2,
        "has_next": False,
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
                "Сумма": 310000.00,  # SPIKE: 148% increase
                "Количество": 100.0
            }
        ]
    }
```

---

## Testing Checklist

- [ ] Health endpoint returns 200 OK
- [ ] Data endpoint returns correct JSON schema
- [ ] Field names are Cyrillic (matching 1C metadata)
- [ ] Pagination works correctly (page, page_size, total_count, has_next)
- [ ] Date filtering works (date_from, date_to inclusive)
- [ ] Dimension filtering works (organization, warehouse)
- [ ] 400 error for missing `register_name`
- [ ] 400 error for missing `date_from`
- [ ] 401 error for invalid credentials
- [ ] 404 error for non-existent register name
- [ ] Response time < 5 seconds for 1000 records

---

## Dependencies

This contract is a **blocking dependency** for Phase 4 (1C Integration).

**Development Track**:
- Anomaly detection service: Phases 1-3 can proceed with mock adapter
- 1C HTTP service: Must be complete before Phase 4
