from ingestion.nfl.schedules import ingest_schedule
from ingestion.nfl.teams import ingest_teams


def ingest_nfl(season: int):
    ingest_schedule(season)
    ingest_teams()
