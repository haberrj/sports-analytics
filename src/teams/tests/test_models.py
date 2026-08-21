import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from games.models import Season
from teams.models import Conference, Division, League, Team, TeamSeason


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
        start_date="2026-09-01",
        end_date="2027-02-15",
    )


@pytest.fixture
def bills():
    return Team.objects.create(
        external_id="0610",
        slug="nfl-buf",
        name="Bills",
        abbreviation="BUF",
        city="Buffalo",
    )


@pytest.mark.django_db
def test_conference_name_must_be_unique_per_league(nfl):
    Conference.objects.create(
        league=nfl,
        name="American Football Conference",
        abbreviation="AFC",
    )

    with pytest.raises(IntegrityError):
        Conference.objects.create(
            league=nfl,
            name="American Football Conference",
            abbreviation="OTHER",
        )


@pytest.mark.django_db
def test_conference_abbreviation_must_be_unique_per_league(nfl):
    Conference.objects.create(
        league=nfl,
        name="American Football Conference",
        abbreviation="AFC",
    )

    with pytest.raises(IntegrityError):
        Conference.objects.create(
            league=nfl,
            name="Another Conference",
            abbreviation="AFC",
        )


@pytest.mark.django_db
def test_same_conference_name_can_exist_in_different_leagues(nfl):
    other_league = League.objects.create(
        name="Other Football League",
        abbreviation="OFL",
    )

    Conference.objects.create(
        league=nfl,
        name="Eastern",
        abbreviation="EAST",
    )

    Conference.objects.create(
        league=other_league,
        name="Eastern",
        abbreviation="EAST",
    )


@pytest.mark.django_db
def test_division_name_must_be_unique_per_conference(nfl):
    conference = Conference.objects.create(
        league=nfl,
        name="American Football Conference",
        abbreviation="AFC",
    )

    Division.objects.create(
        conference=conference,
        name="East",
        abbreviation="E",
    )

    with pytest.raises(IntegrityError):
        Division.objects.create(
            conference=conference,
            name="East",
            abbreviation="OTHER",
        )


@pytest.mark.django_db
def test_division_abbreviation_must_be_unique_per_conference(nfl):
    conference = Conference.objects.create(
        league=nfl,
        name="American Football Conference",
        abbreviation="AFC",
    )

    Division.objects.create(
        conference=conference,
        name="East",
        abbreviation="E",
    )

    with pytest.raises(IntegrityError):
        Division.objects.create(
            conference=conference,
            name="West",
            abbreviation="E",
        )


@pytest.mark.django_db
def test_same_division_name_can_exist_in_different_conferences(nfl):
    afc = Conference.objects.create(
        league=nfl,
        name="American Football Conference",
        abbreviation="AFC",
    )
    nfc = Conference.objects.create(
        league=nfl,
        name="National Football Conference",
        abbreviation="NFC",
    )

    Division.objects.create(
        conference=afc,
        name="East",
        abbreviation="E",
    )

    Division.objects.create(
        conference=nfc,
        name="East",
        abbreviation="E",
    )


@pytest.mark.django_db
def test_team_season_must_be_unique_per_team_and_season(
    season,
    bills,
):
    TeamSeason.objects.create(
        team=bills,
        season=season,
    )

    with pytest.raises(IntegrityError):
        TeamSeason.objects.create(
            team=bills,
            season=season,
        )


@pytest.mark.django_db
def test_team_can_belong_to_multiple_seasons(nfl, season, bills):
    other_season = Season.objects.create(
        league=nfl,
        name="2025",
        start_date="2025-09-01",
        end_date="2026-02-15",
    )

    TeamSeason.objects.create(
        team=bills,
        season=season,
    )

    TeamSeason.objects.create(
        team=bills,
        season=other_season,
    )


@pytest.mark.django_db
def test_team_season_rejects_division_from_different_conference(
    nfl,
    season,
    bills,
):
    afc = Conference.objects.create(
        league=nfl,
        name="American Football Conference",
        abbreviation="AFC",
    )
    nfc = Conference.objects.create(
        league=nfl,
        name="National Football Conference",
        abbreviation="NFC",
    )

    nfc_east = Division.objects.create(
        conference=nfc,
        name="East",
        abbreviation="E",
    )

    membership = TeamSeason(
        team=bills,
        season=season,
        conference=afc,
        division=nfc_east,
    )

    with pytest.raises(
        ValidationError,
        match="Division does not belong to the selected conference",
    ):
        membership.full_clean()


@pytest.mark.django_db
def test_team_season_rejects_division_without_conference(
    nfl,
    season,
    bills,
):
    afc = Conference.objects.create(
        league=nfl,
        name="American Football Conference",
        abbreviation="AFC",
    )

    afc_east = Division.objects.create(
        conference=afc,
        name="East",
        abbreviation="E",
    )

    membership = TeamSeason(
        team=bills,
        season=season,
        division=afc_east,
    )

    with pytest.raises(
        ValidationError,
        match="A division cannot be assigned without a conference",
    ):
        membership.full_clean()
