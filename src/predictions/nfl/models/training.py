from typing import Any

from predictions.nfl.dataset import NFLTrainingDataService
from predictions.nfl.models.optimizer import ClassificationModelOptimizer, OptimizationResult
from predictions.nfl.models.random_forest import NFLRandomForestModel
from predictions.nfl.preprocessing import NFLPreprocessingService


class NFLTrainingService:
    @staticmethod
    def optimize_random_forest(
        validation_seasons: list[int], target: str, iterations: int = 100, n_jobs: int = -1
    ) -> OptimizationResult:
        dataset = NFLTrainingDataService.build_dataset()

        optimizer = ClassificationModelOptimizer(
            NFLRandomForestModel,
            validation_seasons=validation_seasons,
            objective="log_loss",
            random_state=42,
            model_parameters={"n_jobs": n_jobs},
        )

        best, _ = optimizer.bayesian_search(
            dataset=dataset,
            parameter_suggester=NFLRandomForestModel.suggest_random_forest_parameters,
            target=target,
            iterations=iterations,
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
            model_parameters={"n_jobs": n_jobs},
        )

        result = evaluator.evaluate_parameters(dataset=dataset, parameters=parameters, target=target)

        return result

    @staticmethod
    def train_random_forest(
        parameters: dict[str, Any],
        target: str,
        through_season: int,
        n_jobs: int = -1,
    ) -> NFLRandomForestModel:
        dataset = NFLTrainingDataService.build_dataset()

        training_rows = [row for row in dataset if row["season"] <= through_season]

        if not training_rows:
            raise ValueError(f"No training data available through {through_season} season.")

        features, targets = NFLPreprocessingService.split_features_target(rows=training_rows, target=target)

        random_forest = NFLRandomForestModel(
            n_estimators=parameters["n_estimators"],
            max_depth=parameters["max_depth"],
            min_samples_leaf=parameters["min_samples_leaf"],
            max_features=parameters["max_features"],
            n_jobs=n_jobs,
        )

        random_forest.fit(features, targets)

        return random_forest
