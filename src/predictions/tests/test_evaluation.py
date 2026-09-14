import pytest

from predictions.evaluation import ClassificationEvaluator


class FakeClassificationModel:
    def __init__(
        self,
        *,
        predictions: list[int],
        probabilities: list[float],
        stats: dict[str, float],
    ) -> None:
        self._predictions = predictions
        self._probabilities = probabilities
        self._stats = stats

    def predict(self, features: list[dict]) -> list[int]:
        return self._predictions

    def predict_proba(self, features: list[dict]) -> list[float]:
        return self._probabilities

    def get_performance_stats(
        self,
        features: list[dict],
        targets: list[int],
    ) -> dict[str, float]:
        return self._stats


def test_evaluate_returns_classification_metrics_and_calibration():
    model = FakeClassificationModel(
        predictions=[0, 1, 1, 1],
        probabilities=[0.1, 0.4, 0.7, 0.9],
        stats={
            "accuracy": 0.75,
            "log_loss": 0.5,
            "brier_score": 0.2,
            "roc_auc": 0.8,
        },
    )

    features = [
        {"feature": 1},
        {"feature": 2},
        {"feature": 3},
        {"feature": 4},
    ]

    targets = [0, 0, 1, 1]

    result = ClassificationEvaluator.evaluate(
        model=model,
        features=features,
        targets=targets,
        model_name="fake_model",
        calibration_bins=2,
    )

    assert result.model_name == "fake_model"
    assert result.accuracy == 0.75
    assert result.log_loss == 0.5
    assert result.brier_score == 0.2
    assert result.roc_auc == 0.8

    assert len(result.calibration_bins) == 2

    first_bin = result.calibration_bins[0]

    assert first_bin.lower_bound == 0.0
    assert first_bin.upper_bound == 0.5
    assert first_bin.count == 2
    assert first_bin.mean_predicted_probability == pytest.approx(0.25)
    assert first_bin.observed_frequency == pytest.approx(0.0)

    second_bin = result.calibration_bins[1]

    assert second_bin.lower_bound == 0.5
    assert second_bin.upper_bound == 1.0
    assert second_bin.count == 2
    assert second_bin.mean_predicted_probability == pytest.approx(0.8)
    assert second_bin.observed_frequency == pytest.approx(1.0)

    assert result.expected_calibration_error == pytest.approx(0.225)


def test_evaluate_rejects_empty_features():
    model = FakeClassificationModel(
        predictions=[],
        probabilities=[],
        stats={
            "accuracy": 0.0,
            "log_loss": 0.0,
            "brier_score": 0.0,
            "roc_auc": 0.0,
        },
    )

    with pytest.raises(
        ValueError,
        match="Evaluation features cannot be empty",
    ):
        ClassificationEvaluator.evaluate(
            model=model,
            features=[],
            targets=[1],
            model_name="fake_model",
        )


def test_evaluate_rejects_empty_targets():
    model = FakeClassificationModel(
        predictions=[],
        probabilities=[],
        stats={
            "accuracy": 0.0,
            "log_loss": 0.0,
            "brier_score": 0.0,
            "roc_auc": 0.0,
        },
    )

    with pytest.raises(
        ValueError,
        match="Evaluation targets cannot be empty",
    ):
        ClassificationEvaluator.evaluate(
            model=model,
            features=[{"feature": 1}],
            targets=[],
            model_name="fake_model",
        )


def test_evaluate_rejects_mismatched_feature_and_target_counts():
    model = FakeClassificationModel(
        predictions=[],
        probabilities=[],
        stats={
            "accuracy": 0.0,
            "log_loss": 0.0,
            "brier_score": 0.0,
            "roc_auc": 0.0,
        },
    )

    with pytest.raises(
        ValueError,
        match="Features and targets must contain the same number of rows",
    ):
        ClassificationEvaluator.evaluate(
            model=model,
            features=[
                {"feature": 1},
                {"feature": 2},
            ],
            targets=[1],
            model_name="fake_model",
        )


def test_evaluate_rejects_invalid_prediction_count():
    model = FakeClassificationModel(
        predictions=[1],
        probabilities=[0.4, 0.6],
        stats={
            "accuracy": 0.5,
            "log_loss": 0.5,
            "brier_score": 0.2,
            "roc_auc": 0.8,
        },
    )

    with pytest.raises(
        ValueError,
        match="Model predictions must contain one value per target",
    ):
        ClassificationEvaluator.evaluate(
            model=model,
            features=[
                {"feature": 1},
                {"feature": 2},
            ],
            targets=[0, 1],
            model_name="fake_model",
        )


def test_evaluate_rejects_invalid_probability_count():
    model = FakeClassificationModel(
        predictions=[0, 1],
        probabilities=[0.5],
        stats={
            "accuracy": 0.5,
            "log_loss": 0.5,
            "brier_score": 0.2,
            "roc_auc": 0.8,
        },
    )

    with pytest.raises(
        ValueError,
        match="Model probabilities must contain one value per target",
    ):
        ClassificationEvaluator.evaluate(
            model=model,
            features=[
                {"feature": 1},
                {"feature": 2},
            ],
            targets=[0, 1],
            model_name="fake_model",
        )


def test_calibration_rejects_invalid_bin_count():
    with pytest.raises(
        ValueError,
        match="num_bins must be greater than zero",
    ):
        ClassificationEvaluator._calibration(
            probabilities=[0.5],
            targets=[1],
            num_bins=0,
        )


def test_expected_calibration_error_rejects_zero_total_count():
    with pytest.raises(
        ValueError,
        match="total_count must be greater than zero",
    ):
        ClassificationEvaluator._expected_calibration_error(
            [],
            total_count=0,
        )
