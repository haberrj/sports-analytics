from abc import ABC, abstractmethod


class LeagueIngestionService(ABC):
    @abstractmethod
    def get_available_seasons(self) -> list[int]:
        pass

    @abstractmethod
    def ingest_season(self, season: int) -> None:
        pass

    def ingest_all_seasons(self) -> None:
        for season in self.get_available_seasons():
            self.ingest_season(season)
