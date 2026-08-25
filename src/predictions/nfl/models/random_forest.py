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
        ) -> None:
        super().__init__()
        self.model: Pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "classifier", RandomForestClassifier(
                        n_estimators=n_estimators,
                        max_depth=max_depth,
                        min_samples_leaf=min_samples_leaf,
                        max_features=max_features,
                        random_state=random_state,
                    )
                )
            ]
        )

