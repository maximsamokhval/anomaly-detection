# Feature Specification: Financial Anomaly Detection Service MVP

**Feature Branch**: `001-anomaly-detection-mvp`
**Created**: 2026-03-17
**Status**: Draft
**Input**: BRD for Financial Anomaly Detection Service (manufacturing + sales company)

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Detect and Localize Financial Anomalies (Priority: P1)

**As a** financial analyst,  
**I want to** manually trigger anomaly detection for a specific register and time period,  
**So that I can** quickly identify which product/location combinations have suspicious cost or margin values.

**Why this priority**: This is the core value proposition. Without anomaly detection, the product has no purpose. The analyst can run analysis on-demand and immediately see where problems exist.

**Independent Test**: Can be fully tested by: selecting a data source, choosing a date range, clicking "Run Analysis", viewing the heat map with colored cells indicating anomaly types, and clicking a cell to see the time series with anomaly markers.

**Acceptance Scenarios**:

1. **Given** a configured data source with historical data, **When** the analyst selects the source and date range, **Then** the system displays a heat map with rows (product/location combinations) and columns (time periods) colored by anomaly type.

2. **Given** a heat map with anomalous cells, **When** the analyst clicks a colored cell, **Then** the system displays a drill-down view showing the time series chart with anomaly markers and metadata (current value, previous value, % change, z-score).

3. **Given** a data point where quantity equals zero, **When** analysis runs, **Then** the system marks it as MISSING_DATA anomaly without crashing.

---

### User Story 2 — Configure Data Sources and Detection Thresholds (Priority: P2)

**As a** financial analyst or IT administrator,  
**I want to** add, edit, and configure data sources (1C registers) with custom detection thresholds,  
**So that I can** extend anomaly detection to new registers without code changes.

**Why this priority**: Enables scaling from pilot (1-2 registers) to target (10-15 registers). Configuration-driven architecture is core to the product vision.

**Independent Test**: Can be fully tested by: adding a new data source via UI form (name, URL, register name, dimensions, metric fields), configuring threshold rules (spike %, z-score, trend window), testing the connection, and verifying the source appears in the dashboard list.

**Acceptance Scenarios**:

1. **Given** the data source configuration screen, **When** the user fills in required fields (name, endpoint, register name, dimensions, sum/qty fields) and saves, **Then** the source appears in the dashboard source list as enabled.

2. **Given** a configured data source, **When** the user clicks "Test Connection", **Then** the system displays success or error status based on the 1C HTTP service response.

3. **Given** a data source with threshold settings, **When** the user modifies spike_pct from 20 to 30 and saves, **Then** subsequent analyses use the new threshold for SPIKE detection.

---

### User Story 3 — Browse and Filter Anomaly Details (Priority: P3)

**As a** financial control user,  
**I want to** view a sortable, filterable table of all detected anomalies,  
**So that I can** focus on specific types of anomalies or time periods and sort by severity.

**Why this priority**: Provides an alternative view to the heat map for users who prefer tabular data. Enables filtering by anomaly type, period, or dimension values.

**Independent Test**: Can be fully tested by: opening the anomaly table view, applying filters (e.g., show only SPIKE anomalies), sorting by % change descending, and clicking a row to navigate to drill-down.

**Acceptance Scenarios**:

1. **Given** completed analysis with multiple anomaly types, **When** the user opens the anomaly table, **Then** the system displays all anomalies with columns: type, register, dimensions, period, current value, previous value, % change, z-score.

2. **Given** the anomaly table, **When** the user filters by anomaly type "SPIKE" and sorts by % change descending, **Then** only SPIKE anomalies are shown, ordered from highest to lowest % change.

3. **Given** the anomaly table, **When** the user clicks a row, **Then** the system navigates to the drill-down view for that specific combination of dimensions.

---

### Edge Cases

- **Division by zero**: When quantity is zero, the system marks the data point as MISSING_DATA anomaly instead of crashing.

- **Insufficient history**: When fewer than 5 data points exist for a combination, trend-based detection (TREND_BREAK) is skipped; only percentage-change detection runs.

- **Missing expected period**: When a combination has data for January and March but not February, the system marks February as MISSING anomaly (if enabled). MISSING detection operates on monthly periodicity (end of month).

- **1C service unavailable**: When the 1C HTTP service returns an error, the system displays a clear error message ("Unable to connect to data source") without crashing.

- **No anomalies found**: When analysis completes with zero anomalies, the system displays a success message ("No anomalies detected for selected period") with an empty heat map or table.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to manually trigger anomaly analysis by selecting a data source and date range.

- **FR-002**: System MUST display analysis results as a heat map where rows represent unique dimension combinations (e.g., Product + Warehouse + Organization), columns represent time periods, and cell color indicates anomaly type.

- **FR-003**: System MUST detect six anomaly types: SPIKE (sudden jump), TREND_BREAK (trend reversal), ZERO_NEG (zero/negative value), MISSING (missing period), RATIO (out-of-range ratio, disabled by default), MISSING_DATA (division by zero).

