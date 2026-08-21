from abc import ABC, abstractmethod
from collections.abc import Callable

from ingestion.results import IngestionResult


class LeagueIngestionService(ABC):
    @abstractmethod
    def get_available_seasons(self) -> list[int]:
        pass

    @abstractmethod
    def get_current_season(self) -> int:
        pass

    @abstractmethod
    def ingest_season(self, season: int) -> IngestionResult:
        pass

    def ingest_all_seasons(
        self,
        on_season_start: Callable[[int, int, int], None] | None = None,
        on_season_complete: Callable[[int, int, int], None] | None = None,
    ) -> None:
        seasons = self.get_available_seasons()
        total = len(seasons)

        for index, season in enumerate(seasons, start=1):
            if on_season_start:
                on_season_start(season, index, total)

            results = self.ingest_season(season)

            if on_season_complete:
                on_season_complete(season, results)
