from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import polars as pl
import pytest
from django.utils import timezone

from games.models import Game, Season
from ingestion.models import IngestionState
from ingestion.nfl.team_stats import NFLTeamStatsIngestor
from stats.models import NFLTeamGameStats
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
        name="2025",
        start_date="2025-09-01",
        end_date="2026-02-28",
    )


@pytest.fixture
def cardinals():
    return Team.objects.create(
        external_id="3800",
        slug="arizona-cardinals",
        name="Cardinals",
        abbreviation="ARI",
        city="Arizona",
    )


@pytest.fixture
def saints():
    return Team.objects.create(
        external_id="3300",
        slug="new-orleans-saints",
        name="Saints",
        abbreviation="NO",
        city="New Orleans",
    )


@pytest.fixture
def team_seasons(
    season,
    cardinals,
    saints,
):
    TeamSeason.objects.create(
        team=cardinals,
        season=season,
        name="Cardinals",
        abbreviation="ARI",
        city="Arizona",
    )

    TeamSeason.objects.create(
        team=saints,
        season=season,
        name="Saints",
        abbreviation="NO",
        city="New Orleans",
    )


@pytest.fixture
def game(
    season,
    cardinals,
    saints,
    team_seasons,
):
    return Game.objects.create(
        external_id="2025_01_ARI_NO",
        season=season,
        home_team=saints,
        away_team=cardinals,
        start_time=datetime(
            2025,
            9,
            7,
            13,
            0,
            tzinfo=ZoneInfo("America/New_York"),
        ),
        home_score=13,
        away_score=20,
        status=Game.Status.FINAL,
        phase="regular_season",
        finish_type=Game.FinishType.REGULATION,
    )


@pytest.fixture
def team_reference_data():
    return pl.DataFrame(
        [
            {
                "team_id": "3800",
                "team_abbr": "ARI",
            },
            {
                "team_id": "3300",
                "team_abbr": "NO",
            },
        ]
    )


@pytest.fixture
def team_stats_data():
    return pl.DataFrame(
        [
            {
                "season": 2025,
                "week": 1,
                "team": "ARI",
                "season_type": "REG",
                "game_id": "2025_01_ARI_NO",
                "opponent_team": "NO",
                "completions": 21,
                "attempts": 29,
                "passing_yards": 163,
                "passing_interceptions": 1,
                "passing_epa": 1.5,
                "passing_cpoe": -1.7,
                "passing_air_yards": 166,
                "passing_yards_after_catch": 100,
                "carries": 27,
                "rushing_yards": 146,
                "rushing_epa": 1.1,
                "sacks_suffered": 5,
                "fumbles_lost_total": 1,
                "penalties": 9,
                "penalty_yards": 54,
                "def_sacks": 1.0,
                "def_qb_hits": 2,
                "def_tackles_for_loss": 3,
                "fg_made": 2,
                "fg_att": 3,
            },
            {
                "season": 2025,
                "week": 1,
                "team": "NO",
                "season_type": "REG",
                "game_id": "2025_01_ARI_NO",
                "opponent_team": "ARI",
                "completions": 25,
                "attempts": 40,
                "passing_yards": 214,
                "passing_interceptions": 0,
                "passing_epa": -2.0,
                "passing_cpoe": -3.0,
                "passing_air_yards": 220,
                "passing_yards_after_catch": 90,
                "carries": 22,
                "rushing_yards": 89,
                "rushing_epa": -1.0,
                "sacks_suffered": 1,
                "fumbles_lost_total": 0,
                "penalties": 6,
                "penalty_yards": 40,
                "def_sacks": 5.0,
                "def_qb_hits": 7,
                "def_tackles_for_loss": 6,
                "fg_made": 2,
                "fg_att": 2,
            },
        ]
    )


@pytest.mark.django_db
@patch("ingestion.nfl.team_stats.nfl.load_teams")
@patch("ingestion.nfl.team_stats.nfl.load_team_stats")
def test_ingests_team_stats(
    mock_load_team_stats,
    mock_load_teams,
    game,
    team_stats_data,
    team_reference_data,
):
    mock_load_team_stats.return_value = team_stats_data
    mock_load_teams.return_value = team_reference_data

    NFLTeamStatsIngestor(2025).ingest()

    assert NFLTeamGameStats.objects.count() == 2

    arizona = NFLTeamGameStats.objects.get(
        game=game,
        team__abbreviation="ARI",
    )

    assert arizona.points_for == 20
    assert arizona.points_allowed == 13
    assert arizona.offensive_passing_yards == 163
    assert arizona.passing_attempts == 29
    assert arizona.passing_completions == 21
    assert arizona.passing_epa == 1.5
    assert arizona.passing_cpoe == -1.7
    assert arizona.passing_air_yards == 166
    assert arizona.passing_yards_after_catch == 100
    assert arizona.offensive_rushing_yards == 146
    assert arizona.rushing_attempts == 27
    assert arizona.rushing_epa == 1.1
    assert arizona.sacks_allowed == 5
    assert arizona.penalties == 9
    assert arizona.penalty_yards == 54
    assert arizona.offensive_turnovers == 2
    assert arizona.defensive_sacks == 1.0
    assert arizona.defensive_passing_yards_allowed == 214
    assert arizona.defensive_rushing_yards_allowed == 89
    assert arizona.defensive_turnovers_forced == 0
    assert arizona.defensive_qb_hits == 2
    assert arizona.defensive_tackles_for_loss == 3
    assert arizona.field_goals_made == 2
    assert arizona.field_goals_attempted == 3


