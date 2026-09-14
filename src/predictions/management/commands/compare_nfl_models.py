from django.core.management.base import BaseCommand

from predictions.nfl.evaluation import NFLModelEvaluationService


class Command(BaseCommand):
    help = "Compare saved NFL prediction models on a held-out season."

    def add_arguments(self, parser):
        parser.add_argument(
            "--test-season",
            type=int,
            required=True,
        )

        parser.add_argument(
            "--target",
            default="home_win",
        )

        parser.add_argument(
            "--calibration-bins",
            type=int,
            default=10,
        )

    def handle(self, *args, **options):
        comparison = NFLModelEvaluationService.compare_saved_models(
            test_season=options["test_season"],
            target=options["target"],
            calibration_bins=options["calibration_bins"],
        )

        training_cutoff = str(
            comparison.training_through_season
        )

        if comparison.training_through_week is not None:
            training_cutoff += (
                f" week {comparison.training_through_week}"
            )

        self.stdout.write("")
        self.stdout.write(
            f"Target: {options['target']}"
        )
        self.stdout.write(
            f"Training through: {training_cutoff}"
        )
        self.stdout.write(
            f"Test season: {comparison.test_season}"
        )
        self.stdout.write("")

        header = (
            f"{'Model':<20}"
            f"{'Accuracy':>10}"
            f"{'Log Loss':>12}"
            f"{'Brier':>10}"
            f"{'ROC AUC':>10}"
            f"{'ECE':>10}"
        )

        self.stdout.write(header)
        self.stdout.write("-" * len(header))

        for result in comparison.results:
            self.stdout.write(
                f"{result.model_name:<20}"
                f"{result.accuracy:>10.4f}"
                f"{result.log_loss:>12.4f}"
                f"{result.brier_score:>10.4f}"
                f"{result.roc_auc:>10.4f}"
                f"{result.expected_calibration_error:>10.4f}"
            )