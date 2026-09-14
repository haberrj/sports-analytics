from dataclasses import dataclass
from decimal import Decimal

from django.utils.dateparse import parse_datetime

from betting.models import ExternalGameMapping, OddsSnapshot, SportsbookFixture, SportsbookRegion
from betting.services.market_catalog import MarketCatalog, MarketDefinition


@dataclass(frozen=True)
class OddsImportResult:
    fixtures_seen: int = 0
    fixtures_matched: int = 0
    fixtures_unmatched: int = 0
    snapshots_created: int = 0
    snapshots_existing: int = 0


class OddsImporter:
    MARKET_TYPES = {
        "moneyline": OddsSnapshot.MarketType.MONEYLINE,
        "spreads": OddsSnapshot.MarketType.SPREAD,
        "totals": OddsSnapshot.MarketType.TOTAL,
    }

    OUTCOME_SIDES = {
        "1": OddsSnapshot.Side.HOME,
        "2": OddsSnapshot.Side.AWAY,
        "over": OddsSnapshot.Side.OVER,
        "under": OddsSnapshot.Side.UNDER,
    }

    def __init__(self, *, market_catalog: MarketCatalog, sportsbook_region: SportsbookRegion, bookmaker: str) -> None:
        self.market_catalog: MarketCatalog = market_catalog
        self.sportsbook_region: SportsbookRegion = sportsbook_region
        self.bookmaker: str = bookmaker

    def import_payload(self, payload: list[dict]) -> OddsImportResult:
        matched = 0
        unmatched = 0
        created = 0
        existing = 0

        for fixture_payload in payload:
            fixture_id = fixture_payload["fixtureId"]
            mapping = (
                ExternalGameMapping.objects.filter(
                    provider=ExternalGameMapping.Provider.ODDSPAPI, external_fixture_id=fixture_id
                )
                .select_related("game")
                .first()
            )

            if mapping is None:
                unmatched += 1
                continue

            matched += 1
            bookmaker_payload = fixture_payload.get("bookmakerOdds", {}).get(self.bookmaker)

            if not bookmaker_payload:
                continue

            if not bookmaker_payload.get("bookmakerIsActive", True) or bookmaker_payload.get("suspended", False):
                continue

            sportsbook_fixture, _ = SportsbookFixture.objects.update_or_create(
                game=mapping.game,
                sportsbook_region=self.sportsbook_region,
                defaults={
                    "external_fixture_id": bookmaker_payload.get("bookmakerFixtureId"),
                    "event_url": bookmaker_payload.get("fixturePath"),
                },
            )

            for market_id, market_payload in bookmaker_payload.get("markets", {}).items():
                if not market_payload.get("marketActive", True):
                    continue
                definition = self.market_catalog.get(int(market_id))
                if definition is None:
                    continue
                market_type = self.MARKET_TYPES.get(definition.market_type)
                if market_type is None:
                    continue
                market_created, market_existing = self._import_market(
                    sportsbook_fixture=sportsbook_fixture,
                    definition=definition,
                    market_payload=market_payload,
                    market_type=market_type,
                )

                created += market_created
                existing += market_existing

        return OddsImportResult(
            fixtures_seen=len(payload),
            fixtures_matched=matched,
            fixtures_unmatched=unmatched,
            snapshots_created=created,
            snapshots_existing=existing,
        )

    def _import_market(
        self,
        *,
        sportsbook_fixture: SportsbookFixture,
        definition: MarketDefinition,
        market_payload: dict,
        market_type: str,
    ) -> tuple[int, int]:
        created = 0
        existing = 0

        for outcome_id, outcome_payload in market_payload.get("outcomes", {}).items():
            outcome_name = definition.outcomes.get(int(outcome_id))

            if outcome_name is None:
                continue

            side = self.OUTCOME_SIDES.get(outcome_name.lower())

            if side is None:
                continue

            player_payload = outcome_payload.get("players", {}).get("0")

            if not player_payload:
                continue

            if not player_payload.get("active", True):
                continue

            changed_at = parse_datetime(player_payload["changedAt"])

            if changed_at is None:
                raise ValueError(f"Invalid OddsPapi changedAt: {player_payload['changedAt']}")

            line = self._line_for_outcome(definition=definition, market_type=market_type, side=side)

            external_market_id = str(market_payload.get("bookmakerMarketId", definition.market_id))

            external_outcome_id = str(player_payload.get("bookmakerOutcomeId", outcome_id))

            _, was_created = OddsSnapshot.objects.get_or_create(
                sportsbook_fixture=sportsbook_fixture,
                external_market_id=external_market_id,
                external_outcome_id=external_outcome_id,
                source_changed_at=changed_at,
                defaults={
                    "market_type": market_type,
                    "side": side,
                    "line": line,
                    "decimal_odds": Decimal(str(player_payload["price"])),
                    "american_odds": self._american_odds(player_payload.get("priceAmerican")),
                    "betslip_url": player_payload.get("betslip"),
                },
            )

            if was_created:
                created += 1
            else:
                existing += 1

        return created, existing

    @staticmethod
    def _line_for_outcome(*, definition: MarketDefinition, market_type: str, side: str) -> Decimal | None:
        if market_type == OddsSnapshot.MarketType.MONEYLINE or definition.handicap is None:
            return None

        line = Decimal(str(definition.handicap))

        if market_type == OddsSnapshot.MarketType.SPREAD and side == OddsSnapshot.Side.AWAY:
            return -line

        return line

    @staticmethod
    def _american_odds(value: str | int | None) -> int | None:
        if value is None:
            return None

        return int(value)
