from django.db import models

from games.models import Season
from teams.models import League


class IngestionState(models.Model):
    class Dataset(models.TextChoices):
        TEAMS = "teams", "Teams"
        GAMES = "games", "Games"
        TEAM_STATS = "team_stats", "Team Stats"

    league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
        related_name="ingestion_states",
    )
    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
        related_name="ingestion_states",
    )
    dataset = models.CharField(
        max_length=50,
        choices=Dataset.choices,
    )

    last_completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["league", "season", "dataset"],
                name="unique_ingestion_state",
            ),
        ]

    def __str__(self):
        return f"{self.league.abbreviation} {self.season.name} - {self.dataset}"
