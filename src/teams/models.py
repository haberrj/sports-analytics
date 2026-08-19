from django.db import models


class League(models.Model):
    name = models.CharField(max_length=20, unique=True)
    abbreviation = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class Conference(models.Model):
    name = models.CharField(max_length=20)
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
    name = models.CharField(max_length=20)
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
    slug = models.CharField(max_length=50, unique=True)
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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "season"],
                name="unique_team_per_season",
            ),
        ]

    def __str__(self):
        return f"{self.team} - {self.season}"
