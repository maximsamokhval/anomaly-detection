"""Repository interfaces for data persistence abstraction."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from src.domain.models import AnalysisRun, Anomaly, DataSource


class DataSourceRepository(ABC):
    """Abstract repository for DataSource persistence."""

    @abstractmethod
    def get_all(self) -> list[DataSource]:
        """Retrieve all data sources."""
        pass

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[DataSource]:
        """Retrieve a single data source by ID."""
        pass

    @abstractmethod
    def save(self, source: DataSource) -> None:
        """Save or update a data source."""
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        """Delete a data source by ID."""
        pass

    @abstractmethod
    def exists(self, id: str) -> bool:
        """Check if a data source exists."""
        pass


class AnalysisRunRepository(ABC):
    """Abstract repository for AnalysisRun persistence."""

    @abstractmethod
    def create(self, run: AnalysisRun) -> None:
        """Create a new analysis run."""
        pass

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[AnalysisRun]:
        """Retrieve an analysis run by ID."""
        pass

    @abstractmethod
    def update_status(
        self, id: str, status: str, error_message: str | None = None
    ) -> None:
        """Update the status of an analysis run."""
        pass

    @abstractmethod
    def get_latest(self, source_id: str) -> Optional[AnalysisRun]:
        """Get the most recent analysis run for a source."""
        pass


class AnomalyRepository(ABC):
    """Abstract repository for Anomaly persistence."""

    @abstractmethod
    def save_batch(self, anomalies: list[Anomaly]) -> None:
        """Save multiple anomalies at once."""
        pass

    @abstractmethod
    def get_by_run_id(self, run_id: str) -> list[Anomaly]:
        """Get all anomalies for a specific run."""
        pass

    @abstractmethod
    def get_by_filters(
        self,
        source_id: str | None = None,
        anomaly_type: str | None = None,
        period_from: date | None = None,
        period_to: date | None = None,
        dimension_filters: dict[str, str] | None = None,
    ) -> list[Anomaly]:
        """Get anomalies with optional filtering."""
        pass

    @abstractmethod
    def count_by_run_id(self, run_id: str) -> int:
        """Count anomalies for a specific run."""
        pass
