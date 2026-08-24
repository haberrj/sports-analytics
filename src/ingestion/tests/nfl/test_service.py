from unittest.mock import patch

from ingestion.nfl.service import NFLIngestionService
from ingestion.results import IngestionResult


@patch.object(
    NFLIngestionService,
    "_generate_team_profiles",
)
@patch("ingestion.nfl.service.NFLTeamStatsIngestor")
@patch("ingestion.nfl.service.NFLGameIngestor")
@patch("ingestion.nfl.service.NFLTeamIngestor")
def test_ingest_season_runs_pipeline_in_order(
    mock_team_ingestor,
    mock_game_ingestor,
    mock_team_stats_ingestor,
    mock_generate_team_profiles,
):
    mock_team_ingestor.return_value.ingest.return_value = IngestionResult.INGESTED
    mock_game_ingestor.return_value.ingest.return_value = IngestionResult.INGESTED
    mock_team_stats_ingestor.return_value.ingest.return_value = IngestionResult.INGESTED
    mock_generate_team_profiles.return_value = IngestionResult.INGESTED

    service = NFLIngestionService()

    results = service.ingest_season(
        2025,
        force=False,
    )

    mock_team_ingestor.assert_called_once_with(
        2025,
        force=False,
    )
    mock_game_ingestor.assert_called_once_with(
        2025,
        force=False,
    )
    mock_team_stats_ingestor.assert_called_once_with(
        2025,
        force=False,
    )

    mock_generate_team_profiles.assert_called_once_with(
        2025,
    )

    assert results == {
        "teams": IngestionResult.INGESTED,
        "games": IngestionResult.INGESTED,
        "team_stats": IngestionResult.INGESTED,
        "team_profile": IngestionResult.INGESTED,
    }
