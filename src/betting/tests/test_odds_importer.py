from decimal import Decimal

import pytest

from betting.models import (
    ExternalGameMapping,
    OddsSnapshot,
    Sportsbook,
    SportsbookFixture,
    SportsbookRegion,
)
from betting.services.market_catalog import MarketCatalog, MarketDefinition
from betting.services.odds_importer import OddsImporter
from games.models import Game, Season
from teams.models import League, Team


@pytest.fixture
def betting_setup():
    league = League.objects.create(
        name="National Football League",
        abbreviation="NFL",
    )

    season = Season.objects.create(
        league=league,
        name="2026",
        start_date="2026-09-01",
        end_date="2027-02-28",
    )

    home_team = Team.objects.create(
        external_id="home-team",
        slug="home-team",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )

    away_team = Team.objects.create(
        external_id="away-team",
        slug="away-team",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )

    game = Game.objects.create(
        season=season,
        home_team=home_team,
        away_team=away_team,
    )

    ExternalGameMapping.objects.create(
        game=game,
        provider=ExternalGameMapping.Provider.ODDSPAPI,
        external_fixture_id="fixture-123",
    )

    sportsbook = Sportsbook.objects.create(
        name="Bwin",
        slug="bwin",
    )

    sportsbook_region = SportsbookRegion.objects.create(
        sportsbook=sportsbook,
        country_code="DE",
    )

    return {
        "game": game,
        "sportsbook_region": sportsbook_region,
    }


@pytest.mark.django_db
def test_imports_moneyline_for_mapped_game():
    league = League.objects.create(
        name="National Football League",
        abbreviation="NFL",
    )

    season = Season.objects.create(
        league=league,
        name="2026",
        start_date="2026-09-01",
        end_date="2027-02-28",
    )

    home_team = Team.objects.create(
        external_id="home-team",
        slug="home-team",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )

    away_team = Team.objects.create(
        external_id="away-team",
        slug="away-team",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )

    game = Game.objects.create(
        season=season,
        home_team=home_team,
        away_team=away_team,
    )

    ExternalGameMapping.objects.create(
        game=game,
        provider=ExternalGameMapping.Provider.ODDSPAPI,
        external_fixture_id="fixture-123",
    )

    sportsbook = Sportsbook.objects.create(
        name="Bwin",
        slug="bwin",
    )

    sportsbook_region = SportsbookRegion.objects.create(
        sportsbook=sportsbook,
        country_code="DE",
    )

    market_catalog = MarketCatalog(
        definitions={
            141: MarketDefinition(
                market_id=141,
                market_type="moneyline",
                handicap=0.0,
                outcomes={
                    141: "1",
                    142: "2",
                },
            )
        }
    )

    importer = OddsImporter(
        market_catalog=market_catalog,
        sportsbook_region=sportsbook_region,
        bookmaker="bwin.de",
    )

    payload = [
        {
            "fixtureId": "fixture-123",
            "bookmakerOdds": {
                "bwin.de": {
                    "bookmakerFixtureId": "bwin-fixture-456",
                    "fixturePath": "https://sports.bwin.de/event/fixture-456",
                    "bookmakerIsActive": True,
                    "suspended": False,
                    "markets": {
                        "141": {
                            "bookmakerMarketId": "bwin-market-141",
                            "marketActive": True,
                            "outcomes": {
                                "141": {
                                    "players": {
                                        "0": {
                                            "active": True,
                                            "changedAt": "2026-09-14T12:00:00Z",
                                            "price": 1.80,
                                            "priceAmerican": -125,
                                            "bookmakerOutcomeId": "bwin-home",
                                            "betslip": "https://sports.bwin.de/betslip/home",
                                        }
                                    }
                                },
                                "142": {
                                    "players": {
                                        "0": {
                                            "active": True,
                                            "changedAt": "2026-09-14T12:00:00Z",
                                            "price": 2.10,
                                            "priceAmerican": 110,
                                            "bookmakerOutcomeId": "bwin-away",
                                            "betslip": "https://sports.bwin.de/betslip/away",
                                        }
                                    }
                                },
                            },
                        }
                    },
                }
            },
        }
    ]

    result = importer.import_payload(payload)

    assert result.fixtures_seen == 1
    assert result.fixtures_matched == 1
    assert result.fixtures_unmatched == 0
    assert result.snapshots_created == 2
    assert result.snapshots_existing == 0

    assert SportsbookFixture.objects.count() == 1
    assert OddsSnapshot.objects.count() == 2

    sportsbook_fixture = SportsbookFixture.objects.get()

    assert sportsbook_fixture.game == game
    assert sportsbook_fixture.sportsbook_region == sportsbook_region
    assert sportsbook_fixture.external_fixture_id == "bwin-fixture-456"
    assert sportsbook_fixture.event_url == "https://sports.bwin.de/event/fixture-456"

    home_odds = OddsSnapshot.objects.get(
        side=OddsSnapshot.Side.HOME,
    )

    assert home_odds.market_type == OddsSnapshot.MarketType.MONEYLINE
    assert home_odds.line is None
    assert home_odds.decimal_odds == Decimal("1.8000")
    assert home_odds.american_odds == -125
    assert home_odds.external_market_id == "bwin-market-141"
    assert home_odds.external_outcome_id == "bwin-home"

    away_odds = OddsSnapshot.objects.get(
        side=OddsSnapshot.Side.AWAY,
    )

    assert away_odds.market_type == OddsSnapshot.MarketType.MONEYLINE
    assert away_odds.line is None
    assert away_odds.decimal_odds == Decimal("2.1000")
    assert away_odds.american_odds == 110
    assert away_odds.external_market_id == "bwin-market-141"
    assert away_odds.external_outcome_id == "bwin-away"


