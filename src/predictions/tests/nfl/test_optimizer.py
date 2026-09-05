import optuna
import pytest
from optuna.trial import Trial

from predictions.nfl.models.optimizer import (
    ClassificationModelOptimizer,
    OptimizationResult,
)

optuna.logging.set_verbosity(optuna.logging.WARNING)


class FakeClassificationModel:
    """Fake model used to test optimizer behavior."""

    def __init__(self, score: float = 0.5):
        self.score = score
        self.training_targets = []

    def fit(self, features: list[dict], targets: list) -> None:
        self.training_targets = targets

    def get_performance_stats(
        self,
        features: list[dict],
        targets: list,
    ) -> dict[str, float]:
        return {
            "baseline_accuracy": 0.5,
            "accuracy": self.score,
            "log_loss": 1.0 - self.score,
            "brier_score": 1.0 - self.score,
            "roc_auc": self.score,
        }


@pytest.fixture
def dataset():
    return [
        {
            "season": 2019,
            "home_win": True,
            "home_strength": 0.8,
        },
        {
            "season": 2019,
            "home_win": False,
            "home_strength": 0.4,
        },
        {
            "season": 2020,
            "home_win": True,
            "home_strength": 0.7,
        },
        {
            "season": 2020,
            "home_win": False,
            "home_strength": 0.3,
        },
        {
            "season": 2021,
            "home_win": True,
            "home_strength": 0.9,
        },
        {
            "season": 2021,
            "home_win": False,
            "home_strength": 0.2,
        },
    ]


def test_optimizer_rejects_invalid_objective():
    with pytest.raises(
        ValueError,
        match="Unsupported objective: invalid",
    ):
        ClassificationModelOptimizer(
            model_factory=FakeClassificationModel,
            validation_seasons=[2020, 2021],
            objective="invalid",
        )


def test_evaluate_parameters_returns_average_metrics(dataset):
    optimizer = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020, 2021],
    )

    result = optimizer.evaluate_parameters(
        dataset=dataset,
        parameters={"score": 0.7},
        target="home_win",
    )

    assert result.parameters == {"score": 0.7}
    assert result.accuracy == pytest.approx(0.7)
    assert result.log_loss == pytest.approx(0.3)
    assert result.brier_score == pytest.approx(0.3)
    assert result.roc_auc == pytest.approx(0.7)


def test_random_search_runs_requested_number_of_iterations(dataset):
    optimizer = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
    )

    def parameter_sampler(random):
        return {
            "score": random.choice([0.5, 0.6, 0.7]),
        }

    results = optimizer.random_search(
        dataset=dataset,
        parameter_sampler=parameter_sampler,
        target="home_win",
        iterations=5,
    )

    assert len(results) == 5

    for result in results:
        assert isinstance(result, OptimizationResult)


def test_random_search_is_reproducible_with_random_state(dataset):
    def parameter_sampler(random):
        return {
            "score": random.choice([0.5, 0.6, 0.7, 0.8]),
        }

    optimizer_1 = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
        random_state=42,
    )

    optimizer_2 = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
        random_state=42,
    )

    results_1 = optimizer_1.random_search(
        dataset=dataset,
        parameter_sampler=parameter_sampler,
        target="home_win",
        iterations=5,
    )

    results_2 = optimizer_2.random_search(
        dataset=dataset,
        parameter_sampler=parameter_sampler,
        target="home_win",
        iterations=5,
    )

    assert [result.parameters for result in results_1] == [result.parameters for result in results_2]


def test_get_best_result_uses_lowest_log_loss():
    optimizer = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
        objective="log_loss",
    )

    worse = OptimizationResult(
        parameters={"value": 1},
        accuracy=0.7,
        log_loss=0.6,
        brier_score=0.2,
        roc_auc=0.7,
    )

    better = OptimizationResult(
        parameters={"value": 2},
        accuracy=0.6,
        log_loss=0.5,
        brier_score=0.3,
        roc_auc=0.6,
    )

    assert optimizer.get_best_result([worse, better]) == better


def test_get_best_result_uses_lowest_brier_score():
    optimizer = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
        objective="brier_score",
    )

    worse = OptimizationResult(
        parameters={"value": 1},
        accuracy=0.7,
        log_loss=0.5,
        brier_score=0.3,
        roc_auc=0.7,
    )

    better = OptimizationResult(
        parameters={"value": 2},
        accuracy=0.6,
        log_loss=0.6,
        brier_score=0.2,
        roc_auc=0.6,
    )

    assert optimizer.get_best_result([worse, better]) == better


def test_get_best_result_uses_highest_accuracy():
    optimizer = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
        objective="accuracy",
    )

    worse = OptimizationResult(
        parameters={"value": 1},
        accuracy=0.6,
        log_loss=0.5,
        brier_score=0.2,
        roc_auc=0.8,
    )

    better = OptimizationResult(
        parameters={"value": 2},
        accuracy=0.7,
        log_loss=0.6,
        brier_score=0.3,
        roc_auc=0.6,
    )

    assert optimizer.get_best_result([worse, better]) == better


