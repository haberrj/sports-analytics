from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import CommandError, call_command


@patch("ingestion.management.commands.ingest_nfl.NFLIngestionService")
def test_ingest_nfl_specific_season(mock_service_class):
    service = mock_service_class.return_value

    call_command("ingest_nfl", "--season", "2025")

    service.ingest_season.assert_called_once_with(2025)
    service.ingest_all_seasons.assert_not_called()


@patch("ingestion.management.commands.ingest_nfl.NFLIngestionService")
def test_ingest_nfl_defaults_to_current_season(mock_service_class):
    service = mock_service_class.return_value
    service.get_current_season.return_value = 2026

    call_command("ingest_nfl")

    service.get_current_season.assert_called_once_with()
    service.ingest_season.assert_called_once_with(2026)


@patch("ingestion.management.commands.ingest_nfl.NFLIngestionService")
def test_ingest_nfl_all_seasons(mock_service_class):
    service = mock_service_class.return_value
    service.get_available_seasons.return_value = [2023, 2024, 2025]

    call_command("ingest_nfl", "--all")

    service.ingest_all_seasons.assert_called_once()
    service.ingest_season.assert_not_called()


@patch("ingestion.management.commands.ingest_nfl.NFLIngestionService")
def test_ingest_nfl_all_outputs_progress(mock_service_class):
    service = mock_service_class.return_value

    def fake_ingest_all(
        on_season_start=None,
        on_season_complete=None,
    ):
        seasons = [
            (
                2023,
                {
                    "teams": False,
                    "games": False,
                    "team_stats": False,
                },
            ),
            (
                2024,
                {
                    "teams": False,
                    "games": True,
                    "team_stats": True,
                },
            ),
            (
                2025,
                {
                    "teams": True,
                    "games": True,
                    "team_stats": True,
                },
            ),
        ]

        total = len(seasons)

        for index, (season, results) in enumerate(
            seasons,
            start=1,
        ):
            if on_season_start:
                on_season_start(
                    season,
                    index,
                    total,
                )

            if on_season_complete:
                on_season_complete(
                    season,
                    results,
                )

    service.ingest_all_seasons.side_effect = fake_ingest_all

    stdout = StringIO()

    call_command(
        "ingest_nfl",
        "--all",
        stdout=stdout,
    )

    output = stdout.getvalue()

    assert "[1/3] Ingesting NFL season 2023" in output
    assert "[2/3] Ingesting NFL season 2024" in output
    assert "[3/3] Ingesting NFL season 2025" in output
    assert "NFL ingestion complete." in output


def test_ingest_nfl_rejects_season_and_all_together():
    with pytest.raises(CommandError, match="argument --all: not allowed with argument --season"):
        call_command(
            "ingest_nfl",
            "--season",
            "2025",
            "--all",
        )
