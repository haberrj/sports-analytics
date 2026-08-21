import pytest

from games.models import Game, Season, Week
from stats.derived import NFLDerivedStatsService
from stats.models import NFLTeamGameStats
from teams.models import League, Team


@pytest.mark.django_db
def test_get_team_stats_through_week_only_returns_prior_games():
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
    week_3 = Week.objects.create(
        season=season,
        number=3,
    )

    team = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        name="Bills",
        abbreviation="BUF",
        city="Buffalo",
    )

    opponent = Team.objects.create(
        external_id="MIA",
        slug="miami-dolphins",
        name="Dolphins",
        abbreviation="MIA",
        city="Miami",
    )

    for week in [week_1, week_2, week_3]:
        game = Game.objects.create(
            external_id=f"2025_{week.number}_BUF_MIA",
            season=season,
            week=week,
            home_team=team,
            away_team=opponent,
            start_time="2025-09-01T18:00:00Z",
            status=Game.Status.FINAL,
            phase="regular_season",
        )

        NFLTeamGameStats.objects.create(
            game=game,
            team=team,
            offensive_passing_yards=200 + week.number,
        )

    stats = NFLDerivedStatsService.get_team_stats_through_week(
        team=team,
        week=week_2,
    )

    assert stats.count() == 2
    assert set(
        stats.values_list(
            "game__week__number",
            flat=True,
        )
    ) == {1, 2}


@pytest.mark.django_db
def test_get_team_stats_through_week_does_not_include_other_seasons():
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

    week_1_2024 = Week.objects.create(
        season=season_2024,
        number=1,
    )

    week_1_2025 = Week.objects.create(
        season=season_2025,
        number=1,
    )

    team = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        name="Bills",
        abbreviation="BUF",
        city="Buffalo",
    )

    opponent = Team.objects.create(
        external_id="MIA",
        slug="miami-dolphins",
        name="Dolphins",
        abbreviation="MIA",
        city="Miami",
    )

    game_2024 = Game.objects.create(
        external_id="2024_01_BUF_MIA",
        season=season_2024,
        week=week_1_2024,
        home_team=team,
        away_team=opponent,
        start_time="2024-09-01T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    game_2025 = Game.objects.create(
        external_id="2025_01_BUF_MIA",
        season=season_2025,
        week=week_1_2025,
        home_team=team,
        away_team=opponent,
        start_time="2025-09-01T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    NFLTeamGameStats.objects.create(
        game=game_2024,
        team=team,
        offensive_passing_yards=300,
    )

    NFLTeamGameStats.objects.create(
        game=game_2025,
        team=team,
        offensive_passing_yards=200,
    )

    stats = NFLDerivedStatsService.get_team_stats_through_week(
        team=team,
        week=week_1_2025,
    )

    assert stats.count() == 1
    assert stats.first().game == game_2025


@pytest.mark.django_db
def test_get_team_aggregate_through_week():
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

    week_1 = Week.objects.create(season=season, number=1)
    week_2 = Week.objects.create(season=season, number=2)

    team = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        name="Bills",
        abbreviation="BUF",
        city="Buffalo",
    )

    opponent = Team.objects.create(
        external_id="MIA",
        slug="miami-dolphins",
        name="Dolphins",
        abbreviation="MIA",
        city="Miami",
    )

    game_1 = Game.objects.create(
        external_id="2025_01_BUF_MIA",
        season=season,
        week=week_1,
        home_team=team,
        away_team=opponent,
        start_time="2025-09-01T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    game_2 = Game.objects.create(
        external_id="2025_02_MIA_BUF",
        season=season,
        week=week_2,
        home_team=opponent,
        away_team=team,
        start_time="2025-09-08T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    NFLTeamGameStats.objects.create(
        game=game_1,
        team=team,
        offensive_passing_yards=240,
        passing_attempts=30,
        passing_completions=20,
        offensive_rushing_yards=120,
        rushing_attempts=25,
        passing_epa=8.0,
        rushing_epa=2.0,
        defensive_passing_yards_allowed=200,
        defensive_rushing_yards_allowed=100,
        points_for=27,
        points_allowed=20,
        sacks_allowed=2,
        defensive_sacks=3,
        defensive_qb_hits=6,
        offensive_turnovers=1,
        defensive_turnovers_forced=2,
        passing_cpoe=4.0,
    )

    NFLTeamGameStats.objects.create(
        game=game_2,
        team=team,
        offensive_passing_yards=300,
        passing_attempts=40,
        passing_completions=30,
        offensive_rushing_yards=80,
        rushing_attempts=20,
        passing_epa=12.0,
        rushing_epa=-1.0,
        defensive_passing_yards_allowed=250,
        defensive_rushing_yards_allowed=90,
        points_for=31,
        points_allowed=24,
        sacks_allowed=1,
        defensive_sacks=4,
        defensive_qb_hits=8,
        offensive_turnovers=2,
        defensive_turnovers_forced=1,
        passing_cpoe=6.0,
    )

    aggregate = NFLDerivedStatsService.get_team_aggregate_through_week(
        team=team,
        week=week_2,
    )

    assert aggregate["games"] == 2

    assert aggregate["passing_yards"] == 540
    assert aggregate["passing_attempts"] == 70
    assert aggregate["passing_completions"] == 50

    assert aggregate["rushing_yards"] == 200
    assert aggregate["rushing_attempts"] == 45

    assert aggregate["passing_epa"] == 20.0
    assert aggregate["rushing_epa"] == 1.0

    assert aggregate["passing_yards_allowed"] == 450
    assert aggregate["rushing_yards_allowed"] == 190

    assert aggregate["points_for"] == 58
    assert aggregate["points_allowed"] == 44

    assert aggregate["sacks_allowed"] == 3
    assert aggregate["defensive_sacks"] == 7
    assert aggregate["defensive_qb_hits"] == 14

    assert aggregate["offensive_turnovers"] == 3
    assert aggregate["defensive_turnovers_forced"] == 3

    assert aggregate["average_cpoe"] == 5.0


