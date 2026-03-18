"""DataPoint transformer: converts raw 1C rows into domain DataPoint objects.

Constitution III: Computed metrics (Sum/Qty) are calculated here at analysis time.
Raw values are preserved for audit.
"""

from datetime import date

from src.domain.models import DataPoint, DataSource


def transform_raw_data(
    raw_rows: list[dict],
    source: DataSource,
    run_id: str,
) -> list[DataPoint]:
    """Convert raw 1C rows into DataPoint objects.

    Args:
        raw_rows: List of dicts from 1C HTTP service (may have Cyrillic keys).
        source: DataSource config with dimension names and metric field mapping.
        run_id: ID of the current AnalysisRun for traceability.

    Returns:
        List of DataPoint objects. Rows with invalid period strings are skipped.
        Rows with qty == 0 produce a DataPoint with value=0 (raw_qty preserved).
        MISSING_DATA anomaly detection for qty=0 is handled by the detector.
    """
    sum_field = source.metric_fields["sum"]
    qty_field = source.metric_fields["qty"]

    data_points: list[DataPoint] = []

    for row in raw_rows:
        period_str = row.get("Период", "")
        try:
            period = date.fromisoformat(str(period_str))
        except (ValueError, TypeError):
            continue

        dimensions = {dim: str(row.get(dim, "")) for dim in source.dimensions}
        raw_sum = float(row.get(sum_field, 0.0))
        raw_qty = float(row.get(qty_field, 0.0))
        value = raw_sum / raw_qty if raw_qty != 0 else 0.0

        data_points.append(
            DataPoint(
                source_id=source.id,
                dimensions=dimensions,
                period=period,
                value=value,
                raw_sum=raw_sum,
                raw_qty=raw_qty,
                run_id=run_id,
            )
        )

    return data_points
