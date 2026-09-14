from datetime import UTC, datetime, timedelta

import pytest

from betting.models import ExternalGameMapping, ExternalTeamMapping
from betting.services.fixture_matcher import FixtureMatcher
from games.models import Game, Season
from teams.models import League, Team


@pytest.fixture
def fixture_match_setup():
    league = League.objects.create(
        name="National Football League",
        abbreviation="NFL",
    )

    season = Season.objects.create(
        league=league,
        name="2026",
        start_date="2026-09-01",
        end_date="2027-02-28",
    )

    chiefs = Team.objects.create(
        external_id="chiefs",
        slug="kansas-city-chiefs",
        name="Chiefs",
        abbreviation="KC",
        city="Kansas City",
    )

    broncos = Team.objects.create(
        external_id="broncos",
        slug="denver-broncos",
        name="Broncos",
        abbreviation="DEN",
        city="Denver",
    )

    game = Game.objects.create(
        season=season,
        home_team=chiefs,
        away_team=broncos,
        start_time=datetime(
            2026,
            9,
            15,
            0,
            15,
            tzinfo=UTC,
        ),
    )

    ExternalTeamMapping.objects.create(
        team=chiefs,
        provider=ExternalTeamMapping.Provider.ODDSPAPI,
        external_team_id="4422",
    )

    ExternalTeamMapping.objects.create(
        team=broncos,
        provider=ExternalTeamMapping.Provider.ODDSPAPI,
        external_team_id="4418",
    )

    return {
        "chiefs": chiefs,
        "broncos": broncos,
        "game": game,
    }


@pytest.mark.django_db
def test_matches_fixture_within_start_time_tolerance(
    fixture_match_setup,
):
    matcher = FixtureMatcher(
        start_time_tolerance_minutes=30,
    )

    payload = {
        "fixtureId": "fixture-offset",
        "participant1Id": 4422,
        "participant2Id": 4418,
        "startTime": "2026-09-15T00:35:00.000Z",
    }

    result = matcher.match_fixture(payload)

    assert result.matched is True
    assert result.game_id == fixture_match_setup["game"].id


@pytest.mark.django_db
def test_fixture_outside_start_time_tolerance_is_not_matched(
    fixture_match_setup,
):
    matcher = FixtureMatcher(
        start_time_tolerance_minutes=30,
    )

    payload = {
        "fixtureId": "fixture-too-late",
        "participant1Id": 4422,
        "participant2Id": 4418,
        "startTime": "2026-09-15T01:00:00.000Z",
    }

    result = matcher.match_fixture(payload)

    assert result.matched is False
    assert result.game_id is None
    assert result.reason == "no_match"

    assert ExternalGameMapping.objects.count() == 0


@pytest.mark.django_db
def test_missing_team_mapping_does_not_match(
    fixture_match_setup,
):
    ExternalTeamMapping.objects.filter(
        external_team_id="4418",
    ).delete()

    matcher = FixtureMatcher()

    payload = {
        "fixtureId": "fixture-missing-team",
        "participant1Id": 4422,
        "participant2Id": 4418,
        "startTime": "2026-09-15T00:15:00.000Z",
    }

    result = matcher.match_fixture(payload)

    assert result.matched is False
    assert result.game_id is None
    assert result.reason == "missing_team_mapping"

    assert ExternalGameMapping.objects.count() == 0


@pytest.mark.django_db
def test_reversed_participants_do_not_match(
    fixture_match_setup,
):
    matcher = FixtureMatcher()

    payload = {
        "fixtureId": "fixture-reversed",
        "participant1Id": 4418,
        "participant2Id": 4422,
        "startTime": "2026-09-15T00:15:00.000Z",
    }

    result = matcher.match_fixture(payload)

    assert result.matched is False
    assert result.reason == "no_match"

    assert ExternalGameMapping.objects.count() == 0


@pytest.mark.django_db
def test_existing_fixture_mapping_is_reused(
    fixture_match_setup,
):
    existing = ExternalGameMapping.objects.create(
        game=fixture_match_setup["game"],
        provider=ExternalGameMapping.Provider.ODDSPAPI,
        external_fixture_id="fixture-existing",
    )

    matcher = FixtureMatcher()

    payload = {
        "fixtureId": "fixture-existing",
        "participant1Id": 999999,
        "participant2Id": 888888,
        "startTime": "not-even-valid",
    }

    result = matcher.match_fixture(payload)

    assert result.matched is True
    assert result.game_id == fixture_match_setup["game"].id
    assert result.reason == "already_mapped"

    assert ExternalGameMapping.objects.count() == 1
    assert ExternalGameMapping.objects.get() == existing


@pytest.mark.django_db
def test_ambiguous_fixture_is_not_mapped(
    fixture_match_setup,
):
    game = fixture_match_setup["game"]

    Game.objects.create(
        season=game.season,
        home_team=game.home_team,
        away_team=game.away_team,
        start_time=game.start_time + timedelta(minutes=10),
    )

    matcher = FixtureMatcher(
        start_time_tolerance_minutes=30,
    )

    payload = {
        "fixtureId": "fixture-ambiguous",
        "participant1Id": 4422,
        "participant2Id": 4418,
        "startTime": "2026-09-15T00:20:00.000Z",
    }

    result = matcher.match_fixture(payload)

    assert result.matched is False
    assert result.game_id is None
    assert result.reason == "ambiguous_match"

    assert ExternalGameMapping.objects.count() == 0


@pytest.mark.django_db
def test_match_payload_returns_result_for_each_fixture(
    fixture_match_setup,
):
    matcher = FixtureMatcher()

    payload = [
        {
            "fixtureId": "fixture-match",
            "participant1Id": 4422,
            "participant2Id": 4418,
            "startTime": "2026-09-15T00:15:00.000Z",
        },
        {
            "fixtureId": "fixture-no-team",
            "participant1Id": 9999,
            "participant2Id": 8888,
            "startTime": "2026-09-15T00:15:00.000Z",
        },
    ]

    results = matcher.match_payload(payload)

    assert len(results) == 2

    assert results[0].matched is True
    assert results[0].reason == "matched"

    assert results[1].matched is False
    assert results[1].reason == "missing_team_mapping"
