from datetime import datetime
from zoneinfo import ZoneInfo

import nflreadpy as nfl
from polars import DataFrame

from games.models import Game, Season, Week
from ingestion.models import IngestionState
from ingestion.nfl.base import NFLIngestor
from teams.models import League, Team, TeamSeason


class NFLGameIngestor(NFLIngestor):
    dataset = IngestionState.Dataset.GAMES

    NFL_PHASES = {
        "PRE": "preseason",
        "REG": "regular_season",
        "WC": "wild_card",
        "DIV": "divisional",
        "CON": "conference_championship",
        "SB": "championship",
    }

    POSTSEASON_WEEK_NAMES = {
        "WC": "Wild Card",
        "DIV": "Divisional",
        "CON": "Conference Championship",
        "SB": "Super Bowl",
    }

    def __init__(self, season: int | None = None, force: bool = False) -> None:
        super().__init__(season, force)
        self.schedule: DataFrame

    def ingest(self) -> bool:
        league = League.objects.get(abbreviation="NFL")
        season = Season.objects.get(
            league__abbreviation="NFL",
            name=str(self.season),
        )

        if season is not None and not self.should_ingest(season):
            return False

        self.schedule = nfl.load_schedules([self.season])
        season = self._update_or_create_season(league)

        for game_data in self.schedule.iter_rows(named=True):
            week = self._update_or_create_week(season, game_data)
            home_team = self._get_team(season=season, abbreviation=game_data["home_team"])
            away_team = self._get_team(season=season, abbreviation=game_data["away_team"])
            self._update_or_create_game(
                season=season, week=week, home_team=home_team, away_team=away_team, game_data=game_data
            )
        self.complete(season)
        return True

    def _update_or_create_season(self, league: League) -> Season:
        game_dates = [
            datetime.strptime(date_value, "%Y-%m-%d").date()
            for date_value in self.schedule["gameday"].drop_nulls().to_list()
        ]

        season, _ = Season.objects.update_or_create(
            league=league,
            name=str(self.season),
            defaults={
                "start_date": min(game_dates),
                "end_date": max(game_dates),
            },
        )

        return season

    def _update_or_create_week(self, season: Season, game_data: dict) -> Week:
        week_number = game_data["week"]
        game_type = game_data["game_type"]

        week, _ = Week.objects.update_or_create(
            season=season,
            number=week_number,
            defaults={
                "name": self.POSTSEASON_WEEK_NAMES.get(game_type, ""),
            },
        )

        return week

    def _get_team(self, season: Season, abbreviation: str) -> Team:
        return (
            TeamSeason.objects.select_related("team")
            .get(
                season=season,
                abbreviation=abbreviation,
            )
            .team
        )

    def _update_or_create_game(
        self, season: Season, week: Week, home_team: Team, away_team: Team, game_data: dict
    ) -> Game:
        game, _ = Game.objects.update_or_create(
            external_id=game_data["game_id"],
            defaults={
                "season": season,
                "week": week,
                "home_team": home_team,
                "away_team": away_team,
                "start_time": self._get_start_time(game_data),
                "home_score": game_data["home_score"],
                "away_score": game_data["away_score"],
                "status": self._get_status(game_data),
                "phase": self._get_phase(game_data),
                "finish_type": self._get_finish_type(game_data),
                "neutral_site": game_data["location"] == "Neutral",
            },
        )

        return game

    def _get_phase(self, game_data: dict) -> str:
        game_type = game_data["game_type"]

        if game_type not in self.NFL_PHASES:
            raise ValueError(f"Unknown NFL game type: {game_type}")

        return self.NFL_PHASES[game_type]

    @staticmethod
    def _get_status(game_data: dict) -> str:
        if game_data["home_score"] is None or game_data["away_score"] is None:
            return Game.Status.SCHEDULED

        return Game.Status.FINAL

    @staticmethod
    def _get_finish_type(game_data: dict) -> str | None:
        if game_data["home_score"] is None or game_data["away_score"] is None:
            return None

        if game_data["overtime"] == 1:
            return Game.FinishType.OVERTIME

        return Game.FinishType.REGULATION

    @staticmethod
    def _get_start_time(game_data: dict) -> datetime | None:
        if not game_data["gametime"]:
            return None

        naive = datetime.strptime(
            f"{game_data['gameday']} {game_data['gametime']}",
            "%Y-%m-%d %H:%M",
        )

        return naive.replace(tzinfo=ZoneInfo("America/New_York"))
