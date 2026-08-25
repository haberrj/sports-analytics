from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from random import Random
from typing import Any

from predictions.nfl.models.base import ClassificationModel
from predictions.nfl.preprocessing import NFLPreprocessingService


class OptimizationResult:
    parameters: dict[str, Any]
    accuracy: float
    log_loss: float
    brier_score: float
    roc_auc: float


class ClassificationModelOptimizer:
    """Optimize classification model hyperparameters using walk-forward validation."""

    def __init__(
            self, model_factory: Callable,
            validation_seasons: list[int],
            objective: str = "log_loss",
            random_state: int = 42
        ) -> None:
        self.model_factory: Callable = model_factory
        self.validation_seasons: list[int] = validation_seasons
        self.objective: str = objective
        self.random: Random = Random(random_state)

    def evaluation_parameters(self, dataset: list[dict], parameters: dict[str, Any], target: str) -> OptimizationResult:
        """Evaluate one hyperparameter configuration across validation seasons.

        Args:
            dataset: Historical training rows.
            parameters: Model constructor parameters to evaluate.
            target: Prediction target to use.

        Returns:
            Averaged model performance across validation seasons.
        """
        scores = []

        for validation_season in self.validation_seasons:
            training_rows = [
                row
                for row in dataset
                if row["season"] < validation_season
            ]

            validation_rows = [
                row
                for row in dataset
                if row["season"] == validation_season
            ]

            x_train, y_train = NFLPreprocessingService.split_features_target(
                training_rows,
                target,
            )

            x_valid, y_valid = NFLPreprocessingService.split_features_target(
                validation_rows,
                target,
            )

            model = self.model_factory(**parameters)
            model.fit(x_train, y_train)

            scores.append(
                model.get_performance_stats(
                    x_valid,
                    y_valid,
                )
            )

        return OptimizationResult(
            parameters=parameters,
            accuracy=sum(score["accuracy"] for score in scores) / len(scores),
            log_loss=sum(score["log_loss"] for score in scores) / len(scores),
            brier_score=sum(score["brier_score"] for score in scores) / len(scores),
            roc_auc=sum(score["roc_auc"] for score in scores) / len(scores),
        )

    def random_search(
        self,
        dataset: list[dict],
        parameter_sampler: Callable[[Random], dict[str, Any]],
        target: str,
        iterations: int = 50,
    ) -> list[OptimizationResult]:
        """Evaluate randomly sampled hyperparameter configurations.

        Args:
            dataset: Historical training rows.
            parameter_sampler: Function that generates model parameters.
            target: Prediction target to use.
            iterations: Number of parameter configurations to evaluate.

        Returns:
            Results for all evaluated configurations.
        """
        results = []

        for _ in range(iterations):
            parameters = parameter_sampler(self.random)

            result = self.evaluate_parameters(
                dataset=dataset,
                parameters=parameters,
                target=target,
            )

            results.append(result)

        return results

    def sample_random_forest_parameters(random: Random) -> dict[str, Any]:
        return {
            "max_depth": random.randint(1, 20),
            "min_samples_leaf": random.randint(1, 15),
            "n_estimators": random.randint(25, 150),
            "max_features": random.choice(
                [
                    "sqrt",
                    "log2",
                    0.25,
                    0.5,
                    0.75,
                    1.0,
                ]
            ),
        }

    def get_best_result(self, results: list[OptimizationResult]) -> OptimizationResult:
        if self.objective == "log_loss":
            return min(results, key=lambda result: result.log_loss)

        if self.objective == "brier_score":
            return min(results, key=lambda result: result.brier_score)

        if self.objective == "accuracy":
            return max(results, key=lambda result: result.accuracy)

        if self.objective == "roc_auc":
            return max(results, key=lambda result: result.roc_auc)

        raise ValueError(f"Unsupported objective: {self.objective}")