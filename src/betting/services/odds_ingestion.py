from betting.models import Sportsbook, SportsbookRegion
from betting.services.fixture_matcher import FixtureMatcher
from betting.services.market_catalog import MarketCatalog
from betting.services.odds_importer import OddsImporter, OddsImportResult
from betting.services.oddspapi_client import OddsPapiClient
from betting.services.team_mapping import TeamMappingService


class OddsIngestionService:
    def __init__(self, client: OddsPapiClient | None = None) -> None:
        self.client: OddsPapiClient | None = client or OddsPapiClient()

    def ingest(
        self,
        *,
        tournament_id: int,
        bookmaker: str,
        sportsbook_slug: str,
        country_code: str,
    ) -> OddsImportResult:
        market_payload = self.client.get_markets()
        market_catalog = MarketCatalog.from_api(market_payload)

        sportsbook, _ = Sportsbook.objects.get_or_create(
            slug=sportsbook_slug,
            defaults={
                "name": sportsbook_slug.title(),
            },
        )

        sportsbook_region, _ = SportsbookRegion.objects.get_or_create(
            sportsbook=sportsbook,
            country_code=country_code,
        )

        participants = self.client.get_participants(
            sport_id=MarketCatalog.NFL_SPORT_ID,
        )

        TeamMappingService().map_participants(participants)

        odds_payload = self.client.get_odds_by_tournament(
            tournament_id=tournament_id,
            bookmaker=bookmaker,
        )

        FixtureMatcher().match_payload(odds_payload)

        importer = OddsImporter(
            market_catalog=market_catalog,
            sportsbook_region=sportsbook_region,
            bookmaker=bookmaker,
        )

        return importer.import_payload(odds_payload)
