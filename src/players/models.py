from django.core.exceptions import ValidationError
from django.db import models

from games.models import Game
from teams.models import Team, TeamSeason


class NFLPlayer(models.Model):
    """
    Represents an NFL player identity independent of team or season.

    Team membership and availability can change over time, so those
    relationships are stored separately.
    """

    class Positions(models.TextChoices):
        # Offense
        QB = "QB", "Quarterback"
        RB = "RB", "Running Back"
        FB = "FB", "Fullback"
        WR = "WR", "Wide Receiver"
        TE = "TE", "Tight End"

        OL = "OL", "Offensive Line"
        OT = "OT", "Offensive Tackle"
        OG = "OG", "Offensive Guard"
        C = "C", "Center"

        # Defense
        DL = "DL", "Defensive Line"
        DE = "DE", "Defensive End"
        DT = "DT", "Defensive Tackle"
        NT = "NT", "Nose Tackle"

        LB = "LB", "Linebacker"
        ILB = "ILB", "Inside Linebacker"
        OLB = "OLB", "Outside Linebacker"

        DB = "DB", "Defensive Back"
        CB = "CB", "Cornerback"
        S = "S", "Safety"
        FS = "FS", "Free Safety"
        SS = "SS", "Strong Safety"

        # Special Teams
        K = "K", "Kicker"
        P = "P", "Punter"
        LS = "LS", "Long Snapper"

    external_id = models.CharField(max_length=100, unique=True)
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    position = models.CharField(max_length=10, choices=Positions.choices)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class NFLPlayerGameStats(models.Model):
    """
    Stores raw player-level statistics for a single NFL game.

    These records represent observed performance. Derived player-strength
    metrics and rolling features should be calculated elsewhere.
    """

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="nfl_player_stats",
    )
    player = models.ForeignKey(
        NFLPlayer,
        on_delete=models.PROTECT,
        related_name="nfl_game_stats",
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        related_name="nfl_player_game_stats",
    )

    passing_attempts = models.PositiveSmallIntegerField(default=0)
    passing_completions = models.PositiveSmallIntegerField(default=0)
    passing_yards = models.IntegerField(default=0)
    passing_touchdowns = models.PositiveSmallIntegerField(default=0)
    interceptions = models.PositiveSmallIntegerField(default=0)

    rushing_attempts = models.PositiveSmallIntegerField(default=0)
    rushing_yards = models.IntegerField(default=0)
    rushing_touchdowns = models.PositiveSmallIntegerField(default=0)

    targets = models.PositiveSmallIntegerField(default=0)
    receptions = models.PositiveSmallIntegerField(default=0)
    receiving_yards = models.IntegerField(default=0)
    receiving_touchdowns = models.PositiveSmallIntegerField(default=0)

    field_goal_attempts = models.PositiveSmallIntegerField(default=0)
    field_goals_made = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["game", "player"],
                name="unique_nfl_player_stats_per_game",
            ),
        ]

    def clean(self):
        super().clean()

        if not self.game_id or not self.team_id:
            return

        if not TeamSeason.objects.filter(
            team_id=self.team_id,
            season_id=self.game.season_id,
        ).exists():
            raise ValidationError({"team": "Team does not belong to this game's season."})

        if self.team_id not in {
            self.game.home_team_id,
            self.game.away_team_id,
        }:
            raise ValidationError({"team": "Team is not participating in this game."})

    def __str__(self):
        return f"{self.player} - {self.game}"


class NFLGamePlayerStatus(models.Model):
    """
    Stores a player's known availability for a specific NFL game.

    captured_at preserves the point-in-time state so historical models
    can use only information that was available before kickoff.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        QUESTIONABLE = "questionable", "Questionable"
        DOUBTFUL = "doubtful", "Doubtful"
        OUT = "out", "Out"
        IR = "ir", "Injured Reserve"

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="player_statuses",
    )
    player = models.ForeignKey(
        NFLPlayer,
        on_delete=models.PROTECT,
        related_name="game_statuses",
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        related_name="player_game_statuses",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
    )

    expected_to_start = models.BooleanField(default=False)
    captured_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["game", "player", "captured_at"],
                name="unique_nfl_player_status_snapshot",
            ),
        ]

    def clean(self):
        super().clean()

        if not self.game_id or not self.team_id:
            return

        if not TeamSeason.objects.filter(
            team_id=self.team_id,
            season_id=self.game.season_id,
        ).exists():
            raise ValidationError({"team": "Team does not belong to this game's season."})

        if self.team_id not in {
            self.game.home_team_id,
            self.game.away_team_id,
        }:
            raise ValidationError({"team": "Team is not participating in this game."})

    def __str__(self):
        return f"{self.player} - {self.game} - {self.status}"


class NFLPlayerRanking(models.Model):
    """
    Stores a point-in-time, model-generated player ranking.

    Rankings are position-specific and versioned so historical analyses
    can reproduce the player strength values that were known at the time.
    """

    player = models.ForeignKey(
        NFLPlayer,
        on_delete=models.CASCADE,
        related_name="rankings",
    )
    season = models.ForeignKey(
        "games.Season",
        on_delete=models.CASCADE,
        related_name="nfl_player_rankings",
    )

    position = models.CharField(
        max_length=10,
        choices=NFLPlayer.Positions.choices,
    )

    rank = models.PositiveSmallIntegerField()
    score = models.FloatField()

    captured_at = models.DateTimeField()

    model_name = models.CharField(max_length=100)
    model_version = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "player",
                    "season",
                    "captured_at",
                    "model_name",
                    "model_version",
                ],
                name="unique_nfl_player_ranking_snapshot",
            ),
        ]

    def __str__(self):
        return f"{self.player} - {self.position} #{self.rank} ({self.model_name} {self.model_version})"
