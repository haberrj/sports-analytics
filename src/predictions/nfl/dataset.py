import pickle
from pathlib import Path

from games.models import Game, Season
from predictions.base import TrainingDataService
from stats.models import NFLTeamProfile
from teams.models import Team


class NFLTrainingDataService(TrainingDataService[NFLTeamProfile, Game, Team]):
    CACHE_DIRECTORY = Path(__file__).resolve().parents[3] / "data" / "cache"

    @staticmethod
    def get_profile_before_game(team: Team, game: Game) -> NFLTeamProfile | None:
        current_season_profile = (
            NFLTeamProfile.objects.filter(
                team=team,
                season=game.season,
                through_week__number__lt=game.week.number,
            )
            .order_by("-through_week__number")
            .first()
        )
        if current_season_profile is not None:
            return current_season_profile

        previous_season = (
            Season.objects.filter(
                league=game.season.league,
                start_date__lt=game.season.start_date,
            )
            .order_by("-start_date")
            .first()
        )
        if previous_season is None:
            return None

        return (
            NFLTeamProfile.objects.filter(
                team=team,
                season=previous_season,
            )
            .order_by("-through_week__number")
            .first()
        )

    @staticmethod
    def build_training_row(game: Game) -> dict | None:
        home_profile = NFLTrainingDataService.get_profile_before_game(team=game.home_team, game=game)

        away_profile = NFLTrainingDataService.get_profile_before_game(team=game.away_team, game=game)

        if home_profile is None or away_profile is None:
            return None

        if game.home_score is None or game.away_score is None:
            return None

        row = {
            # Metadata
            "game_id": game.external_id,
            "season": int(game.season.name),
            "week": game.week.number,
            "home_team": game.home_team.abbreviation,
            "away_team": game.away_team.abbreviation,
            "home_score": game.home_score,
            "away_score": game.away_score,
            # Game context
            "neutral_site": game.neutral_site,
            # Home absolute metrics
            "home_pass_offense_yards_per_attempt": home_profile.pass_offense_yards_per_attempt,
            "home_rush_offense_yards_per_attempt": home_profile.rush_offense_yards_per_attempt,
            "home_pass_defense_yards_per_attempt": home_profile.pass_defense_yards_per_attempt,
            "home_rush_defense_yards_per_attempt": home_profile.rush_defense_yards_per_attempt,
            "home_pass_offense_yards_per_game": home_profile.pass_offense_yards_per_game,
            "home_rush_offense_yards_per_game": home_profile.rush_offense_yards_per_game,
            "home_pass_defense_yards_per_game": home_profile.pass_defense_yards_per_game,
            "home_rush_defense_yards_per_game": home_profile.rush_defense_yards_per_game,
            "home_pass_offense_epa_per_game": home_profile.pass_offense_epa_per_game,
            "home_rush_offense_epa_per_game": home_profile.rush_offense_epa_per_game,
            # Home league-relative metrics
            "home_pass_offense_yards_per_attempt_strength": (home_profile.pass_offense_yards_per_attempt_strength),
            "home_rush_offense_yards_per_attempt_strength": (home_profile.rush_offense_yards_per_attempt_strength),
            "home_pass_defense_yards_per_attempt_strength": (home_profile.pass_defense_yards_per_attempt_strength),
            "home_rush_defense_yards_per_attempt_strength": (home_profile.rush_defense_yards_per_attempt_strength),
            "home_pass_offense_yards_per_game_strength": (home_profile.pass_offense_yards_per_game_strength),
            "home_rush_offense_yards_per_game_strength": (home_profile.rush_offense_yards_per_game_strength),
            "home_pass_defense_yards_per_game_strength": (home_profile.pass_defense_yards_per_game_strength),
            "home_rush_defense_yards_per_game_strength": (home_profile.rush_defense_yards_per_game_strength),
            "home_pass_offense_epa_per_game_strength": (home_profile.pass_offense_epa_per_game_strength),
            "home_rush_offense_epa_per_game_strength": (home_profile.rush_offense_epa_per_game_strength),
            # Away absolute metrics
            "away_pass_offense_yards_per_attempt": away_profile.pass_offense_yards_per_attempt,
            "away_rush_offense_yards_per_attempt": away_profile.rush_offense_yards_per_attempt,
            "away_pass_defense_yards_per_attempt": away_profile.pass_defense_yards_per_attempt,
            "away_rush_defense_yards_per_attempt": away_profile.rush_defense_yards_per_attempt,
            "away_pass_offense_yards_per_game": away_profile.pass_offense_yards_per_game,
            "away_rush_offense_yards_per_game": away_profile.rush_offense_yards_per_game,
            "away_pass_defense_yards_per_game": away_profile.pass_defense_yards_per_game,
            "away_rush_defense_yards_per_game": away_profile.rush_defense_yards_per_game,
            "away_pass_offense_epa_per_game": away_profile.pass_offense_epa_per_game,
            "away_rush_offense_epa_per_game": away_profile.rush_offense_epa_per_game,
            # Away league-relative metrics
            "away_pass_offense_yards_per_attempt_strength": (away_profile.pass_offense_yards_per_attempt_strength),
            "away_rush_offense_yards_per_attempt_strength": (away_profile.rush_offense_yards_per_attempt_strength),
            "away_pass_defense_yards_per_attempt_strength": (away_profile.pass_defense_yards_per_attempt_strength),
            "away_rush_defense_yards_per_attempt_strength": (away_profile.rush_defense_yards_per_attempt_strength),
            "away_pass_offense_yards_per_game_strength": (away_profile.pass_offense_yards_per_game_strength),
            "away_rush_offense_yards_per_game_strength": (away_profile.rush_offense_yards_per_game_strength),
            "away_pass_defense_yards_per_game_strength": (away_profile.pass_defense_yards_per_game_strength),
            "away_rush_defense_yards_per_game_strength": (away_profile.rush_defense_yards_per_game_strength),
            "away_pass_offense_epa_per_game_strength": (away_profile.pass_offense_epa_per_game_strength),
            "away_rush_offense_epa_per_game_strength": (away_profile.rush_offense_epa_per_game_strength),
            # Targets
            "home_win": game.home_score > game.away_score,
            "total_game_points": game.home_score + game.away_score,
            "score_differential": game.home_score - game.away_score,
            # Home expanded metrics
            "home_points_for_per_game": home_profile.points_for_per_game,
            "home_points_allowed_per_game": home_profile.points_allowed_per_game,
            "home_point_differential_per_game": home_profile.point_differential_per_game,
            "home_pass_attempts_per_game": home_profile.pass_attempts_per_game,
            "home_pass_completion_percentage": home_profile.pass_completion_percentage,
            "home_pass_air_yards_per_attempt": home_profile.pass_air_yards_per_attempt,
            "home_pass_yards_after_catch_per_completion": (home_profile.pass_yards_after_catch_per_completion),
            "home_pass_cpoe": home_profile.pass_cpoe,
            "home_pass_epa_per_attempt": home_profile.pass_epa_per_attempt,
            "home_rush_attempts_per_game": home_profile.rush_attempts_per_game,
            "home_rush_epa_per_attempt": home_profile.rush_epa_per_attempt,
            "home_sacks_allowed_per_game": home_profile.sacks_allowed_per_game,
            "home_first_downs_per_game": home_profile.first_downs_per_game,
            "home_third_down_conversion_rate": home_profile.third_down_conversion_rate,
            "home_fourth_down_conversion_rate": home_profile.fourth_down_conversion_rate,
            "home_penalties_per_game": home_profile.penalties_per_game,
            "home_penalty_yards_per_game": home_profile.penalty_yards_per_game,
            "home_offensive_turnovers_per_game": home_profile.offensive_turnovers_per_game,
            "home_defensive_turnovers_forced_per_game": (home_profile.defensive_turnovers_forced_per_game),
            "home_turnover_differential_per_game": (home_profile.turnover_differential_per_game),
            "home_opponent_pass_attempts_per_game": (home_profile.opponent_pass_attempts_per_game),
            "home_opponent_rush_attempts_per_game": (home_profile.opponent_rush_attempts_per_game),
            "home_defensive_sacks_per_game": home_profile.defensive_sacks_per_game,
            "home_defensive_qb_hits_per_game": home_profile.defensive_qb_hits_per_game,
            "home_defensive_tackles_for_loss_per_game": (home_profile.defensive_tackles_for_loss_per_game),
            "home_field_goals_made_per_game": home_profile.field_goals_made_per_game,
            "home_field_goal_percentage": home_profile.field_goal_percentage,
            # Away
            # Away expanded metrics
            "away_points_for_per_game": away_profile.points_for_per_game,
            "away_points_allowed_per_game": away_profile.points_allowed_per_game,
            "away_point_differential_per_game": away_profile.point_differential_per_game,
            "away_pass_attempts_per_game": away_profile.pass_attempts_per_game,
            "away_pass_completion_percentage": away_profile.pass_completion_percentage,
            "away_pass_air_yards_per_attempt": away_profile.pass_air_yards_per_attempt,
            "away_pass_yards_after_catch_per_completion": (away_profile.pass_yards_after_catch_per_completion),
            "away_pass_cpoe": away_profile.pass_cpoe,
            "away_pass_epa_per_attempt": away_profile.pass_epa_per_attempt,
            "away_rush_attempts_per_game": away_profile.rush_attempts_per_game,
            "away_rush_epa_per_attempt": away_profile.rush_epa_per_attempt,
            "away_sacks_allowed_per_game": away_profile.sacks_allowed_per_game,
            "away_first_downs_per_game": away_profile.first_downs_per_game,
            "away_third_down_conversion_rate": away_profile.third_down_conversion_rate,
            "away_fourth_down_conversion_rate": away_profile.fourth_down_conversion_rate,
            "away_penalties_per_game": away_profile.penalties_per_game,
            "away_penalty_yards_per_game": away_profile.penalty_yards_per_game,
            "away_offensive_turnovers_per_game": away_profile.offensive_turnovers_per_game,
            "away_defensive_turnovers_forced_per_game": (away_profile.defensive_turnovers_forced_per_game),
            "away_turnover_differential_per_game": (away_profile.turnover_differential_per_game),
            "away_opponent_pass_attempts_per_game": (away_profile.opponent_pass_attempts_per_game),
            "away_opponent_rush_attempts_per_game": (away_profile.opponent_rush_attempts_per_game),
            "away_defensive_sacks_per_game": away_profile.defensive_sacks_per_game,
            "away_defensive_qb_hits_per_game": away_profile.defensive_qb_hits_per_game,
            "away_defensive_tackles_for_loss_per_game": (away_profile.defensive_tackles_for_loss_per_game),
            "away_field_goals_made_per_game": away_profile.field_goals_made_per_game,
            "away_field_goal_percentage": away_profile.field_goal_percentage,
        }
        return row

    @staticmethod
    def build_dataset(season: Season | None = None, force_rebuild: bool = False) -> list[dict]:
        season_name = season.name if season is not None else "all"
        cache_path = NFLTrainingDataService.CACHE_DIRECTORY / f"nfl_training_dataset_{season_name}.pkl"
        if cache_path.exists() and not force_rebuild:
            with cache_path.open("rb") as file:
                return pickle.load(file)

        games = Game.objects.filter(
            season__league__abbreviation="NFL", home_score__isnull=False, away_score__isnull=False
        )

        if season is not None:
            games = games.filter(season=season)

        games = games.select_related("season", "week", "home_team", "away_team").order_by(
            "season__start_date", "week__number"
        )

        rows = []
        for game in games:
            row = NFLTrainingDataService.build_training_row(game)
            if row is None:
                continue
            rows.append(row)

        NFLTrainingDataService.CACHE_DIRECTORY.mkdir(parents=True, exist_ok=True)
        with cache_path.open("wb") as file:
            pickle.dump(rows, file)

        return rows
