#!/usr/bin/env python3
"""Database initialization script for Financial Anomaly Detection Service.

Creates all required tables and indexes for SQLite database.
Run this script once to initialize the database before first use.

Usage:
    python scripts/init_db.py [--db-path path/to/database.db]
"""

import argparse
import sqlite3
from pathlib import Path


def init_database(db_path: str | Path) -> None:
    """Initialize database with all required tables and indexes.

    Args:
        db_path: Path to SQLite database file
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Data Sources table
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

    # Analysis Runs table
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

    # Anomalies table
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

    # Optional: Data Points table (for debugging/audit)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS data_points (
            id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            dimensions TEXT NOT NULL,
            period DATE NOT NULL,
            value REAL NOT NULL,
            raw_sum REAL NOT NULL,
            raw_qty REAL NOT NULL,
            FOREIGN KEY (run_id) REFERENCES analysis_runs(id),
            FOREIGN KEY (source_id) REFERENCES data_sources(id)
        )
    """
    )

    # Create indexes for performance
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_runs_source ON analysis_runs(source_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_runs_status ON analysis_runs(status)"
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
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_data_points_run ON data_points(run_id)"
    )

    conn.commit()
    conn.close()

    print(f"✅ Database initialized successfully at: {db_path}")
    print("Tables created:")
    print("  - data_sources")
    print("  - analysis_runs")
    print("  - anomalies")
    print("  - data_points (optional persistence)")
    print("Indexes created:")
    print("  - idx_runs_source, idx_runs_status")
    print("  - idx_anomalies_run, idx_anomalies_source, idx_anomalies_type, idx_anomalies_period")
    print("  - idx_data_points_run")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize SQLite database for Financial Anomaly Detection Service"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="backend/data/anomaly_detection.db",
        help="Path to SQLite database file (default: backend/data/anomaly_detection.db)",
    )
    args = parser.parse_args()

    init_database(args.db_path)


if __name__ == "__main__":
    main()
