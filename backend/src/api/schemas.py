"""Pydantic schemas for API request/response models."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# ============== Request Schemas ==============


class AnalysisRunRequest(BaseModel):
    """Request to trigger anomaly analysis."""

    source_id: str = Field(..., description="Data source identifier")
    date_from: date = Field(..., description="Start of analysis period")
    date_to: date = Field(..., description="End of analysis period")

    @field_validator("date_to")
    @classmethod
    def validate_date_range(cls, v: date, info: Any) -> date:
        """Validate date_from <= date_to."""
        values = info.data
        if "date_from" in values and v < values["date_from"]:
            raise ValueError("date_to must be >= date_from")
        return v


class DataSourceCreateRequest(BaseModel):
    """Request to create a new data source."""

    id: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    name: str = Field(..., min_length=1)
    endpoint: str = Field(..., min_length=1)
    register_name: str = Field(..., min_length=1)
    dimensions: list[str] = Field(..., min_length=1)
    metric_fields: dict[str, str] = Field(...)
    threshold_rules: dict[str, Any] = Field(default_factory=dict)
    auth: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True

    @field_validator("metric_fields")
    @classmethod
    def validate_metric_fields(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate metric_fields has both sum and qty."""
        if "sum" not in v or "qty" not in v:
            raise ValueError("metric_fields must have both 'sum' and 'qty' keys")
        return v


class DataSourceUpdateRequest(DataSourceCreateRequest):
    """Request to update an existing data source."""

    pass


class TestConnectionRequest(BaseModel):
    """Request to test data source connection."""

    source_id: str = Field(..., description="Data source identifier")


class DataPreviewRequest(BaseModel):
    """Request to preview data from 1C."""

    date_from: date = Field(..., description="Start of preview period")
    date_to: date = Field(..., description="End of preview period")
    limit: int = Field(default=10, ge=1, le=100, description="Max records to return")


# ============== Response Schemas ==============


class AnalysisRunResponse(BaseModel):
    """Response with analysis run details."""

    id: str
    source_id: str
    source_name: str | None = None
    date_from: date
    date_to: date
    triggered_by: str
    started_at: datetime
    completed_at: datetime | None
    status: Literal["pending", "running", "completed", "failed"]
    anomaly_count: int


class AnalysisRunShortResponse(BaseModel):
    """Short response for analysis run creation."""

    analysis_id: str
    status: str
    anomaly_count: int
    duration_ms: int | None = None


class AnomalyResponse(BaseModel):
    """Response with anomaly details."""

    id: str
    run_id: str
    source_id: str
    type: str
    dimensions: dict[str, str]
    period: date
    current_value: float | None
    previous_value: float | None
    pct_change: float | None
    zscore: float | None
    threshold_triggered: dict[str, bool] | None


class AnomalyListResponse(BaseModel):
    """Response with list of anomalies and pagination."""

    anomalies: list[AnomalyResponse]
    pagination: dict[str, Any]


class DataSourceResponse(BaseModel):
    """Response with data source details."""

    id: str
    name: str
    endpoint: str
    register_name: str
    dimensions: list[str]
    metric_fields: dict[str, str]
    enabled: bool
    last_analysis: dict[str, Any] | None = None


class DataSourceShortResponse(BaseModel):
    """Short response for data source list."""

    id: str
    name: str
    enabled: bool


class DataSourceListResponse(BaseModel):
    """Response with list of data sources."""

    sources: list[DataSourceShortResponse]


class TestConnectionResponse(BaseModel):
    """Response for connection test."""

    status: Literal["ok", "error"]
    message: str
    response_time_ms: int | None = None


class DataPreviewResponse(BaseModel):
    """Response with data preview."""

    source_id: str
    register_name: str
    date_from: date
    date_to: date
    record_count: int
    data: list[dict[str, Any]]


class HeatMapRow(BaseModel):
    """Heat map row definition."""

    idx: int
    values: dict[str, str]


class HeatMapColumn(BaseModel):
    """Heat map column definition."""

    idx: int
    period: date


class HeatMapCell(BaseModel):
    """Heat map cell with anomaly data."""

    row_idx: int
    col_idx: int
    type: str
    intensity: float
    anomaly_id: str | None = None


class HeatMapLegend(BaseModel):
    """Heat map legend entry."""

    color: str
    label: str
    priority: int


class HeatMapResponse(BaseModel):
    """Response with heat map data."""

    run_id: str
    row_dimensions: list[str]
    rows: list[HeatMapRow]
    columns: list[HeatMapColumn]
    cells: list[HeatMapCell]
    legend: dict[str, HeatMapLegend]


class TimeSeriesDataPoint(BaseModel):
    """Time series data point."""

    period: date
    value: float
    raw_sum: float | None = None
    raw_qty: float | None = None
    anomaly_type: str | None = None


class TimeSeriesResponse(BaseModel):
    """Response with time series data."""

    dimensions: dict[str, str]
    data: list[TimeSeriesDataPoint]


# ============== Error Response Schemas ==============


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    details: dict[str, Any] | None = None


class ValidationErrorDetail(BaseModel):
    """Validation error detail."""

    field: str
    reason: str


class ValidationErrorResponse(BaseModel):
    """Validation error response."""

    error: str = "validation_error"
    message: str
    details: dict[str, Any] | None = None
