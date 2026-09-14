from dataclasses import dataclass
from typing import Any

from predictions.evaluation import ClassificationEvaluationResult, ClassificationEvaluator
from predictions.nfl.dataset import NFLTrainingDataService
from predictions.nfl.models.base import ClassificationModel
from predictions.nfl.preprocessing import NFLPreprocessingService


@dataclass(frozen=True)
class NFLModelEvaluationConfig:
    name: str
    model_class: ClassificationModel
    parameters: dict[str, Any]
    model_parameters: dict[str, Any] | None = None


@dataclass(frozen=True)
class NFLModelComparisonResult:
    test_season: int
    training_seasons: list[int]
    results: list[ClassificationEvaluationResult]


class NFLModelEvaluationService:
    @staticmethod
    def compare_models(
        *,
        model_configs: list[NFLModelEvaluationConfig],
        test_season: int,
        target: str,
        calibration_bins: int = 10,
    ) -> NFLModelComparisonResult:
        if not model_configs:
            raise ValueError("At least one model configuration is required.")

        dataset = NFLTrainingDataService.build_dataset()

        training_rows = [row for row in dataset if row["season"] < test_season]

        test_rows = [row for row in dataset if row["season"] == test_season]

        if not training_rows:
            raise ValueError(f"No training data available before season {test_season}.")

        if not test_rows:
            raise ValueError(f"No evaluation data available for season {test_season}.")

        x_train, y_train = NFLPreprocessingService.split_features_target(
            rows=training_rows,
            target=target,
        )

        x_test, y_test = NFLPreprocessingService.split_features_target(
            rows=test_rows,
            target=target,
        )

        results: list[ClassificationEvaluationResult] = []

        for config in model_configs:
            model_parameters = config.model_parameters or {}

            model = config.model_class(
                **config.parameters,
                **model_parameters,
            )

            model.fit(
                x_train,
                y_train,
            )

            result = ClassificationEvaluator.evaluate(
                model=model,
                features=x_test,
                targets=y_test,
                model_name=config.name,
                calibration_bins=calibration_bins,
            )

            results.append(result)

        training_seasons = sorted({row["season"] for row in training_rows})

        return NFLModelComparisonResult(
            test_season=test_season,
            training_seasons=training_seasons,
            results=results,
        )
