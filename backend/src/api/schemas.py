"""Pydantic v2 schemas for API request/response models with full OpenAPI documentation."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ============== Request Schemas ==============


class AnalysisRunRequest(BaseModel):
    """Request body for triggering a new anomaly analysis run."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "sales_by_product",
                "date_from": "2026-01-01",
                "date_to": "2026-03-31",
            }
        }
    )

    source_id: str = Field(
        description="Identifier of the DataSource to analyze",
        examples=["sales_by_product"],
    )
    date_from: date = Field(
        description="Start of the analysis period (inclusive, ISO 8601 date)",
        examples=["2026-01-01"],
    )
    date_to: date = Field(
        description="End of the analysis period (inclusive, ISO 8601 date)",
        examples=["2026-03-31"],
    )

    @field_validator("date_to")
    @classmethod
    def validate_date_range(cls, v: date, info: Any) -> date:
        """Ensure date_to is not before date_from."""
        values = info.data
        if "date_from" in values and v < values["date_from"]:
            raise ValueError("date_to must be >= date_from")
        return v


class DataSourceCreateRequest(BaseModel):
    """Request body for creating a new data source."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "sales_by_product",
                "name": "Sales by Product",
                "endpoint": "http://1c-server/base/hs/analytics/v1",
                "register_name": "SalesByProduct",
                "dimensions": ["Period", "Warehouse", "Product"],
                "metric_fields": {"sum": "AmountTurnover", "qty": "QuantityTurnover"},
                "threshold_rules": {"spike_pct": 20.0, "spike_zscore": 3.0},
                "auth": {"type": "none"},
                "enabled": True,
            }
        }
    )

    id: str = Field(
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Unique slug identifier (alphanumeric and underscores only, max 50 chars)",
        examples=["sales_by_product"],
    )
    name: str = Field(
        min_length=1,
        description="Human-readable display name for the data source",
        examples=["Sales by Product"],
    )
    endpoint: str = Field(
        min_length=1,
        description="Base URL of the 1C HTTP service endpoint",
        examples=["http://1c-server/base/hs/analytics/v1"],
    )
    register_name: str = Field(
        min_length=1,
        description="Name of the 1C accumulation register to query",
        examples=["SalesByProduct"],
    )
    dimensions: list[str] = Field(
        min_length=1,
        description="List of dimension field names to group by (at least one required)",
        examples=[["Period", "Warehouse", "Product"]],
    )
    metric_fields: dict[str, str] = Field(
        description="Mapping of logical keys to 1C field names. Must include 'sum' and 'qty'",
        examples=[{"sum": "AmountTurnover", "qty": "QuantityTurnover"}],
    )
    threshold_rules: dict[str, Any] = Field(
        default_factory=dict,
        description="Partial override of anomaly detection thresholds. Unset fields use defaults",
        examples=[{"spike_pct": 20.0, "spike_zscore": 3.0, "zero_neg_enabled": True}],
    )
    auth: dict[str, Any] = Field(
        default_factory=dict,
        description="Authentication configuration for the 1C endpoint",
        examples=[{"type": "none"}],
    )
    enabled: bool = Field(
        default=True,
        description="Whether the source is active and eligible for analysis",
        examples=[True],
    )

    @field_validator("metric_fields")
    @classmethod
    def validate_metric_fields(cls, v: dict[str, str]) -> dict[str, str]:
        """Ensure both 'sum' and 'qty' keys are present."""
        if "sum" not in v or "qty" not in v:
            raise ValueError("metric_fields must have both 'sum' and 'qty' keys")
        return v


class DataSourceUpdateRequest(DataSourceCreateRequest):
    """Request body for updating an existing data source (same shape as create)."""

    pass


class TestConnectionRequest(BaseModel):
    """Request body for testing a data source connection."""

    source_id: str = Field(
        description="Identifier of the DataSource to test",
        examples=["sales_by_product"],
    )


class DataPreviewRequest(BaseModel):
    """Request body for previewing raw data from a 1C register."""

    date_from: date = Field(
        description="Start of the preview period",
        examples=["2026-01-01"],
    )
    date_to: date = Field(
        description="End of the preview period",
        examples=["2026-01-31"],
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of records to return (1–100)",
        examples=[10],
    )


# ============== Response Schemas ==============


class AnalysisRunResponse(BaseModel):
    """Full details of a completed or in-progress analysis run."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "source_id": "sales_by_product",
                "source_name": "Sales by Product",
                "date_from": "2026-01-01",
                "date_to": "2026-03-31",
                "triggered_by": "user",
                "started_at": "2026-03-18T10:00:00",
                "completed_at": "2026-03-18T10:00:01",
                "status": "completed",
                "anomaly_count": 5,
            }
        }
    )

    id: str = Field(description="UUID of the analysis run")
    source_id: str = Field(description="ID of the analyzed DataSource")
    source_name: str | None = Field(default=None, description="Display name of the DataSource")
    date_from: date = Field(description="Start of the analyzed period")
    date_to: date = Field(description="End of the analyzed period")
    triggered_by: str = Field(description="Who triggered the run")
    started_at: datetime = Field(description="UTC timestamp when the run started")
    completed_at: datetime | None = Field(description="UTC timestamp when the run finished")
    status: Literal["pending", "running", "completed", "failed"] = Field(
        description="Current lifecycle status"
    )
    anomaly_count: int = Field(description="Number of anomalies detected", ge=0)


