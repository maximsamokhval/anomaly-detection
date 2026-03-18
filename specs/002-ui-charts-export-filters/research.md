# Research: UI Charts, Export & Filters

**Date**: 2026-03-18
**Feature**: 002-ui-charts-export-filters

## Decision 1: Chart Library for Time Series

**Decision**: Plotly.js 2.32 (CDN)

**Rationale**:
- Пользователь явно указал Plotly.js как предпочтительный вариант
- Встроенный zoom/pan/reset (`config.displayModeBar`) без плагинов
- Несколько трасс (`scatter` traces) с разными цветами/маркерами — нативная поддержка нескольких групп точек, что критично для цветового кодирования 6 типов аномалий
- `hovertemplate` позволяет отображать произвольный HTML в тултипе
- `config: { responsive: true }` обеспечивает автоматический resize при изменении ширины окна
- CDN: `https://cdn.plot.ly/plotly-2.32.0.min.js`

**Alternatives Considered**:
- **ApexCharts 3**: Хорошая альтернатива (~400KB), богатый API, но пользователь явно выбрал Plotly
- **Lightweight Charts (TradingView)**: Оптимален для OHLC/финансовых рядов, ~40KB, но нет нативных scatter markers для аномалий
- **Chart.js 4 + плагины**: Текущая реализация; zoom требует `chartjs-plugin-zoom` + `hammerjs`; тултипы кастомизируются сложнее

## Decision 2: Excel Export Library

**Decision**: SheetJS (xlsx.js) 0.20 — клиентская генерация

**Rationale**:
- Стандарт де-факто для клиентского XLSX в браузере
- Не требует изменений в backend API
- CDN: `https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js`
- API: `XLSX.utils.aoa_to_sheet(rows)` → `XLSX.utils.book_new()` → `XLSX.writeFile(wb, name)`
- Поддерживает кириллицу в заголовках и данных без дополнительных настроек

**Alternatives Considered**:
- **Серверный эндпоинт `GET /api/v1/anomalies/export`**: Потребует нового API-маршрута, серверной зависимости (openpyxl), изменений тестов — избыточно для MVP
- **ExcelJS**: ~2MB CDN, более сложный API, оправдан для форматирования ячеек — излишне

## Decision 3: Walking Skeleton — стратегия миграции

**Decision**: Аддитивная инкрементальная миграция без фича-флагов

**Rationale**:
- Plotly.js затрагивает только одну страницу (`drilldown.html`) — нет смысла в механизме A/B переключения
- Chart.js и Plotly.js могут сосуществовать в base.html без конфликтов (разные глобальные объекты: `Chart` vs `Plotly`)
- Порядок фаз: добавить → мигрировать страницу → удалить старое → следующая фича
- Каждая фаза заканчивается рабочим состоянием приложения

**Alternatives Considered**:
- **Фича-флаг `?chart=plotly`**: Избыточен, усложняет код, нет потребности в параллельной поддержке
- **Миграция всех страниц сразу**: Повышает риск регрессии; нарушает требование "каждая задача не ломает UI"

## Decision 4: Цветовая схема легенды

**Decision**: Сохранить текущие цвета типов аномалий из heatmap.html

Текущая схема (из heatmap.js):
- `ZERO_NEG` → `#DC2626` (красный)
- `SPIKE` → `#F59E0B` (жёлтый/оранжевый)
- `RATIO` → `#8B5CF6` (фиолетовый)
- `TREND_BREAK` → `#3B82F6` (синий)
- `MISSING` → `#6B7280` (серый)
- `MISSING_DATA` → `#111827` (тёмно-серый/чёрный)
- Норма → `#22C55E` (зелёный) — для drilldown

**Rationale**: Консистентность цветов между heatmap и drilldown критична для UX — пользователь видит один и тот же цвет типа на обеих страницах. Это же значит, что цветовые константы следует вынести в одно место (JS-объект в base.html или inline в каждом шаблоне).

## Decision 5: Фильтрация — клиентская vs серверная

**Decision**: Клиентская фильтрация по данным, уже загруженным на страницу

**Rationale**:
- Текущая таблица (`table.html`) уже загружает данные через `GET /api/v1/anomalies` с server-side фильтрацией (query params)
- Новые фильтры (текстовый поиск по dimensions, порог %) добавляются **поверх** существующих server-side фильтров: тип и диапазон дат → сервер; текст и порог → клиент
- Мультивыбор типов → передаётся как множественный `type` параметр (API уже поддерживает)
- Это гибридный подход: грубая фильтрация на сервере, тонкая — на клиенте
