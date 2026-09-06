from unittest.mock import MagicMock

from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from predictions.nfl.models.xgboost import NFLXGBoostModel


def test_xgboost_model_initializes_pipeline():
    model = NFLXGBoostModel(
        n_estimators=299,
        max_depth=1,
        learning_rate=0.029849909352061013,
        min_child_weight=9.995824848019023,
        subsample=0.8925937442592672,
        colsample_bytree=0.8774564543659042,
        reg_alpha=1.5644798926956065,
        reg_lambda=1.49230202784724,
        random_state=42,
        n_jobs=-1,
    )

    assert isinstance(model.model, Pipeline)

    imputer = model.model.named_steps["imputer"]
    classifier = model.model.named_steps["classifier"]

    assert isinstance(imputer, SimpleImputer)
    assert imputer.strategy == "median"

    assert isinstance(classifier, XGBClassifier)

    params = classifier.get_params()

    assert params["n_estimators"] == 299
    assert params["max_depth"] == 1
    assert params["learning_rate"] == 0.029849909352061013
    assert params["min_child_weight"] == 9.995824848019023
    assert params["subsample"] == 0.8925937442592672
    assert params["colsample_bytree"] == 0.8774564543659042
    assert params["reg_alpha"] == 1.5644798926956065
    assert params["reg_lambda"] == 1.49230202784724
    assert params["random_state"] == 42
    assert params["n_jobs"] == -1
    assert params["eval_metric"] == "logloss"


def test_suggest_xgboost_parameters():
    trial = MagicMock()

    trial.suggest_int.side_effect = [
        200,
        2,
    ]

    trial.suggest_float.side_effect = [
        0.05,
        5.0,
        0.8,
        0.75,
        1.0,
        0.7,
    ]

    parameters = NFLXGBoostModel.suggest_xgboost_parameters(trial)

    assert parameters == {
        "n_estimators": 200,
        "max_depth": 2,
        "learning_rate": 0.05,
        "min_child_weight": 5.0,
        "subsample": 0.8,
        "colsample_bytree": 0.75,
        "reg_alpha": 1.0,
        "reg_lambda": 0.7,
    }

    trial.suggest_int.assert_any_call(
        "n_estimators",
        50,
        300,
    )

    trial.suggest_int.assert_any_call(
        "max_depth",
        1,
        4,
    )

    trial.suggest_float.assert_any_call(
        "learning_rate",
        0.01,
        0.3,
        log=True,
    )

    trial.suggest_float.assert_any_call(
        "min_child_weight",
        1.0,
        10.0,
    )

    trial.suggest_float.assert_any_call(
        "subsample",
        0.6,
        1.0,
    )

    trial.suggest_float.assert_any_call(
        "colsample_bytree",
        0.5,
        1.0,
    )

    trial.suggest_float.assert_any_call(
        "reg_alpha",
        0.0,
        2.0,
    )

    trial.suggest_float.assert_any_call(
        "reg_lambda",
        0.3,
        5.0,
    )
