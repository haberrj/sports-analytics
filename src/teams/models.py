from django.core.exceptions import ValidationError
from django.db import models


class League(models.Model):
    name = models.CharField(max_length=100, unique=True)
    abbreviation = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class Conference(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=10)
    league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
        related_name="conferences",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["league", "name"],
                name="unique_conference_per_league",
            ),
            models.UniqueConstraint(
                fields=["league", "abbreviation"],
                name="unique_conference_abbrev_per_league",
            ),
        ]

    def __str__(self):
        return f"{self.league.abbreviation} {self.name}"


class Division(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=10)
    conference = models.ForeignKey(
        Conference,
        on_delete=models.CASCADE,
        related_name="divisions",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conference", "name"],
                name="unique_division_per_conference",
            ),
            models.UniqueConstraint(
                fields=["conference", "abbreviation"],
                name="unique_division_abbrev_per_conference",
            ),
        ]

    def __str__(self):
        return f"{self.conference.abbreviation} {self.name}"


class Team(models.Model):
    external_id = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.city} {self.name}"


class TeamSeason(models.Model):
    """
    Represents a team's league structure for a specific season.

    Conference and division membership can change between seasons,
    so these relationships are stored here rather than directly on Team.
    Conference and division are optional because not all leagues use them.
    """

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="season_memberships",
    )
    season = models.ForeignKey(
        "games.Season",
        on_delete=models.CASCADE,
        related_name="team_memberships",
    )
    conference = models.ForeignKey(
        Conference,
        on_delete=models.PROTECT,
        related_name="team_seasons",
        null=True,
        blank=True,
    )
    division = models.ForeignKey(
        Division,
        on_delete=models.PROTECT,
        related_name="team_seasons",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=10)
    city = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "season"],
                name="unique_team_per_season",
            ),
        ]

    def __str__(self):
        return f"{self.team} - {self.season}"

    def clean(self):
        super().clean()

        if not self.season_id:
            return

        if self.conference_id and self.conference.league_id != self.season.league_id:
            raise ValidationError({"conference": ("Conference does not belong to the same league as this season.")})

        if self.division_id:
            if not self.conference_id:
                raise ValidationError({"division": ("A division cannot be assigned without a conference.")})

            if self.division.conference_id != self.conference_id:
                raise ValidationError({"division": ("Division does not belong to the selected conference.")})
