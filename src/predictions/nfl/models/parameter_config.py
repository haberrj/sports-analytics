import json
from pathlib import Path
from typing import Any


class NFLModelParameterConfigService:
    MODEL_DIRECTORY = Path(__file__).resolve().parents[4] / "data" / "models"

    @classmethod
    def _config_path(
        cls,
        *,
        target: str,
    ) -> Path:
        return cls.MODEL_DIRECTORY / target / "parameters.json"

    @classmethod
    def load_all(
        cls,
        *,
        target: str,
    ) -> dict[str, dict[str, Any]]:
        config_path = cls._config_path(
            target=target,
        )

        if not config_path.exists():
            return {}

        with config_path.open() as file:
            return json.load(file)

    @classmethod
    def load(
        cls,
        *,
        model_type: str,
        target: str,
    ) -> dict[str, Any]:
        config = cls.load_all(
            target=target,
        )

        try:
            return config[model_type]
        except KeyError as exc:
            raise FileNotFoundError(f"No saved parameters found for {model_type} target {target}") from exc

    @classmethod
    def save(
        cls,
        *,
        model_type: str,
        target: str,
        parameters: dict[str, Any],
    ) -> Path:
        config_path = cls._config_path(
            target=target,
        )

        config_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        config = cls.load_all(
            target=target,
        )

        config[model_type] = parameters

        with config_path.open("w") as file:
            json.dump(
                config,
                file,
                indent=2,
                sort_keys=True,
            )

        return config_path
