import pytest

from src.minmax_transform import minmax_transform


def test_minmax_transform_maps_training_range_to_unit_interval():
    assert minmax_transform([0.0, 5.0, 10.0], 0.0, 10.0) == [0.0, 0.5, 1.0]


def test_minmax_transform_clips_values_outside_training_range():
    assert minmax_transform([-2.0, 15.0], 0.0, 10.0) == [0.0, 1.0]


def test_minmax_transform_handles_constant_training_stats():
    assert minmax_transform([3.0, 3.0, 8.0], 3.0, 3.0) == [0.0, 0.0, 0.0]


def test_minmax_transform_empty_batch():
    assert minmax_transform([], 0.0, 1.0) == []


def test_minmax_transform_rejects_nan_score():
    with pytest.raises(ValueError, match="inválid"):
        minmax_transform([0.5, float("nan")], 0.0, 1.0)


def test_minmax_transform_rejects_inverted_stats():
    with pytest.raises(ValueError, match="feature_min"):
        minmax_transform([0.5], 1.0, 0.0)
