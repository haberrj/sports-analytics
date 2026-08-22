from unittest.mock import patch

import pytest

from games.models import Game, Season, Week
from stats.models import NFLTeamGameStats, NFLTeamProfile
from stats.nfl.derived import NFLDerivedStatsService
from teams.models import League, Team, TeamSeason


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

    assert strength == pytest.approx(0.20)


def test_relative_defensive_strength_worse_than_league_average():
    strength = NFLDerivedStatsService._relative_defensive_strength(
        team_value=7.5,
        league_value=6.0,
    )

    assert strength == pytest.approx(-0.25)


def test_relative_value_above_league_average():
    strength = NFLDerivedStatsService._relative_value(
        team_value=4.5,
        league_value=3.0,
    )

    assert strength == pytest.approx(1.5)


def test_relative_value_below_league_average():
    strength = NFLDerivedStatsService._relative_value(
        team_value=1.0,
        league_value=2.5,
    )

    assert strength == pytest.approx(-1.5)


def test_relative_value_returns_none_when_team_value_missing():
    strength = NFLDerivedStatsService._relative_value(
        team_value=None,
        league_value=2.5,
    )

    assert strength is None


def test_relative_value_returns_none_when_league_value_missing():
    strength = NFLDerivedStatsService._relative_value(
        team_value=2.5,
        league_value=None,
    )

    assert strength is None


@pytest.mark.django_db
def test_get_team_relative_metrics_through_week():
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
        offensive_passing_yards=300,
        passing_attempts=40,
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
        game=game,
        team=dolphins,
        offensive_passing_yards=200,
        passing_attempts=40,
        offensive_rushing_yards=80,
        rushing_attempts=20,
        passing_epa=2.0,
        rushing_epa=-2.0,
        defensive_passing_yards_allowed=300,
        opponent_passing_attempts=40,
        defensive_rushing_yards_allowed=120,
        opponent_rushing_attempts=24,
    )

    relative = NFLDerivedStatsService.get_team_relative_metrics_through_week(
        team=bills,
        week=week,
    )

    # League passing offense:
    # 500 / 80 = 6.25 Y/A
    #
    # Bills passing offense:
    # 300 / 40 = 7.5 Y/A
    #
    # 7.5 / 6.25 - 1 = 0.20
    assert relative["pass_offense_yards_per_attempt_strength"] == pytest.approx(0.20)

    # League rushing offense:
    # 200 / 44
    #
    # Bills rushing offense:
    # 120 / 24 = 5.0
    assert relative["rush_offense_yards_per_attempt_strength"] == pytest.approx((5.0 / (200 / 44)) - 1)

    # League passing volume:
    # 500 / 2 team-games = 250
    #
    # Bills passing volume:
    # 300 / 1 = 300
    assert relative["pass_offense_yards_per_game_strength"] == pytest.approx(0.20)

    # League rushing volume:
    # 200 / 2 = 100
    #
    # Bills:
    # 120
    assert relative["rush_offense_yards_per_game_strength"] == pytest.approx(0.20)

    # League passing EPA:
    # (8 + 2) / 2 = 5
    #
    # Bills:
    # 8
    #
    # Relative value = 8 - 5 = 3
    assert relative["pass_offense_epa_per_game_strength"] == pytest.approx(3.0)

    # League rushing EPA:
    # (2 + -2) / 2 = 0
    #
    # Bills:
    # 2
    assert relative["rush_offense_epa_per_game_strength"] == pytest.approx(2.0)

    # League passing defense:
    # 480 yards allowed / 70 opponent attempts
    #
    # Bills:
    # 180 / 30 = 6.0
    #
    # Defense is inverted:
    # league / team - 1
    assert relative["pass_defense_yards_per_attempt_strength"] == pytest.approx(1 - (6.0 / (480 / 70)))

    # League rushing defense:
    # 200 yards allowed / 44 opponent attempts
    #
    # Bills:
    # 80 / 20 = 4.0
    assert relative["rush_defense_yards_per_attempt_strength"] == pytest.approx(1 - (4.0 / (200 / 44)))

    # League passing yards allowed/game:
    # 480 / 2 = 240
    #
    # Bills:
    # 180
    assert relative["pass_defense_yards_per_game_strength"] == pytest.approx(1 - (180 / 240))

    # League rushing yards allowed/game:
    # 200 / 2 = 100
    #
    # Bills:
    # 80
    assert relative["rush_defense_yards_per_game_strength"] == pytest.approx(1 - (80 / 100))


