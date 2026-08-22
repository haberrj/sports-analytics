import nflreadpy as nfl

from games.models import Season, Week
from ingestion.nfl.base import NFLIngestor
from ingestion.nfl.games import NFLGameIngestor
from ingestion.nfl.team_stats import NFLTeamStatsIngestor
from ingestion.nfl.teams import NFLTeamIngestor
from ingestion.results import IngestionResult
from ingestion.services import LeagueIngestionService
from stats.nfl.derived import NFLDerivedStatsService


class NFLIngestionService(LeagueIngestionService):
    def get_current_season(self) -> int:
        return NFLIngestor.get_current_season()

    def get_available_seasons(self) -> list[int]:
        schedules = nfl.load_schedules(True)

        return sorted(schedules["season"].drop_nulls().unique().to_list())

    def ingest_season(self, season: int, force: bool = False) -> dict[str, IngestionResult]:
        results = {
            "teams": NFLTeamIngestor(season, force=force).ingest(),
            "games": NFLGameIngestor(season, force=force).ingest(),
            "team_stats": NFLTeamStatsIngestor(season, force=force).ingest(),
        }
        if results["team_stats"] != IngestionResult.UNAVAILABLE:
            results["team_profile"] = self._generate_team_profiles(season)
        else:
            results["team_profile"] = IngestionResult.UNAVAILABLE
        return results

    @staticmethod
    def _generate_team_profiles(season: int) -> IngestionResult:
        nfl_season = Season.objects.get(
            league__abbreviation="NFL",
            name=str(season),
        )

        weeks = Week.objects.filter(season=nfl_season).order_by("number")

        generated = False

        for week in weeks:
            profiles = NFLDerivedStatsService.update_profiles_through_week(week=week)
            if profiles:
                generated = True
        if not generated:
            return IngestionResult.UNAVAILABLE
        return IngestionResult.INGESTED