@pytest.mark.django_db
@patch("ingestion.nfl.team_stats.nfl.load_teams")
@patch("ingestion.nfl.team_stats.nfl.load_team_stats")
def test_missing_opponent_row_saves_available_stats(
    mock_load_team_stats,
    mock_load_teams,
    game,
    team_reference_data,
):
    mock_load_teams.return_value = team_reference_data

    mock_load_team_stats.return_value = pl.DataFrame(
        [
            {
                "season": 2025,
                "week": 1,
                "team": "ARI",
                "season_type": "REG",
                "game_id": "2025_01_ARI_NO",
                "opponent_team": "NO",
                "completions": 21,
                "attempts": 29,
                "passing_yards": 163,
                "passing_interceptions": 0,
                "passing_epa": None,
                "passing_cpoe": None,
                "passing_air_yards": None,
                "passing_yards_after_catch": None,
                "carries": 27,
                "rushing_yards": 146,
                "rushing_epa": None,
                "sacks_suffered": 5,
                "fumbles_lost_total": 0,
                "penalties": 9,
                "penalty_yards": 54,
                "def_sacks": 1.0,
                "def_qb_hits": 2,
                "def_tackles_for_loss": 3,
                "fg_made": 2,
                "fg_att": 3,
            },
        ]
    )

    NFLTeamStatsIngestor(2025).ingest()

    stats = NFLTeamGameStats.objects.get(
        game=game,
        team__abbreviation="ARI",
    )

    assert stats.offensive_passing_yards == 163

    assert stats.defensive_passing_yards_allowed is None
    assert stats.defensive_rushing_yards_allowed is None
    assert stats.defensive_turnovers_forced is None


@pytest.mark.django_db
@patch("ingestion.nfl.team_stats.nfl.load_teams")
@patch("ingestion.nfl.team_stats.nfl.load_team_stats")
def test_null_team_row_is_skipped(
    mock_load_team_stats,
    mock_load_teams,
    game,
    team_reference_data,
):
    mock_load_teams.return_value = team_reference_data

    mock_load_team_stats.return_value = pl.DataFrame(
        [
            {
                "season": 2025,
                "week": 1,
                "team": None,
                "game_id": "2025_01_ARI_NO",
            }
        ]
    )

    NFLTeamStatsIngestor(2025).ingest()

    assert NFLTeamGameStats.objects.count() == 0


@pytest.mark.django_db
@patch("ingestion.nfl.team_stats.nfl.load_teams")
@patch("ingestion.nfl.team_stats.nfl.load_team_stats")
def test_historical_alias_resolves_by_franchise_id(
    mock_load_team_stats,
    mock_load_teams,
    game,
    cardinals,
):
    mock_load_team_stats.return_value = pl.DataFrame([])
    mock_load_teams.return_value = pl.DataFrame(
        [
            {
                "team_id": cardinals.external_id,
                "team_abbr": "ARI",
            }
        ]
    )

    ingestor = NFLTeamStatsIngestor.__new__(NFLTeamStatsIngestor)
    ingestor.teams = mock_load_teams.return_value

    team = ingestor._get_team(
        {
            "team": "ARI",
            "game_id": game.external_id,
        }
    )

    assert team == cardinals


