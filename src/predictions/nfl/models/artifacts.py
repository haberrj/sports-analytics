import pickle
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from predictions.nfl.models.base import ClassificationModel


@dataclass
class NFLModelArtifact:
    model: ClassificationModel
    model_type: str
    target: str
    through_season: int
    parameters: dict[str, Any]
    trained_at: datetime


class NFLModelArtifactService:
    MODEL_DIRECTORY = Path(__file__).resolve().parents[4] / "data" / "models"

    @staticmethod
    def save(
        model: ClassificationModel,
        model_type: str,
        target: str,
        through_season: int,
        parameters: dict[str, Any],
    ) -> Path:
        artifact = NFLModelArtifact(
            model=model,
            model_type=model_type,
            target=target,
            through_season=through_season,
            parameters=parameters,
            trained_at=datetime.now(timezone.utc),  # noqa: UP017
        )

        model_directory = NFLModelArtifactService.MODEL_DIRECTORY / target

        model_directory.mkdir(parents=True, exist_ok=True)

        model_path = model_directory / f"{model_type}.pkl"

        with model_path.open("wb") as file:
            pickle.dump(artifact, file)

        return model_path

    @staticmethod
    def load(model_type: str, target: str) -> NFLModelArtifact:
        model_path = NFLModelArtifactService.MODEL_DIRECTORY / target / f"{model_type}.pkl"

        if not model_path.exists():
            raise FileNotFoundError(f"No saved model found at {model_path}")

        with model_path.open("rb") as file:
            artifact = pickle.load(file)

        return artifact
