from dataclasses import dataclass


@dataclass(frozen=True)
class MarketDefinition:
    market_id: int
    market_type: str
    handicap: float | None
    outcomes: dict[int, str]


class MarketCatalog:
    NFL_SPORT_ID = 14

    SUPPORTED_MARKETS = {
        "Winner (incl. overtime)",
        "Handicap (incl. overtime)",
        "Total (incl. overtime)",
    }

    def __init__(self, definitions: dict[int, MarketDefinition]) -> None:
        self.definitions: dict[int, MarketDefinition] = definitions

    @classmethod
    def from_api(cls, payload: list[dict]) -> "MarketCatalog":
        definitions = {}

        for market in payload:
            if market["sportId"] != cls.NFL_SPORT_ID:
                continue

            if market["marketName"] not in cls.SUPPORTED_MARKETS:
                continue

            definition = MarketDefinition(
                market_id=market["marketId"],
                market_type=market["marketType"],
                handicap=market.get("handicap"),
                outcomes={outcome["outcomeId"]: outcome["outcomeName"] for outcome in market["outcomes"]},
            )
            definitions[definition.market_id] = definition
        return cls(definitions)

    def get(self, market_id: int) -> MarketDefinition | None:
        return self.definitions.get(market_id)
