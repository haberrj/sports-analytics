from random import Random
from typing import Any

from optuna.trial import Trial
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from predictions.nfl.models.base import ClassificationModel


class NFLRandomForestModel(ClassificationModel):
    """Random forest model for NFL game outcomes.
    Optimal values for home_win target
    max_depth = 15
    min_samples_leaf = 7
    n_estimators = 50
    max_features = sqrt
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int | None = None,
        min_samples_leaf: int = 1,
        max_features: str | float | None = "sqrt",
        random_state: int = 42,
        n_jobs: int = -1,
    ) -> None:
        super().__init__()
        self.model: Pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=n_estimators,
                        max_depth=max_depth,
                        min_samples_leaf=min_samples_leaf,
                        max_features=max_features,
                        random_state=random_state,
                        n_jobs=n_jobs,
                    ),
                ),
            ]
        )

    @staticmethod
    def sample_random_forest_parameters(random: Random) -> dict[str, Any]:
        return {
            "max_depth": random.randint(1, 20),
            "min_samples_leaf": random.randint(1, 15),
            "n_estimators": random.randint(25, 150),
            "max_features": random.choice(
                [
                    "sqrt",
                    "log2",
                    0.25,
                    0.5,
                    0.75,
                    1.0,
                ]
            ),
        }

    @staticmethod
    def suggest_random_forest_parameters(trial: Trial) -> dict[str, Any]:
        return {
            "max_depth": trial.suggest_int(
                "max_depth",
                1,
                20,
            ),
            "min_samples_leaf": trial.suggest_int(
                "min_samples_leaf",
                1,
                15,
            ),
            "n_estimators": trial.suggest_int(
                "n_estimators",
                25,
                150,
            ),
            "max_features": trial.suggest_categorical(
                "max_features",
                [
                    "sqrt",
                    "log2",
                    0.25,
                    0.5,
                    0.75,
                    1.0,
                ],
            ),
        }
