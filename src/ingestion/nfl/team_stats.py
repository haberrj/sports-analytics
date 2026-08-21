import nflreadpy as nfl
from polars import DataFrame

from games.models import Game
from ingestion.nfl.base import NFLIngestor
from stats.models import NFLTeamGameStats
from teams.models import TeamSeason


class NFLTeamStatsIngestor(NFLIngestor):
    def __init__(self, season: int | None = None) -> None:
        super().__init__(season)
        self.stats: DataFrame = nfl.load_team_stats()

    def ingest(self) -> None:
        for team_data in self.stats.iter_rows(named=True):
            opponent_data = self._get_opponent_data(team_data)

            game = Game.objects.get(
                external_id=team_data["game_id"],
            )

            team = TeamSeason.objects.select_related("team").get(
                season=game.season,
                abbreviation=team_data["team"],
            ).team

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
                    "passing_yards_after_catch": team_data[
                        "passing_yards_after_catch"
                    ],

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

                    "offensive_turnovers": self._get_offensive_turnovers(
                        team_data
                    ),

                    "defensive_sacks": team_data["def_sacks"],
                    "defensive_passing_yards_allowed": opponent_data[
                        "passing_yards"
                    ],
                    "defensive_rushing_yards_allowed": opponent_data[
                        "rushing_yards"
                    ],
                    "defensive_turnovers_forced": self._get_offensive_turnovers(
                        opponent_data
                    ),
                    "defensive_qb_hits": team_data["def_qb_hits"],
                    "defensive_tackles_for_loss": team_data[
                        "def_tackles_for_loss"
                    ],

                    "field_goals_made": team_data["fg_made"],
                    "field_goals_attempted": team_data["fg_att"],
                },
            )

    def _get_opponent_data(self, team_data: dict) -> dict:
        opponent = self.stats.filter(
            (self.stats["game_id"] == team_data["game_id"])
            & (self.stats["team"] == team_data["opponent_team"])
        )

        rows = opponent.to_dicts()

        if len(rows) != 1:
            raise ValueError(
                f"Expected one opponent row for {team_data['game_id']} "
                f"and {team_data['opponent_team']}, found {len(rows)}."
            )

        return rows[0]

    @staticmethod
    def _get_offensive_turnovers(team_data: dict) -> int:
        return (
            team_data["passing_interceptions"]
            + team_data["fumbles_lost_total"]
        )

    @staticmethod
    def _get_points_for(game: Game, team) -> int:
        if game.home_team_id == team.id:
            return game.home_score or 0

        return game.away_score or 0

    @staticmethod
    def _get_points_allowed(game: Game, team) -> int:
        if game.home_team_id == team.id:
            return game.away_score or 0

        return game.home_score or 0