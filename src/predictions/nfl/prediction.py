from games.models import Game
from predictions.nfl.dataset import NFLTrainingDataService
from predictions.nfl.models.artifacts import NFLModelArtifactService


class NFLPredictionService:
    @staticmethod
    def predict_probability(game: Game, target: str, model_type: str) -> float:
        features = NFLTrainingDataService.build_feature_row(game)

        if features is None:
            raise ValueError(f"Unable to build prediction features for game {game.external_id}.")

        artifact = NFLModelArtifactService.load(model_type=model_type, target=target)

        probabilities = artifact.model.predict_proba([features])

        return float(probabilities[0])