def test_get_best_result_uses_highest_roc_auc():
    optimizer = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
        objective="roc_auc",
    )

    worse = OptimizationResult(
        parameters={"value": 1},
        accuracy=0.7,
        log_loss=0.5,
        brier_score=0.2,
        roc_auc=0.6,
    )

    better = OptimizationResult(
        parameters={"value": 2},
        accuracy=0.6,
        log_loss=0.6,
        brier_score=0.3,
        roc_auc=0.8,
    )

    assert optimizer.get_best_result([worse, better]) == better


def test_get_best_result_rejects_empty_results():
    optimizer = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
    )

    with pytest.raises(
        ValueError,
        match="Optimization results cannot be empty",
    ):
        optimizer.get_best_result([])


def test_bayesian_search_runs_requested_number_of_iterations(dataset):
    optimizer = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
        objective="log_loss",
        random_state=42,
    )

    def parameter_suggester(trial: Trial):
        return {
            "score": trial.suggest_float(
                "score",
                0.5,
                0.9,
            ),
        }

    best, results = optimizer.bayesian_search(
        dataset=dataset,
        parameter_suggester=parameter_suggester,
        target="home_win",
        iterations=5,
    )

    assert len(results) == 5
    assert isinstance(best, OptimizationResult)

    for result in results:
        assert isinstance(result, OptimizationResult)


def test_bayesian_search_returns_best_log_loss_result(dataset):
    optimizer = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
        objective="log_loss",
        random_state=42,
    )

    def parameter_suggester(trial: Trial):
        return {
            "score": trial.suggest_float(
                "score",
                0.5,
                0.9,
            ),
        }

    best, results = optimizer.bayesian_search(
        dataset=dataset,
        parameter_suggester=parameter_suggester,
        target="home_win",
        iterations=10,
    )

    expected = min(
        results,
        key=lambda result: result.log_loss,
    )

    assert best == expected


def test_bayesian_search_returns_best_accuracy_result(dataset):
    optimizer = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
        objective="accuracy",
        random_state=42,
    )

    def parameter_suggester(trial: Trial):
        return {
            "score": trial.suggest_float(
                "score",
                0.5,
                0.9,
            ),
        }

    best, results = optimizer.bayesian_search(
        dataset=dataset,
        parameter_suggester=parameter_suggester,
        target="home_win",
        iterations=10,
    )

    expected = max(
        results,
        key=lambda result: result.accuracy,
    )

    assert best == expected


def test_bayesian_search_passes_suggested_parameters_to_model(dataset):
    optimizer = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
        objective="log_loss",
        random_state=42,
    )

    def parameter_suggester(trial: Trial):
        return {
            "score": trial.suggest_categorical(
                "score",
                [0.6],
            ),
        }

    best, results = optimizer.bayesian_search(
        dataset=dataset,
        parameter_suggester=parameter_suggester,
        target="home_win",
        iterations=3,
    )

    assert len(results) == 3

    for result in results:
        assert result.parameters == {"score": 0.6}
        assert result.accuracy == pytest.approx(0.6)
        assert result.log_loss == pytest.approx(0.4)
        assert result.brier_score == pytest.approx(0.4)
        assert result.roc_auc == pytest.approx(0.6)

    assert best.parameters == {"score": 0.6}


def test_bayesian_search_is_reproducible_with_same_random_state(dataset):
    def parameter_suggester(trial: Trial):
        return {
            "score": trial.suggest_float(
                "score",
                0.5,
                0.9,
            ),
        }

    optimizer_1 = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
        objective="log_loss",
        random_state=42,
    )

    optimizer_2 = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
        objective="log_loss",
        random_state=42,
    )

    _, results_1 = optimizer_1.bayesian_search(
        dataset=dataset,
        parameter_suggester=parameter_suggester,
        target="home_win",
        iterations=10,
    )

    _, results_2 = optimizer_2.bayesian_search(
        dataset=dataset,
        parameter_suggester=parameter_suggester,
        target="home_win",
        iterations=10,
    )

    assert [result.parameters for result in results_1] == [result.parameters for result in results_2]


def test_bayesian_search_uses_lowest_brier_when_configured(dataset):
    optimizer = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
        objective="brier_score",
        random_state=42,
    )

    def parameter_suggester(trial: Trial):
        return {
            "score": trial.suggest_float(
                "score",
                0.5,
                0.9,
            ),
        }

    best, results = optimizer.bayesian_search(
        dataset=dataset,
        parameter_suggester=parameter_suggester,
        target="home_win",
        iterations=10,
    )

    expected = min(
        results,
        key=lambda result: result.brier_score,
    )

    assert best == expected


def test_bayesian_search_uses_highest_roc_auc_when_configured(dataset):
    optimizer = ClassificationModelOptimizer(
        model_factory=FakeClassificationModel,
        validation_seasons=[2020],
        objective="roc_auc",
        random_state=42,
    )

    def parameter_suggester(trial: Trial):
        return {
            "score": trial.suggest_float(
                "score",
                0.5,
                0.9,
            ),
        }

    best, results = optimizer.bayesian_search(
        dataset=dataset,
        parameter_suggester=parameter_suggester,
        target="home_win",
        iterations=10,
    )

    expected = max(
        results,
        key=lambda result: result.roc_auc,
    )

    assert best == expected
