from datetime import date

import nflreadpy as nfl
from django.utils.text import slugify
from polars import DataFrame

from games.models import Season
from ingestion.nfl.base import NFLIngestor
from teams.models import Conference, Division, League, Team, TeamSeason


class NFLTeamIngestor(NFLIngestor):
    """
    Ingests NFL league structure and current franchise data from nflverse.

    The selected season determines which team aliases are considered active,
    allowing historical franchise identities such as STL/LAR or OAK/LV to be
    resolved correctly.

    Running ingestion repeatedly should be idempotent.
    """

    def __init__(self, season: int | None = None) -> None:
        super().__init__(season)
        self.is_current_season: bool = self.season == self.get_current_season()
        self.teams: DataFrame = nfl.load_teams()

    def ingest(self) -> None:
        league = self._get_or_create_league()
        season = self._get_or_create_season(league)
        season_teams = self._get_season_franchises()

        for team_data in season_teams.iter_rows(named=True):
            conference = self._get_or_create_conference(league, team_data)
            division = self._get_or_create_division(conference, team_data)
            team = self._update_or_create_team(team_data)
            self._update_or_create_team_season(
                team=team, division=division, conference=conference, season=season, team_data=team_data
            )

    def _get_or_create_league(self) -> League:
        league, _ = League.objects.update_or_create(
            abbreviation="NFL",
            defaults={
                "name": "National Football League",
            },
        )

        return league

    def _get_or_create_conference(self, league, team_data) -> Conference:
        conference, _ = Conference.objects.update_or_create(
            league=league,
            abbreviation=team_data["team_conf"],
            defaults={
                "name": team_data["team_conf"],
            },
        )

        return conference

    def _get_or_create_division(self, conference, team_data) -> Division:
        division_name = team_data["team_division"].removeprefix(f"{team_data['team_conf']} ")

        division, _ = Division.objects.update_or_create(
            conference=conference,
            abbreviation=division_name.upper(),
            defaults={
                "name": division_name,
            },
        )

        return division

    def _update_or_create_team(self, team_data) -> Team:
        defaults = {
            "slug": slugify(team_data["team_name"]),
            "name": team_data["team_nick"],
            "abbreviation": team_data["team_abbr"],
            "city": self._get_city(
                team_data["team_name"],
                team_data["team_nick"],
            ),
            "active": True,
        }
        if self.is_current_season:
            team, _ = Team.objects.update_or_create(
                external_id=team_data["team_id"],
                defaults=defaults,
            )
        else:
            team, _ = Team.objects.get_or_create(
                external_id=team_data["team_id"],
                defaults=defaults,
            )
        return team

    def _get_season_franchises(self) -> DataFrame:
        schedules = nfl.load_schedules([self.season])

        active_abbreviations = set(schedules["home_team"].to_list() + schedules["away_team"].to_list())

        return self.teams.filter(self.teams["team_abbr"].is_in(active_abbreviations))

    def _get_or_create_season(self, league: League) -> Season:
        season, _ = Season.objects.update_or_create(
            league=league,
            name=str(self.season),
            defaults={
                "start_date": date(self.season, 9, 1),  # Expanded season hard coded dates to be changed later
                "end_date": date(self.season + 1, 2, 28),
            },
        )
        return season

    def _update_or_create_team_season(
        self, team: Team, season: Season, conference: Conference, division: Division, team_data: DataFrame
    ) -> TeamSeason:
        team_season, _ = TeamSeason.objects.update_or_create(
            team=team,
            season=season,
            defaults={
                "conference": conference,
                "division": division,
                "name": team_data["team_nick"],
                "abbreviation": team_data["team_abbr"],
                "city": self._get_city(team_data["team_name"], team_data["team_nick"]),
            },
        )
        return team_season

    @staticmethod
    def _get_city(team_name, nickname) -> str:
        return team_name.removesuffix(nickname).strip()
