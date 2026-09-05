from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from random import Random
from typing import Any

import optuna
from optuna import Trial

from predictions.nfl.preprocessing import NFLPreprocessingService


@dataclass
class OptimizationResult:
    parameters: dict[str, Any]
    accuracy: float
    log_loss: float
    brier_score: float
    roc_auc: float


class ClassificationModelOptimizer:
    """Optimize classification model hyperparameters using walk-forward validation."""
    VALID_OBJECTIVE = {
        "accuracy",
        "log_loss",
        "brier_score",
        "roc_auc"
    }

    def __init__(
            self, model_factory: Callable,
            validation_seasons: list[int],
            objective: str = "log_loss",
            random_state: int = 42,
            model_parameters: dict[str, Any] | None = None,
        ) -> None:
        if objective not in self.VALID_OBJECTIVE:
            raise ValueError(f"Unsupported objective: {objective}")
        self.model_factory: Callable = model_factory
        self.validation_seasons: list[int] = validation_seasons
        self.objective: str = objective
        self.random: Random = Random(random_state)
        self.model_parameters: dict[str, str] = model_parameters or {}

    def evaluate_parameters(self, dataset: list[dict], parameters: dict[str, Any], target: str) -> OptimizationResult:
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

            model = self.model_factory(**parameters, **self.model_parameters)
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

    def get_best_result(self, results: list[OptimizationResult]) -> OptimizationResult:
        if not results:
            raise ValueError("Optimization results cannot be empty.")
    
        if self.objective == "log_loss":
            return min(results, key=lambda result: result.log_loss)

        if self.objective == "brier_score":
            return min(results, key=lambda result: result.brier_score)

        if self.objective == "accuracy":
            return max(results, key=lambda result: result.accuracy)

        if self.objective == "roc_auc":
            return max(results, key=lambda result: result.roc_auc)

        raise ValueError(f"Unsupported objective: {self.objective}")

    def bayesian_search(
        self,
        dataset: list[dict],
        parameter_suggester: Callable[[Trial], dict[str, Any]],
        target: str,
        iterations: int = 50,
    ) -> tuple[OptimizationResult, list[OptimizationResult]]:
        """Optimize hyperparameters using Bayesian optimization.
    
        Args:
            dataset: Historical training rows.
            parameter_suggester: Function that suggests model parameters
                for an Optuna trial.
            target: Prediction target to use.
            iterations: Number of optimization trials.
    
        Returns:
            The best optimization result and all evaluated results.
        """
        results: list[OptimizationResult] = []
    
        direction = (
            "minimize"
            if self.objective in {"log_loss", "brier_score"}
            else "maximize"
        )
    
        sampler = optuna.samplers.TPESampler(
            seed=self.random.randint(0, 2**32 - 1),
            n_startup_trials=10,
        )
    
        study = optuna.create_study(
            direction=direction,
            sampler=sampler,
        )
    
        def objective(trial: Trial) -> float:
            parameters = parameter_suggester(trial)
    
            result = self.evaluate_parameters(
                dataset=dataset,
                parameters=parameters,
                target=target,
            )
    
            results.append(result)
    
            return getattr(result, self.objective)
    
        study.optimize(
            objective,
            n_trials=iterations,
        )
    
        best_result = self.get_best_result(results)
    
        return best_result, results