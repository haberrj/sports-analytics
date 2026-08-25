from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from predictions.nfl.models.base import ClassificationModel


class NFLLogisticRegressionModel(ClassificationModel):
    """Logistic regression model for NFL game outcomes.

    Initial validation results (2023-2024):
    - Accuracy: 0.5965
    - Home-team baseline accuracy: 0.5649
    - Log loss: 0.68375
    - Baseline log loss: 0.68470
    - Brier score: 0.24406
    - Baseline Brier score: 0.24579
    - ROC AUC: 0.6003

    Initial test results (2024-2025):
    - Accuracy: 0.6509
    - Home-team baseline accuracy: 0.5404
    - Log loss: 0.63687
    - Brier score: 0.22262
    - ROC AUC: 0.6928
    """

    def __init__(self, max_iterations: int = 1000):
        super().__init__()
        self.model: Pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("classifier", LogisticRegression(max_iter=max_iterations)),
            ]
        )
