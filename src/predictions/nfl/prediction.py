from dataclasses import dataclass

from games.models import Game, Season
from predictions.nfl.dataset import NFLTrainingDataService
from predictions.nfl.models.artifacts import NFLModelArtifactService
from predictions.nfl.models.base import ClassificationModel


@dataclass
class NFLGamePrediction:
    game_id: str
    home_team: str
    away_team: str
    probabilities: dict[str, float]
    home_score: int | None = None
    away_score: int | None = None
    error: dict[str, str] | None = None


class NFLPredictionService:
    @staticmethod
    def predict_probability(game: Game, target: str, model_type: str) -> float:
        features = NFLTrainingDataService.build_feature_row(game)

        if features is None:
            raise ValueError(f"Unable to build prediction features for game {game.external_id}.")

        artifact = NFLModelArtifactService.load(model_type=model_type, target=target)

        probabilities = artifact.model.predict_proba([features])

        return float(probabilities[0])

    @staticmethod
    def predict_week(season: Season, week: int, model_types: list[str], target: str) -> list[NFLGamePrediction]:
        games = Game.objects.filter(season=season, week__number=week).select_related("home_team", "away_team")

        predictions = []
        for game in games:
            probabilities = {}
            errors = {}
            for model_type in model_types:
                try:
                    probabilities[model_type] = NFLPredictionService.predict_probability(
                        game=game, target=target, model_type=model_type
                    )
                except (ValueError, FileNotFoundError) as error:
                    errors[model_type] = str(error)

            prediction = NFLGamePrediction(
                game_id=game.external_id,
                home_team=game.home_team.abbreviation,
                away_team=game.away_team.abbreviation,
                probabilities=probabilities,
                home_score=game.home_score,
                away_score=game.away_score,
                error=errors or None,
            )

            predictions.append(prediction)

        return predictions

    @staticmethod
    def predict_probability_with_model(
        game: Game,
        model: ClassificationModel,
    ) -> float:
        features = NFLTrainingDataService.build_feature_row(game)

        if features is None:
            raise ValueError(f"Unable to build prediction features for game {game.external_id}.")

        probabilities = model.predict_proba([features])

        return float(probabilities[0])