class AnalysisRunShortResponse(BaseModel):
    """Abbreviated response returned immediately after triggering a run."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "anomaly_count": 5,
                "duration_ms": 120,
            }
        }
    )

    analysis_id: str = Field(description="UUID of the newly created analysis run")
    status: str = Field(description="Final status after synchronous execution")
    anomaly_count: int = Field(description="Number of anomalies found", ge=0)
    duration_ms: int | None = Field(
        default=None,
        description="Wall-clock execution time in milliseconds",
    )


class AnomalyResponse(BaseModel):
    """Single anomaly as returned by the API."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "anomaly-uuid",
                "run_id": "run-uuid",
                "source_id": "sales_by_product",
                "type": "SPIKE",
                "dimensions": {"Warehouse": "Main", "Product": "Widget A"},
                "period": "2026-03-01",
                "current_value": 350.0,
                "previous_value": 150.0,
                "pct_change": 133.3,
                "zscore": 4.2,
                "threshold_triggered": {"spike_pct": True},
            }
        }
    )

    id: str = Field(description="Unique anomaly identifier")
    run_id: str = Field(description="ID of the analysis run that detected this anomaly")
    source_id: str = Field(description="ID of the data source")
    type: str = Field(
        description="Anomaly category: SPIKE | TREND_BREAK | ZERO_NEG | MISSING | RATIO | MISSING_DATA"
    )
    dimensions: dict[str, str] = Field(description="Dimension values of the affected data point")
    period: date = Field(description="Period in which the anomaly was detected")
    current_value: float | None = Field(description="Metric value in the anomalous period")
    previous_value: float | None = Field(
        description="Baseline value used for comparison (moving average)"
    )
    pct_change: float | None = Field(
        description="Percentage change from previous_value to current_value"
    )
    zscore: float | None = Field(
        description="Z-score of current_value relative to historical distribution"
    )
    threshold_triggered: dict[str, Any] | None = Field(
        description="Map of threshold names to values that were triggered"
    )


