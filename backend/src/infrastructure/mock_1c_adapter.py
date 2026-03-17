"""Mock 1C HTTP adapter for development before real 1C service is available.

Returns hardcoded test data with known anomaly patterns for testing.
"""

from datetime import date


async def fetch_1c_data_mock(
    endpoint: str,
    register_name: str,
    date_from: date,
    date_to: date,
    dimensions: list[str] | None = None,
    organization: str | None = None,
    warehouse: str | None = None,
    page: int = 1,
    page_size: int = 500,
) -> dict:
    """Mock 1C HTTP service response with test data.

    Returns data with known anomaly patterns:
    - Product A: SPIKE in February (148% increase)
    - Product B: ZERO_NEG in January (negative value)
    - Product C: TREND_BREAK in March (trend reversal)
    - Product D: MISSING data for February
    - Product E: Normal data (no anomalies)
    """
    # Generate mock data for 5 products
    data = []

    # Product A - SPIKE in February
    data.extend(
        [
            {
                "Период": "2026-01-31",
                "Номенклатура": "Продукт A",
                "Склад": "Центральный",
                "Организация": "ООО Компания",
                "Производитель": "Завод №1",
                "Сумма": 125000.0,
                "Количество": 100.0,
            },
            {
                "Период": "2026-02-28",
                "Номенклатура": "Продукт A",
                "Склад": "Центральный",
                "Организация": "ООО Компания",
                "Производитель": "Завод №1",
                "Сумма": 310000.0,  # SPIKE: 148% increase
                "Количество": 100.0,
            },
            {
                "Период": "2026-03-31",
                "Номенклатура": "Продукт A",
                "Склад": "Центральный",
                "Организация": "ООО Компания",
                "Производитель": "Завод №1",
                "Сумма": 105000.0,
                "Количество": 100.0,
            },
        ]
    )

    # Product B - ZERO_NEG in January
    data.extend(
        [
            {
                "Период": "2026-01-31",
                "Номенклатура": "Продукт B",
                "Склад": "Центральный",
                "Организация": "ООО Компания",
                "Производитель": "Завод №1",
                "Сумма": -5000.0,  # ZERO_NEG: negative value
                "Количество": 50.0,
            },
            {
                "Период": "2026-02-28",
                "Номенклатура": "Продукт B",
                "Склад": "Центральный",
                "Организация": "ООО Компания",
                "Производитель": "Завод №1",
                "Сумма": 80000.0,
                "Количество": 50.0,
            },
            {
                "Период": "2026-03-31",
                "Номенклатура": "Продукт B",
                "Склад": "Центральный",
                "Организация": "ООО Компания",
                "Производитель": "Завод №1",
                "Сумма": 82000.0,
                "Количество": 50.0,
            },
        ]
    )

    # Product C - TREND_BREAK in March
    data.extend(
        [
            {
                "Период": "2026-01-31",
                "Номенклатура": "Продукт C",
                "Склад": "Центральный",
                "Организация": "ООО Компания",
                "Производитель": "Завод №1",
                "Сумма": 50000.0,
                "Количество": 100.0,
            },
            {
                "Период": "2026-02-28",
                "Номенклатура": "Продукт C",
                "Склад": "Центральный",
                "Организация": "ООО Компания",
                "Производитель": "Завод №1",
                "Сумма": 55000.0,  # +10% trend
                "Количество": 100.0,
            },
            {
                "Период": "2026-03-31",
                "Номенклатура": "Продукт C",
                "Склад": "Центральный",
                "Организация": "ООО Компания",
                "Производитель": "Завод №1",
                "Сумма": 45000.0,  # TREND_BREAK: -18% reversal
                "Количество": 100.0,
            },
        ]
    )

    # Product D - MISSING February
    data.extend(
        [
            {
                "Период": "2026-01-31",
                "Номенклатура": "Продукт D",
                "Склад": "Центральный",
                "Организация": "ООО Компания",
                "Производитель": "Завод №1",
                "Сумма": 90000.0,
                "Количество": 100.0,
            },
            # MISSING: February data
            {
                "Период": "2026-03-31",
                "Номенклатура": "Продукт D",
                "Склад": "Центральный",
                "Организация": "ООО Компания",
                "Производитель": "Завод №1",
                "Сумма": 92000.0,
                "Количество": 100.0,
            },
        ]
    )

    # Product E - Normal data (no anomalies)
    data.extend(
        [
            {
                "Период": "2026-01-31",
                "Номенклатура": "Продукт E",
                "Склад": "Центральный",
                "Организация": "ООО Компания",
                "Производитель": "Завод №1",
                "Сумма": 100000.0,
                "Количество": 100.0,
            },
            {
                "Период": "2026-02-28",
                "Номенклатура": "Продукт E",
                "Склад": "Центральный",
                "Организация": "ООО Компания",
                "Производитель": "Завод №1",
                "Сумма": 102000.0,
                "Количество": 100.0,
            },
            {
                "Период": "2026-03-31",
                "Номенклатура": "Продукт E",
                "Склад": "Центральный",
                "Организация": "ООО Компания",
                "Производитель": "Завод №1",
                "Сумма": 104000.0,
                "Количество": 100.0,
            },
        ]
    )

    # Apply filters
    filtered_data = data
    if organization:
        filtered_data = [d for d in filtered_data if d.get("Организация") == organization]
    if warehouse:
        filtered_data = [d for d in filtered_data if d.get("Склад") == warehouse]

    # Pagination
    total_count = len(filtered_data)
    has_next = (page * page_size) < total_count
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_data = filtered_data[start_idx:end_idx]

    return {
        "register_name": register_name,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "has_next": has_next,
        "data": paginated_data,
    }


async def test_connection_mock(
    endpoint: str,
    register_name: str,
    auth: dict | None = None,
) -> dict:
    """Mock connection test - always succeeds in mock mode."""
    return {
        "status": "ok",
        "message": "Connection successful (mock)",
        "response_time_ms": 45,
    }
