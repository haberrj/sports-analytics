from datetime import UTC, date, datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from games.models import Game, Season
from players.models import NFLGamePlayerStatus, NFLPlayer, NFLPlayerGameStats
from teams.models import League, Team, TeamSeason


@pytest.fixture
def nfl():
    return League.objects.create(
        name="National Football League",
        abbreviation="NFL",
    )


@pytest.fixture
def season(nfl):
    return Season.objects.create(
        league=nfl,
        name="2026",
        start_date=date(2026, 9, 1),
        end_date=date(2027, 2, 15),
    )


@pytest.fixture
def bills():
    return Team.objects.create(
        slug="nfl-buf",
        name="Bills",
        abbreviation="BUF",
        city="Buffalo",
    )


@pytest.fixture
def jets():
    return Team.objects.create(
        slug="nfl-nyj",
        name="Jets",
        abbreviation="NYJ",
        city="New York",
    )


@pytest.fixture
def leafs():
    return Team.objects.create(
        slug="nhl-tor",
        name="Maple Leafs",
        abbreviation="TOR",
        city="Toronto",
    )


@pytest.fixture
def game(season, bills, jets):
    TeamSeason.objects.create(
        team=bills,
        season=season,
    )
    TeamSeason.objects.create(
        team=jets,
        season=season,
    )

    return Game.objects.create(
        season=season,
        home_team=bills,
        away_team=jets,
        start_time=datetime(
            2026,
            9,
            10,
            20,
            0,
            tzinfo=UTC,
        ),
    )


@pytest.fixture
def quarterback():
    return NFLPlayer.objects.create(
        external_id="00-0034857",
        first_name="Josh",
        last_name="Allen",
        position=NFLPlayer.Positions.QB,
    )


@pytest.mark.django_db
def test_player_game_stats_accept_team_in_game_season(
    game,
    bills,
    quarterback,
):
    stats = NFLPlayerGameStats(
        game=game,
        player=quarterback,
        team=bills,
        passing_attempts=30,
        passing_completions=20,
        passing_yards=250,
    )

    stats.full_clean()


@pytest.mark.django_db
def test_player_game_stats_reject_team_not_in_game_season(
    game,
    leafs,
    quarterback,
):
    stats = NFLPlayerGameStats(
        game=game,
        player=quarterback,
        team=leafs,
    )

    with pytest.raises(
        ValidationError,
        match="Team does not belong to this game's season",
    ):
        stats.full_clean()


@pytest.mark.django_db
def test_player_game_stats_must_be_unique_per_player_and_game(
    game,
    bills,
    quarterback,
):
    NFLPlayerGameStats.objects.create(
        game=game,
        player=quarterback,
        team=bills,
    )

    with pytest.raises(IntegrityError):
        NFLPlayerGameStats.objects.create(
            game=game,
            player=quarterback,
            team=bills,
        )


@pytest.mark.django_db
def test_player_status_accepts_team_in_game_season(
    game,
    bills,
    quarterback,
):
    status = NFLGamePlayerStatus(
        game=game,
        player=quarterback,
        team=bills,
        status=NFLGamePlayerStatus.Status.ACTIVE,
        expected_to_start=True,
        captured_at=datetime(
            2026,
            9,
            9,
            12,
            0,
            tzinfo=UTC,
        ),
    )

    status.full_clean()


@pytest.mark.django_db
def test_player_status_rejects_team_not_in_game_season(
    game,
    leafs,
    quarterback,
):
    status = NFLGamePlayerStatus(
        game=game,
        player=quarterback,
        team=leafs,
        status=NFLGamePlayerStatus.Status.OUT,
        captured_at=datetime(
            2026,
            9,
            9,
            12,
            0,
            tzinfo=UTC,
        ),
    )

    with pytest.raises(
        ValidationError,
        match="Team does not belong to this game's season",
    ):
        status.full_clean()


@pytest.mark.django_db
def test_player_can_have_multiple_status_snapshots(
    game,
    bills,
    quarterback,
):
    captured_at = datetime(
        2026,
        9,
        8,
        12,
        0,
        tzinfo=UTC,
    )

    NFLGamePlayerStatus.objects.create(
        game=game,
        player=quarterback,
        team=bills,
        status=NFLGamePlayerStatus.Status.QUESTIONABLE,
        captured_at=captured_at,
    )

    NFLGamePlayerStatus.objects.create(
        game=game,
        player=quarterback,
        team=bills,
        status=NFLGamePlayerStatus.Status.ACTIVE,
        captured_at=captured_at + timedelta(days=1),
    )

    assert (
        NFLGamePlayerStatus.objects.filter(
            game=game,
            player=quarterback,
        ).count()
        == 2
    )


@pytest.mark.django_db
def test_duplicate_player_status_snapshot_is_rejected(
    game,
    bills,
    quarterback,
):
    captured_at = datetime(
        2026,
        9,
        9,
        12,
        0,
        tzinfo=UTC,
    )

    NFLGamePlayerStatus.objects.create(
        game=game,
        player=quarterback,
        team=bills,
        status=NFLGamePlayerStatus.Status.QUESTIONABLE,
        captured_at=captured_at,
    )

    with pytest.raises(IntegrityError):
        NFLGamePlayerStatus.objects.create(
            game=game,
            player=quarterback,
            team=bills,
            status=NFLGamePlayerStatus.Status.OUT,
            captured_at=captured_at,
        )


@pytest.fixture
def chiefs():
    return Team.objects.create(
        slug="nfl-kc",
        name="Chiefs",
        abbreviation="KC",
        city="Kansas City",
    )


@pytest.mark.django_db
def test_player_game_stats_reject_team_not_participating_in_game(
    game,
    season,
    chiefs,
    quarterback,
):
    TeamSeason.objects.create(
        team=chiefs,
        season=season,
    )

    stats = NFLPlayerGameStats(
        game=game,
        player=quarterback,
        team=chiefs,
    )

    with pytest.raises(
        ValidationError,
        match="Team is not participating in this game",
    ):
        stats.full_clean()


@pytest.mark.django_db
def test_player_status_rejects_team_not_participating_in_game(
    game,
    season,
    chiefs,
    quarterback,
):
    TeamSeason.objects.create(
        team=chiefs,
        season=season,
    )

    status = NFLGamePlayerStatus(
        game=game,
        player=quarterback,
        team=chiefs,
        status=NFLGamePlayerStatus.Status.ACTIVE,
        captured_at=datetime(
            2026,
            9,
            9,
            12,
            0,
            tzinfo=UTC,
        ),
    )

    with pytest.raises(
        ValidationError,
        match="Team is not participating in this game",
    ):
        status.full_clean()