@pytest.mark.django_db
def test_imports_spread_with_opposite_home_and_away_lines():
    league = League.objects.create(
        name="National Football League",
        abbreviation="NFL",
    )

    season = Season.objects.create(
        league=league,
        name="2026",
        start_date="2026-09-01",
        end_date="2027-02-28",
    )

    home_team = Team.objects.create(
        external_id="home-team",
        slug="home-team",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )

    away_team = Team.objects.create(
        external_id="away-team",
        slug="away-team",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )

    game = Game.objects.create(
        season=season,
        home_team=home_team,
        away_team=away_team,
    )

    ExternalGameMapping.objects.create(
        game=game,
        provider=ExternalGameMapping.Provider.ODDSPAPI,
        external_fixture_id="fixture-123",
    )

    sportsbook = Sportsbook.objects.create(
        name="Bwin",
        slug="bwin",
    )

    sportsbook_region = SportsbookRegion.objects.create(
        sportsbook=sportsbook,
        country_code="DE",
    )

    market_catalog = MarketCatalog(
        definitions={
            14188: MarketDefinition(
                market_id=14188,
                market_type="spreads",
                handicap=-3.5,
                outcomes={
                    14188: "1",
                    14189: "2",
                },
            )
        }
    )

    importer = OddsImporter(
        market_catalog=market_catalog,
        sportsbook_region=sportsbook_region,
        bookmaker="bwin.de",
    )

    payload = [
        {
            "fixtureId": "fixture-123",
            "bookmakerOdds": {
                "bwin.de": {
                    "bookmakerFixtureId": "bwin-fixture-456",
                    "fixturePath": "https://sports.bwin.de/event/fixture-456",
                    "bookmakerIsActive": True,
                    "suspended": False,
                    "markets": {
                        "14188": {
                            "bookmakerMarketId": "bwin-spread-14188",
                            "marketActive": True,
                            "outcomes": {
                                "14188": {
                                    "players": {
                                        "0": {
                                            "active": True,
                                            "changedAt": "2026-09-14T12:00:00Z",
                                            "price": 1.91,
                                            "priceAmerican": -110,
                                            "bookmakerOutcomeId": "bwin-home-spread",
                                            "betslip": "https://sports.bwin.de/betslip/home-spread",
                                        }
                                    }
                                },
                                "14189": {
                                    "players": {
                                        "0": {
                                            "active": True,
                                            "changedAt": "2026-09-14T12:00:00Z",
                                            "price": 1.91,
                                            "priceAmerican": -110,
                                            "bookmakerOutcomeId": "bwin-away-spread",
                                            "betslip": "https://sports.bwin.de/betslip/away-spread",
                                        }
                                    }
                                },
                            },
                        }
                    },
                }
            },
        }
    ]

    result = importer.import_payload(payload)

    assert result.snapshots_created == 2

    home = OddsSnapshot.objects.get(
        side=OddsSnapshot.Side.HOME,
    )
    away = OddsSnapshot.objects.get(
        side=OddsSnapshot.Side.AWAY,
    )

    assert home.market_type == OddsSnapshot.MarketType.SPREAD
    assert away.market_type == OddsSnapshot.MarketType.SPREAD

    assert home.line == Decimal("-3.50")
    assert away.line == Decimal("3.50")

    assert home.decimal_odds == Decimal("1.9100")
    assert away.decimal_odds == Decimal("1.9100")


