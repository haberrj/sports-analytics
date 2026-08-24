import pytest

from predictions.nfl.preprocessing import NFLPreprocessingService


def test_split_features_target_removes_metadata_and_targets():
    rows = [
        {
            "game_id": "2025_01_BUF_KC",
            "season": 2025,
            "week": 1,
            "home_team": "BUF",
            "away_team": "KC",
            "neutral_site": False,
            "home_pass_offense_yards_per_attempt": 7.5,
            "away_pass_offense_yards_per_attempt": 6.8,
            "home_score": 31,
            "away_score": 24,
            "home_win": 1,
            "total_game_points": 55,
            "score_differential": 7,
        }
    ]

    features, targets = NFLPreprocessingService.split_features_target(
        rows,
        target="home_win",
    )

    assert targets == [1]

    assert features == [
        {
            "neutral_site": False,
            "home_pass_offense_yards_per_attempt": 7.5,
            "away_pass_offense_yards_per_attempt": 6.8,
        }
    ]


def test_split_features_target_supports_score_differential():
    rows = [
        {
            "game_id": "2025_01_BUF_KC",
            "season": 2025,
            "week": 1,
            "home_team": "BUF",
            "away_team": "KC",
            "neutral_site": False,
            "home_pass_offense_yards_per_attempt": 7.5,
            "home_score": 31,
            "away_score": 24,
            "home_win": 1,
            "total_game_points": 55,
            "score_differential": 7,
        }
    ]

    features, targets = NFLPreprocessingService.split_features_target(
        rows,
        target="score_differential",
    )

    assert targets == [7]

    assert features == [
        {
            "neutral_site": False,
            "home_pass_offense_yards_per_attempt": 7.5,
        }
    ]


def test_split_features_target_supports_total_game_points():
    rows = [
        {
            "game_id": "2025_01_BUF_KC",
            "season": 2025,
            "week": 1,
            "home_team": "BUF",
            "away_team": "KC",
            "neutral_site": False,
            "home_pass_offense_yards_per_attempt": 7.5,
            "home_score": 31,
            "away_score": 24,
            "home_win": 1,
            "total_game_points": 55,
            "score_differential": 7,
        }
    ]

    _, targets = NFLPreprocessingService.split_features_target(
        rows,
        target="total_game_points",
    )

    assert targets == [55]


def test_split_features_target_removes_all_target_columns():
    rows = [
        {
            "game_id": "2025_01_BUF_KC",
            "season": 2025,
            "week": 1,
            "home_team": "BUF",
            "away_team": "KC",
            "neutral_site": False,
            "home_points_for_per_game": 28.0,
            "away_points_for_per_game": 24.0,
            "home_score": 31,
            "away_score": 24,
            "home_win": 1,
            "total_game_points": 55,
            "score_differential": 7,
        }
    ]

    features, _ = NFLPreprocessingService.split_features_target(
        rows,
        target="home_win",
    )

    feature_row = features[0]

    assert "home_score" not in feature_row
    assert "away_score" not in feature_row
    assert "home_win" not in feature_row
    assert "total_game_points" not in feature_row
    assert "score_differential" not in feature_row


def test_split_features_target_removes_all_metadata_columns():
    rows = [
        {
            "game_id": "2025_01_BUF_KC",
            "season": 2025,
            "week": 1,
            "home_team": "BUF",
            "away_team": "KC",
            "neutral_site": False,
            "home_points_for_per_game": 28.0,
            "home_score": 31,
            "away_score": 24,
            "home_win": 1,
            "total_game_points": 55,
            "score_differential": 7,
        }
    ]

    features, _ = NFLPreprocessingService.split_features_target(
        rows,
        target="home_win",
    )

    feature_row = features[0]

    assert "game_id" not in feature_row
    assert "season" not in feature_row
    assert "week" not in feature_row
    assert "home_team" not in feature_row
    assert "away_team" not in feature_row


