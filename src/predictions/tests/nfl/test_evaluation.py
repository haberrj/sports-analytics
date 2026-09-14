from unittest.mock import Mock

import pytest

from predictions.nfl.evaluation import (
    NFLModelEvaluationConfig,
    NFLModelEvaluationService,
)


class FakeModel:
    instances: list["FakeModel"] = []

    def __init__(self, **kwargs):
        self.parameters = kwargs
        self.fit_features = None
        self.fit_targets = None

        FakeModel.instances.append(self)

    def fit(
        self,
        features: list[dict],
        targets: list[int],
    ) -> None:
        self.fit_features = features
        self.fit_targets = targets

    def predict(self, features: list[dict]) -> list[int]:
        return [1 for _ in features]

    def predict_proba(
        self,
        features: list[dict],
    ) -> list[float]:
        return [0.6 for _ in features]

    def get_performance_stats(
        self,
        features: list[dict],
        targets: list[int],
    ) -> dict[str, float]:
        return {
            "accuracy": 0.75,
            "log_loss": 0.5,
            "brier_score": 0.2,
            "roc_auc": 0.8,
        }


@pytest.fixture(autouse=True)
def reset_fake_models():
    FakeModel.instances = []


def test_compare_models_uses_only_seasons_before_test_season(
    monkeypatch,
):
    dataset = [
        {
            "season": 2022,
            "feature": 1,
            "home_win": 0,
        },
        {
            "season": 2023,
            "feature": 2,
            "home_win": 1,
        },
        {
            "season": 2024,
            "feature": 3,
            "home_win": 0,
        },
        {
            "season": 2025,
            "feature": 4,
            "home_win": 1,
        },
        {
            "season": 2026,
            "feature": 5,
            "home_win": 1,
        },
    ]

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLTrainingDataService.build_dataset",
        Mock(return_value=dataset),
    )

    def fake_split_features_target(
        *,
        rows,
        target,
    ):
        return (
            [{"feature": row["feature"]} for row in rows],
            [row[target] for row in rows],
        )

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLPreprocessingService.split_features_target",
        fake_split_features_target,
    )

    result = NFLModelEvaluationService.compare_models(
        model_configs=[
            NFLModelEvaluationConfig(
                name="model_a",
                model_class=FakeModel,
                parameters={},
            ),
        ],
        test_season=2025,
        target="home_win",
    )

    assert result.test_season == 2025
    assert result.training_seasons == [
        2022,
        2023,
        2024,
    ]

    model = FakeModel.instances[0]

    assert model.fit_features == [
        {"feature": 1},
        {"feature": 2},
        {"feature": 3},
    ]

    assert model.fit_targets == [
        0,
        1,
        0,
    ]

    assert 2026 not in result.training_seasons


def test_compare_models_evaluates_all_models_on_same_test_period(
    monkeypatch,
):
    dataset = [
        {
            "season": 2023,
            "feature": 1,
            "home_win": 0,
        },
        {
            "season": 2024,
            "feature": 2,
            "home_win": 1,
        },
        {
            "season": 2025,
            "feature": 3,
            "home_win": 0,
        },
        {
            "season": 2025,
            "feature": 4,
            "home_win": 1,
        },
    ]

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLTrainingDataService.build_dataset",
        Mock(return_value=dataset),
    )

    def fake_split_features_target(
        *,
        rows,
        target,
    ):
        return (
            [{"feature": row["feature"]} for row in rows],
            [row[target] for row in rows],
        )

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLPreprocessingService.split_features_target",
        fake_split_features_target,
    )

    result = NFLModelEvaluationService.compare_models(
        model_configs=[
            NFLModelEvaluationConfig(
                name="logistic",
                model_class=FakeModel,
                parameters={
                    "parameter": "lr",
                },
            ),
            NFLModelEvaluationConfig(
                name="random_forest",
                model_class=FakeModel,
                parameters={
                    "parameter": "rf",
                },
            ),
            NFLModelEvaluationConfig(
                name="xgboost",
                model_class=FakeModel,
                parameters={
                    "parameter": "xgb",
                },
            ),
        ],
        test_season=2025,
        target="home_win",
        calibration_bins=5,
    )

    assert len(result.results) == 3

    assert [evaluation.model_name for evaluation in result.results] == [
        "logistic",
        "random_forest",
        "xgboost",
    ]

    assert len(FakeModel.instances) == 3

    for model in FakeModel.instances:
        assert model.fit_features == [
            {"feature": 1},
            {"feature": 2},
        ]

        assert model.fit_targets == [
            0,
            1,
        ]


def test_compare_models_passes_parameters_to_model(
    monkeypatch,
):
    dataset = [
        {
            "season": 2024,
            "feature": 1,
            "home_win": 0,
        },
        {
            "season": 2025,
            "feature": 2,
            "home_win": 1,
        },
    ]

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLTrainingDataService.build_dataset",
        Mock(return_value=dataset),
    )

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLPreprocessingService.split_features_target",
        lambda *, rows, target: (
            [{"feature": row["feature"]} for row in rows],
            [row[target] for row in rows],
        ),
    )

    NFLModelEvaluationService.compare_models(
        model_configs=[
            NFLModelEvaluationConfig(
                name="test_model",
                model_class=FakeModel,
                parameters={
                    "max_depth": 5,
                },
                model_parameters={
                    "random_state": 42,
                },
            ),
        ],
        test_season=2025,
        target="home_win",
    )

    assert FakeModel.instances[0].parameters == {
        "max_depth": 5,
        "random_state": 42,
    }


def test_compare_models_rejects_empty_model_configs():
    with pytest.raises(
        ValueError,
        match="At least one model configuration is required",
    ):
        NFLModelEvaluationService.compare_models(
            model_configs=[],
            test_season=2025,
            target="home_win",
        )


def test_compare_models_rejects_missing_training_data(
    monkeypatch,
):
    dataset = [
        {
            "season": 2025,
            "feature": 1,
            "home_win": 1,
        }
    ]

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLTrainingDataService.build_dataset",
        Mock(return_value=dataset),
    )

    with pytest.raises(
        ValueError,
        match="No training data available before season 2025",
    ):
        NFLModelEvaluationService.compare_models(
            model_configs=[
                NFLModelEvaluationConfig(
                    name="model",
                    model_class=FakeModel,
                    parameters={},
                )
            ],
            test_season=2025,
            target="home_win",
        )


def test_compare_models_rejects_missing_test_data(
    monkeypatch,
):
    dataset = [
        {
            "season": 2023,
            "feature": 1,
            "home_win": 0,
        },
        {
            "season": 2024,
            "feature": 2,
            "home_win": 1,
        },
    ]

    monkeypatch.setattr(
        "predictions.nfl.evaluation.NFLTrainingDataService.build_dataset",
        Mock(return_value=dataset),
    )

    with pytest.raises(
        ValueError,
        match="No evaluation data available for season 2025",
    ):
        NFLModelEvaluationService.compare_models(
            model_configs=[
                NFLModelEvaluationConfig(
                    name="model",
                    model_class=FakeModel,
                    parameters={},
                )
            ],
            test_season=2025,
            target="home_win",
        )
