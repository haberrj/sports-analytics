import nflreadpy as nfl

from ingestion.nfl.games import NFLGameIngestor
from ingestion.services import LeagueIngestionService


class NFLIngestionService(LeagueIngestionService):
    def get_available_seasons(self) -> list[int]:
        schedules = nfl.load_schedules(True)

        return sorted(schedules["season"].drop_nulls().unique().to_list())

    def ingest_season(self, season: int) -> None:
        NFLGameIngestor(season).ingest()
