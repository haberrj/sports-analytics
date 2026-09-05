from unittest.mock import MagicMock, patch

from predictions.nfl.models.artifacts import NFLModelArtifact
from predictions.nfl.prediction import NFLPredictionService


@patch(
    "predictions.nfl.prediction."
    "NFLModelArtifactService.load"
)
@patch(
    "predictions.nfl.prediction."
    "NFLTrainingDataService.build_feature_row"
)
def test_predict_probability(
    mock_build_feature_row,
    mock_load,
):
    game = MagicMock()
    game.external_id = "2025_05_BUF_KC"

    features = {
        "home_team": "BUF",
        "away_team": "KC",
        "week": 5,
    }
    mock_build_feature_row.return_value = features

    model = MagicMock()
    model.predict_proba.return_value = [0.73]

    artifact = MagicMock(spec=NFLModelArtifact)
    artifact.model = model
    mock_load.return_value = artifact

    result = NFLPredictionService.predict_probability(
        game=game,
        target="home_win",
        model_type="random_forest",
    )

    mock_build_feature_row.assert_called_once_with(game)

    mock_load.assert_called_once_with(
        model_type="random_forest",
        target="home_win",
    )

    model.predict_proba.assert_called_once_with([features])

    assert result == 0.73
