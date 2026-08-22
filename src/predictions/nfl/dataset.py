
from games.models import Game, Season
from predictions.base import TrainingDataService
from stats.models import NFLTeamProfile
from teams.models import Team


class NFLTrainingDataService(TrainingDataService[NFLTeamProfile, Game, Team]):
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
        }
