from typing import Any


class NFLPreprocessingService:
    METADATA_COLUMNS = {
        "game_id",
        "season",
        "week",
        "home_team",
        "away_team",
    }

    TARGET_COLUMNS = {
        "home_score",
        "away_score",
        "home_win",
        "total_game_points",
        "score_differential",
    }

    @staticmethod
    def split_features_target(rows: list[dict], target: str) -> tuple[list[dict], list[Any]]:
        if target not in NFLPreprocessingService.TARGET_COLUMNS:
            raise ValueError(f"Unsupported target: {target}")
        features = []
        targets = []

        excluded = NFLPreprocessingService.METADATA_COLUMNS | NFLPreprocessingService.TARGET_COLUMNS

        for row in rows:
            features.append({key: value for key, value in row.items() if key not in excluded})
            targets.append(row[target])

        return (features, targets)

    @staticmethod
    def split_dataset_by_season(
        rows: list[dict], validation_season: int, test_season: int
    ) -> tuple[list[dict], list[dict], list[dict]]:
        """Split training data chronologically by NFL season.

        Rows before ``validation_season`` are assigned to training. Rows from
        ``validation_season`` up to, but not including, ``test_season`` are
        assigned to validation. Rows from ``test_season`` onward are assigned
        to testing.

        This chronological split prevents future-season data from leaking into
        the training or validation datasets.

        Args:
            rows: Training dataset rows containing a ``season`` field.
            validation_season: First season assigned to the validation dataset.
            test_season: First season assigned to the test dataset.

        Returns:
            A tuple containing training rows, validation rows, and test rows.

        Raises:
            ValueError: If ``validation_season`` is greater than or equal to
                ``test_season``.
        """
        if validation_season >= test_season:
            raise ValueError(f"Validation season {validation_season} cannot be after the test season {test_season}.")
        training_rows = []
        validation_rows = []
        test_rows = []
        for row in rows:
            season = row["season"]
            if season < validation_season:
                training_rows.append(row)
            elif season < test_season:
                validation_rows.append(row)
            else:
                test_rows.append(row)
        return (training_rows, validation_rows, test_rows)