def test_split_features_target_preserves_none_feature_values():
    rows = [
        {
            "game_id": "2025_01_BUF_KC",
            "season": 2025,
            "week": 1,
            "home_team": "BUF",
            "away_team": "KC",
            "neutral_site": False,
            "home_third_down_conversion_rate": None,
            "away_third_down_conversion_rate": None,
            "home_score": 31,
            "away_score": 24,
            "home_win": 1,
            "total_game_points": 55,
            "score_differential": 7,
        }
    ]

    features, targets = NFLPreprocessingService.split_features_target(
        rows,
        target="home_win",
    )

    assert targets == [1]
    assert features[0]["home_third_down_conversion_rate"] is None
    assert features[0]["away_third_down_conversion_rate"] is None


def test_split_features_target_handles_multiple_rows():
    rows = [
        {
            "game_id": "game-1",
            "season": 2025,
            "week": 1,
            "home_team": "BUF",
            "away_team": "KC",
            "neutral_site": False,
            "home_points_for_per_game": 28.0,
            "home_score": 31,
            "away_score": 24,
            "home_win": 1,
            "total_game_points": 55,
            "score_differential": 7,
        },
        {
            "game_id": "game-2",
            "season": 2025,
            "week": 2,
            "home_team": "KC",
            "away_team": "BUF",
            "neutral_site": False,
            "home_points_for_per_game": 24.0,
            "home_score": 20,
            "away_score": 27,
            "home_win": 0,
            "total_game_points": 47,
            "score_differential": -7,
        },
    ]

    features, targets = NFLPreprocessingService.split_features_target(
        rows,
        target="home_win",
    )

    assert targets == [1, 0]

    assert features == [
        {
            "neutral_site": False,
            "home_points_for_per_game": 28.0,
        },
        {
            "neutral_site": False,
            "home_points_for_per_game": 24.0,
        },
    ]


def test_split_features_target_handles_empty_dataset():
    features, targets = NFLPreprocessingService.split_features_target(
        [],
        target="home_win",
    )

    assert features == []
    assert targets == []


def test_split_features_target_rejects_invalid_target():
    with pytest.raises(
        ValueError,
        match="Unsupported target",
    ):
        NFLPreprocessingService.split_features_target(
            [],
            target="home_score_prediction",
        )


def test_split_dataset_by_season():
    rows = [
        {"game_id": "2021-1", "season": 2021},
        {"game_id": "2022-1", "season": 2022},
        {"game_id": "2023-1", "season": 2023},
        {"game_id": "2024-1", "season": 2024},
        {"game_id": "2025-1", "season": 2025},
    ]

    training_rows, validation_rows, test_rows = NFLPreprocessingService.split_dataset_by_season(
        rows,
        validation_season=2023,
        test_season=2025,
    )

    assert training_rows == [
        {"game_id": "2021-1", "season": 2021},
        {"game_id": "2022-1", "season": 2022},
    ]

    assert validation_rows == [
        {"game_id": "2023-1", "season": 2023},
        {"game_id": "2024-1", "season": 2024},
    ]

    assert test_rows == [
        {"game_id": "2025-1", "season": 2025},
    ]


def test_split_dataset_by_season_includes_seasons_after_test_boundary():
    rows = [
        {"game_id": "2024-1", "season": 2024},
        {"game_id": "2025-1", "season": 2025},
        {"game_id": "2026-1", "season": 2026},
    ]

    _, _, test_rows = NFLPreprocessingService.split_dataset_by_season(
        rows,
        validation_season=2023,
        test_season=2024,
    )

    assert test_rows == [
        {"game_id": "2024-1", "season": 2024},
        {"game_id": "2025-1", "season": 2025},
        {"game_id": "2026-1", "season": 2026},
    ]


def test_split_dataset_by_season_handles_empty_dataset():
    training_rows, validation_rows, test_rows = NFLPreprocessingService.split_dataset_by_season(
        [],
        validation_season=2023,
        test_season=2024,
    )

    assert training_rows == []
    assert validation_rows == []
    assert test_rows == []


@pytest.mark.parametrize(
    ("validation_season", "test_season"),
    [
        (2024, 2024),
        (2025, 2024),
    ],
)
def test_split_dataset_by_season_rejects_invalid_boundaries(
    validation_season,
    test_season,
):
    with pytest.raises(
        ValueError,
        match="cannot be after the test season",
    ):
        NFLPreprocessingService.split_dataset_by_season(
            [],
            validation_season=validation_season,
            test_season=test_season,
        )
