"""Heat map routes - GET /api/v1/heatmap."""

from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from src.api.schemas import HeatMapCell, HeatMapColumn, HeatMapLegend, HeatMapResponse, HeatMapRow
from src.infrastructure.persistence.sqlite import (
    SQLiteAnalysisRunRepository,
    SQLiteAnomalyRepository,
)

router = APIRouter()

_DB_PATH = str(Path(__file__).parents[3] / "data" / "anomaly_detection.db")

_anomaly_repo = SQLiteAnomalyRepository(_DB_PATH)
_run_repo = SQLiteAnalysisRunRepository(_DB_PATH)

# Anomaly type priority for cell conflict resolution (lower = higher severity)
_TYPE_PRIORITY: dict[str, int] = {
    "ZERO_NEG": 1,
    "SPIKE": 2,
    "RATIO": 3,
    "TREND_BREAK": 4,
    "MISSING": 5,
    "MISSING_DATA": 6,
}

_LEGEND: dict[str, tuple[str, str, int]] = {
    # key: (color, label, priority)
    "ZERO_NEG": ("#DC2626", "Zero/Negative", 1),
    "SPIKE": ("#F59E0B", "Spike", 2),
    "RATIO": ("#8B5CF6", "Ratio", 3),
    "TREND_BREAK": ("#3B82F6", "Trend Break", 4),
    "MISSING": ("#6B7280", "Missing", 5),
    "MISSING_DATA": ("#111827", "Missing Data", 6),
}


def _build_legend() -> dict[str, HeatMapLegend]:
    return {
        k: HeatMapLegend(color=color, label=label, priority=priority)
        for k, (color, label, priority) in _LEGEND.items()
    }


@router.get(
    "",
    response_model=HeatMapResponse,
    summary="Get heat map data",
    description=(
        "Returns rows (dimension combinations), columns (periods), and cells "
        "(anomaly type per combination/period) for the heat map visualization."
    ),
    responses={
        400: {"model": dict, "description": "run_id is required"},
        404: {"model": dict, "description": "Analysis run not found"},
    },
)
async def get_heatmap(
    run_id: str = Query(..., description="Analysis run ID"),
) -> HeatMapResponse:
    """Build heat map data from persisted anomalies for the given run."""
    run = _run_repo.get_by_id(run_id)
    if not run:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Analysis run '{run_id}' not found"},
        )

    anomalies = _anomaly_repo.get_by_run_id(run_id)

    if not anomalies:
        return HeatMapResponse(
            run_id=run_id,
            row_dimensions=[],
            rows=[],
            columns=[],
            cells=[],
            legend=_build_legend(),
        )

    # Collect unique dimension combinations (rows) and periods (columns)
    dim_key_to_values: dict[str, dict[str, str]] = {}
    periods: set[str] = set()

    for anomaly in anomalies:
        key = "|".join(f"{k}={v}" for k, v in sorted(anomaly.dimensions.items()))
        dim_key_to_values[key] = anomaly.dimensions
        if anomaly.period:
            periods.add(anomaly.period.isoformat())

    # Sort rows by dim key, columns by period
    sorted_dim_keys = sorted(dim_key_to_values.keys())
    sorted_periods = sorted(periods)

    row_idx_map = {key: i for i, key in enumerate(sorted_dim_keys)}
    col_idx_map = {period: i for i, period in enumerate(sorted_periods)}

    # Build cells: one cell per (row, col) with highest-priority anomaly type
    # Map: (row_idx, col_idx) -> best anomaly
    cell_map: dict[tuple[int, int], dict] = {}

    for anomaly in anomalies:
        if not anomaly.period:
            continue
        dim_key = "|".join(f"{k}={v}" for k, v in sorted(anomaly.dimensions.items()))
        row_i = row_idx_map[dim_key]
        col_i = col_idx_map[anomaly.period.isoformat()]
        cell_key = (row_i, col_i)

        atype = anomaly.anomaly_type
        priority = _TYPE_PRIORITY.get(atype, 99)

        existing = cell_map.get(cell_key)
        if existing is None or priority < existing["_priority"]:
            pct = anomaly.pct_change
            intensity = min(abs(pct) / 200.0, 1.0) if pct is not None else 1.0
            cell_map[cell_key] = {
                "row_idx": row_i,
                "col_idx": col_i,
                "type": atype,
                "intensity": round(intensity, 3),
                "anomaly_id": anomaly.id,
                "pct_change": anomaly.pct_change,
                "current_value": anomaly.current_value,
                "previous_value": anomaly.previous_value,
                "_priority": priority,
            }

    # Build typed cells (strip _priority)
    cells = [
        HeatMapCell(
            row_idx=cell["row_idx"],
            col_idx=cell["col_idx"],
            type=cell["type"],
            intensity=cell["intensity"],
            anomaly_id=cell["anomaly_id"],
            pct_change=cell["pct_change"],
            current_value=cell["current_value"],
            previous_value=cell["previous_value"],
        )
        for cell in cell_map.values()
    ]
    cells.sort(key=lambda c: (c.row_idx, c.col_idx))

    # Determine row_dimensions from first combination's keys
    first_dims = dim_key_to_values[sorted_dim_keys[0]] if sorted_dim_keys else {}
    row_dimensions = sorted(first_dims.keys())

    rows = [
        HeatMapRow(idx=i, values=dim_key_to_values[key]) for i, key in enumerate(sorted_dim_keys)
    ]
    columns = [
        HeatMapColumn(idx=i, period=date.fromisoformat(period))
        for i, period in enumerate(sorted_periods)
    ]

    return HeatMapResponse(
        run_id=run_id,
        row_dimensions=row_dimensions,
        rows=rows,
        columns=columns,
        cells=cells,
        legend=_build_legend(),
    )
