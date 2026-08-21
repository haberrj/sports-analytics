import nflreadpy as nfl
from polars import DataFrame

from games.models import Game, Season
from ingestion.models import IngestionState
from ingestion.nfl.base import NFLIngestor
from ingestion.results import IngestionResult
from stats.models import NFLTeamGameStats
from teams.models import Team


class NFLTeamStatsIngestor(NFLIngestor):
    dataset = IngestionState.Dataset.TEAM_STATS

    def __init__(self, season: int | None = None, force: bool = False) -> None:
        super().__init__(season, force)
        self.stats: DataFrame
        self.teams: DataFrame

    def ingest(self) -> IngestionResult:
        season = Season.objects.get(
            league__abbreviation="NFL",
            name=str(self.season),
        )

        if not self.should_ingest(season):
            return IngestionResult.ALREADY_COMPLETE
        try:
            self.stats = nfl.load_team_stats(self.season)
        except ConnectionError:
            return IngestionResult.UNAVAILABLE
        self.teams = nfl.load_teams()

        for team_data in self.stats.iter_rows(named=True):
            if team_data["team"] is None or team_data["game_id"] is None:
                continue

            opponent_data = self._get_opponent_data(team_data)

            game = Game.objects.get(
                external_id=team_data["game_id"],
            )

            team = self._get_team(team_data)

            NFLTeamGameStats.objects.update_or_create(
                game=game,
                team=team,
                defaults={
                    "points_for": self._get_points_for(game, team),
                    "points_allowed": self._get_points_allowed(game, team),
                    "offensive_passing_yards": team_data["passing_yards"],
                    "passing_attempts": team_data["attempts"],
                    "passing_completions": team_data["completions"],
                    "passing_epa": team_data["passing_epa"],
                    "passing_cpoe": team_data["passing_cpoe"],
                    "passing_air_yards": team_data["passing_air_yards"],
                    "passing_yards_after_catch": team_data["passing_yards_after_catch"],
                    "offensive_rushing_yards": team_data["rushing_yards"],
                    "rushing_attempts": team_data["carries"],
                    "rushing_epa": team_data["rushing_epa"],
                    "sacks_allowed": team_data["sacks_suffered"],
                    "first_downs": None,
                    "third_down_attempts": None,
                    "third_down_conversions": None,
                    "fourth_down_attempts": None,
                    "fourth_down_conversions": None,
                    "penalties": team_data["penalties"],
                    "penalty_yards": team_data["penalty_yards"],
                    "offensive_turnovers": self._get_offensive_turnovers(team_data),
                    "defensive_sacks": team_data["def_sacks"],
                    "defensive_passing_yards_allowed": (
                        opponent_data["passing_yards"] if opponent_data is not None else None
                    ),
                    "defensive_rushing_yards_allowed": (
                        opponent_data["rushing_yards"] if opponent_data is not None else None
                    ),
                    "defensive_turnovers_forced": (
                        self._get_offensive_turnovers(opponent_data) if opponent_data is not None else None
                    ),
                    "opponent_passing_attempts": (opponent_data["attempts"] if opponent_data is not None else None),
                    "opponent_rushing_attempts": (opponent_data["carries"] if opponent_data is not None else None),
                    "defensive_qb_hits": team_data["def_qb_hits"],
                    "defensive_tackles_for_loss": team_data["def_tackles_for_loss"],
                    "field_goals_made": team_data["fg_made"],
                    "field_goals_attempted": team_data["fg_att"],
                },
            )
        self.complete(season)
        return IngestionResult.INGESTED

    def _get_opponent_data(self, team_data: dict) -> dict | None:
        opponent = self.stats.filter(
            (self.stats["game_id"] == team_data["game_id"]) & (self.stats["team"] != team_data["team"])
        )

        rows = opponent.to_dicts()

        if len(rows) == 0:
            return None

        if len(rows) > 1:
            raise ValueError(
                f"Expected one opponent row for {team_data['game_id']} and team {team_data['team']}, found {len(rows)}."
            )

        return rows[0]

    def _get_team(self, team_data: dict) -> Team:
        team_rows = self.teams.filter(self.teams["team_abbr"] == team_data["team"])

        rows = team_rows.to_dicts()

        if len(rows) != 1:
            raise ValueError(f"Expected one team row for {team_data['team']}, found {len(rows)}.")

        return Team.objects.get(
            external_id=rows[0]["team_id"],
        )

    @staticmethod
    def _get_offensive_turnovers(team_data: dict) -> int | None:
        interceptions = team_data["passing_interceptions"]
        fumbles_lost = team_data["fumbles_lost_total"]

        if interceptions is None or fumbles_lost is None:
            return None

        return interceptions + fumbles_lost

    @staticmethod
    def _get_points_for(game: Game, team: Team) -> int:
        score = game.home_score if game.home_team_id == team.id else game.away_score

        if score is None:
            raise ValueError(f"Game {game.external_id} has team stats but no score.")

        return score

    @staticmethod
    def _get_points_allowed(game: Game, team: Team) -> int:
        score = game.away_score if game.home_team_id == team.id else game.home_score

        if score is None:
            raise ValueError(f"Game {game.external_id} has team stats but no score.")

        return score
