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
