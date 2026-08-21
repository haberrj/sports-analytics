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
                on_season_start=lambda season, index, total: self.stdout.write(
                    f"[{index}/{total}] Ingesting NFL season {season}..."
                )
            )
        elif options["season"] is not None:
            season = options["season"]
            self.stdout.write(f"Ingesting the {season} NFL season...")
            service.ingest_season(season)
        else:
            default_season = service.get_current_season()
            self.stdout.write(f"Ingesting the {default_season} NFL season...")
            service.ingest_season(default_season)
        self.stdout.write(self.style.SUCCESS("NFL ingestion complete."))
