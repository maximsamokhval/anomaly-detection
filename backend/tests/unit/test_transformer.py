"""Unit tests for DataPoint transformer (T047)."""

from datetime import date

import pytest

from src.domain.models import AuthConfig, DataSource, ThresholdRules
from src.domain.transformer import transform_raw_data


@pytest.fixture
def source() -> DataSource:
    return DataSource(
        id="sales",
        name="Sales",
        endpoint="http://1c/hs",
        register_name="Sales",
        dimensions=["Номенклатура", "Склад"],
        metric_fields={"sum": "Сумма", "qty": "Количество"},
        threshold_rules=ThresholdRules(),
        auth=AuthConfig(),
    )


def _row(product: str, warehouse: str, period: str, summa: float, qty: float) -> dict:
    return {
        "Номенклатура": product,
        "Склад": warehouse,
        "Период": period,
        "Сумма": summa,
        "Количество": qty,
    }


class TestTransformBasic:
    def test_computes_value_as_sum_div_qty(self, source: DataSource) -> None:
        rows = [_row("A", "W1", "2026-01-31", 100000.0, 100.0)]
        points = transform_raw_data(rows, source, run_id="r1")
        assert len(points) == 1
        assert points[0].value == pytest.approx(1000.0)
        assert points[0].raw_sum == 100000.0
        assert points[0].raw_qty == 100.0

    def test_extracts_dimensions(self, source: DataSource) -> None:
        rows = [_row("Продукт А", "Центральный", "2026-01-31", 50000.0, 50.0)]
        points = transform_raw_data(rows, source, run_id="r1")
        assert points[0].dimensions == {"Номенклатура": "Продукт А", "Склад": "Центральный"}

    def test_parses_period_date(self, source: DataSource) -> None:
        rows = [_row("A", "W", "2026-03-31", 10000.0, 10.0)]
        points = transform_raw_data(rows, source, run_id="r1")
        assert points[0].period == date(2026, 3, 31)

    def test_assigns_source_and_run_id(self, source: DataSource) -> None:
        rows = [_row("A", "W", "2026-01-31", 1000.0, 1.0)]
        points = transform_raw_data(rows, source, run_id="run-xyz")
        assert points[0].source_id == "sales"
        assert points[0].run_id == "run-xyz"

    def test_multiple_rows(self, source: DataSource) -> None:
        rows = [
            _row("A", "W", "2026-01-31", 1000.0, 2.0),
            _row("B", "W", "2026-01-31", 3000.0, 3.0),
        ]
        points = transform_raw_data(rows, source, run_id="r1")
        assert len(points) == 2

    def test_empty_input(self, source: DataSource) -> None:
        assert transform_raw_data([], source, run_id="r1") == []


class TestTransformQtyZero:
    def test_qty_zero_creates_datapoint_with_zero_value(self, source: DataSource) -> None:
        rows = [_row("A", "W", "2026-01-31", 5000.0, 0.0)]
        points = transform_raw_data(rows, source, run_id="r1")
        assert len(points) == 1
        assert points[0].raw_qty == 0.0
        assert points[0].value == 0.0

    def test_qty_zero_preserves_raw_sum(self, source: DataSource) -> None:
        rows = [_row("A", "W", "2026-01-31", 9999.0, 0.0)]
        points = transform_raw_data(rows, source, run_id="r1")
        assert points[0].raw_sum == 9999.0


class TestTransformEdgeCases:
    def test_skips_row_with_invalid_period(self, source: DataSource) -> None:
        rows = [
            {"Номенклатура": "A", "Склад": "W", "Период": "not-a-date", "Сумма": 100.0, "Количество": 1.0}
        ]
        points = transform_raw_data(rows, source, run_id="r1")
        assert len(points) == 0

    def test_missing_dimension_uses_empty_string(self, source: DataSource) -> None:
        rows = [{"Период": "2026-01-31", "Сумма": 100.0, "Количество": 1.0}]
        points = transform_raw_data(rows, source, run_id="r1")
        assert points[0].dimensions == {"Номенклатура": "", "Склад": ""}
