from abc import ABC, abstractmethod
from collections.abc import Callable


class LeagueIngestionService(ABC):
    @abstractmethod
    def get_available_seasons(self) -> list[int]:
        pass

    @abstractmethod
    def get_current_season(self) -> int:
        pass

    @abstractmethod
    def ingest_season(self, season: int) -> None:
        pass

    def ingest_all_seasons(self, on_season_start: Callable[[int, int, int], None] | None = None) -> None:
        seasons = self.get_available_seasons()
        total = len(seasons)

        for index, season in enumerate(seasons, start=1):
            if on_season_start:
                on_season_start(season, index, total)

            self.ingest_season(season)
