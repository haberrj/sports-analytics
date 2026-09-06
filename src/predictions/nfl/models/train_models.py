import os

import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)
django.setup()

from predictions.nfl.models.logistic import NFLLogisticRegressionModel  # noqa: E402
from predictions.nfl.models.random_forest import NFLRandomForestModel  # noqa: E402
from predictions.nfl.models.training import NFLTrainingService  # noqa: E402


def main():
    rf_parameters = {"max_depth": 6, "min_samples_leaf": 4, "n_estimators": 60, "max_features": 0.25}

    logistic_parameters = {"max_iterations": 1000}

    print("Training RF...")

    NFLTrainingService.train_and_save_model(
        model_class=NFLRandomForestModel,
        model_type="random_forest",
        parameters=rf_parameters,
        target="home_win",
        through_season=2024,
        model_parameters={
            "n_jobs": -1,
        },
    )

    print("RF saved")

    NFLTrainingService.train_and_save_model(
        model_class=NFLLogisticRegressionModel,
        model_type="logistic",
        parameters=logistic_parameters,
        target="home_win",
        through_season=2024,
    )

    print("Logistic Saved")


if __name__ == "__main__":
    main()
