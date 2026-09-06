import os
import warnings

import django


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

django.setup()

warnings.filterwarnings(
    "ignore",
    message="Skipping features without any observed values.*",
)

from predictions.nfl.models.training import NFLTrainingService
from predictions.nfl.models.xgboost import NFLXGBoostModel


result = NFLTrainingService.optimize_model(
    model_class=NFLXGBoostModel,
    parameter_suggester=NFLXGBoostModel.suggest_xgboost_parameters,
    validation_seasons=[2020, 2021, 2022, 2023],
    target='home_win',
    iterations=100,
    model_parameters={
        'n_jobs': -1
    }
)

print(result)