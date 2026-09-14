from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock, call

import pytest

from predictions.evaluation import (
    ClassificationEvaluationResult,
)
from predictions.nfl.evaluation import (
    NFLModelEvaluationService,
)
from predictions.nfl.models.artifacts import NFLModelArtifact


def make_artifact(
    *,
    model_type: str,
    target: str = "home_win",
    through_season: int = 2024,
    through_week: int | None = None,
) -> NFLModelArtifact:
    return NFLModelArtifact(
        model=MagicMock(),
        model_type=model_type,
        target=target,
        through_season=through_season,
        through_week=through_week,
        parameters={},
        trained_at=datetime.now(UTC),
    )


def make_evaluation_result(
    model_name: str,
) -> ClassificationEvaluationResult:
    return ClassificationEvaluationResult(
        model_name=model_name,
        accuracy=0.65,
        log_loss=0.63,
        brier_score=0.22,
        roc_auc=0.69,
        expected_calibration_error=0.04,
        calibration_bins=[],
    )


def test_compare_saved_models_loads_default_model_types(
    monkeypatch,
):
    artifacts = {
        "logistic": make_artifact(
            model_type="logistic",
        ),
        "random_forest": make_artifact(
            model_type="random_forest",
        ),
        "xgboost": make_artifact(
            model_type="xgboost",
        ),
    }

    load_artifact = Mock(side_effect=lambda *, model_type, target: artifacts[model_type])

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLModelArtifactService.load",
        load_artifact,
    )

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLTrainingDataService.build_dataset",
        Mock(
            return_value=[
                {
                    "season": 2025,
                    "feature": 1,
                    "home_win": 1,
                }
            ]
        ),
    )

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLPreprocessingService.split_features_target",
        Mock(
            return_value=(
                [{"feature": 1}],
                [1],
            )
        ),
    )

    evaluator = Mock(side_effect=lambda **kwargs: make_evaluation_result(kwargs["model_name"]))

    monkeypatch.setattr(
        "predictions.nfl.evaluation.ClassificationEvaluator.evaluate",
        evaluator,
    )

    result = NFLModelEvaluationService.compare_saved_models(
        test_season=2025,
        target="home_win",
    )

    assert load_artifact.call_args_list == [
        call(
            model_type="logistic",
            target="home_win",
        ),
        call(
            model_type="random_forest",
            target="home_win",
        ),
        call(
            model_type="xgboost",
            target="home_win",
        ),
    ]

    assert result.test_season == 2025
    assert result.training_through_season == 2024
    assert result.training_through_week is None

    assert [evaluation.model_name for evaluation in result.results] == [
        "logistic",
        "random_forest",
        "xgboost",
    ]


def test_compare_saved_models_uses_same_test_data_for_all_models(
    monkeypatch,
):
    artifacts = [
        make_artifact(
            model_type="logistic",
        ),
        make_artifact(
            model_type="random_forest",
        ),
        make_artifact(
            model_type="xgboost",
        ),
    ]

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLModelArtifactService.load",
        Mock(side_effect=artifacts),
    )

    dataset = [
        {
            "season": 2024,
            "feature": 1,
            "home_win": 0,
        },
        {
            "season": 2025,
            "feature": 2,
            "home_win": 0,
        },
        {
            "season": 2025,
            "feature": 3,
            "home_win": 1,
        },
        {
            "season": 2026,
            "feature": 4,
            "home_win": 1,
        },
    ]

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLTrainingDataService.build_dataset",
        Mock(return_value=dataset),
    )

    split_features_target = Mock(
        return_value=(
            [
                {"feature": 2},
                {"feature": 3},
            ],
            [
                0,
                1,
            ],
        )
    )

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLPreprocessingService.split_features_target",
        split_features_target,
    )

    evaluator = Mock(side_effect=lambda **kwargs: make_evaluation_result(kwargs["model_name"]))

    monkeypatch.setattr(
        "predictions.nfl.evaluation.ClassificationEvaluator.evaluate",
        evaluator,
    )

    NFLModelEvaluationService.compare_saved_models(
        test_season=2025,
        target="home_win",
        calibration_bins=5,
    )

    split_features_target.assert_called_once_with(
        rows=[
            {
                "season": 2025,
                "feature": 2,
                "home_win": 0,
            },
            {
                "season": 2025,
                "feature": 3,
                "home_win": 1,
            },
        ],
        target="home_win",
    )

    assert evaluator.call_count == 3

    for evaluation_call in evaluator.call_args_list:
        assert evaluation_call.kwargs["features"] == [
            {"feature": 2},
            {"feature": 3},
        ]
        assert evaluation_call.kwargs["targets"] == [
            0,
            1,
        ]
        assert evaluation_call.kwargs["calibration_bins"] == 5


