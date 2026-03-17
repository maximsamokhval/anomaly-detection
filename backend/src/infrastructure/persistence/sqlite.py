"""SQLite implementation of repository interfaces."""

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.domain.models import AnalysisRun, Anomaly, AuthConfig, DataSource, ThresholdRules
from src.infrastructure.persistence.base import (
    AnalysisRunRepository,
    AnomalyRepository,
    DataSourceRepository,
)


def _serialize_threshold_rules(rules: ThresholdRules) -> str:
    """Serialize ThresholdRules to JSON."""
    return json.dumps(
        {
            "spike_pct": rules.spike_pct,
            "spike_zscore": rules.spike_zscore,
            "spike_logic": rules.spike_logic,
            "moving_avg_window": rules.moving_avg_window,
            "trend_window": rules.trend_window,
            "trend_min_points": rules.trend_min_points,
            "ratio_min": rules.ratio_min,
            "ratio_max": rules.ratio_max,
            "zero_neg_enabled": rules.zero_neg_enabled,
            "missing_enabled": rules.missing_enabled,
            "ratio_enabled": rules.ratio_enabled,
        }
    )


def _deserialize_threshold_rules(data: str) -> ThresholdRules:
    """Deserialize ThresholdRules from JSON."""
    obj = json.loads(data)
    return ThresholdRules(
        spike_pct=obj.get("spike_pct", 20.0),
        spike_zscore=obj.get("spike_zscore", 3.0),
        spike_logic=obj.get("spike_logic", "OR"),
        moving_avg_window=obj.get("moving_avg_window", 6),
        trend_window=obj.get("trend_window", 3),
        trend_min_points=obj.get("trend_min_points", 5),
        ratio_min=obj.get("ratio_min"),
        ratio_max=obj.get("ratio_max"),
        zero_neg_enabled=obj.get("zero_neg_enabled", True),
        missing_enabled=obj.get("missing_enabled", True),
        ratio_enabled=obj.get("ratio_enabled", False),
    )


def _serialize_auth_config(auth: AuthConfig) -> str:
    """Serialize AuthConfig to JSON."""
    return json.dumps({"type": auth.type, "user": auth.user, "password": auth.password})


def _deserialize_auth_config(data: str) -> AuthConfig:
    """Deserialize AuthConfig from JSON."""
    obj = json.loads(data)
    return AuthConfig(
        type=obj.get("type", "none"),
        user=obj.get("user"),
        password=obj.get("password"),
    )


def _serialize_dimensions(dimensions: list[str]) -> str:
    """Serialize dimensions list to JSON."""
    return json.dumps(dimensions)


def _deserialize_dimensions(data: str) -> list[str]:
    """Deserialize dimensions list from JSON."""
    return json.loads(data)  # type: ignore[no-any-return]


def _serialize_metric_fields(fields: dict[str, str]) -> str:
    """Serialize metric fields to JSON."""
    return json.dumps(fields)


def _deserialize_metric_fields(data: str) -> dict[str, str]:
    """Deserialize metric fields from JSON."""
    return json.loads(data)  # type: ignore[no-any-return]


def _serialize_dimensions_dict(dimensions: dict[str, str]) -> str:
    """Serialize dimensions dict to JSON."""
    return json.dumps(dimensions)


def _deserialize_dimensions_dict(data: str) -> dict[str, str]:
    """Deserialize dimensions dict from JSON."""
    return json.loads(data)  # type: ignore[no-any-return]


def _serialize_threshold_triggered(triggered: dict) -> str:
    """Serialize threshold_triggered dict to JSON."""
    return json.dumps(triggered)


def _deserialize_threshold_triggered(data: str) -> dict:
    """Deserialize threshold_triggered dict from JSON."""
    return json.loads(data)  # type: ignore[no-any-return]


def _parse_date(date_str: str) -> date:
    """Parse date from ISO format string."""
    return datetime.fromisoformat(date_str).date()


def _parse_datetime(dt_str: str) -> datetime:
    """Parse datetime from ISO format string."""
    return datetime.fromisoformat(dt_str)


