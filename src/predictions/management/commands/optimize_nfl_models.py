import warnings

from django.core.management.base import BaseCommand

from predictions.nfl.models.parameter_config import NFLModelParameterConfigService
from predictions.nfl.models.random_forest import NFLRandomForestModel
from predictions.nfl.models.training import NFLTrainingService
from predictions.nfl.models.xgboost import NFLXGBoostModel


class Command(BaseCommand):
    help = "Optimize NFL prediction model hyperparameters."

    def add_arguments(self, parser):
        parser.add_argument(
            "--target",
            default="home_win",
        )

        parser.add_argument(
            "--validation-seasons",
            nargs="+",
            type=int,
            required=True,
        )

        parser.add_argument(
            "--iterations",
            type=int,
            default=100,
        )

        parser.add_argument(
            "--model",
            choices=[
                "random_forest",
                "xgboost",
                "all",
            ],
            default="all",
        )

    def handle(self, *args, **options):
        warnings.filterwarnings(
            "ignore",
            message="Skipping features without any observed values.*",
            category=UserWarning,
        )

        target = options["target"]
        validation_seasons = options["validation_seasons"]
        iterations = options["iterations"]
        model = options["model"]

        if model in {
            "random_forest",
            "all",
        }:
            self.stdout.write("Optimizing Random Forest...")

            result = NFLTrainingService.optimize_model(
                model_class=NFLRandomForestModel,
                parameter_suggester=(NFLRandomForestModel.suggest_random_forest_parameters),
                validation_seasons=validation_seasons,
                target=target,
                iterations=iterations,
                model_parameters={
                    "n_jobs": -1,
                },
            )

            self._print_result(
                "Random Forest",
                result,
            )

            NFLModelParameterConfigService.save(
                model_type="random_forest",
                target=target,
                parameters=result.parameters,
            )

        if model in {
            "xgboost",
            "all",
        }:
            self.stdout.write("Optimizing XGBoost...")

            result = NFLTrainingService.optimize_model(
                model_class=NFLXGBoostModel,
                parameter_suggester=(NFLXGBoostModel.suggest_xgboost_parameters),
                validation_seasons=validation_seasons,
                target=target,
                iterations=iterations,
                model_parameters={
                    "n_jobs": -1,
                },
            )

            NFLModelParameterConfigService.save(
                model_type="xgboost",
                target=target,
                parameters=result.parameters,
            )

            self._print_result(
                "XGBoost",
                result,
            )

    def _print_result(
        self,
        model_name,
        result,
    ):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"{model_name} optimization complete"))

        self.stdout.write("")

        self.stdout.write("Best parameters:")

        for key, value in result.parameters.items():
            self.stdout.write(f"  {key}: {value}")

        self.stdout.write("")

        self.stdout.write(f"Accuracy:    {result.accuracy:.4f}")
        self.stdout.write(f"Log loss:    {result.log_loss:.4f}")
        self.stdout.write(f"Brier score: {result.brier_score:.4f}")
        self.stdout.write(f"ROC AUC:     {result.roc_auc:.4f}")

        self.stdout.write("")
