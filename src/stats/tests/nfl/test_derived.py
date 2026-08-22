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
        passing_completions=20,
        offensive_rushing_yards=120,
        rushing_attempts=25,
        passing_epa=8.0,
        rushing_epa=2.0,
        defensive_passing_yards_allowed=200,
        opponent_passing_attempts=32,
        defensive_rushing_yards_allowed=100,
        opponent_rushing_attempts=22,
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
        opponent_passing_attempts=38,
        defensive_rushing_yards_allowed=90,
        opponent_rushing_attempts=24,
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

    assert aggregate["team_games"] == 2

    assert aggregate["passing_yards"] == 540
    assert aggregate["passing_attempts"] == 70
    assert aggregate["passing_completions"] == 50

    assert aggregate["rushing_yards"] == 200
    assert aggregate["rushing_attempts"] == 45

    assert aggregate["passing_epa"] == 20.0
    assert aggregate["rushing_epa"] == 1.0

    assert aggregate["passing_yards_allowed"] == 450
    assert aggregate["rushing_yards_allowed"] == 190

    assert aggregate["opponent_passing_attempts"] == 70
    assert aggregate["opponent_rushing_attempts"] == 46

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
def test_get_team_metrics_through_week():
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
        passing_epa=8.0,
        rushing_epa=2.0,
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
        passing_epa=12.0,
        rushing_epa=-1.0,
        defensive_passing_yards_allowed=210,
        opponent_passing_attempts=30,
        defensive_rushing_yards_allowed=90,
        opponent_rushing_attempts=20,
    )

    metrics = NFLDerivedStatsService.get_team_metrics_through_week(
        team=team,
        week=week_2,
    )

    # Efficiency
    assert metrics["pass_offense_yards_per_attempt"] == pytest.approx(520 / 70)
    assert metrics["rush_offense_yards_per_attempt"] == pytest.approx(220 / 50)
    assert metrics["pass_defense_yards_per_attempt"] == pytest.approx(390 / 60)
    assert metrics["rush_defense_yards_per_attempt"] == pytest.approx(170 / 40)

    # Volume
    assert metrics["pass_offense_yards_per_game"] == pytest.approx(520 / 2)
    assert metrics["rush_offense_yards_per_game"] == pytest.approx(220 / 2)
    assert metrics["pass_defense_yards_per_game"] == pytest.approx(390 / 2)
    assert metrics["rush_defense_yards_per_game"] == pytest.approx(170 / 2)

    # Value
    assert metrics["pass_offense_epa_per_game"] == pytest.approx(20 / 2)
    assert metrics["rush_offense_epa_per_game"] == pytest.approx(1 / 2)


@pytest.mark.django_db
def test_get_team_metrics_handles_missing_attempts():
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
        passing_epa=6.0,
        rushing_epa=1.0,
        defensive_passing_yards_allowed=200,
        opponent_passing_attempts=None,
        defensive_rushing_yards_allowed=90,
        opponent_rushing_attempts=None,
    )

    metrics = NFLDerivedStatsService.get_team_metrics_through_week(
        team=team,
        week=week,
    )

    # Efficiency requires attempt counts.
    assert metrics["pass_offense_yards_per_attempt"] is None
    assert metrics["rush_offense_yards_per_attempt"] is None
    assert metrics["pass_defense_yards_per_attempt"] is None
    assert metrics["rush_defense_yards_per_attempt"] is None

    # Volume remains calculable.
    assert metrics["pass_offense_yards_per_game"] == pytest.approx(250)
    assert metrics["rush_offense_yards_per_game"] == pytest.approx(100)
    assert metrics["pass_defense_yards_per_game"] == pytest.approx(200)
    assert metrics["rush_defense_yards_per_game"] == pytest.approx(90)

    # EPA remains calculable.
    assert metrics["pass_offense_epa_per_game"] == pytest.approx(6.0)
    assert metrics["rush_offense_epa_per_game"] == pytest.approx(1.0)


