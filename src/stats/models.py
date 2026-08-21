from django.core.exceptions import ValidationError
from django.db import models

from games.models import Game, Season, Week
from teams.models import Team, TeamSeason


# Create your models here.
class NFLTeamGameStats(models.Model):
    """
    Stores raw team-level statistics for a single NFL game.

    Each game has one record per participating team. The model stores
    observed game statistics rather than calculated or rolling metrics.

    Derived metrics such as yards per attempt, completion percentage,
    turnover differential, rolling averages, and opponent-adjusted
    statistics should be calculated from these records rather than
    persisted here.

    Offensive fields describe statistics produced by the team, while
    defensive fields describe statistics allowed or produced by the
    team's defense.
    """

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="nfl_team_stats")
    team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="nfl_game_stats")
    points_for = models.PositiveSmallIntegerField(null=True, blank=True)
    points_allowed = models.PositiveSmallIntegerField(null=True, blank=True)
    # Offense
    offensive_passing_yards = models.IntegerField(null=True, blank=True)
    passing_attempts = models.PositiveSmallIntegerField(null=True, blank=True)
    passing_completions = models.PositiveSmallIntegerField(null=True, blank=True)
    passing_epa = models.FloatField(null=True, blank=True)
    passing_cpoe = models.FloatField(null=True, blank=True)
    passing_air_yards = models.IntegerField(null=True, blank=True)
    passing_yards_after_catch = models.IntegerField(null=True, blank=True)

    offensive_rushing_yards = models.IntegerField(null=True, blank=True)
    rushing_attempts = models.PositiveSmallIntegerField(null=True, blank=True)
    rushing_epa = models.FloatField(null=True, blank=True)

    sacks_allowed = models.PositiveSmallIntegerField(null=True, blank=True)
    # Downs are interpreted from data and a direct raw value isn't given by nflreadpy
    first_downs = models.PositiveSmallIntegerField(null=True, blank=True)

    third_down_attempts = models.PositiveSmallIntegerField(null=True, blank=True)
    third_down_conversions = models.PositiveSmallIntegerField(null=True, blank=True)

    fourth_down_attempts = models.PositiveSmallIntegerField(null=True, blank=True)
    fourth_down_conversions = models.PositiveSmallIntegerField(null=True, blank=True)

    penalties = models.PositiveSmallIntegerField(null=True, blank=True)
    penalty_yards = models.PositiveSmallIntegerField(null=True, blank=True)

    offensive_turnovers = models.PositiveSmallIntegerField(null=True, blank=True)
    # Defense
    defensive_sacks = models.FloatField(null=True, blank=True)

    defensive_passing_yards_allowed = models.IntegerField(null=True, blank=True)
    opponent_passing_attempts = models.PositiveSmallIntegerField(null=True, blank=True)

    defensive_rushing_yards_allowed = models.IntegerField(null=True, blank=True)
    opponent_rushing_attempts = models.PositiveSmallIntegerField(null=True, blank=True)

    defensive_turnovers_forced = models.PositiveSmallIntegerField(null=True, blank=True)
    defensive_qb_hits = models.PositiveSmallIntegerField(null=True, blank=True)
    defensive_tackles_for_loss = models.PositiveSmallIntegerField(null=True, blank=True)
    # Special Teams
    field_goals_made = models.PositiveSmallIntegerField(null=True, blank=True)
    field_goals_attempted = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["game", "team"],
                name="unique_nfl_team_stats_per_game",
            )
        ]

    def __str__(self):
        return f"{self.team} - {self.game}"


class NFLTeamProfile(models.Model):
    class TeamType(models.TextChoices):
        PASS = "pass", "Pass"
        RUSH = "rush", "Rush"
        BALANCED = "balanced", "Balanced"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="nfl_profiles")
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="nfl_team_profiles")
    through_week = models.ForeignKey(Week, on_delete=models.CASCADE, related_name="nfl_team_profiles")

    # Offensive efficiency
    pass_offense_yards_per_attempt = models.FloatField(null=True, blank=True)
    rush_offense_yards_per_attempt = models.FloatField(null=True, blank=True)

    # Defensive efficiency
    pass_defense_yards_per_attempt = models.FloatField(null=True, blank=True)
    rush_defense_yards_per_attempt = models.FloatField(null=True, blank=True)

    # Offensive volume
    pass_offense_yards_per_game = models.FloatField(null=True, blank=True)
    rush_offense_yards_per_game = models.FloatField(null=True, blank=True)

    # Defensive volume
    pass_defense_yards_per_game = models.FloatField(null=True, blank=True)
    rush_defense_yards_per_game = models.FloatField(null=True, blank=True)

    # Offensive value
    pass_offense_epa_per_game = models.FloatField(null=True, blank=True)
    rush_offense_epa_per_game = models.FloatField(null=True, blank=True)

    # League relative strengths
    pass_offense_strength = models.FloatField(null=True, blank=True)
    rush_offense_strength = models.FloatField(null=True, blank=True)
    pass_defense_strength = models.FloatField(null=True, blank=True)
    rush_defense_strength = models.FloatField(null=True, blank=True)

    offense_type = models.CharField(max_length=20, choices=TeamType.choices, null=True, blank=True)
    defense_type = models.CharField(max_length=20, choices=TeamType.choices, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "season", "through_week"],
                name="unique_nfl_team_profile_per_week",
            ),
        ]

    def __str__(self):
        return f"{self.team} - {self.season.name} through week {self.through_week.number}"

    def clean(self):
        super().clean()

        if self.through_week_id and self.season_id and self.through_week.season_id != self.season_id:
            raise ValidationError({"through_week": ("Through week does not belong to this season.")})
        if (
            self.team_id
            and self.season_id
            and not TeamSeason.objects.filter(
                team_id=self.team_id,
                season_id=self.season_id,
            ).exists()
        ):
            raise ValidationError({"team": "Team does not belong to this season."})
