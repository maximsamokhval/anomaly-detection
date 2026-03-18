# Tasks: UI — Charts, Export & Filters

**Input**: Design documents from `/specs/002-ui-charts-export-filters/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Не требуются (UI-изменения; существующие 57 backend-тестов не затрагиваются).

**Walking Skeleton Rule**: Каждая завершённая задача оставляет `/heatmap`, `/drilldown`, `/table`, `/sources` в рабочем состоянии. Смотри smoke-checklist в quickstart.md.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Можно выполнять параллельно (разные файлы, нет зависимостей между задачами)
- **[Story]**: К какой user story относится задача (US1–US4)
- Указаны точные пути к файлам

---

## Phase 1: Setup — Подготовка библиотек в base.html

**Purpose**: Добавить Plotly.js и SheetJS CDN рядом с Chart.js. Chart.js остаётся нетронутым. Приложение продолжает работать идентично текущему состоянию.

**⚠️ CRITICAL**: Все последующие задачи зависят от доступности Plotly и XLSX глобально.

- [X] T001 Добавить Plotly.js 2.32 CDN-скрипт в `backend/ui/templates/base.html` после строки с Chart.js CDN: `<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>`
- [X] T002 Добавить SheetJS 0.20 CDN-скрипт в `backend/ui/templates/base.html` после Plotly.js: `<script src="https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js"></script>`

**Checkpoint**: Открыть `/heatmap` и `/table` в браузере, F12 → Console → нет ошибок. `window.Plotly` и `window.XLSX` доступны в консоли.

---

## Phase 2: Foundational — Строга типізація API + спільна кольорова схема

**Purpose**: (1) Додати Pydantic response-схеми для `/heatmap` і `/timeseries` — строга типізація OpenAPI → JS. (2) Узгодити кольорову константу між heatmap і drilldown.

**⚠️ CRITICAL**: Phase 3 (tултипи heatmap) залежить від збагачення cell API (T_api2). Phase 4 залежить від ANOMALY_COLORS (T003–T004).

- [X] T_api1 В `backend/src/api/schemas.py` додати Pydantic v2-схеми: `HeatmapCellSchema(row_idx, col_idx, type, intensity, anomaly_id, pct_change, current_value, previous_value)`, `HeatmapRowSchema(idx, values)`, `HeatmapColumnSchema(idx, period)`, `HeatmapResponse(run_id, row_dimensions, rows, columns, cells, legend)`. Всі поля — з анотаціями типів і `Field(description=...)`.
- [X] T_api2 В `backend/src/api/routes/heatmap.py` додати в словник cell-об'єкта поля `pct_change`, `current_value`, `previous_value` (вони вже доступні в `anomaly` при побудові `cell_map`). Оголосити `response_model=HeatmapResponse` на `@router.get`. Запустити `uv run pytest tests/ -q` — переконатися, що існуючі тести проходять.
- [X] T_api3 В `backend/src/api/schemas.py` додати `TimeseriesPointSchema(period, value, anomaly_type, pct_change, zscore)` і `TimeseriesResponse(run_id, dimensions, points)`. В `backend/src/api/routes/timeseries.py` оголосити `response_model=TimeseriesResponse`. Запустити тести.
- [X] T003 В `backend/ui/templates/heatmap.html` після рядка `const TYPE_CONFIG = { ... };` додати псевдонім `const ANOMALY_COLORS = TYPE_CONFIG;` та константу нормального значення: `ANOMALY_COLORS.NORMAL = {bg:'#22C55E', label:'Норма'};`. Існуючий код залишається незмінним (використовує `TYPE_CONFIG`), новий код (drilldown) використовуватиме `ANOMALY_COLORS`.
- [X] T004 В `backend/ui/templates/drilldown.html` додати ідентичну константу `ANOMALY_COLORS` в блок `<script>` (до Chart.js-коду, який буде замінено в Phase 4): той самий об'єкт з 7 ключами (6 типів + NORMAL) і полями `{bg, label}`.

**Checkpoint**: `/heatmap` рендериться з тими самими кольорами. `GET /api/v1/heatmap` повертає cell з полями `pct_change`, `current_value`. `/openapi.json` містить схему `HeatmapResponse`. Тести проходять.

---

## Phase 3: User Story 1 — Легенда тепловой карты и адаптивность (P1) 🎯 MVP

**Goal**: Постоянная легенда типов аномалий видна рядом с картой без прокрутки; карта не выходит за ширину экрана.

**Independent Test**: Открыть `/heatmap?run_id=...` — легенда видна сразу на экране, тултипы работают, горизонтальная прокрутка отсутствует при 1280×768.

- [X] T005 [US1] В `backend/ui/templates/heatmap.html` перевірити існуючу секцію `<!-- Legend -->` (рядки 55–87): переконатися, що кольори відповідають `TYPE_CONFIG` (ZERO_NEG=#DC2626, SPIKE=#F59E0B, RATIO=#8B5CF6, TREND_BREAK=#3B82F6, MISSING=#6B7280, MISSING_DATA=#111827). Легенда вже є — якщо кольори та підписи збігаються, задача виконана; якщо розходяться — скоригувати HTML легенди.
- [X] T005b [US1] В `backend/ui/templates/heatmap.html` збагатити атрибут `title` клітинки (рядок 182) даними з API (після T_api2): замінити `title="${cell.type}: ${cfg.label}"` на `title="${cell.type}: ${cfg.label}${cell.pct_change != null ? ' | ' + cell.pct_change.toFixed(1) + '%' : ''}${cell.current_value != null ? ' | знач: ' + cell.current_value.toFixed(2) : ''}"`. Це покриває US1 acceptance 2.
- [X] T006 [US1] В `backend/ui/templates/heatmap.html` перевірити контейнер `<div id="heatmap-container" class="overflow-x-auto">` (рядок 50): він вже має `overflow-x-auto`. Додати `max-height: 70vh; overflow-y: auto;` через Tailwind-клас `max-h-[70vh] overflow-y-auto` або inline-стиль якщо >20 рядків рендериться некоректно.
- [X] T007 [US1] В `backend/ui/templates/heatmap.html` перевірити що секція легенди (`<!-- Legend -->`) видна без прокрутки при 1280×768. Якщо легенда нижче першого скрола — перемістити її вище або зробити sticky. Переконатися, що `flex-wrap` на div легенди дозволяє перенос при вузькому вікні.

**Checkpoint**: Легенда видна без прокрутки. При уменьшении окна до 1280px горизонтальный скроллбар не появляется. Остальные страницы не затронуты.

---

## Phase 4: User Story 2 — Миграция drilldown на Plotly.js (P2)

**Goal**: Временной ряд на Plotly.js с zoom, тултипами, раздельными трассами для типов аномалий.

**Independent Test**: Открыть `/drilldown?run_id=...&dimensions=...` — график на Plotly с toolbar, тултипы на нормальных и аномальных точках, легенда ряда справа.

- [X] T008 [US2] В `backend/ui/templates/drilldown.html` заменить `<canvas id="chart">` на `<div id="chart" style="width:100%;height:400px"></div>`. Убрать все вызовы `new Chart(...)` и связанный Chart.js-код инициализации.
- [X] T009 [US2] В `backend/ui/templates/drilldown.html` реализовать функцию `buildPlotlyChart(seriesData)`: принимает массив точек из API `/api/v1/timeseries`, разделяет на нормальные точки и группы по типу аномалии. Для нормальных — trace `{type:'scatter', mode:'lines+markers', name:'Норма', marker:{color:'#22C55E', size:6}, line:{color:'#22C55E', width:1.5}, hovertemplate:'Період: %{x}<br>Значення: %{y:.2f}<extra></extra>'}`. Для каждого типа аномалии — отдельный trace `{type:'scatter', mode:'markers', name: ANOMALY_COLORS[type].label, marker:{color: ANOMALY_COLORS[type].color, size:10, symbol:'circle'}, customdata: [{pct_change, zscore}], hovertemplate:'Тип: TYPE<br>Значення: %{y:.2f}<br>Відхилення: %{customdata[0].pct_change:.1f}%<extra></extra>'}`.
- [X] T010 [US2] В `backend/ui/templates/drilldown.html` вызвать `Plotly.newPlot('chart', traces, layout, config)` где: `layout = {xaxis:{title:'Період'}, yaxis:{title:'Значення'}, legend:{orientation:'v'}, margin:{t:20,b:50,l:60,r:20}}`, `config = {responsive:true, displayModeBar:true, modeBarButtonsToRemove:['select2d','lasso2d']}`.
- [X] T011 [US2] В `backend/ui/templates/drilldown.html` обновить обработку пустого состояния: если API возвращает пустой массив — скрыть `<div id="chart">` и показать сообщение «Дані для цього виміру відсутні».
- [X] T011b [US2] В `backend/ui/templates/drilldown.html` додати guard на початку ініціалізаційного коду: перевірити наявність `run_id` у URL-параметрах (`new URLSearchParams(window.location.search).get('run_id')`). Якщо `run_id` відсутній — приховати контейнер графіка і показати повідомлення «Вкажіть run_id у параметрах URL або перейдіть з теплової карти». Покриває Edge Case зі специфікації.

**Checkpoint**: `/drilldown` работает на Plotly. Zoom/pan/reset кнопки работают. `/heatmap` и `/table` не изменились.

---

## Phase 5: Cleanup — Удаление Chart.js

**Purpose**: Удалить Chart.js из base.html после успешной миграции drilldown. Освобождает ~200KB загрузки на каждой странице.

**Depends on**: Phase 4 полностью завершена и проверена.

- [X] T012 Из `backend/ui/templates/base.html` удалить строку `<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>`.
- [X] T013 Из `backend/ui/templates/base.html` удалить строку `<script src="/static/chart.js"></script>`.
- [X] T014 Очистить содержимое `backend/ui/static/chart.js` (оставить файл с комментарием `/* Migrated to Plotly.js — see drilldown.html */`) или удалить файл и убрать его из маршрутов если он нигде больше не используется.

**Checkpoint**: F12 Network — `chart.js` и Chart CDN больше не загружаются. `window.Chart` — undefined. Все страницы работают.

---

## Phase 6: User Story 3 — Экспорт в Excel (P2)

**Goal**: Кнопка «Експорт в Excel» на странице таблицы скачивает `.xlsx` с текущими отфильтрованными данными.

**Independent Test**: Страница `/table` — нажать «Експорт в Excel» — браузер скачивает файл с русскими заголовками и строками, совпадающими с таблицей.

- [X] T015 [US3] В `backend/ui/templates/table.html` добавить кнопку «Експорт в Excel» рядом с заголовком или панелью фильтров: `<button onclick="exportToExcel()" class="...tailwind-classes..."><span class="material-icons text-sm">download</span> Експорт в Excel</button>`.
- [X] T016 [US3] В `backend/ui/templates/table.html` реализовать функцию `exportToExcel()`: взять текущий массив `allAnomalies` (отфильтрованный), сформировать заголовочную строку `['Період','Тип аномалії','Поточне значення','Попереднє значення','Відхилення, %','Z-score','Виміри']` (мова — українська, відповідно FR-013), для каждой аномалии создать строку значений (null → пустая строка; dimensions → `JSON.stringify(anomaly.dimensions)`), вызвать `const ws = XLSX.utils.aoa_to_sheet([headers, ...rows])`, `const wb = XLSX.utils.book_new()`, `XLSX.utils.book_append_sheet(wb, ws, 'Аномалії')`, `XLSX.writeFile(wb, 'anomalies_' + new Date().toISOString().slice(0,10) + '.xlsx')`.
- [X] T017 [US3] В `backend/ui/templates/table.html` добавить индикацию загрузки во время экспорта: изменить текст кнопки на «Завантаження...» и добавить `disabled` на время выполнения, восстановить после `XLSX.writeFile`. Для пустой выборки: разрешить экспорт (файл с заголовком без строк — допустимо).

**Checkpoint**: Скачанный `.xlsx` открывается в Excel/LibreOffice. Заголовки — кириллица. Строки совпадают с таблицей. При активных фильтрах в файле только отфильтрованные строки.

---

## Phase 7: User Story 4 — Расширенная фильтрация (P3)

**Goal**: Мультивыбор типов аномалий, текстовый поиск по измерениям, фильтр по минимальному проценту отклонения, кнопка сброса.

**Independent Test**: Страница `/table` — комбинировать фильтры (тип + текст + порог) — таблица обновляется без перезагрузки. Кнопка «Скинути» очищает все поля.

- [X] T018 [US4] В `backend/ui/templates/table.html` заменить одиночный `<select>` выбора типа аномалии на группу из 6 чекбоксов (по одному на каждый тип). Каждый чекбокс: `<label class="flex items-center gap-1 text-sm cursor-pointer"><input type="checkbox" value="SPIKE" checked onchange="debouncedFilterChange()"> <span class="w-3 h-3 rounded-sm inline-block" style="background:#F59E0B"></span> Стрибок</label>`. Начальное состояние: все чекбоксы отмечены (все типы показаны).
- [X] T019 [US4] В `backend/ui/templates/table.html` добавить поле текстового поиска по измерениям: `<input type="text" id="dimensionSearch" placeholder="Пошук за виміром..." oninput="debouncedFilterChange()" class="...">`. Реализовать `debouncedFilterChange` через `setTimeout` 300ms. Поиск — `Object.values(anomaly.dimensions).join(' ').toLowerCase().includes(query.toLowerCase())`.
- [X] T020 [US4] В `backend/ui/templates/table.html` добавить числовое поле «Мін. відхилення %»: `<input type="number" id="minPctChange" min="0" max="100" placeholder="0" oninput="debouncedFilterChange()" class="...">`. Логика: если `anomaly.pct_change === null` → строка не фильтруется (MISSING всегда проходит); иначе `Math.abs(anomaly.pct_change) >= minPctChange`.
- [X] T021 [US4] В `backend/ui/templates/table.html` реализовать единую функцию `debouncedFilterChange(delay=300)`: использует `clearTimeout`/`setTimeout` для debounce, затем вызывает `applyFilters()`. Функция `applyFilters()` собирает: выбранные типы из чекбоксов (`document.querySelectorAll('#typeFilters input:checked')`), текст из `#dimensionSearch`, порог из `#minPctChange`. Применяет все три условия через `Array.filter()` к `allAnomalies`. Сбрасывает `currentPage = 1`. Все `onchange`/`oninput` обработчики в T018–T020 должны вызывать только `debouncedFilterChange()`.
- [X] T022 [US4] В `backend/ui/templates/table.html` добавить кнопку «Скинути фільтри»: устанавливает все чекбоксы в `checked=true`, очищает `#dimensionSearch`, устанавливает `#minPctChange` в пустую строку, немедленно вызывает `applyFilters()` (без debounce — сброс должен быть мгновенным).

