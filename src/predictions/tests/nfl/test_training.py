from unittest.mock import MagicMock, patch

from predictions.nfl.models.optimizer import OptimizationResult
from predictions.nfl.models.random_forest import NFLRandomForestModel
from predictions.nfl.models.training import NFLTrainingService


@patch("predictions.nfl.models.training.ClassificationModelOptimizer")
@patch("predictions.nfl.models.training.NFLTrainingDataService.build_dataset")
def test_optimize_random_forest(
    mock_build_dataset,
    mock_optimizer_class,
):
    dataset = [
        {"season": 2020, "home_win": 1},
        {"season": 2021, "home_win": 0},
    ]

    expected_result = OptimizationResult(
        parameters={
            "max_depth": 6,
            "min_samples_leaf": 4,
            "n_estimators": 60,
            "max_features": 0.25,
        },
        accuracy=0.60,
        log_loss=0.65,
        brier_score=0.23,
        roc_auc=0.66,
    )

    mock_build_dataset.return_value = dataset

    optimizer = MagicMock()
    mock_optimizer_class.return_value = optimizer

    optimizer.bayesian_search.return_value = (
        expected_result,
        [],
    )

    result = NFLTrainingService.optimize_random_forest(
        validation_seasons=[
            2020,
            2021,
            2022,
            2023,
        ],
        target="home_win",
        iterations=100,
        n_jobs=4,
    )

    mock_build_dataset.assert_called_once_with()

    mock_optimizer_class.assert_called_once_with(
        NFLRandomForestModel,
        validation_seasons=[
            2020,
            2021,
            2022,
            2023,
        ],
        objective="log_loss",
        random_state=42,
        model_parameters={
            "n_jobs": 4,
        },
    )

    optimizer.bayesian_search.assert_called_once_with(
        dataset=dataset,
        parameter_suggester=(NFLRandomForestModel.suggest_random_forest_parameters),
        target="home_win",
        iterations=100,
    )

    assert result == expected_result


@patch("predictions.nfl.models.training.ClassificationModelOptimizer")
@patch("predictions.nfl.models.training.NFLTrainingDataService.build_dataset")
def test_evaluate_random_forest(
    mock_build_dataset,
    mock_optimizer_class,
):
    dataset = [
        {"season": 2024, "home_win": 1},
    ]

    parameters = {
        "max_depth": 6,
        "min_samples_leaf": 4,
        "n_estimators": 60,
        "max_features": 0.25,
    }

    expected_result = OptimizationResult(
        parameters=parameters,
        accuracy=0.66,
        log_loss=0.61,
        brier_score=0.21,
        roc_auc=0.73,
    )

    mock_build_dataset.return_value = dataset

    optimizer = MagicMock()
    mock_optimizer_class.return_value = optimizer

    optimizer.evaluate_parameters.return_value = expected_result

    result = NFLTrainingService.evaluate_random_forest(
        parameters=parameters,
        test_season=2024,
        target="home_win",
        n_jobs=4,
    )

    mock_build_dataset.assert_called_once_with()

    mock_optimizer_class.assert_called_once_with(
        NFLRandomForestModel,
        validation_seasons=[2024],
        objective="log_loss",
        random_state=42,
        model_parameters={
            "n_jobs": 4,
        },
    )

    optimizer.evaluate_parameters.assert_called_once_with(
        dataset=dataset,
        parameters=parameters,
        target="home_win",
    )

    assert result == expected_result
