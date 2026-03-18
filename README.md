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
│   ├── detector.py         # Реальный детектор: SPIKE, TREND_BREAK, ZERO_NEG, MISSING, RATIO, MISSING_DATA
│   └── mock_detector.py    # Заглушка (сохранена для справки)
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
│   ├── http_client.py      # Реальный async httpx клиент 1С: пагинация, BasicAuth
│   ├── mock_1c_adapter.py  # Заглушка (сохранена для справки)
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

## Подключение источника данных

1. Откройте раздел **Источники** в UI (`/sources`) или используйте API.
2. Нажмите «Добавить источник» и заполните форму:

   | Поле | Описание | Пример |
   |------|----------|--------|
   | `id` | Уникальный идентификатор (латиница, без пробелов) | `sales_by_product` |
   | `name` | Человекочитаемое название | `Продажи по номенклатуре` |
   | `endpoint` | Базовый URL HTTP-сервиса 1С | `http://1c-server/base/hs/analytics/v1` |
   | `register_name` | Имя регистра накопления в 1С | `SalesByProduct` |
   | `dimensions` | Список измерений для группировки | `["Warehouse", "Product"]` |
   | `metric_fields.sum` | Поле суммы из строки 1С | `AmountTurnover` |
   | `metric_fields.qty` | Поле количества из строки 1С | `QuantityTurnover` |
   | `auth.type` | Тип авторизации: `none` или `basic` | `basic` |
   | `auth.user` / `auth.password` | Учётные данные для Basic Auth | — |

3. Нажмите «Проверить соединение» — сервис выполнит тестовый запрос к 1С и покажет статус и время ответа.
4. Сохраните источник. Он появится в выпадающем списке на главной странице.

---

## Контракт 1С HTTP

Сервис отправляет GET-запросы на `{endpoint}/data` с параметрами:

```
register_name, date_from, date_to, page, page_size
```

1С **должна** возвращать JSON следующего формата:

```json
{
  "data": [
    {
      "Период": "2026-01-31",
      "Warehouse": "Центральний",
      "Product": "Продукт A",
      "AmountTurnover": 15000.0,
      "QuantityTurnover": 30.0
    }
  ],
  "has_next": false
}
```

- `"Период"` — обязательное поле, дата в формате `YYYY-MM-DD` или `YYYY-MM-DDTHH:MM:SS`.
- Имена полей измерений и метрик соответствуют `dimensions` и `metric_fields` конфигурации источника.
- `"has_next": true` → сервис автоматически запросит следующую страницу (`page_size` по умолчанию 500).
- Если 1С требует авторизацию — настройте `auth.type: "basic"` в источнике данных.

Подробный контракт: `specs/001-anomaly-detection-mvp/contracts/1c-http.md`.

---

## Логи

Логирование реализовано через **Loguru**. Каждый HTTP-запрос фиксируется middleware:

```
2026-03-18 12:00:01 | DEBUG    | → POST /api/v1/analysis/run
2026-03-18 12:00:02 | DEBUG    | ← 200 POST /api/v1/analysis/run [843ms]
2026-03-18 12:00:05 | WARNING  | ← 504 POST /api/v1/analysis/run [10043ms]
```

Логи пишутся в два места:
- **Консоль** (stderr) — всегда, уровень DEBUG и выше.
- **Файл** `backend/logs/debug.log` — ротация при 10 МБ, хранение 7 дней.

При запуске через Docker логи файла доступны через volume `backend-logs` (см. ниже).

---

## Запуск в Docker

```bash
# Собрать образ и запустить сервис
docker-compose up --build

# В фоне
docker-compose up --build -d

# Просмотр логов контейнера
docker-compose logs -f backend
```

Сервис будет доступен на `http://localhost:8000`.

Данные и логи хранятся в именованных volumes:

| Volume | Путь внутри контейнера | Содержимое |
|--------|------------------------|------------|
| `backend-data` | `/app/data` | SQLite БД (`anomaly_detection.db`) |
| `backend-logs` | `/app/logs` | Файл логов (`debug.log`) |

Чтобы прочитать лог-файл напрямую:
```bash
docker-compose exec backend cat /app/logs/debug.log
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

Результаты: **57 тестов, 73% покрытие**

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
| Phase 4 | Реальная интеграция с 1С HTTP, алгоритмы детекции | ✅ Завершена |
| Phase 5–8 | Динамический UI, Docker, логирование, полный тест-сьют | ✅ Завершена |

---

## Лицензия

Proprietary. Все права защищены.
