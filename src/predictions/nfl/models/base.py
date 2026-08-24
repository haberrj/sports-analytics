from abc import ABC, abstractmethod
from typing import Any


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
