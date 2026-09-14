from unittest.mock import call, patch

from django.core.management import call_command

from predictions.management.commands import optimize_nfl_models
from predictions.nfl.models.optimizer import OptimizationResult
from predictions.nfl.models.random_forest import NFLRandomForestModel
from predictions.nfl.models.xgboost import NFLXGBoostModel


def test_optimize_all_models_saves_best_parameters():
    rf_result = OptimizationResult(
        parameters={
            "max_depth": 6,
            "min_samples_leaf": 4,
            "n_estimators": 60,
            "max_features": 0.25,
        },
        accuracy=0.62,
        log_loss=0.6503,
        brier_score=0.23,
        roc_auc=0.67,
    )

    xgb_result = OptimizationResult(
        parameters={
            "n_estimators": 200,
            "max_depth": 2,
            "learning_rate": 0.05,
            "min_child_weight": 5.0,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "reg_alpha": 1.0,
            "reg_lambda": 1.5,
        },
        accuracy=0.63,
        log_loss=0.6510,
        brier_score=0.23,
        roc_auc=0.68,
    )

    with (
        patch.object(
            optimize_nfl_models.NFLTrainingService,
            "optimize_model",
            side_effect=[
                rf_result,
                xgb_result,
            ],
        ) as mock_optimize_model,
        patch.object(
            optimize_nfl_models.NFLModelParameterConfigService,
            "save",
        ) as mock_save_parameters,
    ):
        call_command(
            "optimize_nfl_models",
            target="home_win",
            validation_seasons=[
                2021,
                2022,
                2023,
                2024,
            ],
            iterations=50,
            model="all",
        )

    assert mock_optimize_model.call_args_list == [
        call(
            model_class=NFLRandomForestModel,
            parameter_suggester=(NFLRandomForestModel.suggest_random_forest_parameters),
            validation_seasons=[
                2021,
                2022,
                2023,
                2024,
            ],
            target="home_win",
            iterations=50,
            model_parameters={
                "n_jobs": -1,
            },
        ),
        call(
            model_class=NFLXGBoostModel,
            parameter_suggester=(NFLXGBoostModel.suggest_xgboost_parameters),
            validation_seasons=[
                2021,
                2022,
                2023,
                2024,
            ],
            target="home_win",
            iterations=50,
            model_parameters={
                "n_jobs": -1,
            },
        ),
    ]

    assert mock_save_parameters.call_args_list == [
        call(
            model_type="random_forest",
            target="home_win",
            parameters=rf_result.parameters,
        ),
        call(
            model_type="xgboost",
            target="home_win",
            parameters=xgb_result.parameters,
        ),
    ]


def test_optimize_random_forest_only():
    result = OptimizationResult(
        parameters={
            "max_depth": 6,
        },
        accuracy=0.62,
        log_loss=0.65,
        brier_score=0.23,
        roc_auc=0.67,
    )

    with (
        patch.object(
            optimize_nfl_models.NFLTrainingService,
            "optimize_model",
            return_value=result,
        ) as mock_optimize_model,
        patch.object(
            optimize_nfl_models.NFLModelParameterConfigService,
            "save",
        ) as mock_save_parameters,
    ):
        call_command(
            "optimize_nfl_models",
            target="home_win",
            validation_seasons=[
                2023,
                2024,
            ],
            iterations=10,
            model="random_forest",
        )

    mock_optimize_model.assert_called_once_with(
        model_class=NFLRandomForestModel,
        parameter_suggester=(NFLRandomForestModel.suggest_random_forest_parameters),
        validation_seasons=[
            2023,
            2024,
        ],
        target="home_win",
        iterations=10,
        model_parameters={
            "n_jobs": -1,
        },
    )

    mock_save_parameters.assert_called_once_with(
        model_type="random_forest",
        target="home_win",
        parameters=result.parameters,
    )


def test_optimize_xgboost_only():
    result = OptimizationResult(
        parameters={
            "max_depth": 2,
        },
        accuracy=0.63,
        log_loss=0.65,
        brier_score=0.23,
        roc_auc=0.68,
    )

    with (
        patch.object(
            optimize_nfl_models.NFLTrainingService,
            "optimize_model",
            return_value=result,
        ) as mock_optimize_model,
        patch.object(
            optimize_nfl_models.NFLModelParameterConfigService,
            "save",
        ) as mock_save_parameters,
    ):
        call_command(
            "optimize_nfl_models",
            target="home_win",
            validation_seasons=[
                2023,
                2024,
            ],
            iterations=10,
            model="xgboost",
        )

    mock_optimize_model.assert_called_once_with(
        model_class=NFLXGBoostModel,
        parameter_suggester=(NFLXGBoostModel.suggest_xgboost_parameters),
        validation_seasons=[
            2023,
            2024,
        ],
        target="home_win",
        iterations=10,
        model_parameters={
            "n_jobs": -1,
        },
    )

    mock_save_parameters.assert_called_once_with(
        model_type="xgboost",
        target="home_win",
        parameters=result.parameters,
    )
