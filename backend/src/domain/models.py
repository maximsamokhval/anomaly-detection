"""Domain entities for Financial Anomaly Detection Service."""

from datetime import date, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ThresholdRules(BaseModel):
    """Detection thresholds configuration for anomaly algorithms."""

    model_config = ConfigDict(frozen=False)

    spike_pct: float = Field(
        default=20.0,
        ge=0,
        description="Spike detection threshold as percentage change from moving average",
        examples=[20.0],
    )
    spike_zscore: float = Field(
        default=3.0,
        ge=0,
        description="Spike detection threshold as Z-score (standard deviations from mean)",
        examples=[3.0],
    )
    spike_logic: Literal["AND", "OR"] = Field(
        default="OR",
        description="Logic operator for combining spike_pct and spike_zscore conditions",
        examples=["OR"],
    )
    moving_avg_window: int = Field(
        default=6,
        ge=1,
        description="Number of prior periods used for moving average baseline",
        examples=[6],
    )
    trend_window: int = Field(
        default=3,
        ge=1,
        description="Number of consecutive periods required to confirm a trend break",
        examples=[3],
    )
    trend_min_points: int = Field(
        default=5,
        ge=1,
        description="Minimum data points needed before trend detection is applied",
        examples=[5],
    )
    ratio_min: float | None = Field(
        default=None,
        description="Minimum allowed ratio (sum/qty). None disables lower-bound check",
        examples=[None],
    )
    ratio_max: float | None = Field(
        default=None,
        description="Maximum allowed ratio (sum/qty). None disables upper-bound check",
        examples=[None],
    )
    zero_neg_enabled: bool = Field(
        default=True,
        description="Enable detection of zero or negative metric values",
        examples=[True],
    )
    missing_enabled: bool = Field(
        default=True,
        description="Enable detection of missing data points for expected periods",
        examples=[True],
    )
    ratio_enabled: bool = Field(
        default=False,
        description="Enable ratio anomaly detection",
        examples=[False],
    )


class AuthConfig(BaseModel):
    """Authentication configuration for 1C HTTP service."""

    model_config = ConfigDict(frozen=False)

    type: Literal["none", "basic"] = Field(
        default="none",
        description="Authentication scheme for the 1C HTTP endpoint",
        examples=["none"],
    )
    user: str | None = Field(
        default=None,
        description="Username for HTTP Basic authentication",
        examples=[None],
    )
    password: str | None = Field(
        default=None,
        description="Password for HTTP Basic authentication",
        examples=[None],
    )


class DataSource(BaseModel):
    """Configuration for a single 1C accumulation register data source."""

    model_config = ConfigDict(frozen=False)

    id: str = Field(
        description="Unique slug identifier (alphanumeric + underscore)",
        examples=["sales_by_product"],
    )
    name: str = Field(
        description="Human-readable display name",
        examples=["Sales by Product"],
    )
    endpoint: str = Field(
        description="Base URL of the 1C HTTP service endpoint",
        examples=["http://1c-server/base/hs/analytics/v1"],
    )
    register_name: str = Field(
        description="Name of the 1C accumulation register to query",
        examples=["SalesByProduct"],
    )
    dimensions: list[str] = Field(
        description="List of dimension field names to group by (e.g. Warehouse, Product)",
        examples=[["Period", "Warehouse", "Product"]],
    )
    metric_fields: dict[str, str] = Field(
        description="Mapping of logical keys ('sum', 'qty') to actual 1C field names",
        examples=[{"sum": "AmountTurnover", "qty": "QuantityTurnover"}],
    )
    threshold_rules: ThresholdRules = Field(
        default_factory=ThresholdRules,
        description="Anomaly detection threshold configuration",
    )
    auth: AuthConfig = Field(
        default_factory=AuthConfig,
        description="Authentication configuration for the 1C endpoint",
    )
    enabled: bool = Field(
        default=True,
        description="Whether this data source is active and eligible for analysis",
        examples=[True],
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="UTC timestamp when the source was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="UTC timestamp of the last update",
    )

    def validate_config(self) -> list[str]:
        """Return a list of validation error messages, or empty list if valid."""
        errors: list[str] = []
        if not self.register_name:
            errors.append("register_name is required")
        if not self.dimensions:
            errors.append("dimensions must have at least one value")
        if "sum" not in self.metric_fields or "qty" not in self.metric_fields:
            errors.append("metric_fields must have both 'sum' and 'qty' keys")
        return errors


