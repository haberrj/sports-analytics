from django.core.management.base import BaseCommand

from ingestion.nfl.service import NFLIngestionService


class Command(BaseCommand):
    help = "Ingest NFL data"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()

        group.add_argument("--season", type=int, help="Ingest a specific NFL season.")

        group.add_argument("--all", action="store_true", help="Ingest all available NFL seasons.")

    def handle(self, *args, **options):
        service = NFLIngestionService()

        if options["all"]:
            self.stdout.write("Ingesting all NFL seasons...")

            service.ingest_all_seasons(
                on_season_start=self._write_season_progress, on_season_complete=self._write_season_result
            )
        elif options["season"] is not None:
            season = options["season"]
            self.stdout.write(f"Ingesting the {season} NFL season...")
            results = service.ingest_season(season)
            self._write_season_result(season, results)
        else:
            default_season = service.get_current_season()
            self.stdout.write(f"Ingesting the {default_season} NFL season...")
            results = service.ingest_season(default_season)
            self._write_season_result(default_season, results)
        self.stdout.write(self.style.SUCCESS("NFL ingestion complete."))

    def _write_season_progress(self, season: int, index: int, total: int) -> None:
        self.stdout.write(f"[{index}/{total}] Ingesting NFL season {season}...")

    def _write_season_result(self, season: int, results: dict[str, bool]) -> None:
        if not any(results.values()):
            self.stdout.write(f"NFL season {season} has already been ingested.")
            return
        ingested = [dataset for dataset, completed in results.items() if completed]
        self.stdout.write(f"NFL season {season} ingested: {', '.join(ingested)}.")
