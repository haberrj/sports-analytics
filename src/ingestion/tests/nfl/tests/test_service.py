from unittest.mock import Mock, call, patch

from ingestion.nfl.service import NFLIngestionService


@patch("ingestion.nfl.service.NFLTeamStatsIngestor")
@patch("ingestion.nfl.service.NFLGameIngestor")
@patch("ingestion.nfl.service.NFLTeamIngestor")
def test_ingest_season_runs_pipeline_in_order(
    mock_team_ingestor,
    mock_game_ingestor,
    mock_team_stats_ingestor,
):
    parent = Mock()

    parent.attach_mock(
        mock_team_ingestor.return_value.ingest,
        "teams",
    )
    parent.attach_mock(
        mock_game_ingestor.return_value.ingest,
        "games",
    )
    parent.attach_mock(
        mock_team_stats_ingestor.return_value.ingest,
        "team_stats",
    )

    NFLIngestionService().ingest_season(2025)

    assert parent.mock_calls == [
        call.teams(),
        call.games(),
        call.team_stats(),
    ]