def test_compare_saved_models_can_select_model_subset(
    monkeypatch,
):
    artifact = make_artifact(
        model_type="xgboost",
    )

    load_artifact = Mock(
        return_value=artifact,
    )

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLModelArtifactService.load",
        load_artifact,
    )

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLTrainingDataService.build_dataset",
        Mock(
            return_value=[
                {
                    "season": 2025,
                    "home_win": 1,
                }
            ]
        ),
    )

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLPreprocessingService.split_features_target",
        Mock(
            return_value=(
                [{"feature": 1}],
                [1],
            )
        ),
    )

    monkeypatch.setattr(
        "predictions.nfl.evaluation.ClassificationEvaluator.evaluate",
        Mock(return_value=make_evaluation_result("xgboost")),
    )

    result = NFLModelEvaluationService.compare_saved_models(
        test_season=2025,
        target="home_win",
        model_types=("xgboost",),
    )

    load_artifact.assert_called_once_with(
        model_type="xgboost",
        target="home_win",
    )

    assert len(result.results) == 1
    assert result.results[0].model_name == "xgboost"


def test_compare_saved_models_rejects_empty_model_types():
    with pytest.raises(
        ValueError,
        match="At least one model type is required",
    ):
        NFLModelEvaluationService.compare_saved_models(
            test_season=2025,
            target="home_win",
            model_types=(),
        )


def test_validate_artifacts_rejects_target_mismatch():
    artifacts = [
        make_artifact(
            model_type="logistic",
            target="home_win",
        ),
        make_artifact(
            model_type="random_forest",
            target="away_win",
        ),
    ]

    with pytest.raises(
        ValueError,
        match=("All model artifacts must match the requested target"),
    ):
        NFLModelEvaluationService._validate_artifacts(
            artifacts=artifacts,
            target="home_win",
        )


def test_validate_artifacts_rejects_training_season_mismatch():
    artifacts = [
        make_artifact(
            model_type="logistic",
            through_season=2024,
        ),
        make_artifact(
            model_type="random_forest",
            through_season=2023,
        ),
    ]

    with pytest.raises(
        ValueError,
        match=("All model artifacts must have the same training season cutoff"),
    ):
        NFLModelEvaluationService._validate_artifacts(
            artifacts=artifacts,
            target="home_win",
        )


def test_validate_artifacts_rejects_training_week_mismatch():
    artifacts = [
        make_artifact(
            model_type="logistic",
            through_season=2025,
            through_week=4,
        ),
        make_artifact(
            model_type="random_forest",
            through_season=2025,
            through_week=5,
        ),
    ]

    with pytest.raises(
        ValueError,
        match=("All model artifacts must have the same training week cutoff"),
    ):
        NFLModelEvaluationService._validate_artifacts(
            artifacts=artifacts,
            target="home_win",
        )


def test_validate_artifacts_rejects_empty_artifact_list():
    with pytest.raises(
        ValueError,
        match="At least one model artifact is required",
    ):
        NFLModelEvaluationService._validate_artifacts(
            artifacts=[],
            target="home_win",
        )


def test_compare_saved_models_rejects_training_on_test_season(
    monkeypatch,
):
    artifact = make_artifact(
        model_type="logistic",
        through_season=2025,
    )

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLModelArtifactService.load",
        Mock(return_value=artifact),
    )

    with pytest.raises(
        ValueError,
        match=("Model training cutoff must be before the evaluation season"),
    ):
        NFLModelEvaluationService.compare_saved_models(
            test_season=2025,
            target="home_win",
            model_types=("logistic",),
        )


def test_compare_saved_models_rejects_training_after_test_season(
    monkeypatch,
):
    artifact = make_artifact(
        model_type="logistic",
        through_season=2026,
    )

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLModelArtifactService.load",
        Mock(return_value=artifact),
    )

    with pytest.raises(
        ValueError,
        match=("Model training cutoff must be before the evaluation season"),
    ):
        NFLModelEvaluationService.compare_saved_models(
            test_season=2025,
            target="home_win",
            model_types=("logistic",),
        )


def test_compare_saved_models_rejects_missing_test_data(
    monkeypatch,
):
    artifact = make_artifact(
        model_type="logistic",
        through_season=2024,
    )

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLModelArtifactService.load",
        Mock(return_value=artifact),
    )

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLTrainingDataService.build_dataset",
        Mock(
            return_value=[
                {
                    "season": 2024,
                    "home_win": 1,
                }
            ]
        ),
    )

    with pytest.raises(
        ValueError,
        match=("No evaluation data available for season 2025"),
    ):
        NFLModelEvaluationService.compare_saved_models(
            test_season=2025,
            target="home_win",
            model_types=("logistic",),
        )
