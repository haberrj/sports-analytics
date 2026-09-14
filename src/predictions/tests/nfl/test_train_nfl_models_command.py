from unittest.mock import call, patch

import pytest
from django.core.management import call_command

from predictions.management.commands import train_nfl_models
from predictions.nfl.models.logistic import NFLLogisticRegressionModel
from predictions.nfl.models.random_forest import NFLRandomForestModel
from predictions.nfl.models.xgboost import NFLXGBoostModel


def test_train_models_uses_saved_optimized_parameters():
    rf_parameters = {
        "max_depth": 6,
        "min_samples_leaf": 4,
        "n_estimators": 60,
        "max_features": 0.25,
    }

    xgb_parameters = {
        "n_estimators": 200,
        "max_depth": 2,
        "learning_rate": 0.05,
        "min_child_weight": 5.0,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_alpha": 1.0,
        "reg_lambda": 1.5,
    }

    def load_parameters(*, model_type, target):
        assert target == "home_win"

        return {
            "random_forest": rf_parameters,
            "xgboost": xgb_parameters,
        }[model_type]

    with (
        patch.object(
            train_nfl_models.NFLModelParameterConfigService,
            "load",
            side_effect=load_parameters,
        ) as mock_load_parameters,
        patch.object(
            train_nfl_models.NFLTrainingService,
            "train_and_save_model",
        ) as mock_train_and_save_model,
    ):
        call_command(
            "train_nfl_models",
            target="home_win",
            through_season=2024,
        )

    assert mock_load_parameters.call_args_list == [
        call(
            model_type="random_forest",
            target="home_win",
        ),
        call(
            model_type="xgboost",
            target="home_win",
        ),
    ]

    assert mock_train_and_save_model.call_args_list == [
        call(
            model_class=NFLRandomForestModel,
            model_type="random_forest",
            parameters=rf_parameters,
            target="home_win",
            through_season=2024,
            through_week=None,
            model_parameters={
                "n_jobs": -1,
            },
        ),
        call(
            model_class=NFLLogisticRegressionModel,
            model_type="logistic",
            parameters={
                "max_iterations": 1000,
            },
            target="home_win",
            through_season=2024,
            through_week=None,
        ),
        call(
            model_class=NFLXGBoostModel,
            model_type="xgboost",
            parameters=xgb_parameters,
            target="home_win",
            through_season=2024,
            through_week=None,
        ),
    ]


def test_train_models_passes_through_week():
    with (
        patch.object(
            train_nfl_models.NFLModelParameterConfigService,
            "load",
            side_effect=[
                {
                    "max_depth": 6,
                },
                {
                    "max_depth": 2,
                },
            ],
        ),
        patch.object(
            train_nfl_models.NFLTrainingService,
            "train_and_save_model",
        ) as mock_train_and_save_model,
    ):
        call_command(
            "train_nfl_models",
            target="home_win",
            through_season=2025,
            through_week=8,
        )

    assert mock_train_and_save_model.call_count == 3

    for training_call in mock_train_and_save_model.call_args_list:
        assert training_call.kwargs["through_season"] == 2025
        assert training_call.kwargs["through_week"] == 8


def test_train_models_does_not_train_when_parameters_missing():
    with (
        patch.object(
            train_nfl_models.NFLModelParameterConfigService,
            "load",
            side_effect=FileNotFoundError("No saved parameters found"),
        ),
        patch.object(
            train_nfl_models.NFLTrainingService,
            "train_and_save_model",
        ) as mock_train_and_save_model,
        pytest.raises(
            FileNotFoundError,
            match="No saved parameters found",
        ),
    ):
        call_command(
            "train_nfl_models",
            target="home_win",
            through_season=2024,
        )

    mock_train_and_save_model.assert_not_called()
