from abc import ABC, abstractmethod
from datetime import date


class NFLIngestor(ABC):
    def __init__(self, season: int | None = None) -> None:
        self.season = season if season is not None else self.get_current_season()

    @staticmethod
    def get_current_season() -> int:
        today = date.today()

        if today.month <= 2:
            return today.year - 1

        return today.year

    @abstractmethod
    def ingest(self) -> None:
        pass