@pytest.mark.django_db
def test_imports_total_with_same_line_for_over_and_under():
    league = League.objects.create(
        name="National Football League",
        abbreviation="NFL",
    )

    season = Season.objects.create(
        league=league,
        name="2026",
        start_date="2026-09-01",
        end_date="2027-02-28",
    )

    home_team = Team.objects.create(
        external_id="home-team",
        slug="home-team",
        name="Home Team",
        abbreviation="HOM",
        city="Home City",
    )

    away_team = Team.objects.create(
        external_id="away-team",
        slug="away-team",
        name="Away Team",
        abbreviation="AWY",
        city="Away City",
    )

    game = Game.objects.create(
        season=season,
        home_team=home_team,
        away_team=away_team,
    )

    ExternalGameMapping.objects.create(
        game=game,
        provider=ExternalGameMapping.Provider.ODDSPAPI,
        external_fixture_id="fixture-123",
    )

    sportsbook = Sportsbook.objects.create(
        name="Bwin",
        slug="bwin",
    )

    sportsbook_region = SportsbookRegion.objects.create(
        sportsbook=sportsbook,
        country_code="DE",
    )

    market_catalog = MarketCatalog(
        definitions={
            14200: MarketDefinition(
                market_id=14200,
                market_type="totals",
                handicap=47.5,
                outcomes={
                    14200: "Over",
                    14201: "Under",
                },
            )
        }
    )

    importer = OddsImporter(
        market_catalog=market_catalog,
        sportsbook_region=sportsbook_region,
        bookmaker="bwin.de",
    )

    payload = [
        {
            "fixtureId": "fixture-123",
            "bookmakerOdds": {
                "bwin.de": {
                    "bookmakerFixtureId": "bwin-fixture-456",
                    "fixturePath": "https://sports.bwin.de/event/fixture-456",
                    "bookmakerIsActive": True,
                    "suspended": False,
                    "markets": {
                        "14200": {
                            "bookmakerMarketId": "bwin-total-14200",
                            "marketActive": True,
                            "outcomes": {
                                "14200": {
                                    "players": {
                                        "0": {
                                            "active": True,
                                            "changedAt": "2026-09-14T12:00:00Z",
                                            "price": 1.95,
                                            "priceAmerican": -105,
                                            "bookmakerOutcomeId": "bwin-over",
                                            "betslip": "https://sports.bwin.de/betslip/over",
                                        }
                                    }
                                },
                                "14201": {
                                    "players": {
                                        "0": {
                                            "active": True,
                                            "changedAt": "2026-09-14T12:00:00Z",
                                            "price": 1.87,
                                            "priceAmerican": -115,
                                            "bookmakerOutcomeId": "bwin-under",
                                            "betslip": "https://sports.bwin.de/betslip/under",
                                        }
                                    }
                                },
                            },
                        }
                    },
                }
            },
        }
    ]

    result = importer.import_payload(payload)

    assert result.snapshots_created == 2

    over = OddsSnapshot.objects.get(
        side=OddsSnapshot.Side.OVER,
    )
    under = OddsSnapshot.objects.get(
        side=OddsSnapshot.Side.UNDER,
    )

    assert over.market_type == OddsSnapshot.MarketType.TOTAL
    assert under.market_type == OddsSnapshot.MarketType.TOTAL

    assert over.line == Decimal("47.50")
    assert under.line == Decimal("47.50")

    assert over.decimal_odds == Decimal("1.9500")
    assert under.decimal_odds == Decimal("1.8700")


@pytest.mark.django_db
def test_reimporting_same_odds_does_not_create_duplicates(betting_setup):
    catalog = MarketCatalog(
        definitions={
            141: MarketDefinition(
                market_id=141,
                market_type="moneyline",
                handicap=0.0,
                outcomes={
                    141: "1",
                    142: "2",
                },
            )
        }
    )

    importer = OddsImporter(
        market_catalog=catalog,
        sportsbook_region=betting_setup["sportsbook_region"],
        bookmaker="bwin.de",
    )

    payload = [
        {
            "fixtureId": "fixture-123",
            "bookmakerOdds": {
                "bwin.de": {
                    "bookmakerFixtureId": "bwin-fixture-456",
                    "fixturePath": "https://sports.bwin.de/event/fixture-456",
                    "bookmakerIsActive": True,
                    "suspended": False,
                    "markets": {
                        "141": {
                            "bookmakerMarketId": "bwin-market-141",
                            "marketActive": True,
                            "outcomes": {
                                "141": {
                                    "players": {
                                        "0": {
                                            "active": True,
                                            "changedAt": "2026-09-14T12:00:00Z",
                                            "price": 1.80,
                                            "priceAmerican": -125,
                                            "bookmakerOutcomeId": "bwin-home",
                                        }
                                    }
                                },
                                "142": {
                                    "players": {
                                        "0": {
                                            "active": True,
                                            "changedAt": "2026-09-14T12:00:00Z",
                                            "price": 2.10,
                                            "priceAmerican": 110,
                                            "bookmakerOutcomeId": "bwin-away",
                                        }
                                    }
                                },
                            },
                        }
                    },
                }
            },
        }
    ]

    first_result = importer.import_payload(payload)
    second_result = importer.import_payload(payload)

    assert first_result.snapshots_created == 2
    assert first_result.snapshots_existing == 0

    assert second_result.snapshots_created == 0
    assert second_result.snapshots_existing == 2

    assert OddsSnapshot.objects.count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("bookmaker_is_active", "suspended"),
    [
        (False, False),
        (True, True),
    ],
)
def test_inactive_or_suspended_bookmaker_is_skipped(
    betting_setup,
    bookmaker_is_active,
    suspended,
):
    importer = OddsImporter(
        market_catalog=MarketCatalog(definitions={}),
        sportsbook_region=betting_setup["sportsbook_region"],
        bookmaker="bwin.de",
    )

    payload = [
        {
            "fixtureId": "fixture-123",
            "bookmakerOdds": {
                "bwin.de": {
                    "bookmakerIsActive": bookmaker_is_active,
                    "suspended": suspended,
                    "markets": {},
                }
            },
        }
    ]

    result = importer.import_payload(payload)

    assert result.fixtures_seen == 1
    assert result.fixtures_matched == 1
    assert result.fixtures_unmatched == 0
    assert result.snapshots_created == 0

    assert SportsbookFixture.objects.count() == 0
    assert OddsSnapshot.objects.count() == 0