- **FR-004**: System MUST compute the metric value as Sum / Quantity at analysis time; raw sum and quantity values MUST be preserved for audit.

- **FR-005**: System MUST provide a drill-down view showing the time series chart with anomaly markers and metadata (current value, previous value, % change, z-score, triggered thresholds).

- **FR-006**: System MUST allow users to configure data sources via UI: name, 1C endpoint URL, register name, dimensions list, sum/quantity field names, authentication type.

- **FR-007**: System MUST allow users to configure detection thresholds per data source: spike percentage, z-score threshold, trend window size, ratio min/max, enable/disable flags per anomaly type.

- **FR-008**: System MUST provide a test connection feature that validates connectivity to the 1C HTTP service and displays success or error status.

- **FR-009**: System MUST display an anomaly table view with columns: anomaly type, register, dimensions, period, current value, previous value, % change, z-score.

- **FR-010**: System MUST allow filtering the anomaly table by anomaly type, register, period, and individual dimension values.

- **FR-011**: System MUST allow sorting the anomaly table by % change or z-score in ascending or descending order.

- **FR-012**: System MUST fetch data from 1C via HTTP GET request with parameters: register_name, date_from, date_to, dimensions, optional filters (organization, warehouse), pagination (page, page_size).

- **FR-013**: System MUST persist analysis results (raw data points and detected anomalies) to the database for historical reference.

- **FR-014**: System MUST complete analysis execution within 30 seconds for a single register with up to 100 dimension combinations.

- **FR-015**: System MUST render heat map visualization within 2 seconds after analysis completion for up to 100 dimension combinations and 12 time periods.

- **FR-016**: System MUST render anomaly table within 2 seconds after loading for up to 500 anomalies.

---

### Key Entities

- **DataSource**: Configuration for a single 1C register. Contains: unique identifier, display name, 1C HTTP endpoint URL, register name, list of dimension names, sum/quantity field names, detection threshold rules, authentication credentials, enabled/disabled status.

- **AnalysisRun**: A single execution of anomaly detection. Contains: unique identifier, data source reference, date range, triggered by (user), start time, completion time, status (pending/running/completed/failed), anomaly count, error message (if failed).

- **DataPoint**: A single computed metric value for a specific combination of dimensions at a specific time period. Contains: data source reference, dimension values (key-value pairs), period date, computed value (sum/qty), raw sum, raw quantity.

- **Anomaly**: A detected deviation from expected behavior. Contains: data source reference, dimension values, period date, anomaly type (SPIKE/TREND_BREAK/ZERO_NEG/MISSING/RATIO/MISSING_DATA), current value, previous value, percentage change, z-score, triggered threshold details.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Financial analysts can complete a full analysis cycle (select source, choose period, run analysis, identify anomalous combination) in under 2 minutes.

- **SC-002**: System completes anomaly detection for a single register with up to 100 dimension combinations in under 30 seconds.

- **SC-003**: Heat map and anomaly table load and render in under 2 seconds after analysis completion.

- **SC-004**: Team stops manually searching for errors in financial data spreadsheets (measured by user survey: 100% of target users report "no manual error hunting" within 4 weeks of deployment).

- **SC-005**: System successfully detects all three BRD-defined test scenarios: (1) cost spike after calculation change, (2) trend break in margin data, (3) zero/negative value detection. RATIO detection is disabled by default and excluded from MVP validation.

- **SC-006**: Users can configure a new data source end-to-end (form entry, test connection, run first analysis) in under 10 minutes without developer assistance.

---

## Assumptions

- **A-001**: 1C HTTP service will be developed in parallel and will expose the `/hs/analytics/v1/data` endpoint with the specified JSON schema.

- **A-002**: Pilot register will have at least 3-6 months of historical data for meaningful trend analysis.

- **A-003**: Users access the system from within the internal corporate network; no external access or internet exposure required.

- **A-004**: Data cardinality will not exceed 100 unique dimension combinations per register in MVP scope.

- **A-005**: Basic Auth credentials for 1C service will be provided by IT team during configuration.

---

## Clarifications

### Session 2026-03-17

- Q: What is the pilot register name? → A: ПартииТоваровНаСкладахПоПроизводителям
- Q: What are the dimension fields for the pilot register? → A: Period, Product, Warehouse, Organization, Manufacturer (5 dimensions)
- Q: What is the MISSING anomaly periodicity? → A: Monthly (missing data between months)

---

## Assumptions (Updated)

- **A-006**: Pilot register is "ПартииТоваровНаСкладахПоПроизводителям" (Product Batches at Warehouses by Manufacturers) with 5 dimensions: Период, Номенклатура, Склад, Организация, Производитель. Resources: Сумма, Количество.

- **A-007**: Data periodicity is monthly (end of month) for MISSING anomaly detection. Missing data between consecutive months triggers MISSING anomaly.

- **A-008**: RATIO anomaly detection requires price data from a separate source (e.g., sales register or price list). This feature is disabled by default (`ratio_enabled: false`) and may be deferred to Post-MVP until price source is identified.

---

*Specification derived from BRD v1.0 (March 2026), based on 37 product interview questions.*
