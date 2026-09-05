import os
import warnings

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
warnings.filterwarnings(
    "ignore",
    message="Skipping features without any observed values",
    category=UserWarning,
)

from predictions.nfl.dataset import NFLTrainingDataService  # noqa: E402
from predictions.nfl.models.optimizer import ClassificationModelOptimizer  # noqa: E402
from predictions.nfl.models.random_forest import NFLRandomForestModel  # noqa: E402

dataset = NFLTrainingDataService.build_dataset()
validation_seasons = [2020, 2021, 2022, 2023]
test_season = [2024]

optimizer = ClassificationModelOptimizer(
    NFLRandomForestModel,
    validation_seasons=validation_seasons,
    objective='log_loss',
    random_state=42,
)

best, results = optimizer.bayesian_search(
    dataset=dataset,
    parameter_suggester=NFLRandomForestModel.suggest_random_forest_parameters,
    target='home_win',
    iterations=100
)

test_evaluator = ClassificationModelOptimizer(
    NFLRandomForestModel,
    validation_seasons=test_season,
    objective='log_loss',
    random_state=42
)

test_result = test_evaluator.evaluate_parameters(
    dataset=dataset,
    parameters=best.parameters,
    target="home_win",
)

print("Bayesian Optimization Results:")
print(f"Parameters: {best.parameters}")
print(f"Accuracy: {best.accuracy}")
print(f"Log Loss: {best.log_loss}")
print(f"Brier Score: {best.brier_score}")
print(f"ROC AUC: {best.roc_auc}")

print("Test Results:")
print(f"Parameters: {test_result.parameters}")
print(f"Accuracy: {test_result.accuracy}")
print(f"Log Loss: {test_result.log_loss}")
print(f"Brier Score: {test_result.brier_score}")
print(f"ROC AUC: {test_result.roc_auc}")