@pytest.mark.django_db
def test_get_league_stats_through_week_only_returns_prior_games():
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
        name="Bills",
        abbreviation="BUF",
        city="Buffalo",
    )

    dolphins = Team.objects.create(
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
        home_team=bills,
        away_team=dolphins,
        start_time="2025-09-01T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    game_2 = Game.objects.create(
        external_id="2025_02_MIA_BUF",
        season=season,
        week=week_2,
        home_team=dolphins,
        away_team=bills,
        start_time="2025-09-08T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    for game in [game_1, game_2]:
        NFLTeamGameStats.objects.create(
            game=game,
            team=bills,
        )
        NFLTeamGameStats.objects.create(
            game=game,
            team=dolphins,
        )

    stats = NFLDerivedStatsService.get_league_stats_through_week(
        week=week_1,
    )

    assert stats.count() == 2
    assert set(
        stats.values_list(
            "game__week__number",
            flat=True,
        )
    ) == {1}


@pytest.mark.django_db
def test_get_league_metrics_through_week():
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
        name="Bills",
        abbreviation="BUF",
        city="Buffalo",
    )

    dolphins = Team.objects.create(
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
        home_team=bills,
        away_team=dolphins,
        start_time="2025-09-01T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    NFLTeamGameStats.objects.create(
        game=game,
        team=bills,
        offensive_passing_yards=280,
        passing_attempts=40,
        offensive_rushing_yards=120,
        rushing_attempts=30,
        passing_epa=10.0,
        rushing_epa=2.0,
        defensive_passing_yards_allowed=210,
        opponent_passing_attempts=30,
        defensive_rushing_yards_allowed=90,
        opponent_rushing_attempts=25,
    )

    NFLTeamGameStats.objects.create(
        game=game,
        team=dolphins,
        offensive_passing_yards=210,
        passing_attempts=30,
        offensive_rushing_yards=90,
        rushing_attempts=25,
        passing_epa=4.0,
        rushing_epa=-1.0,
        defensive_passing_yards_allowed=280,
        opponent_passing_attempts=40,
        defensive_rushing_yards_allowed=120,
        opponent_rushing_attempts=30,
    )

    metrics = NFLDerivedStatsService.get_league_metrics_through_week(
        week=week,
    )

    # League totals:
    #
    # Passing:
    # 490 yards / 70 attempts
    #
    # Rushing:
    # 210 yards / 55 attempts
    #
    # There are 2 team-games.

    # Efficiency
    assert metrics["pass_offense_yards_per_attempt"] == pytest.approx(490 / 70)

    assert metrics["rush_offense_yards_per_attempt"] == pytest.approx(210 / 55)

    assert metrics["pass_defense_yards_per_attempt"] == pytest.approx(490 / 70)

    assert metrics["rush_defense_yards_per_attempt"] == pytest.approx(210 / 55)

    # Volume
    assert metrics["pass_offense_yards_per_game"] == pytest.approx(490 / 2)

    assert metrics["rush_offense_yards_per_game"] == pytest.approx(210 / 2)

    assert metrics["pass_defense_yards_per_game"] == pytest.approx(490 / 2)

    assert metrics["rush_defense_yards_per_game"] == pytest.approx(210 / 2)

    # Value
    assert metrics["pass_offense_epa_per_game"] == pytest.approx(14 / 2)

    assert metrics["rush_offense_epa_per_game"] == pytest.approx(1 / 2)


def test_relative_offensive_strength_above_league_average():
    strength = NFLDerivedStatsService._relative_offensive_strength(
        team_value=7.5,
        league_value=6.0,
    )

    assert strength == pytest.approx(0.25)


def test_relative_offensive_strength_below_league_average():
    strength = NFLDerivedStatsService._relative_offensive_strength(
        team_value=6.0,
        league_value=7.5,
    )

    assert strength == pytest.approx(-0.20)


def test_relative_defensive_strength_better_than_league_average():
    strength = NFLDerivedStatsService._relative_defensive_strength(
        team_value=6.0,
        league_value=7.5,
    )

    assert strength == pytest.approx(0.25)


def test_relative_defensive_strength_worse_than_league_average():
    strength = NFLDerivedStatsService._relative_defensive_strength(
        team_value=7.5,
        league_value=6.0,
    )

    assert strength == pytest.approx(-0.20)
