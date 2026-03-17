"""Jinja2 templates configuration."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

# Templates directory - located at backend/ui/templates (sibling of src/)
templates_path = Path(__file__).parent.parent.parent / "ui" / "templates"
templates_path.mkdir(parents=True, exist_ok=True)

# Jinja2 templates with autoescape enabled for security
templates = Jinja2Templates(directory=str(templates_path))

# Custom Jinja2 filters
templates.env.filters["to_json"] = lambda value: __import__("json").dumps(value, default=str)


def format_number_filter(value: float | None, decimals: int = 2) -> str:
    """Format number with specified decimal places."""
    if value is None:
        return "Н/Д"
    return f"{value:,.{decimals}f}".replace(",", " ")


templates.env.filters["format_number"] = format_number_filter


def format_date_filter(value: object) -> str:
    """Format date for display."""
    if value is None:
        return "Н/Д"
    from datetime import date, datetime
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    elif isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


templates.env.filters["format_date"] = format_date_filter


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


templates.env.filters["anomaly_color"] = anomaly_color_filter


def anomaly_label_filter(anomaly_type: str) -> str:
    """Get human-readable label for anomaly type in Ukrainian."""
    labels = {
        "ZERO_NEG": "Нуль/Негативне",
        "SPIKE": "Спалах",
        "RATIO": "Відношення",
        "TREND_BREAK": "Розрив тренду",
        "MISSING": "Відсутні",
        "MISSING_DATA": "Відсутні дані",
    }
    return labels.get(anomaly_type, anomaly_type)


templates.env.filters["anomaly_label"] = anomaly_label_filter
