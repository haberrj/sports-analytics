from dataclasses import dataclass


@dataclass(frozen=True)
class CalibrationBin:
    lower_bound: float
    upper_bound: float
    mean_predicted_probability: float
    observed_frequency: float
    count: int


@dataclass(frozen=True)
class ClassificationEvaluationResult:
    model_name: str
    accuracy: float
    log_loss: float
    brier_score: float
    roc_auc: float
    expected_calibration_error: float
    calibration_bins: list[CalibrationBin]


class ClassificationEvaluator:
    @staticmethod
    def evaluate(
        *,
        model,
        features: list[dict],
        targets: list[int],
        model_name: str,
        calibration_bins: int = 10,
    ) -> ClassificationEvaluationResult:
        if not features:
            raise ValueError("Evaluation features cannot be empty.")

        if not targets:
            raise ValueError("Evaluation targets cannot be empty.")

        if len(features) != len(targets):
            raise ValueError("Features and targets must contain the same number of rows.")

        predictions = model.predict(features)
        probabilities = model.predict_proba(features)

        if len(predictions) != len(targets):
            raise ValueError("Model predictions must contain one value per target.")

        if len(probabilities) != len(targets):
            raise ValueError("Model probabilities must contain one value per target.")

        stats = model.get_performance_stats(
            features,
            targets,
        )

        calibration = ClassificationEvaluator._calibration(
            probabilities=probabilities,
            targets=targets,
            num_bins=calibration_bins,
        )

        expected_calibration_error = ClassificationEvaluator._expected_calibration_error(
            calibration,
            total_count=len(targets),
        )

        return ClassificationEvaluationResult(
            model_name=model_name,
            accuracy=stats["accuracy"],
            log_loss=stats["log_loss"],
            brier_score=stats["brier_score"],
            roc_auc=stats["roc_auc"],
            expected_calibration_error=expected_calibration_error,
            calibration_bins=calibration,
        )

    @staticmethod
    def _calibration(
        *,
        probabilities: list[float],
        targets: list[int],
        num_bins: int,
    ) -> list[CalibrationBin]:
        if num_bins <= 0:
            raise ValueError("num_bins must be greater than zero.")

        bins: list[CalibrationBin] = []

        for bin_index in range(num_bins):
            lower_bound = bin_index / num_bins
            upper_bound = (bin_index + 1) / num_bins

            if bin_index == num_bins - 1:
                indices = [
                    index
                    for index, probability in enumerate(probabilities)
                    if lower_bound <= probability <= upper_bound
                ]
            else:
                indices = [
                    index for index, probability in enumerate(probabilities) if lower_bound <= probability < upper_bound
                ]

            if not indices:
                continue

            bin_probabilities = [probabilities[index] for index in indices]

            bin_targets = [targets[index] for index in indices]

            bins.append(
                CalibrationBin(
                    lower_bound=lower_bound,
                    upper_bound=upper_bound,
                    mean_predicted_probability=sum(bin_probabilities) / len(bin_probabilities),
                    observed_frequency=sum(bin_targets) / len(bin_targets),
                    count=len(indices),
                )
            )

        return bins

    @staticmethod
    def _expected_calibration_error(
        bins: list[CalibrationBin],
        *,
        total_count: int,
    ) -> float:
        if total_count <= 0:
            raise ValueError("total_count must be greater than zero.")

        return sum(
            (calibration_bin.count / total_count)
            * abs(calibration_bin.observed_frequency - calibration_bin.mean_predicted_probability)
            for calibration_bin in bins
        )
