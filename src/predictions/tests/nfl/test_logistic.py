
from predictions.nfl.models.logistic import NFLLogisticRegressionModel


def test_logistic_model_fit_and_predict():
    features = [
        {"home_strength": 1.0, "away_strength": 0.0},
        {"home_strength": 0.0, "away_strength": 1.0},
        {"home_strength": 0.9, "away_strength": 0.1},
        {"home_strength": 0.1, "away_strength": 0.9},
    ]
    targets = [1, 0, 1, 0]

    model = NFLLogisticRegressionModel()
    model.fit(features, targets)

    predictions = model.predict(features)

    assert len(predictions) == 4
    assert predictions == [1, 0, 1, 0]


def test_logistic_model_predict_proba():
    features = [
        {"home_strength": 1.0, "away_strength": 0.0},
        {"home_strength": 0.0, "away_strength": 1.0},
        {"home_strength": 0.9, "away_strength": 0.1},
        {"home_strength": 0.1, "away_strength": 0.9},
    ]
    targets = [1, 0, 1, 0]

    model = NFLLogisticRegressionModel()
    model.fit(features, targets)

    probabilities = model.predict_proba(features)

    assert len(probabilities) == 4

    for probability in probabilities:
        assert 0.0 <= probability <= 1.0

    assert probabilities[0] > 0.5
    assert probabilities[1] < 0.5


def test_logistic_model_handles_missing_values():
    features = [
        {"home_strength": 1.0, "away_strength": None},
        {"home_strength": 0.0, "away_strength": 1.0},
        {"home_strength": None, "away_strength": 0.0},
        {"home_strength": 0.1, "away_strength": 0.9},
    ]
    targets = [1, 0, 1, 0]

    model = NFLLogisticRegressionModel()
    model.fit(features, targets)

    predictions = model.predict(features)

    assert len(predictions) == 4


def test_logistic_model_uses_configured_max_iterations():
    model = NFLLogisticRegressionModel(max_iterations=500)

    classifier = model.model.named_steps["classifier"]

    assert classifier.max_iter == 500
