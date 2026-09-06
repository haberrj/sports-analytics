import os
import warnings

import django
from sklearn.metrics import brier_score_loss, log_loss

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)
django.setup()

warnings.filterwarnings(
    "ignore",
    message="Skipping features without any observed values.*",
    category=UserWarning,
)

from games.models import Game, Season
from predictions.nfl.models.logistic import (
    NFLLogisticRegressionModel,
)
from predictions.nfl.models.random_forest import (
    NFLRandomForestModel,
)
from predictions.nfl.models.training import NFLTrainingService
from predictions.nfl.models.xgboost import NFLXGBoostModel
from predictions.nfl.prediction import NFLPredictionService


def main():
    season = Season.objects.get(name="2025")

    model_configs = {
        "random_forest": {
            "model_class": NFLRandomForestModel,
            "parameters": {
                "max_depth": 6,
                "min_samples_leaf": 4,
                "n_estimators": 60,
                "max_features": 0.25,
            },
            "model_parameters": {
                "n_jobs": -1,
            },
        },
        "logistic": {
            "model_class": NFLLogisticRegressionModel,
            "parameters": {
                "max_iterations": 1000,
            },
            "model_parameters": {},
        },
        "xgboost": {
            "model_class": NFLXGBoostModel,
            "parameters": {
                "n_estimators": 299,
                "max_depth": 1,
                "learning_rate": 0.029849909352061013,
                "min_child_weight": 9.995824848019023,
                "subsample": 0.8925937442592672,
                "colsample_bytree": 0.8774564543659042,
                "reg_alpha": 1.5644798926956065,
                "reg_lambda": 1.49230202784724,
            },
            "model_parameters": {
                "n_jobs": -1,
            },
        },
    }

    results = {
        model_type: {
            "correct": 0,
            "games": 0,
            "actuals": [],
            "probabilities": [],
        }
        for model_type in model_configs
    }

    for week in range(1, 19):
        if week == 1:
            through_season = 2024
            through_week = None
        else:
            through_season = 2025
            through_week = week - 1

        trained_models = {}

        for model_type, config in model_configs.items():
            trained_models[model_type] = (
                NFLTrainingService.train_model(
                    model_class=config["model_class"],
                    parameters=config["parameters"],
                    target="home_win",
                    through_season=through_season,
                    through_week=through_week,
                    model_parameters=config["model_parameters"],
                )
            )

        games = (
            Game.objects.filter(
                season=season,
                week__number=week,
            )
            .select_related(
                "home_team",
                "away_team",
            )
        )

        weekly_results = {
            model_type: {
                "correct": 0,
                "games": 0,
            }
            for model_type in model_configs
        }

        for game in games:
            if (
                game.home_score is None
                or game.away_score is None
            ):
                continue

            actual_home_win = (
                game.home_score > game.away_score
            )
            actual = int(actual_home_win)

            for model_type, model in trained_models.items():
                probability = (
                    NFLPredictionService
                    .predict_probability_with_model(
                        game=game,
                        model=model,
                    )
                )

                predicted_home_win = probability >= 0.5

                is_correct = (
                    predicted_home_win
                    == actual_home_win
                )

                weekly_results[model_type]["games"] += 1

                results[model_type]["games"] += 1
                results[model_type]["actuals"].append(
                    actual
                )
                results[model_type]["probabilities"].append(
                    probability
                )

                if is_correct:
                    weekly_results[
                        model_type
                    ]["correct"] += 1

                    results[
                        model_type
                    ]["correct"] += 1

        print(f"\nWeek {week}")

        for model_type in model_configs:
            weekly_correct = (
                weekly_results[model_type]["correct"]
            )
            weekly_games = (
                weekly_results[model_type]["games"]
            )

            total_correct = (
                results[model_type]["correct"]
            )
            total_games = (
                results[model_type]["games"]
            )

            weekly_accuracy = (
                weekly_correct / weekly_games * 100
                if weekly_games
                else 0
            )

            cumulative_accuracy = (
                total_correct / total_games * 100
                if total_games
                else 0
            )

            print(
                f"  {model_type}: "
                f"{weekly_correct}/{weekly_games} "
                f"({weekly_accuracy:.1f}%) "
                f"| cumulative: "
                f"{total_correct}/{total_games} "
                f"({cumulative_accuracy:.1f}%)"
            )

    print("\nFinal 2025 Walk-Forward Results")

    for model_type, result in results.items():
        accuracy = (
            result["correct"]
            / result["games"]
        )

        loss = log_loss(
            result["actuals"],
            result["probabilities"],
        )

        brier = brier_score_loss(
            result["actuals"],
            result["probabilities"],
        )

        print(f"\n{model_type}")
        print(
            f"  Accuracy: "
            f"{accuracy:.4f} "
            f"({accuracy * 100:.2f}%)"
        )
        print(
            f"  Log loss: {loss:.5f}"
        )
        print(
            f"  Brier score: {brier:.5f}"
        )


if __name__ == "__main__":
    main()