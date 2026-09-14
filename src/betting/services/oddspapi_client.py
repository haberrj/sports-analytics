import os

import requests


class OddsPapiClient:
    BASE_URL = "https://api.oddspapi.io/v4"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["ODDSPAPI_TOKEN"]

    def _get(self, path: str, params: dict | None = None):
        request_params = dict(params or {})
        request_params["apiKey"] = self.api_key

        response = requests.get(
            f"{self.BASE_URL}/{path}",
            params=request_params,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(data["error"])

        return data

    def get_markets(self):
        return self._get(
            "markets",
            {
                "language": "en",
            },
        )

    def get_odds_by_tournament(
        self,
        tournament_id: int,
        bookmaker: str,
    ):
        return self._get(
            "odds-by-tournaments",
            {
                "tournamentIds": tournament_id,
                "bookmaker": bookmaker,
            },
        )

    def get_participants(self, sport_id: int):
        return self._get(
            "participants",
            {
                "sportId": sport_id,
                "language": "en",
            },
        )
