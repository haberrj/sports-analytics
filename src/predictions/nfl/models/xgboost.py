from typing import Any

from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from predictions.nfl.models.base import ClassificationModel


class NFLXGBoostModel(ClassificationModel):
    def __init__(
        self,
        n_estimators: int,
        max_depth: int,
        learning_rate: float,
        min_child_weight: float,
        subsample: float,
        colsample_bytree: float,
        reg_alpha: float,
        reg_lambda: float,
        random_state: int = 42,
        n_jobs: int = -1,
    ) -> None:
        super().__init__()
        self.model = Pipeline(
            [
                (
                    "imputer",
                    SimpleImputer(strategy="median"),
                ),
                (
                    "classifier",
                    XGBClassifier(
                        n_estimators=n_estimators,
                        max_depth=max_depth,
                        learning_rate=learning_rate,
                        min_child_weight=min_child_weight,
                        subsample=subsample,
                        colsample_bytree=colsample_bytree,
                        reg_alpha=reg_alpha,
                        reg_lambda=reg_lambda,
                        random_state=random_state,
                        n_jobs=n_jobs,
                        eval_metric="logloss",
                    ),
                ),
            ]
        )

    @staticmethod
    def suggest_xgboost_parameters(trial) -> dict[str, Any]:
        return {
            "n_estimators": trial.suggest_int(
                "n_estimators",
                50,
                300,
            ),
            "max_depth": trial.suggest_int(
                "max_depth",
                1,
                4,
            ),
            "learning_rate": trial.suggest_float(
                "learning_rate",
                0.01,
                0.3,
                log=True,
            ),
            "min_child_weight": trial.suggest_float(
                "min_child_weight",
                1.0,
                10.0,
            ),
            "subsample": trial.suggest_float(
                "subsample",
                0.6,
                1.0,
            ),
            "colsample_bytree": trial.suggest_float(
                "colsample_bytree",
                0.5,
                1.0,
            ),
            "reg_alpha": trial.suggest_float(
                "reg_alpha",
                0.0,
                2.0,
            ),
            "reg_lambda": trial.suggest_float(
                "reg_lambda",
                0.3,
                5.0,
            ),
        }
