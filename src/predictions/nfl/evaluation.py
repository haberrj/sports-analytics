from dataclasses import dataclass

from predictions.evaluation import (
    ClassificationEvaluationResult,
    ClassificationEvaluator,
)
from predictions.nfl.dataset import NFLTrainingDataService
from predictions.nfl.models.artifacts import (
    NFLModelArtifact,
    NFLModelArtifactService,
)
from predictions.nfl.preprocessing import NFLPreprocessingService


@dataclass(frozen=True)
class NFLModelComparisonResult:
    test_season: int
    training_through_season: int
    training_through_week: int | None
    results: list[ClassificationEvaluationResult]


class NFLModelEvaluationService:
    DEFAULT_MODEL_TYPES = (
        "logistic",
        "random_forest",
        "xgboost",
    )

    @staticmethod
    def compare_saved_models(
        *,
        test_season: int,
        target: str,
        model_types: tuple[str, ...] | None = None,
        calibration_bins: int = 10,
    ) -> NFLModelComparisonResult:
        selected_model_types = model_types if model_types is not None else NFLModelEvaluationService.DEFAULT_MODEL_TYPES

        if not selected_model_types:
            raise ValueError("At least one model type is required.")

        artifacts = [
            NFLModelArtifactService.load(
                model_type=model_type,
                target=target,
            )
            for model_type in selected_model_types
        ]

        NFLModelEvaluationService._validate_artifacts(
            artifacts=artifacts,
            target=target,
        )

        first_artifact = artifacts[0]

        if first_artifact.through_season >= test_season:
            raise ValueError("Model training cutoff must be before the evaluation season.")

        dataset = NFLTrainingDataService.build_dataset()

        test_rows = [row for row in dataset if row["season"] == test_season]

        if not test_rows:
            raise ValueError(f"No evaluation data available for season {test_season}.")

        x_test, y_test = NFLPreprocessingService.split_features_target(
            rows=test_rows,
            target=target,
        )

        results = [
            ClassificationEvaluator.evaluate(
                model=artifact.model,
                features=x_test,
                targets=y_test,
                model_name=artifact.model_type,
                calibration_bins=calibration_bins,
            )
            for artifact in artifacts
        ]

        first_artifact = artifacts[0]

        return NFLModelComparisonResult(
            test_season=test_season,
            training_through_season=first_artifact.through_season,
            training_through_week=first_artifact.through_week,
            results=results,
        )

    @staticmethod
    def _validate_artifacts(
        *,
        artifacts: list[NFLModelArtifact],
        target: str,
    ) -> None:
        if not artifacts:
            raise ValueError("At least one model artifact is required.")

        first_artifact = artifacts[0]

        for artifact in artifacts:
            if artifact.target != target:
                raise ValueError("All model artifacts must match the requested target.")

            if artifact.through_season != first_artifact.through_season:
                raise ValueError("All model artifacts must have the same training season cutoff.")

            if artifact.through_week != first_artifact.through_week:
                raise ValueError("All model artifacts must have the same training week cutoff.")
