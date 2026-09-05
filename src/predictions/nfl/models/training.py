from collections.abc import Callable
from typing import Any

from predictions.nfl.dataset import NFLTrainingDataService
from predictions.nfl.models.artifacts import NFLModelArtifactService
from predictions.nfl.models.base import ClassificationModel
from predictions.nfl.models.optimizer import (
    ClassificationModelOptimizer,
    OptimizationResult,
)
from predictions.nfl.preprocessing import NFLPreprocessingService


class NFLTrainingService:
    @staticmethod
    def optimize_model(
        model_class: type[ClassificationModel],
        parameter_suggester: Callable,
        validation_seasons: list[int],
        target: str,
        iterations: int = 100,
        model_parameters: dict[str, Any] | None = None,
    ) -> OptimizationResult:
        dataset = NFLTrainingDataService.build_dataset()

        optimizer = ClassificationModelOptimizer(
            model_class,
            validation_seasons=validation_seasons,
            objective="log_loss",
            random_state=42,
            model_parameters=model_parameters,
        )

        best, _ = optimizer.bayesian_search(
            dataset=dataset,
            parameter_suggester=parameter_suggester,
            target=target,
            iterations=iterations,
        )

        return best

    @staticmethod
    def evaluate_model(
        model_class: type[ClassificationModel],
        parameters: dict[str, Any],
        test_season: int,
        target: str,
        model_parameters: dict[str, Any] | None = None,
    ) -> OptimizationResult:
        dataset = NFLTrainingDataService.build_dataset()

        evaluator = ClassificationModelOptimizer(
            model_class,
            validation_seasons=[test_season],
            objective="log_loss",
            random_state=42,
            model_parameters=model_parameters,
        )

        return evaluator.evaluate_parameters(
            dataset=dataset,
            parameters=parameters,
            target=target,
        )

    @staticmethod
    def train_model(
        model_class: type[ClassificationModel],
        parameters: dict[str, Any],
        target: str,
        through_season: int,
        model_parameters: dict[str, Any] | None = None,
    ) -> ClassificationModel:
        dataset = NFLTrainingDataService.build_dataset()

        training_rows = [row for row in dataset if row["season"] <= through_season]

        if not training_rows:
            raise ValueError(f"No training data available through {through_season} season.")

        features, targets = NFLPreprocessingService.split_features_target(
            rows=training_rows,
            target=target,
        )

        model_parameters = model_parameters or {}

        model = model_class(
            **parameters,
            **model_parameters,
        )

        model.fit(
            features,
            targets,
        )

        return model

    @staticmethod
    def train_and_save_model(
        model_class: type[ClassificationModel],
        model_type: str,
        parameters: dict[str, Any],
        target: str,
        through_season: int,
        model_parameters: dict[str, Any] | None = None,
    ) -> ClassificationModel:
        model = NFLTrainingService.train_model(
            model_class=model_class,
            parameters=parameters,
            target=target,
            through_season=through_season,
            model_parameters=model_parameters,
        )

        NFLModelArtifactService.save(
            model=model,
            model_type=model_type,
            target=target,
            through_season=through_season,
            parameters=parameters,
        )

        return model
