from typing import Any

from sklearn.feature_extraction import DictVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from predictions.nfl.models.base import PredictionModel


class NFLLogisticRegressionModel(PredictionModel):
    """Logistic regression model for NFL game outcomes."""

    def __init__(self, max_iterations: int = 1000):
        self.vectorizer: DictVectorizer = DictVectorizer(sparse=False)
        self.model: Pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("classifier", LogisticRegression(max_iter=max_iterations)),
            ]
        )

    def fit(self, features: list[dict], targets: list[Any]) -> None:
        transformed_features = self.vectorizer.fit_transform(features)
        self.model.fit(transformed_features, targets)

    def predict(self, features: list[dict]) -> list[Any]:
        transformed_features = self.vectorizer.transform(features)
        return self.model.predict(transformed_features).tolist()

    def predict_proba(self, features: list[dict]) -> list[float]:
        transformed_features = self.vectorizer.transform(features)
        probabilities = self.model.predict_proba(transformed_features)

        return probabilities[:, 1].tolist()
