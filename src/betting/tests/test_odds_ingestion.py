from unittest.mock import Mock

import pytest

from betting.models import Sportsbook, SportsbookRegion
from betting.services.market_catalog import MarketCatalog
from betting.services.odds_importer import OddsImportResult
from betting.services.odds_ingestion import OddsIngestionService


@pytest.mark.django_db
def test_ingests_odds_from_oddspapi(monkeypatch):
    sportsbook = Sportsbook.objects.create(
        name="Bwin",
        slug="bwin",
    )

    SportsbookRegion.objects.create(
        sportsbook=sportsbook,
        country_code="DE",
    )

    client = Mock()

    client.get_markets.return_value = []
    client.get_participants.return_value = {}
    client.get_odds_by_tournament.return_value = []

    expected_result = OddsImportResult(
        fixtures_seen=0,
        fixtures_matched=0,
        fixtures_unmatched=0,
        snapshots_created=0,
        snapshots_existing=0,
    )

    import_payload = Mock(return_value=expected_result)

    monkeypatch.setattr(
        "betting.services.odds_ingestion.OddsImporter.import_payload",
        import_payload,
    )

    service = OddsIngestionService(client=client)

    result = service.ingest(
        tournament_id=31,
        bookmaker="bwin.de",
        sportsbook_slug="bwin",
        country_code="DE",
    )

    client.get_markets.assert_called_once_with()

    client.get_participants.assert_called_once_with(
        sport_id=MarketCatalog.NFL_SPORT_ID,
    )

    client.get_odds_by_tournament.assert_called_once_with(
        tournament_id=31,
        bookmaker="bwin.de",
    )

    import_payload.assert_called_once_with([])

    assert result == expected_result


@pytest.mark.django_db
def test_creates_missing_sportsbook_region(monkeypatch):
    client = Mock()

    client.get_markets.return_value = []
    client.get_participants.return_value = {}
    client.get_odds_by_tournament.return_value = []

    import_payload = Mock(return_value=OddsImportResult())

    monkeypatch.setattr(
        "betting.services.odds_ingestion.OddsImporter.import_payload",
        import_payload,
    )

    service = OddsIngestionService(client=client)

    service.ingest(
        tournament_id=31,
        bookmaker="bwin.de",
        sportsbook_slug="bwin",
        country_code="DE",
    )

    sportsbook = Sportsbook.objects.get(slug="bwin")

    assert sportsbook.name == "Bwin"

    assert SportsbookRegion.objects.filter(
        sportsbook=sportsbook,
        country_code="DE",
    ).exists()
