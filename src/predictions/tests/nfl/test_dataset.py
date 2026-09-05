import pickle
from unittest.mock import patch

import pytest

from games.models import Game, Season, Week
from predictions.nfl.dataset import NFLTrainingDataService
from stats.models import NFLTeamProfile
from teams.models import League, Team, TeamSeason


@pytest.mark.django_db
def test_get_profile_before_game_uses_latest_current_season_profile():
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

    week_8 = Week.objects.create(season=season, number=8)
    week_9 = Week.objects.create(season=season, number=9)
    week_10 = Week.objects.create(season=season, number=10)

    team = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    opponent = Team.objects.create(
        external_id="KC",
        slug="kansas-city-chiefs",
        city="Kansas City",
        name="Chiefs",
        abbreviation="KC",
    )

    TeamSeason.objects.create(
        team=team,
        season=season,
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    NFLTeamProfile.objects.create(
        team=team,
        season=season,
        through_week=week_8,
    )

    week_9_profile = NFLTeamProfile.objects.create(
        team=team,
        season=season,
        through_week=week_9,
    )

    game = Game.objects.create(
        external_id="2025_10_BUF_KC",
        season=season,
        week=week_10,
        home_team=opponent,
        away_team=team,
        start_time="2025-11-02T18:00:00Z",
        status=Game.Status.SCHEDULED,
        phase="regular_season",
    )

    profile = NFLTrainingDataService.get_profile_before_game(
        team=team,
        game=game,
    )

    assert profile == week_9_profile


@pytest.mark.django_db
def test_get_profile_before_game_handles_bye_week():
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

    week_8 = Week.objects.create(season=season, number=8)
    week_10 = Week.objects.create(season=season, number=10)

    team = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    opponent = Team.objects.create(
        external_id="KC",
        slug="kansas-city-chiefs",
        city="Kansas City",
        name="Chiefs",
        abbreviation="KC",
    )

    TeamSeason.objects.create(
        team=team,
        season=season,
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    week_8_profile = NFLTeamProfile.objects.create(
        team=team,
        season=season,
        through_week=week_8,
    )

    game = Game.objects.create(
        external_id="2025_10_BUF_KC",
        season=season,
        week=week_10,
        home_team=opponent,
        away_team=team,
        start_time="2025-11-02T18:00:00Z",
        status=Game.Status.SCHEDULED,
        phase="regular_season",
    )

    profile = NFLTrainingDataService.get_profile_before_game(
        team=team,
        game=game,
    )

    assert profile == week_8_profile


@pytest.mark.django_db
def test_get_profile_before_game_falls_back_to_previous_season():
    league = League.objects.create(
        name="National Football League",
        abbreviation="NFL",
    )

    season_2024 = Season.objects.create(
        league=league,
        name="2024",
        start_date="2024-09-01",
        end_date="2025-02-28",
    )

    season_2025 = Season.objects.create(
        league=league,
        name="2025",
        start_date="2025-09-01",
        end_date="2026-02-28",
    )

    week_18_2024 = Week.objects.create(
        season=season_2024,
        number=18,
    )

    week_1_2025 = Week.objects.create(
        season=season_2025,
        number=1,
    )

    team = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    opponent = Team.objects.create(
        external_id="KC",
        slug="kansas-city-chiefs",
        city="Kansas City",
        name="Chiefs",
        abbreviation="KC",
    )

    TeamSeason.objects.create(
        team=team,
        season=season_2024,
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    TeamSeason.objects.create(
        team=team,
        season=season_2025,
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    previous_profile = NFLTeamProfile.objects.create(
        team=team,
        season=season_2024,
        through_week=week_18_2024,
    )

    game = Game.objects.create(
        external_id="2025_01_BUF_KC",
        season=season_2025,
        week=week_1_2025,
        home_team=team,
        away_team=opponent,
        start_time="2025-09-04T18:00:00Z",
        status=Game.Status.SCHEDULED,
        phase="regular_season",
    )

    profile = NFLTrainingDataService.get_profile_before_game(
        team=team,
        game=game,
    )

    assert profile == previous_profile


@pytest.mark.django_db
def test_get_profile_before_game_returns_none_without_history():
    league = League.objects.create(
        name="National Football League",
        abbreviation="NFL",
    )

    season = Season.objects.create(
        league=league,
        name="1999",
        start_date="1999-09-01",
        end_date="2000-02-28",
    )

    week_1 = Week.objects.create(
        season=season,
        number=1,
    )

    team = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    opponent = Team.objects.create(
        external_id="MIA",
        slug="miami-dolphins",
        city="Miami",
        name="Dolphins",
        abbreviation="MIA",
    )

    TeamSeason.objects.create(
        team=team,
        season=season,
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    game = Game.objects.create(
        external_id="1999_01_BUF_MIA",
        season=season,
        week=week_1,
        home_team=team,
        away_team=opponent,
        start_time="1999-09-01T18:00:00Z",
        status=Game.Status.SCHEDULED,
        phase="regular_season",
    )

    profile = NFLTrainingDataService.get_profile_before_game(
        team=team,
        game=game,
    )

    assert profile is None


@pytest.mark.django_db
@patch.object(
    NFLTrainingDataService,
    "get_profile_before_game",
)
def test_build_feature_row_for_upcoming_game(mock_get_profile):
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

    week = Week.objects.create(
        season=season,
        number=5,
    )

    bills = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    chiefs = Team.objects.create(
        external_id="KC",
        slug="kansas-city-chiefs",
        city="Kansas City",
        name="Chiefs",
        abbreviation="KC",
    )

    profile = NFLTeamProfile(
        team=bills,
        season=season,
        through_week=week,
    )

    mock_get_profile.return_value = profile

    game = Game.objects.create(
        external_id="2025_05_BUF_KC",
        season=season,
        week=week,
        home_team=bills,
        away_team=chiefs,
        home_score=None,
        away_score=None,
        neutral_site=False,
        start_time="2025-10-05T18:00:00Z",
        status=Game.Status.SCHEDULED,
        phase="regular_season",
    )

    row = NFLTrainingDataService.build_feature_row(game)

    assert row is not None
    assert row["game_id"] == "2025_05_BUF_KC"
    assert row["season"] == 2025
    assert row["week"] == 5
    assert row["home_team"] == "BUF"
    assert row["away_team"] == "KC"
    assert row["neutral_site"] is False

    assert "home_score" not in row
    assert "away_score" not in row
    assert "home_win" not in row
    assert "total_game_points" not in row
    assert "score_differential" not in row


@pytest.mark.django_db
def test_build_training_row():
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

    week_4 = Week.objects.create(
        season=season,
        number=4,
    )

    week_5 = Week.objects.create(
        season=season,
        number=5,
    )

    bills = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    chiefs = Team.objects.create(
        external_id="KC",
        slug="kansas-city-chiefs",
        city="Kansas City",
        name="Chiefs",
        abbreviation="KC",
    )

    for team in [bills, chiefs]:
        TeamSeason.objects.create(
            team=team,
            season=season,
            city=team.city,
            name=team.name,
            abbreviation=team.abbreviation,
        )

    NFLTeamProfile.objects.create(
        team=bills,
        season=season,
        through_week=week_4,
        points_for_per_game=30.0,
        points_allowed_per_game=20.0,
        point_differential_per_game=10.0,
        pass_offense_yards_per_attempt=8.0,
        rush_offense_yards_per_attempt=5.0,
        pass_epa_per_attempt=0.25,
        defensive_sacks_per_game=3.0,
        turnover_differential_per_game=1.0,
        field_goal_percentage=0.9,
        pass_offense_yards_per_attempt_strength=0.15,
    )

    NFLTeamProfile.objects.create(
        team=chiefs,
        season=season,
        through_week=week_4,
        points_for_per_game=27.0,
        points_allowed_per_game=23.0,
        point_differential_per_game=4.0,
        pass_offense_yards_per_attempt=7.0,
        rush_offense_yards_per_attempt=4.5,
        pass_epa_per_attempt=0.18,
        defensive_sacks_per_game=2.0,
        turnover_differential_per_game=-0.5,
        field_goal_percentage=0.8,
        pass_offense_yards_per_attempt_strength=0.05,
    )

    game = Game.objects.create(
        external_id="2025_05_BUF_KC",
        season=season,
        week=week_5,
        home_team=bills,
        away_team=chiefs,
        home_score=31,
        away_score=24,
        neutral_site=False,
        start_time="2025-10-05T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    row = NFLTrainingDataService.build_training_row(game)

    assert row is not None

    # Metadata
    assert row["game_id"] == "2025_05_BUF_KC"
    assert row["season"] == 2025
    assert row["week"] == 5
    assert row["home_team"] == "BUF"
    assert row["away_team"] == "KC"
    assert row["neutral_site"] is False

    # Representative home features
    assert row["home_points_for_per_game"] == 30.0
    assert row["home_point_differential_per_game"] == 10.0
    assert row["home_pass_offense_yards_per_attempt"] == 8.0
    assert row["home_pass_epa_per_attempt"] == 0.25
    assert row["home_defensive_sacks_per_game"] == 3.0
    assert row["home_turnover_differential_per_game"] == 1.0
    assert row["home_field_goal_percentage"] == 0.9
    assert row["home_pass_offense_yards_per_attempt_strength"] == 0.15

    # Representative away features
    assert row["away_points_for_per_game"] == 27.0
    assert row["away_point_differential_per_game"] == 4.0
    assert row["away_pass_offense_yards_per_attempt"] == 7.0
    assert row["away_pass_epa_per_attempt"] == 0.18
    assert row["away_defensive_sacks_per_game"] == 2.0
    assert row["away_turnover_differential_per_game"] == -0.5
    assert row["away_field_goal_percentage"] == 0.8
    assert row["away_pass_offense_yards_per_attempt_strength"] == 0.05

    # Targets
    assert row["home_score"] == 31
    assert row["away_score"] == 24
    assert row["home_win"] == 1
    assert row["total_game_points"] == 55
    assert row["score_differential"] == 7


@pytest.mark.django_db
def test_build_training_row_returns_none_when_profile_missing():
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

    week = Week.objects.create(
        season=season,
        number=1,
    )

    bills = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    chiefs = Team.objects.create(
        external_id="KC",
        slug="kansas-city-chiefs",
        city="Kansas City",
        name="Chiefs",
        abbreviation="KC",
    )

    game = Game.objects.create(
        external_id="2025_01_BUF_KC",
        season=season,
        week=week,
        home_team=bills,
        away_team=chiefs,
        home_score=31,
        away_score=24,
        start_time="2025-09-04T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    row = NFLTrainingDataService.build_training_row(game)

    assert row is None


@pytest.mark.django_db
def test_build_training_row_returns_none_when_game_has_no_score():
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

    week_4 = Week.objects.create(
        season=season,
        number=4,
    )

    week_5 = Week.objects.create(
        season=season,
        number=5,
    )

    bills = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    chiefs = Team.objects.create(
        external_id="KC",
        slug="kansas-city-chiefs",
        city="Kansas City",
        name="Chiefs",
        abbreviation="KC",
    )

    for team in [bills, chiefs]:
        TeamSeason.objects.create(
            team=team,
            season=season,
            city=team.city,
            name=team.name,
            abbreviation=team.abbreviation,
        )

        NFLTeamProfile.objects.create(
            team=team,
            season=season,
            through_week=week_4,
        )

    game = Game.objects.create(
        external_id="2025_05_BUF_KC",
        season=season,
        week=week_5,
        home_team=bills,
        away_team=chiefs,
        home_score=None,
        away_score=None,
        start_time="2025-10-05T18:00:00Z",
        status=Game.Status.SCHEDULED,
        phase="regular_season",
    )

    row = NFLTrainingDataService.build_training_row(game)

    assert row is None


@pytest.mark.django_db
@patch.object(
    NFLTrainingDataService,
    "get_profile_before_game",
)
def test_build_training_row_handles_tie(mock_get_profile):
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

    week = Week.objects.create(
        season=season,
        number=5,
    )

    bills = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    chiefs = Team.objects.create(
        external_id="KC",
        slug="kansas-city-chiefs",
        city="Kansas City",
        name="Chiefs",
        abbreviation="KC",
    )

    profile = NFLTeamProfile(
        team=bills,
        season=season,
        through_week=week,
    )

    mock_get_profile.return_value = profile

    game = Game.objects.create(
        external_id="2025_05_BUF_KC",
        season=season,
        week=week,
        home_team=bills,
        away_team=chiefs,
        home_score=24,
        away_score=24,
        neutral_site=False,
        start_time="2025-10-05T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    row = NFLTrainingDataService.build_training_row(game)

    assert row is not None
    assert row["home_win"] == 0
    assert row["total_game_points"] == 48
    assert row["score_differential"] == 0


@pytest.mark.django_db
@patch.object(
    NFLTrainingDataService,
    "build_training_row",
)
def test_build_dataset(mock_build_training_row, tmp_path):
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

    week_1 = Week.objects.create(
        season=season,
        number=1,
    )

    week_2 = Week.objects.create(
        season=season,
        number=2,
    )

    bills = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        city="Buffalo",
        name="Bills",
        abbreviation="BUF",
    )

    chiefs = Team.objects.create(
        external_id="KC",
        slug="kansas-city-chiefs",
        city="Kansas City",
        name="Chiefs",
        abbreviation="KC",
    )

    Game.objects.create(
        external_id="2025_01_BUF_KC",
        season=season,
        week=week_1,
        home_team=bills,
        away_team=chiefs,
        home_score=24,
        away_score=17,
        start_time="2025-09-04T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    Game.objects.create(
        external_id="2025_02_KC_BUF",
        season=season,
        week=week_2,
        home_team=chiefs,
        away_team=bills,
        home_score=20,
        away_score=27,
        start_time="2025-09-11T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    mock_build_training_row.side_effect = [
        {"game_id": "2025_01_BUF_KC"},
        {"game_id": "2025_02_KC_BUF"},
    ]

    with patch.object(
        NFLTrainingDataService,
        "CACHE_DIRECTORY",
        tmp_path,
    ):
        rows = NFLTrainingDataService.build_dataset(
            season=season,
            force_rebuild=True,
        )

    assert rows == [
        {"game_id": "2025_01_BUF_KC"},
        {"game_id": "2025_02_KC_BUF"},
    ]

    assert mock_build_training_row.call_count == 2


def test_build_dataset_uses_cache(tmp_path):
    cached_rows = [
        {"game_id": "cached_game"},
    ]

    cache_path = tmp_path / "nfl_training_dataset_all.pkl"

    with cache_path.open("wb") as file:
        pickle.dump(cached_rows, file)

    with (
        patch.object(
            NFLTrainingDataService,
            "CACHE_DIRECTORY",
            tmp_path,
        ),
        patch.object(
            NFLTrainingDataService,
            "build_training_row",
        ) as mock_build_training_row,
    ):
        rows = NFLTrainingDataService.build_dataset()

    assert rows == cached_rows
    mock_build_training_row.assert_not_called()
