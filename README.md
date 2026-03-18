# Financial Anomaly Detection Service

Сервис обнаружения финансовых аномалий в данных из регистров накопления 1С.
Позволяет аналитику вручную запускать анализ по любому источнику данных, мгновенно видеть аномалии на тепловой карте и детализировать подозрительные ячейки в виде временного ряда.

---

## Технологический стек

| Слой | Технология |
|------|-----------|
| API-фреймворк | FastAPI 0.109+ |
| Валидация / схемы | Pydantic v2 |
| ASGI-сервер | Uvicorn |
| База данных | SQLite (MVP) |
| Шаблонизатор | Jinja2 |
| Проверка типов | Pyright (standard) + mypy (strict) |
| Линтер / форматтер | Ruff |
| Тесты | pytest + pytest-asyncio |
| Управление зависимостями | uv |
| Язык | Python 3.12+ |

---

## Архитектура

Проект следует **Clean Architecture** с тремя слоями:

```
backend/src/
├── domain/                 # Бизнес-сущности и логика (без зависимостей)
│   ├── models.py           # Pydantic v2 BaseModel: DataSource, AnalysisRun, Anomaly, …
│   └── mock_detector.py    # Заглушка детектора (Phase 2)
├── api/                    # Слой API (FastAPI)
│   ├── schemas.py          # OpenAPI-схемы запросов и ответов
│   └── routes/             # Маршруты по доменам
│       ├── analysis.py     # POST /api/v1/analysis/run
│       ├── anomalies.py    # GET  /api/v1/anomalies
│       ├── sources.py      # CRUD /api/v1/sources
│       ├── heatmap.py      # GET  /api/v1/heatmap
│       └── timeseries.py   # GET  /api/v1/timeseries
├── infrastructure/         # Внешние адаптеры
│   ├── persistence/
│   │   ├── base.py         # Абстрактные репозитории
│   │   └── sqlite.py       # SQLite-реализация
│   ├── mock_1c_adapter.py  # Заглушка HTTP-адаптера 1С
│   └── logging.py          # Loguru
├── ui/                     # Server-side rendering
│   ├── templates/          # Jinja2 HTML-шаблоны
│   └── static/             # CSS / JS
└── main.py                 # Точка входа FastAPI
```

### Паттерны

- **Repository Pattern** — абстрактные интерфейсы + SQLite-реализация, легко заменяемые на PostgreSQL
- **Pydantic v2 Domain Models** — все доменные сущности описаны через `BaseModel` с полными Field-описаниями и примерами (используются в OpenAPI)
- **Typed Routes** — все endpoint'ы объявляют `request`-схему и `response_model`, FastAPI автоматически валидирует и документирует

---

## Типы аномалий

| Код | Описание |
|-----|----------|
| `SPIKE` | Значение отклоняется от скользящего среднего более чем на `spike_pct`% или `spike_zscore` σ |
| `TREND_BREAK` | Разворот устойчивого тренда за `trend_window` периодов |
| `ZERO_NEG` | Значение метрики ≤ 0 |
| `MISSING` | Ожидаемый период отсутствует в данных |
| `RATIO` | Отношение sum/qty выходит за пределы `ratio_min`…`ratio_max` |
| `MISSING_DATA` | Вся группа измерений отсутствует |

---

## Быстрый старт

### Требования

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

### Установка и запуск

```bash
# Клонировать репозиторий
git clone <repo-url>
cd anomaly-detection/backend

# Установить зависимости
uv sync

# Запустить сервер
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Приложение будет доступно:
- UI: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

---

## API

Базовый префикс: `/api/v1`

### Analysis

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/analysis/run` | Запустить анализ аномалий |
| `GET` | `/analysis/{run_id}` | Получить детали запуска |

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/api/v1/analysis/run \
  -H "Content-Type: application/json" \
  -d '{"source_id": "sales_by_product", "date_from": "2026-01-01", "date_to": "2026-03-31"}'
```

**Пример ответа:**
```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "anomaly_count": 5,
  "duration_ms": 12
}
```

### Anomalies

| Метод | Путь | Параметры | Описание |
|-------|------|-----------|----------|
| `GET` | `/anomalies` | `run_id`, `type`, `period_from`, `period_to` | Список аномалий с фильтрацией |

### Data Sources

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/sources` | Список источников |
| `POST` | `/sources` | Создать источник |
| `PUT` | `/sources/{id}` | Обновить источник |
| `DELETE` | `/sources/{id}` | Удалить источник |
| `POST` | `/sources/{id}/test` | Проверить соединение с 1С |
| `GET` | `/sources/{id}/preview` | Превью данных из регистра |

### Конфигурация источника данных

```json
{
  "id": "sales_by_product",
  "name": "Продажи по номенклатуре",
  "endpoint": "http://1c-server/base/hs/analytics/v1",
  "register_name": "SalesByProduct",
  "dimensions": ["Warehouse", "Product"],
  "metric_fields": {
    "sum": "AmountTurnover",
    "qty": "QuantityTurnover"
  },
  "threshold_rules": {
    "spike_pct": 20.0,
    "spike_zscore": 3.0,
    "spike_logic": "OR",
    "moving_avg_window": 6,
    "trend_window": 3,
    "zero_neg_enabled": true,
    "missing_enabled": true,
    "ratio_enabled": false
  },
  "auth": { "type": "none" },
  "enabled": true
}
```

---

## Разработка

### Запуск тестов

```bash
cd backend

# Все тесты с покрытием
uv run pytest tests/ -v

# Только контрактные тесты
uv run pytest tests/contract/ -v
```

Результаты: **20 тестов, 79% покрытие**

### Проверка типов

```bash
# Pyright (быстрая проверка)
uv run pyright src/

# mypy (строгая проверка)
uv run mypy src/
```

Результаты: **0 ошибок, 0 предупреждений** (Pyright standard mode)

### Линтинг

```bash
uv run ruff check src/
uv run ruff format src/
```

### Установка dev-зависимостей

```bash
uv sync --extra dev
```

---

## Структура базы данных (SQLite)

```sql
data_sources      -- конфигурация источников 1С
analysis_runs     -- история запусков анализа
anomalies         -- обнаруженные аномалии (индексы по run_id, source_id, type, period)
```

---

## Спецификации

Документация по разработке находится в `specs/001-anomaly-detection-mvp/`:

| Файл | Содержание |
|------|-----------|
| `spec.md` | User Stories и acceptance-сценарии |
| `data-model.md` | Модель данных |
| `plan.md` | Фазы реализации |
| `tasks.md` | Декомпозиция задач |
| `contracts/api.md` | API-контракт |
| `contracts/1c-http.md` | Контракт интеграции с 1С HTTP |

---

## Статус реализации

| Фаза | Описание | Статус |
|------|----------|--------|
| Phase 1 | Инфраструктура, модели, БД, UI-шаблоны | ✅ Завершена |
| Phase 2 | Walking Skeleton — mock-детектор, API-маршруты, контрактные тесты | ✅ Завершена |
| Phase 3 | OpenAPI-документация, Pydantic v2 доменные модели, Pyright | ✅ Завершена |
| Phase 4 | Реальная интеграция с 1С HTTP, алгоритмы детекции | 🔲 Запланировано |

---

## Лицензия

Proprietary. Все права защищены.
