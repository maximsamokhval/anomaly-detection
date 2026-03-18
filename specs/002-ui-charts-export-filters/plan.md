# Implementation Plan: UI — Charts, Export & Filters

**Branch**: `002-ui-charts-export-filters` | **Date**: 2026-03-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-ui-charts-export-filters/spec.md`

## Summary

Замена Chart.js на Plotly.js для временного ряда (drilldown), обогащение тултипов тепловой карты данными аномалий, клиентский экспорт в Excel через SheetJS, расширенная панель фильтров на странице таблицы, верификация адаптивности. Добавляются Pydantic response-схемы для `/heatmap` и `/timeseries` (OpenAPI → строгая типизация). Стратегия: **walking skeleton** — каждый коммит оставляет приложение рабочим; Chart.js сохраняется до полной миграции drilldown.

## Technical Context

**Language/Version**: Python 3.12 + Jinja2 (SSR); vanilla JS (ES2020, no bundler)
**Primary Dependencies**:
- Tailwind CSS 3 (CDN) — существующий UI-фреймворк
- Chart.js 4.4.0 (CDN) — заменяется Plotly.js на странице drilldown
- Plotly.js 2.32 (CDN, ~3.4 MB) — интерактивные графики с zoom, тултипами, легендой
- SheetJS (xlsx.js 0.20, CDN, ~1 MB) — клиентская генерация `.xlsx` без обращения к серверу
- Material Icons (уже подключены)

**Storage**: SQLite — не затрагивается (все изменения клиентские)
**Testing**: pytest (57 тестов) — не затрагивается; UI тестируется вручную
**Target Platform**: Modern browser (Chrome/Firefox/Edge), min screen 1280×768
**Project Type**: Server-rendered web app (Jinja2 + FastAPI)
**Performance Goals**: Экспорт 1000 строк < 3 сек; фильтрация < 500ms; тултип < 100ms
**Constraints**: Все JS-библиотеки через CDN, без npm/webpack; сохранить текущие Tailwind-стили
**Scale/Scope**: 1–5 тысяч аномалий за один прогон; до 50 измерений в тепловой карте

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Принцип | Статус | Обоснование |
|---------|--------|-------------|
| I. Detector Purity | ✅ PASS | Изменений в `domain/` нет |
| II. Manual Trigger Only | ✅ PASS | Новых фоновых задач нет; экспорт — синхронный клиентский код |
| III. Computed Metrics | ✅ PASS | Transformer не затрагивается |
| IV. DataSource as Config | ✅ PASS | Нет изменений в DataSource-модели |
| V. Repository Pattern | ✅ PASS | Нет изменений в persistence-слое |
| VI. Observability | ✅ PASS | График и данные остаются JSON; экспорт — бинарный XLSX только в браузере (исключение допустимо как клиентский формат) |

**Architecture Standards — Frontend**: Конституция разрешает замену Chart.js при сохранении SSR (Jinja2). Plotly.js и SheetJS добавляются через CDN — соответствует установленному паттерну.

## Project Structure

### Documentation (this feature)

```text
specs/002-ui-charts-export-filters/
├── plan.md              ← этот файл
├── research.md          ← Phase 0: выбор библиотек
├── data-model.md        ← Phase 1: FilterState, ExportRow
├── quickstart.md        ← Phase 1: гайд по ручному тестированию
└── tasks.md             ← Phase 2 (/speckit.tasks)
```

### Source Code (изменяемые файлы)

```text
backend/
├── ui/
│   ├── templates/
│   │   ├── base.html          # +Plotly.js CDN, +SheetJS CDN; Chart.js остаётся до T-last
│   │   ├── heatmap.html       # обогащение тултипов; адаптивность (легенда уже есть)
│   │   ├── drilldown.html     # Chart.js → Plotly.js; тултипы; легенда ряда; run_id guard
│   │   └── table.html         # +мультифильтр типов, +текстовый поиск, +порог %, +экспорт
│   └── static/
│       └── styles.css         # только точечные правки при необходимости
├── src/api/
│   ├── schemas.py             # +HeatmapCellSchema, HeatmapResponse, TimeseriesPointSchema, TimeseriesResponse
│   └── routes/
│       ├── heatmap.py         # response_model=HeatmapResponse; +pct_change/current_value в cell
│       └── timeseries.py      # response_model=TimeseriesResponse
└── tests/contract/            # +/- тесты если необходимо
```

**Structure Decision**: Single-project, SSR. Основные изменения в `ui/`; добавляются Pydantic-схемы в `src/api/schemas.py` и обновляются два route-файла для строгой типизации.

**Backlog (не входит в эту итерацию)**: Экспорт тепловой карты в Excel — вынесен в следующий спринт; требует отдельной задачи в `heatmap.html` + дополнительной SheetJS-функции для матрицы.

## Walking Skeleton Strategy

Ключевое требование пользователя: **каждая закрытая задача не должна ломать UI и приложение**.

Принцип реализации:
1. **Аддитивные изменения первыми** — сначала добавляем новые библиотеки (Plotly.js, SheetJS) *рядом* с существующими, не удаляя Chart.js.
2. **Страница за страницей** — мигрируем drilldown на Plotly.js полностью, только потом переходим к следующей странице.
3. **Chart.js удаляется последним** — только после полной миграции drilldown; до этого обе библиотеки сосуществуют.
4. **Фича-флаг не нужен** — поскольку drilldown — единственная страница с Chart.js, миграция атомарна (одна страница, один коммит).
5. **Каждый коммит проверяется вручную** — открыть /heatmap, /drilldown, /table, убедиться в отсутствии JS-ошибок.

## Phases

### Phase A — Подготовка: добавление новых библиотек в base.html

**Цель**: Plotly.js и SheetJS доступны на всех страницах; Chart.js остаётся.
**Риск**: нулевой — старый код не меняется.

Задачи:
- A1: Добавить Plotly.js CDN в `base.html` (после Chart.js, перед `</head>`)
- A2: Добавить SheetJS CDN в `base.html`

**Результат**: `/heatmap`, `/drilldown`, `/table` работают идентично текущему состоянию.

---

### Phase B — Heatmap: легенда и адаптивность

**Цель**: Легенда типов аномалий, контейнер без горизонтальной прокрутки.
**Риск**: низкий — только добавление HTML/CSS; данные и логика не меняются.

Задачи:
- B1: Добавить статическую легенду типов аномалий в `heatmap.html` (цвет + название + описание для каждого из 6 типов)
- B2: Проверить и исправить контейнер тепловой карты: `overflow-x: hidden` на основном контейнере, `overflow-y: auto` для таблицы при большом числе строк
- B3: Убедиться, что легенда видна без прокрутки при 1280×768

**Результат**: Тепловая карта работает как прежде + появляется легенда.

---

### Phase C — Drilldown: миграция Chart.js → Plotly.js

**Цель**: Временной ряд на Plotly.js с интерактивным zoom, тултипами, легендой.
**Риск**: средний — полная замена JS-кода на drilldown; Chart.js в base.html сохраняется.

Задачи:
- C1: Заменить инициализацию Chart.js в `drilldown.html` на `Plotly.newPlot()`
- C2: Реализовать два типа трасс: `scatter` для нормальных точек, отдельные `scatter` трассы для каждого типа аномалии (отдельный цвет и маркер)
- C3: Настроить `hovertemplate` с полями: период, значение, тип аномалии, отклонение %
- C4: Добавить `layout.legend` с описанием цветового кодирования
- C5: Настроить `config: { responsive: true, displayModeBar: true }` для zoom/pan/reset

**Результат**: `/drilldown` работает на Plotly.js; `/heatmap`, `/table`, остальные страницы не тронуты.

---

### Phase D — Удаление Chart.js

**Цель**: Удалить неиспользуемую библиотеку из base.html и static/chart.js.
**Риск**: низкий — только после успешной Phase C.

Задачи:
- D1: Удалить `<script src="chart.js">` из `base.html`
- D2: Удалить `/static/chart.js` или очистить его содержимое
- D3: Удалить `chart.js` CDN из `base.html`

**Результат**: base.html загружает только Plotly.js, SheetJS, Tailwind.

---

### Phase E — Table: расширенная фильтрация

**Цель**: Мультивыбор типов, текстовый поиск по измерениям, порог отклонения.
**Риск**: низкий — расширение существующей JS-логики фильтрации; API не меняется.

Задачи:
- E1: Заменить одиночный select типа аномалии на группу чекбоксов (все 6 типов)
- E2: Добавить текстовое поле поиска по измерениям (debounce 300ms, поиск по `dimensions` объекту)
- E3: Добавить числовое поле «Мін. відхилення %» (фильтрация по `|pct_change|`)
- E4: Реализовать кнопку «Скинути фільтри» — сбрасывает все поля
- E5: Обновить функцию `applyFilters()` для обработки всех новых параметров

**Результат**: Таблица работает со всеми комбинациями фильтров; старые фильтры продолжают работать.

---

### Phase F — Table: экспорт в Excel

**Цель**: Кнопка «Експорт в Excel» скачивает `.xlsx` с активными фильтрами.
**Риск**: низкий — клиентский код SheetJS; никаких изменений в API.

Задачи:
- F1: Добавить кнопку «Експорт в Excel» в `table.html` (рядом с фильтрами)
- F2: Реализовать функцию `exportToExcel()`:
  - Собрать текущий отфильтрованный массив аномалий из состояния страницы
  - Сформировать массив строк с колонками: Період, Тип аномалії, Поточне значення, Попереднє значення, Відхилення %, Z-score, Виміри (JSON-строка)
  - Создать `workbook` через `XLSX.utils.aoa_to_sheet()`, добавить `workbook`, вызвать `XLSX.writeFile()`
- F3: Обработать случай пустой выборки (файл с заголовком без строк)

**Результат**: Экспорт работает; таблица и фильтры не затронуты.

---

### Phase G — Финальная верификация и responsive-правки

**Цель**: Проверить все страницы при 1280px; устранить оставшиеся overflow-проблемы.

Задачи:
- G1: Проверить `/heatmap` при >20 измерениях — вертикальный скролл внутри контейнера
- G2: Проверить `/drilldown` — Plotly responsive:true работает при изменении размера окна
- G3: Проверить `/table` — панель фильтров не выходит за 1280px
- G4: Добавить `overflow-x: hidden` на `<body>` в styles.css если нужно

## Technology Decisions

### Chart Library: Plotly.js

| Вариант | Размер | Zoom | Тултипы | Легенда | Вердикт |
|---------|--------|------|---------|---------|---------|
| Chart.js 4 (текущий) | ~200KB | ручной плагин | базовые | ✅ | заменяется |
| **Plotly.js 2.32** | ~3.4MB | ✅ built-in | ✅ rich | ✅ built-in | **выбран** |
| ApexCharts 3 | ~400KB | ✅ | ✅ | ✅ | альтернатива |
| Lightweight Charts | ~40KB | ✅ | базовые | ❌ | только финансовые |

**Обоснование выбора Plotly.js**: пользователь явно указал Plotly.js; встроенный zoom/pan/reset без дополнительного кода; богатые тултипы с `hovertemplate`; хорошая поддержка scatter с несколькими трассами для цветового кодирования аномалий; CDN-совместим.

### Excel Export: SheetJS (xlsx.js)

| Вариант | Размер | Клиентская генерация | Вердикт |
|---------|--------|----------------------|---------|
| **SheetJS 0.20** | ~1MB | ✅ браузер | **выбран** |
| ExcelJS | ~2MB | частично | больше размер |
| Серверный эндпоинт | 0KB JS | N/A | требует изменений API |

**Обоснование**: SheetJS — стандарт де-факто для клиентского XLSX; не требует изменений backend; CDN-совместим.

### OpenAPI → Pydantic Strict Typing

**Decision**: Добавить Pydantic v2 `response_model` для `/heatmap` и `/timeseries`; обогатить cell-объект полями `pct_change`, `current_value`, `previous_value`.

**Rationale**:
- Текущие маршруты возвращают `dict` — FastAPI генерирует пустую OpenAPI-схему (`{}`)
- JS-код templates обращается к `cell.pct_change` и `point.value` по магическим строкам без проверки
- Добавление `response_model` гарантирует: (1) валидацию ответа на сервере, (2) точную OpenAPI-документацию, (3) соответствие JS-полей Pydantic-именам
- Обогащение cell добавляет `pct_change`, `current_value`, `previous_value` → тултипы heatmap получают данные для US1 acceptance 2

**Walking Skeleton**: схемы добавляются как аддитивные изменения; `response_model` добавляется после схем; JS обновляется после API.

## Constitution Check (Post-Design)

Повторная проверка после Phase 1 дизайна:

| Принцип | Статус | Примечание |
|---------|--------|------------|
| VI. Observability | ✅ PASS | XLSX — клиентский формат; API-ответы остаются JSON |
| VI. Observability | ✅ PASS | Plotly.js получает данные из существующих JSON API-ответов |
| Все остальные | ✅ PASS | Без изменений vs. первичной проверки |