@pytest.mark.django_db
def test_get_team_relative_metrics_handles_missing_data():
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
        offensive_passing_yards=250,
        passing_attempts=None,
        offensive_rushing_yards=100,
        rushing_attempts=20,
        passing_epa=None,
        rushing_epa=1.0,
        defensive_passing_yards_allowed=200,
        opponent_passing_attempts=None,
        defensive_rushing_yards_allowed=80,
        opponent_rushing_attempts=20,
    )

    NFLTeamGameStats.objects.create(
        game=game,
        team=dolphins,
        offensive_passing_yards=200,
        passing_attempts=30,
        offensive_rushing_yards=80,
        rushing_attempts=20,
        passing_epa=4.0,
        rushing_epa=1.0,
        defensive_passing_yards_allowed=250,
        opponent_passing_attempts=None,
        defensive_rushing_yards_allowed=100,
        opponent_rushing_attempts=20,
    )

    relative = NFLDerivedStatsService.get_team_relative_metrics_through_week(
        team=bills,
        week=week,
    )

    assert relative["pass_offense_yards_per_attempt_strength"] is None

    assert relative["pass_defense_yards_per_attempt_strength"] is None

    assert relative["pass_offense_epa_per_game_strength"] is None

    # Independent metrics should still calculate.
    assert relative["rush_offense_yards_per_attempt_strength"] is not None

    assert relative["rush_defense_yards_per_attempt_strength"] is not None


@pytest.mark.django_db
@patch.object(
    NFLDerivedStatsService,
    "get_team_relative_metrics_through_week",
)
@patch.object(
    NFLDerivedStatsService,
    "get_team_metrics_through_week",
)
def test_update_team_profile_through_week(
    mock_get_metrics,
    mock_get_relative_metrics,
):
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

    team = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        name="Bills",
        abbreviation="BUF",
        city="Buffalo",
    )

    TeamSeason.objects.create(
        team=team,
        season=season,
        name="Bills",
        abbreviation="BUF",
        city="Buffalo",
    )

    mock_get_metrics.return_value = {
        "pass_offense_yards_per_attempt": 7.5,
        "rush_offense_yards_per_attempt": 4.8,
        "pass_defense_yards_per_attempt": 6.1,
        "rush_defense_yards_per_attempt": 3.9,
        "pass_offense_yards_per_game": 270.0,
        "rush_offense_yards_per_game": 125.0,
        "pass_defense_yards_per_game": 215.0,
        "rush_defense_yards_per_game": 92.0,
        "pass_offense_epa_per_game": 6.4,
        "rush_offense_epa_per_game": 1.8,
    }

    mock_get_relative_metrics.return_value = {
        "pass_offense_yards_per_attempt_strength": 0.12,
        "pass_offense_yards_per_game_strength": 0.09,
        "pass_offense_epa_per_game_strength": 1.4,
        "rush_offense_yards_per_attempt_strength": 0.05,
        "rush_offense_yards_per_game_strength": 0.02,
        "rush_offense_epa_per_game_strength": 0.4,
        "pass_defense_yards_per_attempt_strength": 0.08,
        "pass_defense_yards_per_game_strength": 0.06,
        "rush_defense_yards_per_attempt_strength": 0.17,
        "rush_defense_yards_per_game_strength": 0.11,
    }

    profile = NFLDerivedStatsService.update_team_profile_through_week(
        team=team,
        week=week,
    )

    assert NFLTeamProfile.objects.count() == 1

    assert profile.team == team
    assert profile.season == season
    assert profile.through_week == week

    assert profile.pass_offense_yards_per_attempt == 7.5
    assert profile.rush_offense_yards_per_attempt == 4.8
    assert profile.pass_defense_yards_per_attempt == 6.1
    assert profile.rush_defense_yards_per_attempt == 3.9

    assert profile.pass_offense_yards_per_game == 270.0
    assert profile.rush_offense_yards_per_game == 125.0
    assert profile.pass_defense_yards_per_game == 215.0
    assert profile.rush_defense_yards_per_game == 92.0

    assert profile.pass_offense_epa_per_game == 6.4
    assert profile.rush_offense_epa_per_game == 1.8

    assert profile.pass_offense_yards_per_attempt_strength == 0.12
    assert profile.pass_offense_yards_per_game_strength == 0.09
    assert profile.pass_offense_epa_per_game_strength == 1.4

    assert profile.rush_offense_yards_per_attempt_strength == 0.05
    assert profile.rush_offense_yards_per_game_strength == 0.02
    assert profile.rush_offense_epa_per_game_strength == 0.4

    assert profile.pass_defense_yards_per_attempt_strength == 0.08
    assert profile.pass_defense_yards_per_game_strength == 0.06

    assert profile.rush_defense_yards_per_attempt_strength == 0.17
    assert profile.rush_defense_yards_per_game_strength == 0.11


