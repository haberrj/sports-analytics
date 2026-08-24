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
            points_for=Sum("points_for"),
            points_allowed=Sum("points_allowed"),
            passing_yards=Sum("offensive_passing_yards"),
            passing_attempts=Sum("passing_attempts"),
            passing_completions=Sum("passing_completions"),
            passing_epa=Sum("passing_epa"),
            average_cpoe=Avg("passing_cpoe"),
            passing_air_yards=Sum("passing_air_yards"),
            passing_yards_after_catch=Sum("passing_yards_after_catch"),
            rushing_yards=Sum("offensive_rushing_yards"),
            rushing_attempts=Sum("rushing_attempts"),
            rushing_epa=Sum("rushing_epa"),
            sacks_allowed=Sum("sacks_allowed"),
            first_downs=Sum("first_downs"),
            third_down_attempts=Sum("third_down_attempts"),
            third_down_conversions=Sum("third_down_conversions"),
            fourth_down_attempts=Sum("fourth_down_attempts"),
            fourth_down_conversions=Sum("fourth_down_conversions"),
            penalties=Sum("penalties"),
            penalty_yards=Sum("penalty_yards"),
            offensive_turnovers=Sum("offensive_turnovers"),
            defensive_sacks=Sum("defensive_sacks"),
            passing_yards_allowed=Sum("defensive_passing_yards_allowed"),
            opponent_passing_attempts=Sum("opponent_passing_attempts"),
            rushing_yards_allowed=Sum("defensive_rushing_yards_allowed"),
            opponent_rushing_attempts=Sum("opponent_rushing_attempts"),
            defensive_turnovers_forced=Sum("defensive_turnovers_forced"),
            defensive_qb_hits=Sum("defensive_qb_hits"),
            defensive_tackles_for_loss=Sum("defensive_tackles_for_loss"),
            field_goals_made=Sum("field_goals_made"),
            field_goals_attempted=Sum("field_goals_attempted"),
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
            # Scoring
            "points_for_per_game": NFLDerivedStatsService._safe_divide(aggregate["points_for"], team_games),
            "points_allowed_per_game": NFLDerivedStatsService._safe_divide(aggregate["points_allowed"], team_games),
            "point_differential_per_game": NFLDerivedStatsService._safe_divide(
                (
                    aggregate["points_for"] - aggregate["points_allowed"]
                    if aggregate["points_for"] is not None and aggregate["points_allowed"] is not None
                    else None
                ),
                team_games,
            ),
            # Passing detail
            "pass_attempts_per_game": NFLDerivedStatsService._safe_divide(aggregate["passing_attempts"], team_games),
            "pass_completion_percentage": NFLDerivedStatsService._safe_divide(
                aggregate["passing_completions"],
                aggregate["passing_attempts"],
            ),
            "pass_air_yards_per_attempt": NFLDerivedStatsService._safe_divide(
                aggregate["passing_air_yards"],
                aggregate["passing_attempts"],
            ),
            "pass_yards_after_catch_per_completion": NFLDerivedStatsService._safe_divide(
                aggregate["passing_yards_after_catch"],
                aggregate["passing_completions"],
            ),
            "pass_cpoe": aggregate["average_cpoe"],
            "pass_epa_per_attempt": NFLDerivedStatsService._safe_divide(
                aggregate["passing_epa"],
                aggregate["passing_attempts"],
            ),
            # Rushing detail
            "rush_attempts_per_game": NFLDerivedStatsService._safe_divide(aggregate["rushing_attempts"], team_games),
            "rush_epa_per_attempt": NFLDerivedStatsService._safe_divide(
                aggregate["rushing_epa"],
                aggregate["rushing_attempts"],
            ),
            # Protection
            "sacks_allowed_per_game": NFLDerivedStatsService._safe_divide(aggregate["sacks_allowed"], team_games),
            # Downs
            "first_downs_per_game": NFLDerivedStatsService._safe_divide(aggregate["first_downs"], team_games),
            "third_down_conversion_rate": NFLDerivedStatsService._safe_divide(
                aggregate["third_down_conversions"],
                aggregate["third_down_attempts"],
            ),
            "fourth_down_conversion_rate": NFLDerivedStatsService._safe_divide(
                aggregate["fourth_down_conversions"],
                aggregate["fourth_down_attempts"],
            ),
            # Discipline
            "penalties_per_game": NFLDerivedStatsService._safe_divide(aggregate["penalties"], team_games),
            "penalty_yards_per_game": NFLDerivedStatsService._safe_divide(aggregate["penalty_yards"], team_games),
            # Turnovers
            "offensive_turnovers_per_game": NFLDerivedStatsService._safe_divide(
                aggregate["offensive_turnovers"], team_games
            ),
            "defensive_turnovers_forced_per_game": NFLDerivedStatsService._safe_divide(
                aggregate["defensive_turnovers_forced"], team_games
            ),
            "turnover_differential_per_game": NFLDerivedStatsService._safe_divide(
                (
                    aggregate["defensive_turnovers_forced"] - aggregate["offensive_turnovers"]
                    if aggregate["defensive_turnovers_forced"] is not None
                    and aggregate["offensive_turnovers"] is not None
                    else None
                ),
                team_games,
            ),
            # Defensive volume / pressure
            "opponent_pass_attempts_per_game": NFLDerivedStatsService._safe_divide(
                aggregate["opponent_passing_attempts"], team_games
            ),
            "opponent_rush_attempts_per_game": NFLDerivedStatsService._safe_divide(
                aggregate["opponent_rushing_attempts"], team_games
            ),
            "defensive_sacks_per_game": NFLDerivedStatsService._safe_divide(aggregate["defensive_sacks"], team_games),
            "defensive_qb_hits_per_game": NFLDerivedStatsService._safe_divide(
                aggregate["defensive_qb_hits"], team_games
            ),
            "defensive_tackles_for_loss_per_game": NFLDerivedStatsService._safe_divide(
                aggregate["defensive_tackles_for_loss"], team_games
            ),
            # Special teams
            "field_goals_made_per_game": NFLDerivedStatsService._safe_divide(aggregate["field_goals_made"], team_games),
            "field_goal_percentage": NFLDerivedStatsService._safe_divide(
                aggregate["field_goals_made"],
                aggregate["field_goals_attempted"],
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
                # Scoring
                "points_for_per_game": metrics["points_for_per_game"],
                "points_allowed_per_game": metrics["points_allowed_per_game"],
                "point_differential_per_game": metrics["point_differential_per_game"],
                # Passing detail
                "pass_attempts_per_game": metrics["pass_attempts_per_game"],
                "pass_completion_percentage": metrics["pass_completion_percentage"],
                "pass_air_yards_per_attempt": metrics["pass_air_yards_per_attempt"],
                "pass_yards_after_catch_per_completion": metrics["pass_yards_after_catch_per_completion"],
                "pass_cpoe": metrics["pass_cpoe"],
                "pass_epa_per_attempt": metrics["pass_epa_per_attempt"],
                # Rushing detail
                "rush_attempts_per_game": metrics["rush_attempts_per_game"],
                "rush_epa_per_attempt": metrics["rush_epa_per_attempt"],
                # Protection
                "sacks_allowed_per_game": metrics["sacks_allowed_per_game"],
                # Downs
                "first_downs_per_game": metrics["first_downs_per_game"],
                "third_down_conversion_rate": metrics["third_down_conversion_rate"],
                "fourth_down_conversion_rate": metrics["fourth_down_conversion_rate"],
                # Discipline
                "penalties_per_game": metrics["penalties_per_game"],
                "penalty_yards_per_game": metrics["penalty_yards_per_game"],
                # Turnovers
                "offensive_turnovers_per_game": metrics["offensive_turnovers_per_game"],
                "defensive_turnovers_forced_per_game": metrics["defensive_turnovers_forced_per_game"],
                "turnover_differential_per_game": metrics["turnover_differential_per_game"],
                # Defensive volume / pressure
                "opponent_pass_attempts_per_game": metrics["opponent_pass_attempts_per_game"],
                "opponent_rush_attempts_per_game": metrics["opponent_rush_attempts_per_game"],
                "defensive_sacks_per_game": metrics["defensive_sacks_per_game"],
                "defensive_qb_hits_per_game": metrics["defensive_qb_hits_per_game"],
                "defensive_tackles_for_loss_per_game": metrics["defensive_tackles_for_loss_per_game"],
                # Special teams
                "field_goals_made_per_game": metrics["field_goals_made_per_game"],
                "field_goal_percentage": metrics["field_goal_percentage"],
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
