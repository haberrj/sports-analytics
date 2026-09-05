from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer

from predictions.nfl.models.random_forest import NFLRandomForestModel


def test_random_forest_model_uses_expected_pipeline():
    model = NFLRandomForestModel()

    assert list(model.model.named_steps.keys()) == [
        "imputer",
        "classifier",
    ]

    assert isinstance(
        model.model.named_steps["imputer"],
        SimpleImputer,
    )

    assert isinstance(
        model.model.named_steps["classifier"],
        RandomForestClassifier,
    )


def test_random_forest_model_passes_parameters_to_classifier():
    model = NFLRandomForestModel(
        n_estimators=75,
        max_depth=8,
        min_samples_leaf=4,
        max_features=0.5,
        random_state=123,
        n_jobs=2,
    )

    classifier = model.model.named_steps["classifier"]

    assert classifier.n_estimators == 75
    assert classifier.max_depth == 8
    assert classifier.min_samples_leaf == 4
    assert classifier.max_features == 0.5
    assert classifier.random_state == 123
    assert classifier.n_jobs == 2


def test_suggest_random_forest_parameters():
    class FakeTrial:
        def suggest_int(self, name, low, high):
            values = {
                "max_depth": 6,
                "min_samples_leaf": 4,
                "n_estimators": 60,
            }

            return values[name]

        def suggest_categorical(self, name, choices):
            assert name == "max_features"
            assert choices == [
                "sqrt",
                "log2",
                0.25,
                0.5,
                0.75,
                1.0,
            ]

            return 0.25

    parameters = NFLRandomForestModel.suggest_random_forest_parameters(FakeTrial())

    assert parameters == {
        "max_depth": 6,
        "min_samples_leaf": 4,
        "n_estimators": 60,
        "max_features": 0.25,
    }