def test_safe_divide_returns_result():
    assert NFLDerivedStatsService._safe_divide(10, 2) == 5


def test_safe_divide_returns_none_for_zero_denominator():
    assert NFLDerivedStatsService._safe_divide(10, 0) is None


def test_safe_divide_returns_none_for_none_denominator():
    assert NFLDerivedStatsService._safe_divide(10, None) is None


def test_safe_divide_returns_none_for_none_numerator():
    assert NFLDerivedStatsService._safe_divide(None, 10) is None


@pytest.mark.django_db
def test_get_team_efficiency_through_week():
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

    team = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        name="Bills",
        abbreviation="BUF",
        city="Buffalo",
    )

    opponent = Team.objects.create(
        external_id="MIA",
        slug="miami-dolphins",
        name="Dolphins",
        abbreviation="MIA",
        city="Miami",
    )

    game_1 = Game.objects.create(
        external_id="2025_01_BUF_MIA",
        season=season,
        week=week_1,
        home_team=team,
        away_team=opponent,
        start_time="2025-09-01T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    game_2 = Game.objects.create(
        external_id="2025_02_MIA_BUF",
        season=season,
        week=week_2,
        home_team=opponent,
        away_team=team,
        start_time="2025-09-08T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    NFLTeamGameStats.objects.create(
        game=game_1,
        team=team,
        offensive_passing_yards=240,
        passing_attempts=30,
        offensive_rushing_yards=120,
        rushing_attempts=24,
        defensive_passing_yards_allowed=180,
        opponent_passing_attempts=30,
        defensive_rushing_yards_allowed=80,
        opponent_rushing_attempts=20,
    )

    NFLTeamGameStats.objects.create(
        game=game_2,
        team=team,
        offensive_passing_yards=280,
        passing_attempts=40,
        offensive_rushing_yards=100,
        rushing_attempts=26,
        defensive_passing_yards_allowed=210,
        opponent_passing_attempts=30,
        defensive_rushing_yards_allowed=90,
        opponent_rushing_attempts=20,
    )

    efficiency = NFLDerivedStatsService.get_team_efficiency_through_week(
        team=team,
        week=week_2,
    )

    assert efficiency["pass_offense"] == pytest.approx(520 / 70)

    assert efficiency["rush_offense"] == pytest.approx(220 / 50)

    assert efficiency["pass_defense"] == pytest.approx(390 / 60)

    assert efficiency["rush_defense"] == pytest.approx(170 / 40)


@pytest.mark.django_db
def test_get_team_efficiency_returns_none_when_attempts_missing():
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

    team = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        name="Bills",
        abbreviation="BUF",
        city="Buffalo",
    )

    opponent = Team.objects.create(
        external_id="MIA",
        slug="miami-dolphins",
        name="Dolphins",
        abbreviation="MIA",
        city="Miami",
    )

    game = Game.objects.create(
        external_id="2025_01_BUF_MIA",
        season=season,
        week=week,
        home_team=team,
        away_team=opponent,
        start_time="2025-09-01T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    NFLTeamGameStats.objects.create(
        game=game,
        team=team,
        offensive_passing_yards=250,
        passing_attempts=None,
        offensive_rushing_yards=100,
        rushing_attempts=None,
        defensive_passing_yards_allowed=200,
        opponent_passing_attempts=None,
        defensive_rushing_yards_allowed=90,
        opponent_rushing_attempts=None,
    )

    efficiency = NFLDerivedStatsService.get_team_efficiency_through_week(
        team=team,
        week=week,
    )

    assert efficiency["pass_offense"] is None
    assert efficiency["rush_offense"] is None
    assert efficiency["pass_defense"] is None
    assert efficiency["rush_defense"] is None