class SQLiteDataSourceRepository(DataSourceRepository):
    """SQLite implementation of DataSourceRepository."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS data_sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                register_name TEXT NOT NULL,
                dimensions TEXT NOT NULL,
                metric_fields TEXT NOT NULL,
                threshold_rules TEXT NOT NULL,
                auth_config TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        """
        )
        conn.commit()
        conn.close()

    def get_all(self) -> list[DataSource]:
        """Retrieve all data sources."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data_sources")
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_source(row) for row in rows]

    def get_by_id(self, id: str) -> DataSource | None:
        """Retrieve a single data source by ID."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data_sources WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_source(row) if row else None

    def save(self, source: DataSource) -> None:
        """Save or update a data source."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO data_sources
            (id, name, endpoint, register_name, dimensions, metric_fields,
             threshold_rules, auth_config, enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                source.id,
                source.name,
                source.endpoint,
                source.register_name,
                _serialize_dimensions(source.dimensions),
                _serialize_metric_fields(source.metric_fields),
                _serialize_threshold_rules(source.threshold_rules),
                _serialize_auth_config(source.auth),
                1 if source.enabled else 0,
                source.created_at.isoformat(),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

    def delete(self, id: str) -> None:
        """Delete a data source by ID."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM data_sources WHERE id = ?", (id,))
        conn.commit()
        conn.close()

    def exists(self, id: str) -> bool:
        """Check if a data source exists."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM data_sources WHERE id = ?", (id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def _row_to_source(self, row: tuple[Any, ...]) -> DataSource:
        """Convert database row to DataSource."""
        return DataSource(
            id=row[0],
            name=row[1],
            endpoint=row[2],
            register_name=row[3],
            dimensions=_deserialize_dimensions(row[4]),
            metric_fields=_deserialize_metric_fields(row[5]),
            threshold_rules=_deserialize_threshold_rules(row[6]),
            auth=_deserialize_auth_config(row[7]),
            enabled=bool(row[8]),
            created_at=_parse_datetime(row[9]) if row[9] else datetime.now(),
            updated_at=_parse_datetime(row[10]) if row[10] else datetime.now(),
        )


class SQLiteAnalysisRunRepository(AnalysisRunRepository):
    """SQLite implementation of AnalysisRunRepository."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                date_from DATE NOT NULL,
                date_to DATE NOT NULL,
                triggered_by TEXT DEFAULT 'user',
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed')) NOT NULL,
                anomaly_count INTEGER,
                error_message TEXT,
                FOREIGN KEY (source_id) REFERENCES data_sources(id)
            )
        """
        )
        conn.commit()
        conn.close()

    def create(self, run: AnalysisRun) -> None:
        """Create a new analysis run."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO analysis_runs
            (id, source_id, date_from, date_to, triggered_by, started_at,
             completed_at, status, anomaly_count, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                run.id,
                run.source_id,
                run.date_from.isoformat(),
                run.date_to.isoformat(),
                run.triggered_by,
                run.started_at.isoformat(),
                run.completed_at.isoformat() if run.completed_at else None,
                run.status,
                run.anomaly_count,
                run.error_message,
            ),
        )
        conn.commit()
        conn.close()

    def get_by_id(self, id: str) -> AnalysisRun | None:
        """Retrieve an analysis run by ID."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_runs WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        return self._row_to_run(row) if row else None

    def update_status(
        self, id: str, status: str, error_message: str | None = None
    ) -> None:
        """Update the status of an analysis run."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE analysis_runs
            SET status = ?, error_message = ?, completed_at = ?
            WHERE id = ?
        """,
            (
                status,
                error_message,
                datetime.now().isoformat() if status in ("completed", "failed") else None,
                id,
            ),
        )
        conn.commit()
        conn.close()

    def get_latest(self, source_id: str) -> AnalysisRun | None:
        """Get the most recent analysis run for a source."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM analysis_runs
            WHERE source_id = ?
            ORDER BY started_at DESC
            LIMIT 1
        """,
            (source_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return self._row_to_run(row) if row else None

    def _row_to_run(self, row: tuple[Any, ...]) -> AnalysisRun:
        """Convert database row to AnalysisRun."""
        return AnalysisRun(
            id=row[0],
            source_id=row[1],
            date_from=_parse_date(row[2]),
            date_to=_parse_date(row[3]),
            triggered_by=row[4] or "user",
            started_at=_parse_datetime(row[5]),
            completed_at=_parse_datetime(row[6]) if row[6] else None,
            status=row[7],
            anomaly_count=row[8] or 0,
            error_message=row[9],
        )


class SQLiteAnomalyRepository(AnomalyRepository):
    """SQLite implementation of AnomalyRepository."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS anomalies (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                dimensions TEXT NOT NULL,
                period DATE NOT NULL,
                anomaly_type TEXT CHECK(anomaly_type IN (
                    'SPIKE', 'TREND_BREAK', 'ZERO_NEG', 'MISSING', 'RATIO', 'MISSING_DATA'
                )) NOT NULL,
                current_value REAL,
                previous_value REAL,
                pct_change REAL,
                zscore REAL,
                threshold_triggered TEXT,
                FOREIGN KEY (run_id) REFERENCES analysis_runs(id),
                FOREIGN KEY (source_id) REFERENCES data_sources(id)
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_anomalies_run ON anomalies(run_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_anomalies_source ON anomalies(source_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_anomalies_type ON anomalies(anomaly_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_anomalies_period ON anomalies(period)"
        )
        conn.commit()
        conn.close()

    def save_batch(self, anomalies: list[Anomaly]) -> None:
        """Save multiple anomalies at once."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        for anomaly in anomalies:
            cursor.execute(
                """
                INSERT INTO anomalies
                (id, run_id, source_id, dimensions, period, anomaly_type,
                 current_value, previous_value, pct_change, zscore, threshold_triggered)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    anomaly.id,
                    anomaly.run_id,
                    anomaly.source_id,
                    _serialize_dimensions_dict(anomaly.dimensions),
                    anomaly.period.isoformat(),
                    anomaly.anomaly_type,
                    anomaly.current_value,
                    anomaly.previous_value,
                    anomaly.pct_change,
                    anomaly.zscore,
                    _serialize_threshold_triggered(anomaly.threshold_triggered)
                    if anomaly.threshold_triggered
                    else None,
                ),
            )
        conn.commit()
        conn.close()

    def get_by_run_id(self, run_id: str) -> list[Anomaly]:
        """Get all anomalies for a specific run."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM anomalies WHERE run_id = ? ORDER BY period DESC", (run_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_anomaly(row) for row in rows]

    def get_by_filters(
        self,
        source_id: str | None = None,
        anomaly_type: str | None = None,
        period_from: date | None = None,
        period_to: date | None = None,
        dimension_filters: dict[str, str] | None = None,
    ) -> list[Anomaly]:
        """Get anomalies with optional filtering."""
        query = "SELECT * FROM anomalies WHERE 1=1"
        params: list[Any] = []

        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)

        if anomaly_type:
            query += " AND anomaly_type = ?"
            params.append(anomaly_type)

        if period_from:
            query += " AND period >= ?"
            params.append(period_from.isoformat())

        if period_to:
            query += " AND period <= ?"
            params.append(period_to.isoformat())

        if dimension_filters:
            # JSON extraction for dimension filters
            for key, value in dimension_filters.items():
                query += f" AND json_extract(dimensions, '$.{key}') = ?"
                params.append(value)

        query += " ORDER BY period DESC"

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_anomaly(row) for row in rows]

    def count_by_run_id(self, run_id: str) -> int:
        """Count anomalies for a specific run."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM anomalies WHERE run_id = ?", (run_id,)
        )
        count = cursor.fetchone()[0]  # type: ignore[no-any-return]
        conn.close()
        return count

    def _row_to_anomaly(self, row: tuple[Any, ...]) -> Anomaly:
        """Convert database row to Anomaly."""
        return Anomaly(
            id=row[0],
            run_id=row[1],
            source_id=row[2],
            dimensions=_deserialize_dimensions_dict(row[3]),
            period=_parse_date(row[4]),
            anomaly_type=row[5],
            current_value=row[6],
            previous_value=row[7],
            pct_change=row[8],
            zscore=row[9],
            threshold_triggered=_deserialize_threshold_triggered(row[10])
            if row[10]
            else {},
        )
