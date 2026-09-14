import warnings

from django.core.management.base import BaseCommand

from predictions.nfl.models.logistic import NFLLogisticRegressionModel
from predictions.nfl.models.parameter_config import NFLModelParameterConfigService
from predictions.nfl.models.random_forest import NFLRandomForestModel
from predictions.nfl.models.training import NFLTrainingService
from predictions.nfl.models.xgboost import NFLXGBoostModel


class Command(BaseCommand):
    help = "Train and save NFL prediction models."

    def add_arguments(self, parser):
        parser.add_argument(
            "--target",
            default="home_win",
        )

        parser.add_argument(
            "--through-season",
            type=int,
            required=True,
        )

        parser.add_argument(
            "--through-week",
            type=int,
            default=None,
        )

    def handle(self, *args, **options):
        warnings.filterwarnings(
            "ignore",
            message="Skipping features without any observed values.*",
            category=UserWarning,
        )

        target = options["target"]
        through_season = options["through_season"]
        through_week = options["through_week"]

        rf_parameters = NFLModelParameterConfigService.load(model_type="random_forest", target=target)

        logistic_parameters = {
            "max_iterations": 1000,
        }

        xgboost_parameters = NFLModelParameterConfigService.load(model_type="xgboost", target=target)

        self.stdout.write("Training Random Forest...")

        NFLTrainingService.train_and_save_model(
            model_class=NFLRandomForestModel,
            model_type="random_forest",
            parameters=rf_parameters,
            target=target,
            through_season=through_season,
            through_week=through_week,
            model_parameters={
                "n_jobs": -1,
            },
        )

        self.stdout.write(self.style.SUCCESS("Random Forest saved"))

        self.stdout.write("Training Logistic Regression...")

        NFLTrainingService.train_and_save_model(
            model_class=NFLLogisticRegressionModel,
            model_type="logistic",
            parameters=logistic_parameters,
            target=target,
            through_season=through_season,
            through_week=through_week,
        )

        self.stdout.write(self.style.SUCCESS("Logistic Regression saved"))

        self.stdout.write("Training XGBoost...")

        NFLTrainingService.train_and_save_model(
            model_class=NFLXGBoostModel,
            model_type="xgboost",
            parameters=xgboost_parameters,
            target=target,
            through_season=through_season,
            through_week=through_week,
        )

        self.stdout.write(self.style.SUCCESS("XGBoost saved"))
