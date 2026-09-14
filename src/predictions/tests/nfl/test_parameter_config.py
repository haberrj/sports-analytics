from unittest.mock import patch

import pytest

from predictions.nfl.models.parameter_config import (
    NFLModelParameterConfigService,
)


def test_save_and_load_parameters(tmp_path):
    parameters = {
        "max_depth": 6,
        "n_estimators": 60,
    }

    with patch.object(
        NFLModelParameterConfigService,
        "MODEL_DIRECTORY",
        tmp_path,
    ):
        config_path = NFLModelParameterConfigService.save(
            model_type="random_forest",
            target="home_win",
            parameters=parameters,
        )

        loaded_parameters = NFLModelParameterConfigService.load(
            model_type="random_forest",
            target="home_win",
        )

    assert config_path == (tmp_path / "home_win" / "parameters.json")

    assert loaded_parameters == parameters


def test_save_preserves_existing_model_parameters(tmp_path):
    random_forest_parameters = {
        "max_depth": 6,
        "n_estimators": 60,
    }

    xgboost_parameters = {
        "max_depth": 2,
        "learning_rate": 0.05,
    }

    with patch.object(
        NFLModelParameterConfigService,
        "MODEL_DIRECTORY",
        tmp_path,
    ):
        NFLModelParameterConfigService.save(
            model_type="random_forest",
            target="home_win",
            parameters=random_forest_parameters,
        )

        NFLModelParameterConfigService.save(
            model_type="xgboost",
            target="home_win",
            parameters=xgboost_parameters,
        )

        config = NFLModelParameterConfigService.load_all(
            target="home_win",
        )

    assert config == {
        "random_forest": random_forest_parameters,
        "xgboost": xgboost_parameters,
    }


def test_save_updates_existing_model_parameters(tmp_path):
    with patch.object(
        NFLModelParameterConfigService,
        "MODEL_DIRECTORY",
        tmp_path,
    ):
        NFLModelParameterConfigService.save(
            model_type="random_forest",
            target="home_win",
            parameters={
                "max_depth": 5,
            },
        )

        NFLModelParameterConfigService.save(
            model_type="random_forest",
            target="home_win",
            parameters={
                "max_depth": 8,
            },
        )

        parameters = NFLModelParameterConfigService.load(
            model_type="random_forest",
            target="home_win",
        )

    assert parameters == {
        "max_depth": 8,
    }


def test_load_all_returns_empty_dict_when_config_missing(
    tmp_path,
):
    with patch.object(
        NFLModelParameterConfigService,
        "MODEL_DIRECTORY",
        tmp_path,
    ):
        config = NFLModelParameterConfigService.load_all(
            target="home_win",
        )

    assert config == {}


def test_load_raises_when_model_parameters_missing(
    tmp_path,
):
    with patch.object(
        NFLModelParameterConfigService,
        "MODEL_DIRECTORY",
        tmp_path,
    ):
        NFLModelParameterConfigService.save(
            model_type="random_forest",
            target="home_win",
            parameters={
                "max_depth": 6,
            },
        )

        with pytest.raises(
            FileNotFoundError,
            match=("No saved parameters found for xgboost target home_win"),
        ):
            NFLModelParameterConfigService.load(
                model_type="xgboost",
                target="home_win",
            )
