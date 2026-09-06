import argparse
import os
import warnings

import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)
django.setup()

from predictions.nfl.models.logistic import NFLLogisticRegressionModel  # noqa: E402
from predictions.nfl.models.random_forest import NFLRandomForestModel  # noqa: E402
from predictions.nfl.models.training import NFLTrainingService  # noqa: E402
from predictions.nfl.models.xgboost import NFLXGBoostModel  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--target",
        default="home_win",
    )

    parser.add_argument(
        "--through-season",
        type=int,
        default=2024,
    )

    parser.add_argument(
        "--through-week",
        type=int,
        default=None,
    )

    return parser.parse_args()


def main():
    warnings.filterwarnings(
        "ignore",
        message="Skipping features without any observed values.*",
        category=UserWarning,
    )

    args = parse_args()

    rf_parameters = {
        "max_depth": 6,
        "min_samples_leaf": 4,
        "n_estimators": 60,
        "max_features": 0.25,
    }

    logistic_parameters = {
        "max_iterations": 1000,
    }

    xgboost_parameters = {
        "n_estimators": 299,
        "max_depth": 1,
        "learning_rate": 0.029849909352061013,
        "min_child_weight": 9.995824848019023,
        "subsample": 0.8925937442592672,
        "colsample_bytree": 0.8774564543659042,
        "reg_alpha": 1.5644798926956065,
        "reg_lambda": 1.49230202784724,
    }

    print("Training RF...")

    NFLTrainingService.train_and_save_model(
        model_class=NFLRandomForestModel,
        model_type="random_forest",
        parameters=rf_parameters,
        target=args.target,
        through_season=args.through_season,
        through_week=args.through_week,
        model_parameters={
            "n_jobs": -1,
        },
    )

    print("RF saved")

    print("Training Logistic...")

    NFLTrainingService.train_and_save_model(
        model_class=NFLLogisticRegressionModel,
        model_type="logistic",
        parameters=logistic_parameters,
        target=args.target,
        through_season=args.through_season,
        through_week=args.through_week,
    )

    print("Logistic saved")

    print("Training XGBoost...")

    NFLTrainingService.train_and_save_model(
        model_class=NFLXGBoostModel,
        model_type="xgboost",
        parameters=xgboost_parameters,
        target=args.target,
        through_season=args.through_season,
        through_week=args.through_week,
    )

    print("XGBoost saved")


if __name__ == "__main__":
    main()