**Checkpoint**: Все комбинации фильтров работают. Тип + текст + порог работают вместе. Экспорт (Phase 6) экспортирует только отфильтрованные строки (т.к. использует `allAnomalies` после фильтрации).

---

## Phase 8: Polish — Верификация и responsive-правки

**Purpose**: Финальная проверка всех страниц при 1280px, устранение оставшихся проблем.

- [X] T023 [P] Проверить `/heatmap` при >20 строках: убедиться что `max-height` и `overflow-y:auto` работают на контейнере таблицы; если нет — добавить в `backend/ui/static/styles.css` класс `.heatmap-container { max-height: 70vh; overflow-y: auto; }` и применить к соответствующему div в `heatmap.html`.
- [X] T024 [P] Проверить `/drilldown` при resize окна: Plotly `responsive:true` должен перерисовывать график. Если нет — добавить `window.addEventListener('resize', () => Plotly.Plots.resize('chart'))` в `drilldown.html`.
- [X] T025 [P] Проверить `/table` при 1280px: панель фильтров (чекбоксы + текст + порог + кнопки) должна умещаться в строку или переноситься на новую без горизонтального скролла. При необходимости применить `flex-wrap: wrap` к контейнеру фильтров.
- [X] T026 Выполнить полный smoke-тест согласно `specs/002-ui-charts-export-filters/quickstart.md`: все 5 разделов (данные, легенда heatmap, Plotly drilldown, фильтры, экспорт). Отметить все пункты пройденными.
- [X] T027 Запустить `cd backend && uv run pytest tests/ -q` — убедиться, что все 57 тестов проходят (изменения UI не должны затрагивать backend).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Нет зависимостей — начинать сразу
- **Phase 2 (Foundational)**: Зависит от Phase 1. T_api1→T_api2→T_api3 (последовательно). T003/T004 параллельно после T_api1. Блокирует US1 (T005b требует T_api2) и US2 (T004 требует Phase 2).
- **Phase 3 (US1)**: T005 независим; T005b зависит от T_api2; T006, T007 независимы.
- **Phase 4 (US2)**: T008→T009→T010→T011→T011b (последовательно); T004 (Phase 2) должен быть готов.
- **Phase 5 (Cleanup)**: Зависит от Phase 4 — нельзя удалять Chart.js до завершения миграции
- **Phase 6 (US3)**: Зависит от Phase 1 (SheetJS) — не зависит от Phase 4/5
- **Phase 7 (US4)**: Не зависит от Phase 4/5/6 — можно начинать после Phase 1
- **Phase 8 (Polish)**: Зависит от всех предыдущих

