from django.core.management.base import BaseCommand

from betting.services.odds_ingestion import OddsIngestionService


class Command(BaseCommand):
    help = "Ingest sportsbook odds from OddsPapi"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tournament-id",
            type=int,
            required=True,
            help="OddsPapi tournament ID.",
        )

        parser.add_argument(
            "--bookmaker",
            default="bwin.de",
            help="OddsPapi bookmaker key. Default: bwin.de",
        )

        parser.add_argument(
            "--sportsbook",
            default="bwin",
            help="Internal Sportsbook slug. Default: bwin",
        )

        parser.add_argument(
            "--country",
            default="DE",
            help="Sportsbook region country code. Default: DE",
        )

    def handle(self, *args, **options):
        self.stdout.write(f"Ingesting odds from {options['bookmaker']} for tournament {options['tournament_id']}...")

        service = OddsIngestionService()

        result = service.ingest(
            tournament_id=options["tournament_id"],
            bookmaker=options["bookmaker"],
            sportsbook_slug=options["sportsbook"],
            country_code=options["country"],
        )

        self.stdout.write(
            f"Fixtures: "
            f"{result.fixtures_matched} matched, "
            f"{result.fixtures_unmatched} unmatched, "
            f"{result.fixtures_seen} total."
        )

        self.stdout.write(
            f"Snapshots: {result.snapshots_created} created, {result.snapshots_existing} already existed."
        )

        self.stdout.write(self.style.SUCCESS("Odds ingestion complete."))
