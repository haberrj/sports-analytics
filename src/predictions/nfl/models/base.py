from abc import ABC, abstractmethod
from typing import Any

from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline


class PredictionModel(ABC):
    """Base interface for the prediction models."""

    @abstractmethod
    def fit(self, features: list[dict], targets: list[Any]) -> None:
        """Train the model.

        Args:
            features: Pre-game feature rows used for training.
            targets: Target values corresponding to each feature row.
        """
        raise NotImplementedError

    @abstractmethod
    def predict(self, features: list[dict]) -> list[Any]:
        """Generate predictions for feature rows.

        Args:
            features: Feature rows to predict.

        Returns:
            Predictions for each supplied feature row.
        """
        raise NotImplementedError


class ClassificationModel(PredictionModel):
    """Base interface for the prediction models."""

    def __init__(self):
        self.vectorizer: DictVectorizer = DictVectorizer(sparse=False)
        self.model: Pipeline

    def fit(self, features: list[dict], targets: list[Any]) -> None:
        """Train the classifier.

        Args:
            features: Pre-game feature rows used for training.
            targets: Target classes corresponding to each feature row.
        """
        transformed_features = self.vectorizer.fit_transform(features)
        self.model.fit(transformed_features, targets)

    def predict(self, features: list[dict]) -> list[Any]:
        """Generate class predictions.

        Args:
            features: Feature rows to predict.

        Returns:
            Predicted class for each supplied feature row.
        """
        transformed_features = self.vectorizer.transform(features)
        return self.model.predict(transformed_features).tolist()

    def predict_proba(self, features: list[dict]) -> list[Any]:
        """Generate positive-class probabilities.

        Args:
            features: Feature rows to predict.

        Returns:
            Positive-class probability for each supplied feature row.
        """
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

    def get_performance_stats(self, features, targets: list[Any]) -> dict[str, float]:
        preds = self.predict(features)
        preds_prob = self.predict_proba(features)
        output = {
            "baseline_accuracy": self.baseline_accuracy(targets),
            "accuracy": accuracy_score(targets, preds),
            "log_loss": log_loss(targets, preds_prob),
            "brier_score": brier_score_loss(targets, preds_prob),
            "roc_auc": roc_auc_score(targets, preds_prob),
        }
        return output

    @staticmethod
    def baseline_accuracy(targets: list[Any]) -> float:
        return max(
            sum(targets) / len(targets),
            1 - (sum(targets) / len(targets)),
        )