### User Story Dependencies

- **US1 (P1 Heatmap)**: Phase 2 → можно начинать
- **US2 (P2 Drilldown)**: Phase 2 → можно начинать параллельно с US1
- **US3 (P2 Export)**: Phase 1 (SheetJS) → не зависит от US1/US2
- **US4 (P3 Filters)**: Phase 1 → не зависит от US1/US2/US3

### Parallel Opportunities

- T001 и T002 (Phase 1) — один файл, выполнять последовательно
- T003 и T004 (Phase 2) — разные файлы [P]
- T005, T006, T007 (Phase 3) — один файл, последовательно
- T008, T009, T010, T011 (Phase 4) — один файл, последовательно
- T012, T013, T014 (Phase 5) — T012/T013 параллельно [P], T014 после
- T015, T016, T017 (Phase 6) — один файл, последовательно
- T018, T019, T020 (Phase 7) — один файл, последовательно; T021, T022 зависят от предыдущих
- T023, T024, T025 (Phase 8) — разные файлы [P]

---

## Parallel Example: Phase 3 + Phase 6 одновременно

```
Phase 3 (US1 - heatmap.html):          Phase 6 (US3 - table.html):
  T005 - добавить легенду               T015 - добавить кнопку экспорта
  T006 - исправить контейнер            T016 - реализовать exportToExcel()
  T007 - проверить layout               T017 - индикация загрузки
```