@pytest.mark.django_db
@patch("ingestion.nfl.team_stats.nfl.load_teams")
@patch("ingestion.nfl.team_stats.nfl.load_team_stats")
def test_nullable_metrics_remain_null(
    mock_load_team_stats,
    mock_load_teams,
    game,
    team_reference_data,
):
    mock_load_teams.return_value = team_reference_data

    data = pl.DataFrame(
        [
            {
                "season": 2025,
                "week": 1,
                "team": "ARI",
                "season_type": "REG",
                "game_id": "2025_01_ARI_NO",
                "opponent_team": "NO",
                "completions": 21,
                "attempts": 29,
                "passing_yards": 163,
                "passing_interceptions": 0,
                "passing_epa": None,
                "passing_cpoe": None,
                "passing_air_yards": None,
                "passing_yards_after_catch": None,
                "carries": 27,
                "rushing_yards": 146,
                "rushing_epa": None,
                "sacks_suffered": 5,
                "fumbles_lost_total": 0,
                "penalties": None,
                "penalty_yards": None,
                "def_sacks": None,
                "def_qb_hits": None,
                "def_tackles_for_loss": None,
                "fg_made": None,
                "fg_att": None,
            },
        ]
    )

    mock_load_team_stats.return_value = data

    NFLTeamStatsIngestor(2025).ingest()

    stats = NFLTeamGameStats.objects.get(
        game=game,
        team=game.away_team,
    )

    assert stats.passing_epa is None
    assert stats.passing_cpoe is None
    assert stats.rushing_epa is None
    assert stats.passing_air_yards is None


@pytest.mark.django_db
@patch("ingestion.nfl.team_stats.nfl.load_teams")
@patch("ingestion.nfl.team_stats.nfl.load_team_stats")
def test_team_stats_ingestion_is_idempotent(
    mock_load_team_stats,
    mock_load_teams,
    game,
    team_stats_data,
    team_reference_data,
):
    mock_load_team_stats.return_value = team_stats_data
    mock_load_teams.return_value = team_reference_data

    NFLTeamStatsIngestor(
        2025,
        force=True,
    ).ingest()

    NFLTeamStatsIngestor(
        2025,
        force=True,
    ).ingest()

    assert NFLTeamGameStats.objects.count() == 2


@pytest.mark.django_db
@patch("ingestion.nfl.team_stats.nfl.load_teams")
@patch("ingestion.nfl.team_stats.nfl.load_team_stats")
def test_team_stats_ingestion_marks_dataset_complete(
    mock_load_team_stats,
    mock_load_teams,
    season,
    game,
    team_stats_data,
    team_reference_data,
):
    mock_load_team_stats.return_value = team_stats_data
    mock_load_teams.return_value = team_reference_data

    NFLTeamStatsIngestor(2025).ingest()

    state = IngestionState.objects.get(
        season=season,
        dataset=IngestionState.Dataset.TEAM_STATS,
    )

    assert state.last_completed_at is not None


@pytest.mark.django_db
@patch("ingestion.nfl.team_stats.nfl.load_teams")
@patch("ingestion.nfl.team_stats.nfl.load_team_stats")
def test_completed_team_stats_do_not_reload_source(
    mock_load_team_stats,
    mock_load_teams,
    season,
    game,
):
    IngestionState.objects.create(
        league=season.league,
        season=season,
        dataset=IngestionState.Dataset.TEAM_STATS,
        last_completed_at=timezone.now(),
    )

    result = NFLTeamStatsIngestor(2025).ingest()

    assert result is False

    mock_load_team_stats.assert_not_called()
    mock_load_teams.assert_not_called()


@pytest.mark.django_db
@patch("ingestion.nfl.team_stats.nfl.load_teams")
@patch("ingestion.nfl.team_stats.nfl.load_team_stats")
def test_force_reloads_completed_team_stats(
    mock_load_team_stats,
    mock_load_teams,
    season,
    game,
    team_stats_data,
    team_reference_data,
):
    IngestionState.objects.create(
        league=season.league,
        season=season,
        dataset=IngestionState.Dataset.TEAM_STATS,
        last_completed_at=timezone.now(),
    )

    mock_load_team_stats.return_value = team_stats_data
    mock_load_teams.return_value = team_reference_data

    result = NFLTeamStatsIngestor(
        2025,
        force=True,
    ).ingest()

    assert result is True

    mock_load_team_stats.assert_called_once_with(2025)


def test_offensive_turnovers_combines_interceptions_and_lost_fumbles():
    assert (
        NFLTeamStatsIngestor._get_offensive_turnovers(
            {
                "passing_interceptions": 2,
                "fumbles_lost_total": 1,
            }
        )
        == 3
    )


def test_offensive_turnovers_returns_none_when_data_missing():
    assert (
        NFLTeamStatsIngestor._get_offensive_turnovers(
            {
                "passing_interceptions": None,
                "fumbles_lost_total": 1,
            }
        )
        is None
    )


@pytest.mark.django_db
def test_points_for_raises_when_game_has_no_score(
    season,
    cardinals,
    saints,
    team_seasons,
):
    game = Game.objects.create(
        external_id="2025_02_ARI_NO",
        season=season,
        home_team=saints,
        away_team=cardinals,
        start_time=None,
        home_score=None,
        away_score=None,
        status=Game.Status.SCHEDULED,
        phase="regular_season",
    )

    with pytest.raises(
        ValueError,
        match="has team stats but no score",
    ):
        NFLTeamStatsIngestor._get_points_for(
            game,
            cardinals,
        )
