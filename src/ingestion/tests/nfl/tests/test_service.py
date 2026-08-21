from unittest.mock import Mock, call, patch

from ingestion.nfl.service import NFLIngestionService


@patch.object(
    NFLIngestionService,
    "ingest_season",
)
@patch.object(
    NFLIngestionService,
    "get_available_seasons",
)
def test_ingest_all_seasons_calls_progress_callback(
    mock_get_available_seasons,
    mock_ingest_season,
):
    mock_get_available_seasons.return_value = [
        2023,
        2024,
        2025,
    ]

    callback = Mock()
    service = NFLIngestionService()

    service.ingest_all_seasons(
        on_season_start=callback,
    )

    callback.assert_has_calls(
        [
            call(2023, 1, 3),
            call(2024, 2, 3),
            call(2025, 3, 3),
        ]
    )

    mock_ingest_season.assert_has_calls(
        [
            call(2023),
            call(2024),
            call(2025),
        ]
    )