Эти фазы затрагивают разные файлы и могут выполняться параллельно после завершения Phase 1.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: T001–T002 (добавить CDN)
2. Phase 2: T003–T004 (цвета)
3. Phase 3: T005–T007 (легенда heatmap)
4. **STOP и ПРОВЕРИТЬ**: тепловая карта с легендой работает — это уже улучшение UX
5. Продолжить с Phase 4 (Plotly) или Phase 6 (Export)

### Incremental Delivery

1. Phase 1+2 → Foundation
2. Phase 3 (US1) → Легенда на heatmap ✅
3. Phase 4+5 (US2) → Plotly.js drilldown ✅, Chart.js удалён ✅
4. Phase 6 (US3) → Excel export ✅
5. Phase 7 (US4) → Расширенные фильтры ✅
6. Phase 8 → Финальная верификация ✅

---

## Notes

- Все задачи — только в `backend/ui/`; backend Python-код не изменяется
- После каждой задачи: открыть браузер, F12 Console — нет JS-ошибок
- [P] задачи = разные файлы, нет зависимостей
- Smoke-тест из `quickstart.md` после каждой Phase
- `uv run pytest tests/ -q` должен проходить на протяжении всей реализации

---

## Phase 9: Sources UI — Полная реализация (была заглушка «Фаза 2»)

