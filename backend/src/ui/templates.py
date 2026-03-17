"""Jinja2 templates configuration."""

from fastapi.templating import Jinja2Templates
from pathlib import Path

# Templates directory
templates_path = Path(__file__).parent / "templates"
templates_path.mkdir(parents=True, exist_ok=True)

# Jinja2 templates with autoescape enabled for security
templates = Jinja2Templates(directory=str/templates_path))

# Custom Jinja2 filters
@templates.env.filter("to_json")
def to_json_filter(value: object) -> str:
    """Convert value to JSON string for embedding in templates."""
    import json
    return json.dumps(value, default=str)


@templates.env.filter("format_number")
def format_number_filter(value: float | None, decimals: int = 2) -> str:
    """Format number with specified decimal places."""
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


@templates.env.filter("format_date")
def format_date_filter(value: object) -> str:
    """Format date for display."""
    if value is None:
        return "N/A"
    from datetime import date, datetime
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    elif isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


@templates.env.filter("anomaly_color")
def anomaly_color_filter(anomaly_type: str) -> str:
    """Get color code for anomaly type."""
    colors = {
        "ZERO_NEG": "#DC2626",  # Red - highest priority
        "SPIKE": "#F59E0B",     # Orange - high priority
        "RATIO": "#8B5CF6",     # Purple - medium priority
        "TREND_BREAK": "#3B82F6",  # Blue - low priority
        "MISSING": "#6B7280",   # Gray - low priority
        "MISSING_DATA": "#9CA3AF",  # Light gray
    }
    return colors.get(anomaly_type, "#6B7280")


@templates.env.filter("anomaly_label")
def anomaly_label_filter(anomaly_type: str) -> str:
    """Get human-readable label for anomaly type."""
    labels = {
        "ZERO_NEG": "Zero/Negative",
        "SPIKE": "Spike",
        "RATIO": "Ratio",
        "TREND_BREAK": "Trend Break",
        "MISSING": "Missing",
        "MISSING_DATA": "Missing Data",
    }
    return labels.get(anomaly_type, anomaly_type)
