"""Domain entities for Financial Anomaly Detection Service."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal
from uuid import uuid4


@dataclass
class ThresholdRules:
    """Detection thresholds configuration."""

    spike_pct: float = 20.0
    spike_zscore: float = 3.0
    spike_logic: Literal["AND", "OR"] = "OR"
    moving_avg_window: int = 6
    trend_window: int = 3
    trend_min_points: int = 5
    ratio_min: float | None = None
    ratio_max: float | None = None
    zero_neg_enabled: bool = True
    missing_enabled: bool = True
    ratio_enabled: bool = False


@dataclass
class AuthConfig:
    """Authentication configuration for 1C HTTP service."""

    type: Literal["none", "basic"] = "none"
    user: str | None = None
    password: str | None = None


@dataclass
class DataSource:
    """Configuration for a single 1C register."""

    id: str
    name: str
    endpoint: str
    register_name: str
    dimensions: list[str]
    metric_fields: dict[str, str]
    threshold_rules: ThresholdRules
    auth: AuthConfig
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def validate(self) -> list[str]:
        """Validate DataSource configuration."""
        errors = []
        if not self.register_name:
            errors.append("register_name is required")
        if not self.dimensions:
            errors.append("dimensions must have at least one value")
        if "sum" not in self.metric_fields or "qty" not in self.metric_fields:
            errors.append("metric_fields must have both 'sum' and 'qty' keys")
        return errors


@dataclass
class AnalysisRun:
    """A single execution of anomaly detection."""

    source_id: str
    date_from: date
    date_to: date
    triggered_by: str = "user"
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    anomaly_count: int = 0
    error_message: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))

    def mark_completed(self, anomaly_count: int) -> None:
        """Mark analysis as completed."""
        self.completed_at = datetime.now()
        self.status = "completed"
        self.anomaly_count = anomaly_count

    def mark_failed(self, error_message: str) -> None:
        """Mark analysis as failed."""
        self.completed_at = datetime.now()
        self.status = "failed"
        self.error_message = error_message


@dataclass
class DataPoint:
    """Computed metric value for a specific dimension combination."""

    source_id: str
    dimensions: dict[str, str]
    period: date
    value: float
    raw_sum: float
    raw_qty: float
    run_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        """Validate DataPoint invariant."""
        if self.raw_qty != 0:
            expected_value = self.raw_sum / self.raw_qty
            if abs(self.value - expected_value) > 0.0001:
                raise ValueError(
                    f"value must equal raw_sum/raw_qty: {self.value} != {expected_value}"
                )


@dataclass
class Anomaly:
    """Detected deviation from expected behavior."""

    source_id: str
    dimensions: dict[str, str]
    period: date
    anomaly_type: Literal["SPIKE", "TREND_BREAK", "ZERO_NEG", "MISSING", "RATIO", "MISSING_DATA"]
    current_value: float | None = None
    previous_value: float | None = None
    pct_change: float | None = None
    zscore: float | None = None
    threshold_triggered: dict = field(default_factory=dict)
    run_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> dict:
        """Convert Anomaly to dictionary."""
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
