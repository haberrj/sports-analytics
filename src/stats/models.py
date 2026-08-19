from django.db import models

from games.models import Game
from teams.models import Team


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
    points_for = models.PositiveSmallIntegerField(default=0)
    points_allowed = models.PositiveSmallIntegerField(default=0)
    # Offense
    offensive_passing_yards = models.IntegerField(default=0)
    passing_attempts = models.PositiveSmallIntegerField(default=0)
    passing_completions = models.PositiveSmallIntegerField(default=0)

    offensive_rushing_yards = models.IntegerField(default=0)
    rushing_attempts = models.PositiveSmallIntegerField(default=0)

    sacks_allowed = models.PositiveSmallIntegerField(default=0)
    first_downs = models.PositiveSmallIntegerField(default=0)

    third_down_attempts = models.PositiveSmallIntegerField(default=0)
    third_down_conversions = models.PositiveSmallIntegerField(default=0)

    fourth_down_attempts = models.PositiveSmallIntegerField(default=0)
    fourth_down_conversions = models.PositiveSmallIntegerField(default=0)

    penalties = models.PositiveSmallIntegerField(default=0)
    penalty_yards = models.PositiveSmallIntegerField(default=0)

    offensive_turnovers = models.PositiveSmallIntegerField(default=0)
    # Defense
    defensive_sacks = models.PositiveSmallIntegerField(default=0)
    defensive_passing_yards_allowed = models.IntegerField(default=0)
    defensive_rushing_yards_allowed = models.IntegerField(default=0)
    defensive_turnovers_forced = models.PositiveSmallIntegerField(default=0)
    # Special Teams
    field_goals_made = models.PositiveSmallIntegerField(default=0)
    field_goals_attempted = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["game", "team"],
                name="unique_nfl_team_stats_per_game",
            )
        ]

    def __str__(self):
        return f"{self.team} - {self.game}"