@pytest.mark.django_db
@patch.object(
    NFLDerivedStatsService,
    "get_team_relative_metrics_through_week",
)
@patch.object(
    NFLDerivedStatsService,
    "get_team_metrics_through_week",
)
def test_update_team_profile_through_week_is_idempotent(
    mock_get_metrics,
    mock_get_relative_metrics,
):
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

    team = Team.objects.create(
        external_id="BUF",
        slug="buffalo-bills",
        name="Bills",
        abbreviation="BUF",
        city="Buffalo",
    )

    TeamSeason.objects.create(
        team=team,
        season=season,
        name="Bills",
        abbreviation="BUF",
        city="Buffalo",
    )

    mock_get_metrics.return_value = {
        "pass_offense_yards_per_attempt": 7.5,
        "rush_offense_yards_per_attempt": 4.8,
        "pass_defense_yards_per_attempt": 6.1,
        "rush_defense_yards_per_attempt": 3.9,
        "pass_offense_yards_per_game": 270.0,
        "rush_offense_yards_per_game": 125.0,
        "pass_defense_yards_per_game": 215.0,
        "rush_defense_yards_per_game": 92.0,
        "pass_offense_epa_per_game": 6.4,
        "rush_offense_epa_per_game": 1.8,
    }

    mock_get_relative_metrics.return_value = {
        "pass_offense_yards_per_attempt_strength": 0.12,
        "pass_offense_yards_per_game_strength": 0.09,
        "pass_offense_epa_per_game_strength": 1.4,
        "rush_offense_yards_per_attempt_strength": 0.05,
        "rush_offense_yards_per_game_strength": 0.02,
        "rush_offense_epa_per_game_strength": 0.4,
        "pass_defense_yards_per_attempt_strength": 0.08,
        "pass_defense_yards_per_game_strength": 0.06,
        "rush_defense_yards_per_attempt_strength": 0.17,
        "rush_defense_yards_per_game_strength": 0.11,
    }

    NFLDerivedStatsService.update_team_profile_through_week(
        team=team,
        week=week,
    )

    mock_get_metrics.return_value["pass_offense_yards_per_attempt"] = 8.0

    NFLDerivedStatsService.update_team_profile_through_week(
        team=team,
        week=week,
    )

    assert NFLTeamProfile.objects.count() == 1

    profile = NFLTeamProfile.objects.get(
        team=team,
        season=season,
        through_week=week,
    )

    assert profile.pass_offense_yards_per_attempt == 8.0


@pytest.mark.django_db
def test_update_profiles_through_week_creates_profiles_for_teams_with_stats():
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

    jets = Team.objects.create(
        external_id="NYJ",
        slug="new-york-jets",
        name="Jets",
        abbreviation="NYJ",
        city="New York",
    )

    for team in [bills, dolphins, jets]:
        TeamSeason.objects.create(
            team=team,
            season=season,
            name=team.name,
            abbreviation=team.abbreviation,
            city=team.city,
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
        offensive_passing_yards=300,
        passing_attempts=40,
        offensive_rushing_yards=120,
        rushing_attempts=24,
        passing_epa=8.0,
        rushing_epa=2.0,
        defensive_passing_yards_allowed=200,
        opponent_passing_attempts=40,
        defensive_rushing_yards_allowed=80,
        opponent_rushing_attempts=20,
    )

    NFLTeamGameStats.objects.create(
        game=game,
        team=dolphins,
        offensive_passing_yards=200,
        passing_attempts=40,
        offensive_rushing_yards=80,
        rushing_attempts=20,
        passing_epa=2.0,
        rushing_epa=-2.0,
        defensive_passing_yards_allowed=300,
        opponent_passing_attempts=40,
        defensive_rushing_yards_allowed=120,
        opponent_rushing_attempts=24,
    )

    profiles = NFLDerivedStatsService.update_profiles_through_week(
        week=week,
    )

    assert len(profiles) == 2
    assert NFLTeamProfile.objects.count() == 2

    assert {profile.team for profile in profiles} == {
        bills,
        dolphins,
    }

    assert NFLTeamProfile.objects.filter(
        team=bills,
        season=season,
        through_week=week,
    ).exists()

    assert NFLTeamProfile.objects.filter(
        team=dolphins,
        season=season,
        through_week=week,
    ).exists()

    assert not NFLTeamProfile.objects.filter(
        team=jets,
        season=season,
        through_week=week,
    ).exists()