**Goal**: Страница `/sources` работает с реальным API. Все 7 alert-заглушек заменены на функциональный код. Жёстко захардкоденные карточки заменены динамической загрузкой.

**Walking Skeleton Rule**: После каждой задачи `/sources` остаётся в рабочем состоянии — не ломается, не показывает белый экран.

### Phase 9A: Backend — расширить ответ списка источников

- [X] T_s01 В `backend/src/api/schemas.py` расширить `DataSourceShortResponse`: добавить поля `endpoint: str`, `register_name: str`, `dimensions: list[str]` с `Field(description=...)`. Обновить `DataSourceListResponse.model_config json_schema_extra` пример.
- [X] T_s02 В `backend/src/api/routes/sources.py` обновить `list_sources`: заменить маппинг `DataSourceShortResponse(id, name, enabled)` на полный маппинг с новыми полями. Запустить `uv run pytest tests/ -q` — убедиться, что 57 тестов проходят.

**Checkpoint**: `GET /api/v1/sources` возвращает `endpoint`, `register_name`, `dimensions` в каждом элементе.

---

### Phase 9B: UI — Toast-уведомления и динамический список

**Depends on**: T_s01, T_s02

- [X] T_s03 В `backend/ui/templates/sources.html` в блоке `<script>` в самом начале добавить функцию `showToast(message, type='success')`: создаёт `<div>` с Tailwind-классами (зелёный/красный/синий по type), прикрепляет к `document.body`, автоматически удаляет через 3500ms. Никакого `alert()` в новом коде.
- [X] T_s04 В `backend/ui/templates/sources.html` добавить функцию `renderSourceCard(s)`: принимает объект source из API, возвращает строку HTML карточки с теми же Tailwind-классами что у статичных карточек. Атрибуты `data-source-id` на каждой кнопке (.edit-source-btn, .test-connection-btn, .delete-source-btn). Показывает `s.dimensions.join(', ')` и `s.endpoint`.
- [X] T_s05 В `backend/ui/templates/sources.html` добавить функцию `loadSources()`: `fetch('/api/v1/sources')` → берёт `data.sources`, рендерит карточки через `renderSourceCard`, заменяет содержимое контейнера. При `sources.length === 0` — показывает заглушку «Джерела ще не додані». Удалить 2 жёстко захардкоденные карточки (Source 1, Source 2) из HTML. Вызвать `loadSources()` при загрузке страницы (DOMContentLoaded).

