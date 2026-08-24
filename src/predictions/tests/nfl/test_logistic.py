import pytest
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score

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


def test_logistic_model_accuracy():
    features = [
        {"home_strength": 1.0, "away_strength": 0.0},
        {"home_strength": 0.0, "away_strength": 1.0},
        {"home_strength": 0.9, "away_strength": 0.1},
        {"home_strength": 0.1, "away_strength": 0.9},
    ]
    targets = [1, 0, 1, 0]

    model = NFLLogisticRegressionModel()
    model.fit(features, targets)

    expected = accuracy_score(targets, model.predict(features))

    assert model.accuracy(features, targets) == expected


def test_logistic_model_log_loss():
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
    expected = log_loss(targets, probabilities)

    assert model.log_loss(features, targets) == pytest.approx(expected)


def test_logistic_model_brier_score():
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
    expected = brier_score_loss(targets, probabilities)

    assert model.brier_score(features, targets) == pytest.approx(expected)


def test_logistic_model_roc_auc():
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
    expected = roc_auc_score(targets, probabilities)

    assert model.roc_auc(features, targets) == pytest.approx(expected)


def test_logistic_model_baseline_accuracy_when_home_wins_are_majority():
    targets = [1, 1, 1, 0]

    baseline = NFLLogisticRegressionModel.baseline_accuracy(targets)

    assert baseline == pytest.approx(0.75)


def test_logistic_model_baseline_accuracy_when_home_losses_are_majority():
    targets = [1, 0, 0, 0]

    baseline = NFLLogisticRegressionModel.baseline_accuracy(targets)

    assert baseline == pytest.approx(0.75)


def test_logistic_model_baseline_accuracy_when_classes_are_balanced():
    targets = [1, 0, 1, 0]

    baseline = NFLLogisticRegressionModel.baseline_accuracy(targets)

    assert baseline == pytest.approx(0.5)
