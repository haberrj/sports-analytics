from django.core.exceptions import ValidationError
from django.db import models

from teams.models import League, Team, TeamSeason


# Create your models here.
class Season(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="seasons")
    name = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["league", "name"], name="unique_season_per_league")]

    def __str__(self):
        return f"{self.league.abbreviation} {self.name}"


class Week(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="weeks")
    number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=50, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["season", "number"], name="unique_week_per_season")]

    def __str__(self):
        return self.name or f"{self.season} Week {self.number}"


class Game(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In Progress"
        SUSPENDED = "suspended", "Suspended"
        FINAL = "final", "Final"
        POSTPONED = "postponed", "Postponed"
        CANCELLED = "cancelled", "Cancelled"

    class FinishType(models.TextChoices):
        REGULATION = "regulation", "Regulation"
        OVERTIME = "overtime", "Overtime"
        SHOOTOUT = "shootout", "Shootout"

    external_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="games")
    week = models.ForeignKey(Week, on_delete=models.SET_NULL, related_name="games", null=True, blank=True)
    home_team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="home_games")
    away_team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="away_games")
    start_time = models.DateTimeField(null=True, blank=True)
    home_score = models.PositiveSmallIntegerField(null=True, blank=True)
    away_score = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    phase = models.CharField(max_length=50, blank=True)
    series_game_number = models.PositiveSmallIntegerField(null=True, blank=True)
    finish_type = models.CharField(max_length=20, choices=FinishType.choices, null=True, blank=True)
    neutral_site = models.BooleanField(default=False)
    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(home_team=models.F("away_team")), name="different_home_and_away"
            ),
        ]

    def __str__(self):
        return f"{self.away_team} @ {self.home_team}"

    def clean(self):
        super().clean()

        if not self.season_id:
            return

        if self.week_id and self.week.season_id != self.season_id:
            raise ValidationError({"week": "Week does not belong to this season."})

        if self.home_team_id and not TeamSeason.objects.filter(team=self.home_team_id, season=self.season).exists():
            raise ValidationError({"home_team": "Home team does not belong to this season"})
        if self.away_team_id and not TeamSeason.objects.filter(team=self.away_team_id, season=self.season).exists():
            raise ValidationError({"away_team": "Away team does not belong to this season"})