class AnomalyListResponse(BaseModel):
    """Paginated list of anomalies."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "anomalies": [],
                "pagination": {"total": 0, "page": 1, "page_size": 50},
            }
        }
    )

    anomalies: list[AnomalyResponse] = Field(description="List of anomaly records")
    pagination: dict[str, Any] = Field(description="Pagination metadata: total, page, page_size")


class ThresholdRulesResponse(BaseModel):
    """Threshold rules as returned in DataSource responses."""

    spike_pct: float = Field(description="Spike threshold as percentage")
    spike_zscore: float = Field(description="Spike threshold as Z-score")
    spike_logic: str = Field(description="AND / OR logic for spike conditions")
    moving_avg_window: int = Field(description="Moving average window in periods")
    trend_window: int = Field(description="Trend detection window in periods")
    trend_min_points: int = Field(description="Minimum points for trend detection")
    ratio_min: float | None = Field(description="Minimum allowed ratio")
    ratio_max: float | None = Field(description="Maximum allowed ratio")
    zero_neg_enabled: bool = Field(description="Zero/negative detection enabled")
    missing_enabled: bool = Field(description="Missing data detection enabled")
    ratio_enabled: bool = Field(description="Ratio anomaly detection enabled")


class DataSourceResponse(BaseModel):
    """Full data source configuration as returned by the API."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "sales_by_product",
                "name": "Sales by Product",
                "endpoint": "http://1c-server/base/hs/analytics/v1",
                "register_name": "SalesByProduct",
                "dimensions": ["Period", "Warehouse", "Product"],
                "metric_fields": {"sum": "AmountTurnover", "qty": "QuantityTurnover"},
                "threshold_rules": {
                    "spike_pct": 20.0,
                    "spike_zscore": 3.0,
                    "spike_logic": "OR",
                    "moving_avg_window": 6,
                    "trend_window": 3,
                    "trend_min_points": 5,
                    "ratio_min": None,
                    "ratio_max": None,
                    "zero_neg_enabled": True,
                    "missing_enabled": True,
                    "ratio_enabled": False,
                },
                "auth": {"type": "none", "user": None, "password": None},
                "enabled": True,
                "last_analysis": None,
            }
        }
    )

    id: str = Field(description="Unique slug identifier")
    name: str = Field(description="Human-readable display name")
    endpoint: str = Field(description="1C HTTP service endpoint URL")
    register_name: str = Field(description="1C accumulation register name")
    dimensions: list[str] = Field(description="List of grouping dimension field names")
    metric_fields: dict[str, str] = Field(description="Metric key-to-field mapping")
    threshold_rules: ThresholdRulesResponse | None = Field(
        default=None,
        description="Current anomaly detection thresholds",
    )
    auth: dict[str, Any] | None = Field(
        default=None,
        description="Authentication configuration (password is masked)",
    )
    enabled: bool = Field(description="Whether the source is active")
    last_analysis: dict[str, Any] | None = Field(
        default=None,
        description="Summary of the most recent analysis run, if any",
    )


class DataSourceShortResponse(BaseModel):
    """Abbreviated data source for list views."""

    id: str = Field(description="Unique slug identifier")
    name: str = Field(description="Human-readable display name")
    enabled: bool = Field(description="Whether the source is active")
    endpoint: str = Field(description="1C HTTP service base URL")
    register_name: str = Field(description="1C accumulation register name")
    dimensions: list[str] = Field(description="Grouping dimension field names")


class DataSourceListResponse(BaseModel):
    """Response containing a list of data sources."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sources": [
                    {
                        "id": "sales_by_product",
                        "name": "Sales by Product",
                        "enabled": True,
                        "endpoint": "http://1c-server/base/hs/analytics/v1",
                        "register_name": "ПартіїТоварів",
                        "dimensions": ["Період", "Номенклатура"],
                    }
                ]
            }
        }
    )

    sources: list[DataSourceShortResponse] = Field(description="List of data sources")


class TestConnectionResponse(BaseModel):
    """Response for a connection test request."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"status": "ok", "message": "Connected successfully", "response_time_ms": 45}
        }
    )

    status: Literal["ok", "error"] = Field(
        description="'ok' if connection succeeded, 'error' otherwise"
    )
    message: str = Field(description="Human-readable result message")
    response_time_ms: int | None = Field(
        default=None,
        description="Round-trip time in milliseconds",
    )