**Checkpoint**: `/sources` показывает реальные данные из БД (или «пусто»). Нет статичных карточек.

---

### Phase 9C: UI — Управление измерениями

- [X] T_s06 В `backend/ui/templates/sources.html` реализовать `addDimension(value='')`: создаёт `<div class="flex gap-2 items-center">` с `<input class="dimension-input ...">` и кнопкой `.remove-dimension`, добавляет в конец `#dimensions-container`. Убрать alert с `#add-dimension-btn`.
- [X] T_s07 В `backend/ui/templates/sources.html` реализовать делегирование удаления: навесить обработчик `click` на `#dimensions-container`, внутри проверять `e.target.closest('.remove-dimension')`. При клике: если кол-во `.dimension-input` > 1 — удалить родительский div; иначе — `showToast('Має бути хоча б один вимір', 'error')`. Убрать цикл по `.remove-dimension` с alert.

**Checkpoint**: Добавление и удаление измерений работает динамически. Последнее измерение удалить нельзя.

---

### Phase 9D: UI — Сохранение формы (Create / Update)

- [X] T_s08 В `backend/ui/templates/sources.html` добавить переменную `let editingSourceId = null` и функции `showAddForm()` / `showEditForm(source)` / `hideForm()`: управляют видимостью `#source-form-card`, заголовком формы (`Додати` vs `Редагувати`), полем `#source-id` (readonly при редактировании), значениями всех полей.
- [X] T_s09 В `backend/ui/templates/sources.html` реализовать `collectFormData()`: собирает `id`, `name`, `endpoint`, `register_name`, `dimensions` (массив из всех `input.dimension-input`), `metric_fields: {sum, qty}`, `threshold_rules` (все 11 полей: spike_pct, spike_zscore, spike_logic, moving_avg_window, trend_window, trend_min_points, zero_neg_enabled, missing_enabled, ratio_enabled, ratio_min=null, ratio_max=null), `auth: {type, user, password}`, `enabled: true`. Числовые поля — parseFloat/parseInt.
- [X] T_s10 В `backend/ui/templates/sources.html` заменить alert-обработчик `source-form submit` на реальную функцию `saveSource()`: если `editingSourceId === null` → `fetch('/api/v1/sources', {method:'POST', ...})`, иначе → `fetch('/api/v1/sources/' + editingSourceId, {method:'PUT', ...})`. При 201/200: `hideForm()`, `loadSources()`, `showToast('Джерело збережено')`. При 409: `showToast('ID вже існує', 'error')`. При 422: `showToast(data.detail.message, 'error')`. Кнопка submit: disabled + «Збереження...» на время запроса.

