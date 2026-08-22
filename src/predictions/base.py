from abc import ABC, abstractmethod
from typing import TypeVar

from django.db import models

ProfileT = TypeVar("ProfileT", bound=models.Model)
GameT = TypeVar("GameT", bound=models.Model)
TeamT = TypeVar("TeamT", bound=models.Model)


class TrainingDataService[ProfileT: models.Model, GameT: models.Model, TeamT: models.Model](ABC):
    @staticmethod
    @abstractmethod
    def get_profile_before_game(team: TeamT, game: GameT) -> ProfileT | None:
        pass

    @staticmethod
    @abstractmethod
    def build_training_row(game: GameT) -> dict:
        pass
