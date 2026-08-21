from unittest.mock import patch

import polars as pl
import pytest

from ingestion.nfl.teams import NFLTeamIngestor
from teams.models import Conference, Division, League, Team, TeamSeason


@pytest.fixture
def teams_data():
    return pl.DataFrame(
        [
            {
                "team_id": "2510",
                "team_abbr": "LAR",
                "team_name": "Los Angeles Rams",
                "team_nick": "Rams",
                "team_conf": "NFC",
                "team_division": "NFC West",
            },
            {
                "team_id": "2510",
                "team_abbr": "STL",
                "team_name": "St. Louis Rams",
                "team_nick": "Rams",
                "team_conf": "NFC",
                "team_division": "NFC West",
            },
            {
                "team_id": "0610",
                "team_abbr": "BUF",
                "team_name": "Buffalo Bills",
                "team_nick": "Bills",
                "team_conf": "AFC",
                "team_division": "AFC East",
            },
        ]
    )


def schedule_for(*abbreviations):
    return pl.DataFrame(
        {
            "home_team": list(abbreviations),
            "away_team": list(reversed(abbreviations)),
        }
    )


@pytest.mark.django_db
@patch("ingestion.nfl.teams.nfl.load_schedules")
@patch("ingestion.nfl.teams.nfl.load_teams")
def test_ingests_only_teams_active_for_season(
    mock_load_teams,
    mock_load_schedules,
    teams_data,
):
    mock_load_teams.return_value = teams_data
    mock_load_schedules.return_value = schedule_for("LAR", "BUF")

    NFLTeamIngestor(2026).ingest()

    assert Team.objects.count() == 2
    assert Team.objects.filter(external_id="2510", abbreviation="LAR").exists()
    assert not TeamSeason.objects.filter(abbreviation="STL").exists()


@pytest.mark.django_db
@patch("ingestion.nfl.teams.nfl.load_schedules")
@patch("ingestion.nfl.teams.nfl.load_teams")
def test_team_ingestion_is_idempotent(
    mock_load_teams,
    mock_load_schedules,
    teams_data,
):
    mock_load_teams.return_value = teams_data
    mock_load_schedules.return_value = schedule_for("LAR", "BUF")

    ingestor = NFLTeamIngestor(2026)

    ingestor.ingest()
    ingestor.ingest()

    assert League.objects.count() == 1
    assert Conference.objects.count() == 2
    assert Division.objects.count() == 2
    assert Team.objects.count() == 2
    assert TeamSeason.objects.count() == 2


@pytest.mark.django_db
@patch("ingestion.nfl.base.NFLIngestor.get_current_season")
@patch("ingestion.nfl.teams.nfl.load_schedules")
@patch("ingestion.nfl.teams.nfl.load_teams")
def test_historical_ingestion_does_not_overwrite_current_team_identity(
    mock_load_teams,
    mock_load_schedules,
    mock_default_season,
    teams_data,
):
    mock_default_season.return_value = 2026
    mock_load_teams.return_value = teams_data

    mock_load_schedules.return_value = schedule_for("LAR")
    NFLTeamIngestor(2026).ingest()

    mock_load_schedules.return_value = schedule_for("STL")
    NFLTeamIngestor(2015).ingest()

    rams = Team.objects.get(external_id="2510")

    assert rams.city == "Los Angeles"
    assert rams.abbreviation == "LAR"

    historical = rams.season_memberships.get(season__name="2015")

    assert historical.city == "St. Louis"
    assert historical.abbreviation == "STL"


@pytest.mark.django_db
@patch("ingestion.nfl.teams.nfl.load_schedules")
@patch("ingestion.nfl.teams.nfl.load_teams")
def test_team_season_contains_conference_and_division(
    mock_load_teams,
    mock_load_schedules,
    teams_data,
):
    mock_load_teams.return_value = teams_data
    mock_load_schedules.return_value = schedule_for("BUF")

    NFLTeamIngestor(2026).ingest()

    membership = TeamSeason.objects.get(
        team__external_id="0610",
        season__name="2026",
    )

    assert membership.conference.abbreviation == "AFC"
    assert membership.division.name == "East"
