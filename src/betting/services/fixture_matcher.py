from dataclasses import dataclass
from datetime import timedelta

from django.utils.dateparse import parse_datetime

from betting.models import ExternalGameMapping, ExternalTeamMapping
from games.models import Game


@dataclass(frozen=True)
class FixtureMatchResult:
    fixture_id: str
    matched: bool
    game_id: int | None = None
    reason: str | None = None


class FixtureMatcher:
    def __init__(self, *, start_time_tolerance_minutes: int = 30) -> None:
        self.start_time_tolerance = timedelta(minutes=start_time_tolerance_minutes)

    def match_fixture(self, fixture_payload: dict) -> FixtureMatchResult:
        fixture_id = fixture_payload["fixtureId"]

        existing_mapping = ExternalGameMapping.objects.filter(
            provider=ExternalGameMapping.Provider.ODDSPAPI,
            external_fixture_id=fixture_id,
        ).first()

        if existing_mapping is not None:
            return FixtureMatchResult(
                fixture_id=fixture_id,
                matched=True,
                game_id=existing_mapping.game_id,
                reason="already_mapped",
            )

        start_time = parse_datetime(fixture_payload["startTime"])

        if start_time is None:
            return FixtureMatchResult(
                fixture_id=fixture_id,
                matched=False,
                reason="invalid_start_time",
            )

        participant1_id = str(fixture_payload["participant1Id"])
        participant2_id = str(fixture_payload["participant2Id"])

        participant1_mapping = ExternalTeamMapping.objects.filter(
            provider=ExternalTeamMapping.Provider.ODDSPAPI,
            external_team_id=participant1_id,
        ).first()

        participant2_mapping = ExternalTeamMapping.objects.filter(
            provider=ExternalTeamMapping.Provider.ODDSPAPI,
            external_team_id=participant2_id,
        ).first()

        if participant1_mapping is None or participant2_mapping is None:
            return FixtureMatchResult(
                fixture_id=fixture_id,
                matched=False,
                reason="missing_team_mapping",
            )

        minimum_start = start_time - self.start_time_tolerance
        maximum_start = start_time + self.start_time_tolerance

        matches = list(
            Game.objects.filter(
                home_team=participant1_mapping.team,
                away_team=participant2_mapping.team,
                start_time__gte=minimum_start,
                start_time__lte=maximum_start,
            )
        )

        if len(matches) == 0:
            return FixtureMatchResult(
                fixture_id=fixture_id,
                matched=False,
                reason="no_match",
            )

        if len(matches) > 1:
            return FixtureMatchResult(
                fixture_id=fixture_id,
                matched=False,
                reason="ambiguous_match",
            )

        game = matches[0]

        ExternalGameMapping.objects.create(
            game=game,
            provider=ExternalGameMapping.Provider.ODDSPAPI,
            external_fixture_id=fixture_id,
        )

        return FixtureMatchResult(
            fixture_id=fixture_id,
            matched=True,
            game_id=game.id,
            reason="matched",
        )

    def match_payload(
        self,
        payload: list[dict],
    ) -> list[FixtureMatchResult]:
        return [self.match_fixture(fixture_payload) for fixture_payload in payload]
