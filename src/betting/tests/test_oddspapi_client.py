import pytest
import requests

from betting.services.oddspapi_client import OddsPapiClient


def test_get_markets(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [{"marketId": 141, "marketType": "moneyline"}]

    def mock_get(url, params, timeout):
        assert url == "https://api.oddspapi.io/v4/markets"
        assert params == {
            "language": "en",
            "apiKey": "test-key",
        }
        assert timeout == 30

        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    client = OddsPapiClient(api_key="test-key")

    result = client.get_markets()

    assert result == [
        {
            "marketId": 141,
            "marketType": "moneyline",
        }
    ]


def test_get_odds_by_tournament(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [{"fixtureId": "fixture-123"}]

    def mock_get(url, params, timeout):
        assert url == ("https://api.oddspapi.io/v4/odds-by-tournaments")
        assert params == {
            "tournamentIds": 31,
            "bookmaker": "bwin.de",
            "apiKey": "test-key",
        }
        assert timeout == 30

        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    client = OddsPapiClient(api_key="test-key")

    result = client.get_odds_by_tournament(
        tournament_id=31,
        bookmaker="bwin.de",
    )

    assert result == [{"fixtureId": "fixture-123"}]


def test_http_error_is_raised(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            raise requests.HTTPError("500 Server Error")

        def json(self):
            return {}

    def mock_get(url, params, timeout):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    client = OddsPapiClient(api_key="test-key")

    with pytest.raises(requests.HTTPError):
        client.get_markets()


def test_api_error_payload_raises_runtime_error(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "error": {
                    "message": "Invalid bookmaker",
                    "code": "INVALID_PARAMETER",
                }
            }

    def mock_get(url, params, timeout):
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    client = OddsPapiClient(api_key="test-key")

    with pytest.raises(RuntimeError):
        client.get_odds_by_tournament(
            tournament_id=31,
            bookmaker="bad-bookmaker",
        )
