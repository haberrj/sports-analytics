from datetime import UTC, date, datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from games.models import Game, Season, Week
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
def nfl_teams(season, bills, jets):
    TeamSeason.objects.create(
        team=bills,
        season=season,
    )
    TeamSeason.objects.create(
        team=jets,
        season=season,
    )

    return bills, jets


@pytest.mark.django_db
def test_game_accepts_teams_in_season(season, nfl_teams):
    bills, jets = nfl_teams

    game = Game(
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

    game.full_clean()


@pytest.mark.django_db
def test_game_rejects_home_team_not_in_season(
    season,
    jets,
    leafs,
):
    TeamSeason.objects.create(
        team=jets,
        season=season,
    )

    game = Game(
        season=season,
        home_team=leafs,
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

    with pytest.raises(
        ValidationError,
        match="Home team does not belong to this season",
    ):
        game.full_clean()


@pytest.mark.django_db
def test_game_rejects_away_team_not_in_season(
    season,
    bills,
    leafs,
):
    TeamSeason.objects.create(
        team=bills,
        season=season,
    )

    game = Game(
        season=season,
        home_team=bills,
        away_team=leafs,
        start_time=datetime(
            2026,
            9,
            10,
            20,
            0,
            tzinfo=UTC,
        ),
    )

    with pytest.raises(
        ValidationError,
        match="Away team does not belong to this season",
    ):
        game.full_clean()


@pytest.mark.django_db
def test_game_rejects_same_home_and_away_team(
    season,
    bills,
):
    TeamSeason.objects.create(
        team=bills,
        season=season,
    )

    with pytest.raises(IntegrityError):
        Game.objects.create(
            season=season,
            home_team=bills,
            away_team=bills,
            start_time=datetime(
                2026,
                9,
                10,
                20,
                0,
                tzinfo=UTC,
            ),
        )


@pytest.mark.django_db
def test_week_must_be_unique_per_season(season):
    Week.objects.create(
        season=season,
        number=1,
    )

    with pytest.raises(IntegrityError):
        Week.objects.create(
            season=season,
            number=1,
        )


@pytest.mark.django_db
def test_game_rejects_week_from_different_season(
    nfl,
    season,
    nfl_teams,
):
    bills, jets = nfl_teams

    other_season = Season.objects.create(
        league=nfl,
        name="2025",
        start_date=date(2025, 9, 1),
        end_date=date(2026, 2, 15),
    )

    wrong_week = Week.objects.create(
        season=other_season,
        number=1,
    )

    game = Game(
        season=season,
        week=wrong_week,
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

    with pytest.raises(
        ValidationError,
        match="Week does not belong to this season",
    ):
        game.full_clean()
