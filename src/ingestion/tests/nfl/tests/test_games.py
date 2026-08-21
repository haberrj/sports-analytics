from unittest.mock import patch

import polars as pl
import pytest

from games.models import Game, Week
from ingestion.nfl.games import NFLGameIngestor
from teams.models import TeamSeason


@pytest.fixture
def schedule_data():
    return pl.DataFrame(
        [
            {
                "game_id": "2025_01_DAL_PHI",
                "season": 2025,
                "game_type": "REG",
                "week": 1,
                "gameday": "2025-09-04",
                "gametime": "20:20",
                "away_team": "DAL",
                "away_score": 20,
                "home_team": "PHI",
                "home_score": 24,
                "location": "Home",
                "overtime": 0,
            },
            {
                "game_id": "2025_02_NYG_DAL",
                "season": 2025,
                "game_type": "REG",
                "week": 2,
                "gameday": "2025-09-14",
                "gametime": "13:00",
                "away_team": "NYG",
                "away_score": 37,
                "home_team": "DAL",
                "home_score": 40,
                "location": "Home",
                "overtime": 1,
            },
        ]
    )


@pytest.fixture
def ingested_teams():
    from games.models import Season
    from teams.models import Conference, Division, League, Team

    league = League.objects.create(
        name="National Football League",
        abbreviation="NFL",
    )
    season = Season.objects.create(
        league=league,
        name="2025",
        start_date="2025-09-01",
        end_date="2026-02-28",
    )

    nfc = Conference.objects.create(
        league=league,
        name="NFC",
        abbreviation="NFC",
    )
    east = Division.objects.create(
        conference=nfc,
        name="East",
        abbreviation="EAST",
    )

    teams = {}

    for abbr, city, name, external_id in [
        ("DAL", "Dallas", "Cowboys", "1200"),
        ("PHI", "Philadelphia", "Eagles", "3700"),
        ("NYG", "New York", "Giants", "3410"),
    ]:
        team = Team.objects.create(
            external_id=external_id,
            slug=f"{city}-{name}".lower().replace(" ", "-"),
            city=city,
            name=name,
            abbreviation=abbr,
        )

        TeamSeason.objects.create(
            team=team,
            season=season,
            conference=nfc,
            division=east,
            city=city,
            name=name,
            abbreviation=abbr,
        )

        teams[abbr] = team

    return season, teams


@pytest.mark.django_db
@patch("ingestion.nfl.games.NFLTeamIngestor.ingest")
@patch("ingestion.nfl.games.nfl.load_schedules")
def test_ingests_completed_game(
    mock_load_schedules,
    mock_team_ingest,
    schedule_data,
    ingested_teams,
):
    mock_load_schedules.return_value = schedule_data

    NFLGameIngestor(2025).ingest()

    game = Game.objects.get(
        external_id="2025_01_DAL_PHI",
    )

    assert game.home_team.abbreviation == "PHI"
    assert game.away_team.abbreviation == "DAL"
    assert game.home_score == 24
    assert game.away_score == 20
    assert game.status == Game.Status.FINAL
    assert game.phase == "regular_season"
    assert game.finish_type == Game.FinishType.REGULATION
    assert game.neutral_site is False


@pytest.mark.django_db
@patch("ingestion.nfl.games.NFLTeamIngestor.ingest")
@patch("ingestion.nfl.games.nfl.load_schedules")
def test_ingests_overtime_game(
    mock_load_schedules,
    mock_team_ingest,
    schedule_data,
    ingested_teams,
):
    mock_load_schedules.return_value = schedule_data

    NFLGameIngestor(2025).ingest()

    game = Game.objects.get(
        external_id="2025_02_NYG_DAL",
    )

    assert game.finish_type == Game.FinishType.OVERTIME


@pytest.mark.django_db
@patch("ingestion.nfl.games.NFLTeamIngestor.ingest")
@patch("ingestion.nfl.games.nfl.load_schedules")
def test_game_ingestion_is_idempotent(
    mock_load_schedules,
    mock_team_ingest,
    schedule_data,
    ingested_teams,
):
    mock_load_schedules.return_value = schedule_data

    ingestor = NFLGameIngestor(2025)

    ingestor.ingest()
    ingestor.ingest()

    assert Game.objects.count() == 2
    assert Week.objects.count() == 2


@pytest.mark.django_db
@patch("ingestion.nfl.games.NFLTeamIngestor.ingest")
@patch("ingestion.nfl.games.nfl.load_schedules")
def test_game_ingestor_ensures_team_dependency(
    mock_load_schedules,
    mock_team_ingest,
    schedule_data,
    ingested_teams,
):
    mock_load_schedules.return_value = schedule_data

    NFLGameIngestor(2025).ingest()

    mock_team_ingest.assert_called_once()


def test_unknown_game_type_raises_error():
    ingestor = object.__new__(NFLGameIngestor)

    with pytest.raises(ValueError, match="Unknown NFL game type"):
        ingestor._get_phase({"game_type": "UNKNOWN"})


def test_scheduled_game_has_no_finish_type():
    game_data = {
        "home_score": None,
        "away_score": None,
        "overtime": 0,
    }

    assert NFLGameIngestor._get_status(game_data) == Game.Status.SCHEDULED
    assert NFLGameIngestor._get_finish_type(game_data) is None