@pytest.mark.django_db
def test_update_profiles_through_week_excludes_teams_with_only_future_stats():
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

    jets = Team.objects.create(
        external_id="NYJ",
        slug="new-york-jets",
        name="Jets",
        abbreviation="NYJ",
        city="New York",
    )

    patriots = Team.objects.create(
        external_id="NE",
        slug="new-england-patriots",
        name="Patriots",
        abbreviation="NE",
        city="New England",
    )

    for team in [bills, dolphins, jets, patriots]:
        TeamSeason.objects.create(
            team=team,
            season=season,
            name=team.name,
            abbreviation=team.abbreviation,
            city=team.city,
        )

    week_1_game = Game.objects.create(
        external_id="2025_01_BUF_MIA",
        season=season,
        week=week_1,
        home_team=bills,
        away_team=dolphins,
        start_time="2025-09-01T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    week_2_game = Game.objects.create(
        external_id="2025_02_NYJ_NE",
        season=season,
        week=week_2,
        home_team=jets,
        away_team=patriots,
        start_time="2025-09-08T18:00:00Z",
        status=Game.Status.FINAL,
        phase="regular_season",
    )

    NFLTeamGameStats.objects.create(
        game=week_1_game,
        team=bills,
        offensive_passing_yards=300,
        passing_attempts=40,
        offensive_rushing_yards=120,
        rushing_attempts=24,
        passing_epa=8.0,
        rushing_epa=2.0,
        defensive_passing_yards_allowed=200,
        opponent_passing_attempts=40,
        defensive_rushing_yards_allowed=80,
        opponent_rushing_attempts=20,
    )

    NFLTeamGameStats.objects.create(
        game=week_1_game,
        team=dolphins,
        offensive_passing_yards=200,
        passing_attempts=40,
        offensive_rushing_yards=80,
        rushing_attempts=20,
        passing_epa=2.0,
        rushing_epa=-2.0,
        defensive_passing_yards_allowed=300,
        opponent_passing_attempts=40,
        defensive_rushing_yards_allowed=120,
        opponent_rushing_attempts=24,
    )

    NFLTeamGameStats.objects.create(
        game=week_2_game,
        team=jets,
        offensive_passing_yards=250,
        passing_attempts=35,
        offensive_rushing_yards=110,
        rushing_attempts=25,
        passing_epa=4.0,
        rushing_epa=1.0,
        defensive_passing_yards_allowed=220,
        opponent_passing_attempts=32,
        defensive_rushing_yards_allowed=95,
        opponent_rushing_attempts=22,
    )

    NFLTeamGameStats.objects.create(
        game=week_2_game,
        team=patriots,
        offensive_passing_yards=220,
        passing_attempts=32,
        offensive_rushing_yards=95,
        rushing_attempts=22,
        passing_epa=3.0,
        rushing_epa=0.5,
        defensive_passing_yards_allowed=250,
        opponent_passing_attempts=35,
        defensive_rushing_yards_allowed=110,
        opponent_rushing_attempts=25,
    )

    profiles = NFLDerivedStatsService.update_profiles_through_week(
        week=week_1,
    )

    assert len(profiles) == 2

    assert {profile.team for profile in profiles} == {
        bills,
        dolphins,
    }

    assert not NFLTeamProfile.objects.filter(
        team=jets,
        through_week=week_1,
    ).exists()

    assert not NFLTeamProfile.objects.filter(
        team=patriots,
        through_week=week_1,
    ).exists()
