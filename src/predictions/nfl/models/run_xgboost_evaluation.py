import os

import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

django.setup()

from predictions.nfl.models.training import NFLTrainingService
from predictions.nfl.models.xgboost import NFLXGBoostModel


XGBOOST_PARAMETERS = {
    "n_estimators": 299,
    "max_depth": 1,
    "learning_rate": 0.029849909352061013,
    "min_child_weight": 9.995824848019023,
    "subsample": 0.8925937442592672,
    "colsample_bytree": 0.8774564543659042,
    "reg_alpha": 1.5644798926956065,
    "reg_lambda": 1.49230202784724,
}


result = NFLTrainingService.evaluate_model(
    model_class=NFLXGBoostModel,
    parameters=XGBOOST_PARAMETERS,
    test_season=2024,
    target="home_win",
    model_parameters={
        "n_jobs": -1,
    },
)

print(result)