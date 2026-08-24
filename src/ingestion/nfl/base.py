from abc import ABC, abstractmethod
from datetime import date

from games.models import Season
from ingestion.results import IngestionResult
from ingestion.state import is_complete, mark_complete


class NFLIngestor(ABC):
    dataset: str

    def __init__(self, season: int | None = None, force: bool = False) -> None:
        self.season: int = season if season is not None else self.get_current_season()
        self.force: bool = force

    @staticmethod
    def get_current_season() -> int:
        today = date.today()

        if today.month <= 2:
            return today.year - 1

        return today.year

    def should_ingest(self, season: Season) -> bool:
        if self.force:
            return True
        return not is_complete(season, self.dataset)

    def complete(self, season: Season) -> None:
        mark_complete(season, self.dataset)

    @abstractmethod
    def ingest(self) -> IngestionResult:
        pass