@pytest.mark.django_db
def test_inactive_market_is_skipped(betting_setup):
    catalog = MarketCatalog(
        definitions={
            141: MarketDefinition(
                market_id=141,
                market_type="moneyline",
                handicap=0.0,
                outcomes={
                    141: "1",
                    142: "2",
                },
            )
        }
    )

    importer = OddsImporter(
        market_catalog=catalog,
        sportsbook_region=betting_setup["sportsbook_region"],
        bookmaker="bwin.de",
    )

    payload = [
        {
            "fixtureId": "fixture-123",
            "bookmakerOdds": {
                "bwin.de": {
                    "bookmakerFixtureId": "bwin-fixture-456",
                    "fixturePath": "https://sports.bwin.de/event/fixture-456",
                    "bookmakerIsActive": True,
                    "suspended": False,
                    "markets": {
                        "141": {
                            "bookmakerMarketId": "bwin-market-141",
                            "marketActive": False,
                            "outcomes": {},
                        }
                    },
                }
            },
        }
    ]

    result = importer.import_payload(payload)

    assert result.snapshots_created == 0
    assert result.snapshots_existing == 0

    assert SportsbookFixture.objects.count() == 1
    assert OddsSnapshot.objects.count() == 0


@pytest.mark.django_db
def test_inactive_outcome_is_skipped(betting_setup):
    catalog = MarketCatalog(
        definitions={
            141: MarketDefinition(
                market_id=141,
                market_type="moneyline",
                handicap=0.0,
                outcomes={
                    141: "1",
                    142: "2",
                },
            )
        }
    )

    importer = OddsImporter(
        market_catalog=catalog,
        sportsbook_region=betting_setup["sportsbook_region"],
        bookmaker="bwin.de",
    )

    payload = [
        {
            "fixtureId": "fixture-123",
            "bookmakerOdds": {
                "bwin.de": {
                    "bookmakerFixtureId": "bwin-fixture-456",
                    "fixturePath": "https://sports.bwin.de/event/fixture-456",
                    "bookmakerIsActive": True,
                    "suspended": False,
                    "markets": {
                        "141": {
                            "bookmakerMarketId": "bwin-market-141",
                            "marketActive": True,
                            "outcomes": {
                                "141": {
                                    "players": {
                                        "0": {
                                            "active": False,
                                            "changedAt": "2026-09-14T12:00:00Z",
                                            "price": 1.80,
                                            "priceAmerican": -125,
                                            "bookmakerOutcomeId": "bwin-home",
                                        }
                                    }
                                },
                                "142": {
                                    "players": {
                                        "0": {
                                            "active": True,
                                            "changedAt": "2026-09-14T12:00:00Z",
                                            "price": 2.10,
                                            "priceAmerican": 110,
                                            "bookmakerOutcomeId": "bwin-away",
                                        }
                                    }
                                },
                            },
                        }
                    },
                }
            },
        }
    ]

    result = importer.import_payload(payload)

    assert result.snapshots_created == 1
    assert result.snapshots_existing == 0

    assert OddsSnapshot.objects.count() == 1

    snapshot = OddsSnapshot.objects.get()

    assert snapshot.side == OddsSnapshot.Side.AWAY
    assert snapshot.market_type == OddsSnapshot.MarketType.MONEYLINE
    assert snapshot.decimal_odds == Decimal("2.1000")