**Checkpoint**: Создание нового источника через форму работает — появляется в списке. Редактирование сохраняет изменения.

---

### Phase 9E: UI — Редактирование и удаление из списка

- [X] T_s11 В `backend/ui/templates/sources.html` реализовать `editSource(sourceId)` вместо alert: `fetch('/api/v1/sources/' + sourceId)` → получает полный `DataSourceResponse`, вызывает `showEditForm(source)` для заполнения всех полей (включая threshold_rules, auth). Прокручивает к форме.
- [X] T_s12 В `backend/ui/templates/sources.html` реализовать `deleteSource(sourceId, sourceName)` вместо alert: показывает `confirm('Видалити джерело "' + sourceName + '"?')`. При подтверждении: `fetch('/api/v1/sources/' + sourceId, {method:'DELETE'})` → `loadSources()`, `showToast('Джерело видалено')`. При 404: `showToast('Джерело вже видалено', 'error')`, `loadSources()`.
- [X] T_s13 В `backend/ui/templates/sources.html` навесить обработчик `click` делегированием на контейнер списка: распознавать `.edit-source-btn` → `editSource(id)`, `.delete-source-btn` → `deleteSource(id, name)`, `.test-connection-btn` (без `#id`) → `testConnection(id)`. Убрать 3 старых цикла forEach с alert.

**Checkpoint**: Edit/Delete в карточках списка работают. После delete карточка исчезает. После edit форма заполнена реальными данными.

---

### Phase 9F: UI — Тест соединения

- [X] T_s14 В `backend/ui/templates/sources.html` реализовать `testConnection(sourceId)` вместо двух alert'ов (форма + список): `fetch('/api/v1/sources/' + sourceId + '/test', {method:'POST'})`. При `status='ok'`: `showToast('З\'єднання успішне · ' + data.response_time_ms + 'ms', 'success')`. При `status='error'`: `showToast('Помилка: ' + data.message, 'error')`. Кнопка: disabled + «Перевірка...» во время запроса.
- [X] T_s15 В `backend/ui/templates/sources.html` кнопку «Тест з'єднання» в форме (`#test-connection-btn`) сделать активной только когда `editingSourceId !== null` (при создании нового — disabled с title «Спочатку збережіть джерело»). Обновлять состояние кнопки в `showAddForm()` / `showEditForm()`.

**Checkpoint**: Тест соединения из карточки и из формы (при редактировании) работает. Показывает реальный ответ от `/api/v1/sources/{id}/test`.

---

### Phase 9G: Финальная очистка

- [X] T_s16 Из `backend/ui/templates/sources.html` удалить статичный баннер «Статичний UI демо...» (строка 359–362 оригинала).
- [X] T_s17 Убедиться что `#add-source-btn` вызывает `showAddForm()` (сбрасывает форму в пустое состояние, заголовок «Додати нове джерело», id-поле не readonly). Заменить захардкоденный заголовок «Редагувати джерело» в старом обработчике.
- [X] T_s18 Запустить `cd backend && uv run pytest tests/ -q` — 57 тестов проходят. Проверить `/sources` в браузере: список загружается из API, CRUD работает, нет alert-заглушек, нет JS-ошибок в консоли.

**Checkpoint**: Полный smoke-тест страницы `/sources`: загрузка списка → создать → редактировать → тест соединения → удалить.
