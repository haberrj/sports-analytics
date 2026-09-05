from typing import Any

from predictions.nfl.dataset import NFLTrainingDataService
from predictions.nfl.models.optimizer import ClassificationModelOptimizer, OptimizationResult
from predictions.nfl.models.random_forest import NFLRandomForestModel


class NFLTrainingService:
    @staticmethod
    def optimize_random_forest(
        validation_seasons: list[int],
        target: str,
        iterations: int = 100,
        n_jobs: int = -1
    ) -> OptimizationResult:
        dataset = NFLTrainingDataService.build_dataset()

        optimizer = ClassificationModelOptimizer(
            NFLRandomForestModel,
            validation_seasons=validation_seasons,
            objective='log_loss',
            random_state=42,
            model_parameters={
                'n_jobs': n_jobs
            }
        )

        best, _ = optimizer.bayesian_search(
            dataset=dataset,
            parameter_suggester=NFLRandomForestModel.suggest_random_forest_parameters,
            target=target,
            iterations=iterations
        )

        return best

    @staticmethod
    def evaluate_random_forest(
        parameters: dict[str, Any],
        test_season: int,
        target: str,
        n_jobs: int = -1,
    ) -> OptimizationResult:
        dataset = NFLTrainingDataService.build_dataset()

        evaluator = ClassificationModelOptimizer(
            NFLRandomForestModel,
            validation_seasons=[test_season],
            objective="log_loss",
            random_state=42,
            model_parameters={
                'n_jobs': n_jobs
            }
        )

        result = evaluator.evaluate_parameters(
            dataset=dataset,
            parameters=parameters,
            target=target
        )

        return result
