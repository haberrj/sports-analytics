from unittest.mock import call, patch

import polars as pl

from ingestion.nfl.service import NFLIngestionService


@patch("ingestion.nfl.service.nfl.load_schedules")
def test_get_available_seasons_returns_sorted_unique_seasons(
    mock_load_schedules,
):
    mock_load_schedules.return_value = pl.DataFrame(
        {
            "season": [
                2025,
                2023,
                2025,
                2024,
            ]
        }
    )

    service = NFLIngestionService()

    assert service.get_available_seasons() == [
        2023,
        2024,
        2025,
    ]


@patch("ingestion.nfl.service.NFLGameIngestor")
def test_ingest_season_uses_game_ingestor(
    mock_game_ingestor,
):
    service = NFLIngestionService()

    service.ingest_season(2025)

    mock_game_ingestor.assert_called_once_with(2025)
    mock_game_ingestor.return_value.ingest.assert_called_once_with()


@patch.object(
    NFLIngestionService,
    "ingest_season",
)
@patch.object(
    NFLIngestionService,
    "get_available_seasons",
)
def test_ingest_all_seasons(
    mock_get_available_seasons,
    mock_ingest_season,
):
    mock_get_available_seasons.return_value = [
        2023,
        2024,
        2025,
    ]

    service = NFLIngestionService()
    service.ingest_all_seasons()

    assert mock_ingest_season.call_count == 3

    mock_ingest_season.assert_has_calls(
        [
            call(2023),
            call(2024),
            call(2025),
        ]
    )
