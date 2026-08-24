from typing import Any

from sklearn.feature_extraction import DictVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from predictions.nfl.models.base import PredictionModel


class NFLLogisticRegressionModel(PredictionModel):
    """Logistic regression model for NFL game outcomes.

    Initial validation results (2023-2024):
    - Accuracy: 0.5965
    - Home-team baseline accuracy: 0.5649
    - Log loss: 0.68375
    - Baseline log loss: 0.68470
    - Brier score: 0.24406
    - Baseline Brier score: 0.24579
    - ROC AUC: 0.6003

    Initial test results (2024-2025):
    - Accuracy: 0.6509
    - Home-team baseline accuracy: 0.5404
    - Log loss: 0.63687
    - Brier score: 0.22262
    - ROC AUC: 0.6928
    """

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

    def accuracy(self, features: list[dict], targets: list[Any]) -> float:
        predictions = self.predict(features)
        return accuracy_score(targets, predictions)

    def log_loss(self, features: list[dict], targets: list[Any]) -> float:
        predictions_proba = self.predict_proba(features)
        return log_loss(targets, predictions_proba)

    def brier_score(self, features: list[dict], targets: list[Any]) -> float:
        predictions_proba = self.predict_proba(features)
        return brier_score_loss(targets, predictions_proba)

    def roc_auc(self, features: list[dict], targets: list[Any]) -> float:
        predictions_proba = self.predict_proba(features)
        return roc_auc_score(targets, predictions_proba)

    @staticmethod
    def baseline_accuracy(targets: list[Any]) -> float:
        return max(
            sum(targets) / len(targets),
            1 - (sum(targets) / len(targets)),
        )
