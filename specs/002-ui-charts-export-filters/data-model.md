# Data Model: UI Charts, Export & Filters

**Date**: 2026-03-18
**Feature**: 002-ui-charts-export-filters
**Scope**: Клиентские структуры данных (JavaScript). Никаких изменений в backend-моделях нет.

---

## FilterState (JS object, in-memory)

Хранит активные параметры фильтрации в `table.html`.

```js
FilterState = {
  types: string[],          // массив активных типов: ["SPIKE", "ZERO_NEG", ...]
                            // пустой массив = все типы
  dimensionSearch: string,  // подстрока для поиска в значениях измерений; ""= без фильтра
  minPctChange: number|null,// абсолютный порог |pct_change|; null = без фильтра
  dateFrom: string,         // "YYYY-MM-DD"; "" = без ограничения
  dateTo: string,           // "YYYY-MM-DD"; "" = без ограничения
  sortBy: string,           // "period" | "pct_change" | "zscore" | "current_value"
  sortOrder: string,        // "asc" | "desc"
  page: number,             // текущая страница (1-based)
  pageSize: number,         // строк на страницу
}
```

**Правила**:
- `types` с пустым массивом = все типы отображаются (не фильтруется)
- `dimensionSearch` применяется как `string.includes()` по объединённым значениям объекта `dimensions`
- `minPctChange` фильтрует по `Math.abs(anomaly.pct_change) >= minPctChange`; аномалии с `pct_change === null` **не исключаются** (тип MISSING не имеет отклонения)

---

## AnomalyExportRow (массив для SheetJS)

Плоская строка для экспорта в Excel. Формируется из объекта аномалии на лету.

| Колонка (заголовок RU) | Источник из API | Тип |
|------------------------|-----------------|-----|
| Період | `anomaly.period` | string |
| Тип аномалії | `anomaly.anomaly_type` | string |
| Поточне значення | `anomaly.current_value` | number\|null |
| Попереднє значення | `anomaly.previous_value` | number\|null |
| Відхилення % | `anomaly.pct_change` | number\|null |
| Z-score | `anomaly.zscore` | number\|null |
| Виміри | `JSON.stringify(anomaly.dimensions)` | string |

**Порядок колонок** в файле: как в таблице выше.
**Пустые значения**: `null` → пустая ячейка (SheetJS по умолчанию).

---

## AnomalyColorMap (JS константа, shared)

Используется на heatmap.html (ячейки), drilldown.html (точки), legend-компонентах.

```js
const ANOMALY_COLORS = {
  SPIKE:        { color: '#F59E0B', label: 'Стрибок (Spike)' },
  TREND_BREAK:  { color: '#3B82F6', label: 'Зрив тренду' },
  ZERO_NEG:     { color: '#DC2626', label: 'Нульове/від\'ємне значення' },
  MISSING:      { color: '#6B7280', label: 'Відсутній період' },
  RATIO:        { color: '#8B5CF6', label: 'Аномальне співвідношення' },
  MISSING_DATA: { color: '#111827', label: 'Відсутні дані' },
  NORMAL:       { color: '#22C55E', label: 'Норма' },
};
```

**Размещение**: Инлайн в каждом шаблоне (drilldown.html, heatmap.html), чтобы не требовать дополнительного JS-файла. Обе страницы будут содержать идентичный объект.

---

## PlotlyTrace (структура для drilldown.html)

Plotly.js expects array of trace objects. One trace per anomaly type + one trace for normal points.

```js
traces = [
  {
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Норма',
    x: [...periods],          // string dates
    y: [...values],            // number|null
    marker: { color: '#22C55E', size: 6 },
    line: { color: '#22C55E', width: 1.5 },
    hovertemplate: 'Період: %{x}<br>Значення: %{y:.2f}<extra></extra>',
  },
  // Для каждого типа аномалии из ANOMALY_COLORS (кроме NORMAL):
  {
    type: 'scatter',
    mode: 'markers',
    name: ANOMALY_COLORS[type].label,
    x: [...anomalyPeriods],
    y: [...anomalyValues],
    marker: { color: ANOMALY_COLORS[type].color, size: 10, symbol: 'circle' },
    customdata: [...{ pct_change, zscore }],
    hovertemplate: 'Тип: ' + label + '<br>Значення: %{y:.2f}<br>Відхилення: %{customdata.pct_change:.1f}%<extra></extra>',
  }
]
```