class DataPreviewResponse(BaseModel):
    """Response containing a sample of raw register data."""

    source_id: str = Field(description="ID of the queried data source")
    register_name: str = Field(description="1C register name that was queried")
    date_from: date = Field(description="Start of the queried period")
    date_to: date = Field(description="End of the queried period")
    record_count: int = Field(description="Number of records returned")
    data: list[dict[str, Any]] = Field(description="Raw register rows")


class HeatMapRow(BaseModel):
    """A row in the heat map grid, identified by its dimension values."""

    idx: int = Field(description="Zero-based row index")
    values: dict[str, str] = Field(description="Dimension key-value pairs for this row")


class HeatMapColumn(BaseModel):
    """A column in the heat map grid, corresponding to a single period."""

    idx: int = Field(description="Zero-based column index")
    period: date = Field(description="Period date this column represents")


class HeatMapCell(BaseModel):
    """A single cell in the heat map, carrying anomaly severity data."""

    row_idx: int = Field(description="Row index of this cell")
    col_idx: int = Field(description="Column index of this cell")
    type: str = Field(description="Anomaly type code or 'none'")
    intensity: float = Field(description="Severity score 0.0–1.0 for colour mapping", ge=0, le=1)
    anomaly_id: str | None = Field(default=None, description="ID of the underlying Anomaly record")
    pct_change: float | None = Field(
        default=None, description="Percentage change from previous value"
    )
    current_value: float | None = Field(default=None, description="Current metric value")
    previous_value: float | None = Field(default=None, description="Previous baseline value")


class HeatMapLegend(BaseModel):
    """Legend entry mapping an anomaly type to a display colour and label."""

    color: str = Field(description="Hex colour code, e.g. '#FF6B6B'")
    label: str = Field(description="Human-readable label for this anomaly category")
    priority: int = Field(description="Display sort priority (lower = more prominent)")


class HeatMapResponse(BaseModel):
    """Full heat map data payload for a completed analysis run."""

    run_id: str = Field(description="ID of the analysis run this heat map belongs to")
    row_dimensions: list[str] = Field(description="Dimension names used to build the row axis")
    rows: list[HeatMapRow] = Field(description="Row definitions (dimension value sets)")
    columns: list[HeatMapColumn] = Field(description="Column definitions (periods)")
    cells: list[HeatMapCell] = Field(description="Populated cells with anomaly data")
    legend: dict[str, HeatMapLegend] = Field(description="Anomaly type → legend entry mapping")


class TimeSeriesDataPoint(BaseModel):
    """A single time series observation."""

    period: date = Field(description="Observation date")
    value: float = Field(description="Computed metric value for this period")
    raw_sum: float | None = Field(default=None, description="Raw sum from 1C")
    raw_qty: float | None = Field(default=None, description="Raw quantity from 1C")
    anomaly_type: str | None = Field(
        default=None,
        description="Anomaly type if this period was flagged, else null",
    )
    pct_change: float | None = Field(
        default=None, description="Percentage change from previous value if anomalous"
    )
    zscore: float | None = Field(
        default=None, description="Z-score of this observation if anomalous"
    )


class TimeSeriesResponse(BaseModel):
    """Time series drill-down for a specific dimension combination."""

    dimensions: dict[str, str] = Field(
        description="Dimension key-value pairs identifying the drill-down slice"
    )
    data: list[TimeSeriesDataPoint] = Field(description="Ordered list of time series observations")


# ============== Error Response Schemas ==============


class ErrorResponse(BaseModel):
    """Standard error response body."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "invalid_source",
                "message": "Source 'xyz' not found",
                "details": None,
            }
        }
    )

    error: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error description")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured details for debugging",
    )


class ValidationErrorDetail(BaseModel):
    """Detail entry for a single field validation failure."""

    field: str = Field(description="Name of the field that failed validation")
    reason: str = Field(description="Description of the validation failure")


class ValidationErrorResponse(BaseModel):
    """Response body for 422 Unprocessable Entity errors."""

    error: str = Field(default="validation_error", description="Always 'validation_error'")
    message: str = Field(description="Summary of the validation failure")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Per-field validation error details",
    )
