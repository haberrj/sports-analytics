from betting.services.market_catalog import MarketCatalog


def test_parses_nfl_moneyline():
    payload = [
        {
            "marketId": 141,
            "marketName": "Winner (incl. overtime)",
            "marketType": "moneyline",
            "sportId": 14,
            "handicap": 0.0,
            "outcomes": [
                {
                    "outcomeId": 141,
                    "outcomeName": "1",
                },
                {
                    "outcomeId": 142,
                    "outcomeName": "2",
                },
            ],
        }
    ]

    catalog = MarketCatalog.from_api(payload)

    market = catalog.definitions[141]

    assert market.market_id == 141
    assert market.market_type == "moneyline"
    assert market.handicap == 0.0
    assert market.outcomes == {
        141: "1",
        142: "2",
    }


def test_parses_nfl_spread():
    payload = [
        {
            "marketId": 14188,
            "marketName": "Handicap (incl. overtime)",
            "marketType": "spreads",
            "sportId": 14,
            "handicap": -24.5,
            "outcomes": [
                {
                    "outcomeId": 14188,
                    "outcomeName": "1",
                },
                {
                    "outcomeId": 14189,
                    "outcomeName": "2",
                },
            ],
        }
    ]

    catalog = MarketCatalog.from_api(payload)

    market = catalog.definitions[14188]

    assert market.market_type == "spreads"
    assert market.handicap == -24.5


def test_ignores_non_nfl_markets():
    payload = [
        {
            "marketId": 123,
            "marketName": "Winner",
            "marketType": "moneyline",
            "sportId": 13,
            "handicap": 0.0,
            "outcomes": [],
        }
    ]

    catalog = MarketCatalog.from_api(payload)

    assert catalog.definitions == {}


def test_ignores_non_full_game_nfl_market():
    payload = [
        {
            "marketId": 999,
            "marketName": "1st Half - Total",
            "marketType": "totals",
            "sportId": 14,
            "period": "1h",
            "handicap": 21.5,
            "outcomes": [
                {
                    "outcomeId": 1000,
                    "outcomeName": "Over",
                },
                {
                    "outcomeId": 1001,
                    "outcomeName": "Under",
                },
            ],
        }
    ]

    catalog = MarketCatalog.from_api(payload)

    assert catalog.definitions == {}


def test_get_market_by_id():
    payload = [
        {
            "marketId": 141,
            "marketName": "Winner (incl. overtime)",
            "marketType": "moneyline",
            "sportId": 14,
            "handicap": 0.0,
            "outcomes": [
                {"outcomeId": 141, "outcomeName": "1"},
                {"outcomeId": 142, "outcomeName": "2"},
            ],
        }
    ]

    catalog = MarketCatalog.from_api(payload)

    assert catalog.get(141) is not None
    assert catalog.get(141).market_type == "moneyline"
    assert catalog.get(999) is None
