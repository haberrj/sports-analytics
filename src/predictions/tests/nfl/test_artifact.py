from datetime import datetime
from unittest.mock import patch

import pytest

from predictions.nfl.models.artifacts import NFLModelArtifactService
from predictions.nfl.models.random_forest import NFLRandomForestModel


def test_save_and_load_model_artifact(tmp_path):
    model = NFLRandomForestModel(
        n_estimators=60,
        max_depth=6,
        min_samples_leaf=4,
        max_features=0.25,
        n_jobs=1,
    )

    parameters = {
        "n_estimators": 60,
        "max_depth": 6,
        "min_samples_leaf": 4,
        "max_features": 0.25,
    }

    with patch.object(
        NFLModelArtifactService,
        "MODEL_DIRECTORY",
        tmp_path,
    ):
        model_path = NFLModelArtifactService.save(
            model=model,
            model_type="random_forest",
            target="home_win",
            through_season=2024,
            parameters=parameters,
        )

        artifact = NFLModelArtifactService.load(
            model_type="random_forest",
            target="home_win",
        )

    assert model_path == (tmp_path / "home_win" / "random_forest.pkl")

    assert model_path.exists()
    assert artifact.model_type == "random_forest"
    assert artifact.target == "home_win"
    assert artifact.through_season == 2024
    assert artifact.parameters == parameters
    assert isinstance(artifact.trained_at, datetime)
    assert isinstance(
        artifact.model,
        NFLRandomForestModel,
    )


def test_load_model_artifact_raises_when_missing(tmp_path):
    with patch.object(
        NFLModelArtifactService,
        "MODEL_DIRECTORY",
        tmp_path,
    ), pytest.raises(
        FileNotFoundError,
        match="No saved model found",
    ):
        NFLModelArtifactService.load(
            model_type="random_forest",
            target="home_win",
        )
