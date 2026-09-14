from django.db import models

from games.models import Game
from teams.models import Team


class Sportsbook(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class SportsbookRegion(models.Model):
    sportsbook = models.ForeignKey(Sportsbook, on_delete=models.CASCADE, related_name="regions")
    country_code = models.CharField(max_length=2)
    fee_rate = models.DecimalField(max_digits=6, decimal_places=5, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sportsbook", "country_code"],
                name="unique_sportsbook_region",
            )
        ]

    def __str__(self):
        return f"{self.sportsbook} ({self.country_code})"


class ExternalGameMapping(models.Model):
    class Provider(models.TextChoices):
        ODDSPAPI = "oddspapi", "OddsPapi"

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="external_mappings")
    provider = models.CharField(max_length=50, choices=Provider.choices)
    external_fixture_id = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_fixture_id"],
                name="unique_external_fixture",
            ),
            models.UniqueConstraint(
                fields=["game", "provider"],
                name="unique_game_provider",
            ),
        ]

    def __str__(self):
        return f"{self.provider}: {self.external_fixture_id}"


class SportsbookFixture(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="sportsbook_fixtures")
    sportsbook_region = models.ForeignKey(SportsbookRegion, on_delete=models.CASCADE, related_name="fixtures")
    external_fixture_id = models.CharField(max_length=255, null=True, blank=True)
    event_url = models.URLField(max_length=500, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["game", "sportsbook_region"],
                name="unique_game_sportsbook_region",
            )
        ]

    def __str__(self):
        return f"{self.game} - {self.sportsbook_region}"


class OddsSnapshot(models.Model):
    class MarketType(models.TextChoices):
        MONEYLINE = "moneyline", "Moneyline"
        SPREAD = "spread", "Spread"
        TOTAL = "total", "Total"

    class Side(models.TextChoices):
        HOME = "home", "Home"
        AWAY = "away", "Away"
        OVER = "over", "Over"
        UNDER = "under", "Under"

    sportsbook_fixture = models.ForeignKey(SportsbookFixture, on_delete=models.CASCADE, related_name="odds_snapshots")
    market_type = models.CharField(max_length=20, choices=MarketType.choices)
    side = models.CharField(max_length=20, choices=Side.choices)
    line = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    decimal_odds = models.DecimalField(max_digits=8, decimal_places=4)
    american_odds = models.IntegerField(null=True, blank=True)
    external_market_id = models.CharField(max_length=100)
    external_outcome_id = models.CharField(max_length=100)
    betslip_url = models.URLField(max_length=1000, null=True, blank=True)
    source_changed_at = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "sportsbook_fixture",
                    "external_market_id",
                    "external_outcome_id",
                    "source_changed_at",
                ],
                name="unique_odds_snapshot",
            ),
        ]
        indexes = [
            models.Index(
                fields=[
                    "sportsbook_fixture",
                    "market_type",
                    "side",
                    "-source_changed_at",
                ],
                name="odds_latest_lookup_idx",
            ),
        ]

    def __str__(self):
        line = f" {self.line}" if self.line is not None else ""
        return f"{self.sportsbook_fixture} {self.market_type} {self.side}{line} @ {self.decimal_odds}"


class ExternalTeamMapping(models.Model):
    class Provider(models.TextChoices):
        ODDSPAPI = "oddspapi", "OddsPapi"

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="external_mappings",
    )
    provider = models.CharField(
        max_length=50,
        choices=Provider.choices,
    )
    external_team_id = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "external_team_id"],
                name="unique_external_team",
            ),
            models.UniqueConstraint(
                fields=["team", "provider"],
                name="unique_team_provider",
            ),
        ]

    def __str__(self):
        return f"{self.provider}: {self.external_team_id} -> {self.team}"
