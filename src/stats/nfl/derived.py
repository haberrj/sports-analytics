from django.db.models import Avg, Count, QuerySet, Sum

from games.models import Week
from stats.models import NFLTeamGameStats, NFLTeamProfile
from teams.models import Team


class NFLDerivedStatsService:
    @staticmethod
    def get_team_stats_through_week(team: Team, week: Week) -> QuerySet[NFLTeamGameStats]:
        return NFLTeamGameStats.objects.filter(
            team=team,
            game__season=week.season,
            game__week__number__lte=week.number,
        )

    @staticmethod
    def get_team_aggregate_through_week(team: Team, week: Week) -> dict:
        stats = NFLDerivedStatsService.get_team_stats_through_week(
            team=team,
            week=week,
        )
        return NFLDerivedStatsService._aggregate_stats(stats)

    @staticmethod
    def get_league_aggregate_through_week(week: Week) -> dict:
        stats = NFLDerivedStatsService.get_league_stats_through_week(week)
        return NFLDerivedStatsService._aggregate_stats(stats)

    @staticmethod
    def _safe_divide(numerator: int | float | None, denominator: int | float | None) -> float | None:
        if numerator is None or denominator in (None, 0):
            return None
        return numerator / denominator

    @staticmethod
    def get_team_metrics_through_week(team: Team, week: Week) -> dict[str, float | None]:
        aggregate = NFLDerivedStatsService.get_team_aggregate_through_week(team=team, week=week)
        return NFLDerivedStatsService._get_metrics_from_aggregate(aggregate)

    @staticmethod
    def get_league_stats_through_week(week: Week) -> QuerySet[NFLTeamGameStats]:
        return NFLTeamGameStats.objects.filter(
            game__season=week.season,
            game__week__number__lte=week.number,
        )

    @staticmethod
    def get_league_metrics_through_week(week: Week) -> dict[str, float | None]:
        aggregate = NFLDerivedStatsService.get_league_aggregate_through_week(week)
        return NFLDerivedStatsService._get_metrics_from_aggregate(aggregate)

    @staticmethod
    def get_team_relative_metrics_through_week(team: Team, week: Week) -> dict[str, float | None]:
        team_metrics = NFLDerivedStatsService.get_team_metrics_through_week(
            team=team,
            week=week,
        )
        league_metrics = NFLDerivedStatsService.get_league_metrics_through_week(
            week=week,
        )

        return {
            # Passing offense
            "pass_offense_yards_per_attempt_strength": NFLDerivedStatsService._relative_offensive_strength(
                team_metrics["pass_offense_yards_per_attempt"],
                league_metrics["pass_offense_yards_per_attempt"],
            ),
            "pass_offense_yards_per_game_strength": NFLDerivedStatsService._relative_offensive_strength(
                team_metrics["pass_offense_yards_per_game"],
                league_metrics["pass_offense_yards_per_game"],
            ),
            "pass_offense_epa_per_game_strength": NFLDerivedStatsService._relative_value(
                team_metrics["pass_offense_epa_per_game"],
                league_metrics["pass_offense_epa_per_game"],
            ),
            # Rushing offense
            "rush_offense_yards_per_attempt_strength": NFLDerivedStatsService._relative_offensive_strength(
                team_metrics["rush_offense_yards_per_attempt"],
                league_metrics["rush_offense_yards_per_attempt"],
            ),
            "rush_offense_yards_per_game_strength": NFLDerivedStatsService._relative_offensive_strength(
                team_metrics["rush_offense_yards_per_game"],
                league_metrics["rush_offense_yards_per_game"],
            ),
            "rush_offense_epa_per_game_strength": NFLDerivedStatsService._relative_value(
                team_metrics["rush_offense_epa_per_game"],
                league_metrics["rush_offense_epa_per_game"],
            ),
            # Passing defense
            "pass_defense_yards_per_attempt_strength": NFLDerivedStatsService._relative_defensive_strength(
                team_metrics["pass_defense_yards_per_attempt"],
                league_metrics["pass_defense_yards_per_attempt"],
            ),
            "pass_defense_yards_per_game_strength": NFLDerivedStatsService._relative_defensive_strength(
                team_metrics["pass_defense_yards_per_game"],
                league_metrics["pass_defense_yards_per_game"],
            ),
            # Rushing defense
            "rush_defense_yards_per_attempt_strength": NFLDerivedStatsService._relative_defensive_strength(
                team_metrics["rush_defense_yards_per_attempt"],
                league_metrics["rush_defense_yards_per_attempt"],
            ),
            "rush_defense_yards_per_game_strength": NFLDerivedStatsService._relative_defensive_strength(
                team_metrics["rush_defense_yards_per_game"],
                league_metrics["rush_defense_yards_per_game"],
            ),
        }

    @staticmethod
    def _relative_value(team_value: float | None, league_value: float | None) -> float | None:
        if team_value is None or league_value is None:
            return None

        return team_value - league_value

    @staticmethod
    def _relative_offensive_strength(team_value: float | None, league_value: float | None) -> float | None:
        strength = NFLDerivedStatsService._safe_divide(team_value, league_value)
        if strength is None:
            return None
        return strength - 1

    @staticmethod
    def _relative_defensive_strength(team_value: float | None, league_value: float | None) -> float | None:
        strength = NFLDerivedStatsService._safe_divide(team_value, league_value)
        if strength is None:
            return None
        return 1 - strength

    @staticmethod
    def _aggregate_stats(stats: QuerySet[NFLTeamGameStats]) -> dict:
        return stats.aggregate(
            team_games=Count("id"),
            passing_yards=Sum("offensive_passing_yards"),
            passing_attempts=Sum("passing_attempts"),
            passing_completions=Sum("passing_completions"),
            rushing_yards=Sum("offensive_rushing_yards"),
            rushing_attempts=Sum("rushing_attempts"),
            passing_epa=Sum("passing_epa"),
            rushing_epa=Sum("rushing_epa"),
            passing_yards_allowed=Sum("defensive_passing_yards_allowed"),
            rushing_yards_allowed=Sum("defensive_rushing_yards_allowed"),
            opponent_passing_attempts=Sum("opponent_passing_attempts"),
            opponent_rushing_attempts=Sum("opponent_rushing_attempts"),
            points_for=Sum("points_for"),
            points_allowed=Sum("points_allowed"),
            sacks_allowed=Sum("sacks_allowed"),
            defensive_sacks=Sum("defensive_sacks"),
            defensive_qb_hits=Sum("defensive_qb_hits"),
            offensive_turnovers=Sum("offensive_turnovers"),
            defensive_turnovers_forced=Sum("defensive_turnovers_forced"),
            average_cpoe=Avg("passing_cpoe"),
        )

    @staticmethod
    def _get_metrics_from_aggregate(aggregate: dict) -> dict[str, float | None]:
        team_games = aggregate["team_games"]
        return {
            # Efficiency
            "pass_offense_yards_per_attempt": NFLDerivedStatsService._safe_divide(
                aggregate["passing_yards"],
                aggregate["passing_attempts"],
            ),
            "rush_offense_yards_per_attempt": NFLDerivedStatsService._safe_divide(
                aggregate["rushing_yards"], aggregate["rushing_attempts"]
            ),
            "pass_defense_yards_per_attempt": NFLDerivedStatsService._safe_divide(
                aggregate["passing_yards_allowed"],
                aggregate["opponent_passing_attempts"],
            ),
            "rush_defense_yards_per_attempt": NFLDerivedStatsService._safe_divide(
                aggregate["rushing_yards_allowed"],
                aggregate["opponent_rushing_attempts"],
            ),
            # Volume
            "pass_offense_yards_per_game": NFLDerivedStatsService._safe_divide(
                aggregate["passing_yards"],
                team_games,
            ),
            "rush_offense_yards_per_game": NFLDerivedStatsService._safe_divide(
                aggregate["rushing_yards"],
                team_games,
            ),
            "pass_defense_yards_per_game": NFLDerivedStatsService._safe_divide(
                aggregate["passing_yards_allowed"],
                team_games,
            ),
            "rush_defense_yards_per_game": NFLDerivedStatsService._safe_divide(
                aggregate["rushing_yards_allowed"],
                team_games,
            ),
            # Value
            "pass_offense_epa_per_game": NFLDerivedStatsService._safe_divide(
                aggregate["passing_epa"],
                team_games,
            ),
            "rush_offense_epa_per_game": NFLDerivedStatsService._safe_divide(
                aggregate["rushing_epa"],
                team_games,
            ),
        }

    @staticmethod
    def update_team_profile_through_week(team: Team, week: Week) -> NFLTeamProfile:
        metrics = NFLDerivedStatsService.get_team_metrics_through_week(
            team=team,
            week=week,
        )

        relative_metrics = NFLDerivedStatsService.get_team_relative_metrics_through_week(
            team=team,
            week=week,
        )

        profile, _ = NFLTeamProfile.objects.update_or_create(
            team=team,
            season=week.season,
            through_week=week,
            defaults={
                # Absolute metrics
                "pass_offense_yards_per_attempt": metrics["pass_offense_yards_per_attempt"],
                "rush_offense_yards_per_attempt": metrics["rush_offense_yards_per_attempt"],
                "pass_defense_yards_per_attempt": metrics["pass_defense_yards_per_attempt"],
                "rush_defense_yards_per_attempt": metrics["rush_defense_yards_per_attempt"],
                "pass_offense_yards_per_game": metrics["pass_offense_yards_per_game"],
                "rush_offense_yards_per_game": metrics["rush_offense_yards_per_game"],
                "pass_defense_yards_per_game": metrics["pass_defense_yards_per_game"],
                "rush_defense_yards_per_game": metrics["rush_defense_yards_per_game"],
                "pass_offense_epa_per_game": metrics["pass_offense_epa_per_game"],
                "rush_offense_epa_per_game": metrics["rush_offense_epa_per_game"],
                # League-relative metrics
                "pass_offense_yards_per_attempt_strength": relative_metrics["pass_offense_yards_per_attempt_strength"],
                "pass_offense_yards_per_game_strength": relative_metrics["pass_offense_yards_per_game_strength"],
                "pass_offense_epa_per_game_strength": relative_metrics["pass_offense_epa_per_game_strength"],
                "rush_offense_yards_per_attempt_strength": relative_metrics["rush_offense_yards_per_attempt_strength"],
                "rush_offense_yards_per_game_strength": relative_metrics["rush_offense_yards_per_game_strength"],
                "rush_offense_epa_per_game_strength": relative_metrics["rush_offense_epa_per_game_strength"],
                "pass_defense_yards_per_attempt_strength": relative_metrics["pass_defense_yards_per_attempt_strength"],
                "pass_defense_yards_per_game_strength": relative_metrics["pass_defense_yards_per_game_strength"],
                "rush_defense_yards_per_attempt_strength": relative_metrics["rush_defense_yards_per_attempt_strength"],
                "rush_defense_yards_per_game_strength": relative_metrics["rush_defense_yards_per_game_strength"],
            },
        )

        return profile

    @staticmethod
    def update_profiles_through_week(week: Week) -> list[NFLTeamProfile]:
        team_ids = (
            NFLTeamGameStats.objects.filter(
                game__season=week.season,
                game__week=week,
            )
            .values_list("team_id", flat=True)
            .distinct()
        )

        profiles = []

        for team in Team.objects.filter(id__in=team_ids):
            profiles.append(
                NFLDerivedStatsService.update_team_profile_through_week(
                    team=team,
                    week=week,
                )
            )

        return profiles