class AnalysisRun(BaseModel):
    """A single execution of anomaly detection for a data source."""

    model_config = ConfigDict(frozen=False)

    source_id: str = Field(
        description="ID of the DataSource being analyzed",
        examples=["sales_by_product"],
    )
    date_from: date = Field(
        description="Start date of the analysis period (inclusive)",
        examples=["2026-01-01"],
    )
    date_to: date = Field(
        description="End date of the analysis period (inclusive)",
        examples=["2026-03-31"],
    )
    triggered_by: str = Field(
        default="user",
        description="Identity of who triggered the analysis run",
        examples=["user"],
    )
    started_at: datetime = Field(
        default_factory=datetime.now,
        description="UTC timestamp when execution started",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when execution finished (None if still running)",
    )
    status: Literal["pending", "running", "completed", "failed"] = Field(
        default="pending",
        description="Current lifecycle status of the analysis run",
        examples=["completed"],
    )
    anomaly_count: int = Field(
        default=0,
        ge=0,
        description="Number of anomalies found during the run",
        examples=[5],
    )
    error_message: str | None = Field(
        default=None,
        description="Error description if status is 'failed'",
    )
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="UUID identifying this analysis run",
    )

    def mark_completed(self, anomaly_count: int) -> None:
        """Transition run to completed state."""
        self.completed_at = datetime.now()
        self.status = "completed"
        self.anomaly_count = anomaly_count

    def mark_failed(self, error_message: str) -> None:
        """Transition run to failed state."""
        self.completed_at = datetime.now()
        self.status = "failed"
        self.error_message = error_message


class DataPoint(BaseModel):
    """Computed aggregated metric value for a specific dimension combination and period."""

    model_config = ConfigDict(frozen=False)

    source_id: str = Field(
        description="ID of the originating DataSource",
        examples=["sales_by_product"],
    )
    dimensions: dict[str, str] = Field(
        description="Dimension key-value pairs that uniquely identify this row",
        examples=[{"Warehouse": "Main", "Product": "Widget A"}],
    )
    period: date = Field(
        description="Reporting period (typically month-start date)",
        examples=["2026-03-01"],
    )
    value: float = Field(
        description="Computed ratio value: raw_sum / raw_qty",
        examples=[150.5],
    )
    raw_sum: float = Field(
        description="Raw sum turnover from 1C",
        examples=[15050.0],
    )
    raw_qty: float = Field(
        description="Raw quantity turnover from 1C",
        examples=[100.0],
    )
    run_id: str | None = Field(
        default=None,
        description="ID of the AnalysisRun that produced this data point",
    )
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this data point",
    )

    @model_validator(mode="after")
    def validate_value_invariant(self) -> "DataPoint":
        """Ensure value == raw_sum / raw_qty when raw_qty != 0."""
        if self.raw_qty != 0:
            expected = self.raw_sum / self.raw_qty
            if abs(self.value - expected) > 0.0001:
                raise ValueError(
                    f"value must equal raw_sum/raw_qty: {self.value} != {expected:.4f}"
                )
        return self


class Anomaly(BaseModel):
    """A detected deviation from expected behavior in a data point."""

    model_config = ConfigDict(frozen=False)

    source_id: str = Field(
        description="ID of the DataSource where the anomaly was detected",
        examples=["sales_by_product"],
    )
    dimensions: dict[str, str] = Field(
        description="Dimension values of the affected data point",
        examples=[{"Warehouse": "Main", "Product": "Widget A"}],
    )
    period: date = Field(
        description="Period in which the anomaly was detected",
        examples=["2026-03-01"],
    )
    anomaly_type: Literal["SPIKE", "TREND_BREAK", "ZERO_NEG", "MISSING", "RATIO", "MISSING_DATA"] = Field(
        description="Category of the detected anomaly",
        examples=["SPIKE"],
    )
    current_value: float | None = Field(
        default=None,
        description="Metric value in the anomalous period",
        examples=[350.0],
    )
    previous_value: float | None = Field(
        default=None,
        description="Baseline value used for comparison (e.g. moving average)",
        examples=[150.0],
    )
    pct_change: float | None = Field(
        default=None,
        description="Percentage change from previous_value to current_value",
        examples=[133.3],
    )
    zscore: float | None = Field(
        default=None,
        description="Z-score of current_value relative to historical distribution",
        examples=[4.2],
    )
    threshold_triggered: dict[str, Any] = Field(
        default_factory=dict,
        description="Map of threshold names to the values that triggered them",
        examples=[{"spike_pct": True, "spike_zscore": False}],
    )
    run_id: str | None = Field(
        default=None,
        description="ID of the AnalysisRun that produced this anomaly",
    )
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this anomaly",
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize anomaly to a plain dictionary."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "source_id": self.source_id,
            "dimensions": self.dimensions,
            "period": self.period.isoformat() if self.period else None,
            "anomaly_type": self.anomaly_type,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "pct_change": self.pct_change,
            "zscore": self.zscore,
            "threshold_triggered": self.threshold_triggered,
        }
