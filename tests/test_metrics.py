import numpy as np
import pytest

from dermaface.training.metrics import (
    classification_metrics,
    confusion,
    fairness_by_skin_type,
)


def test_classification_metrics_perfect_predictions():
    y_true = [0, 1, 2, 3]
    y_pred = [0, 1, 2, 3]

    results = classification_metrics(y_true, y_pred)

    assert results["accuracy"] == pytest.approx(1.0)
    assert results["macro_f1"] == pytest.approx(1.0)
    assert results["macro_precision"] == pytest.approx(1.0)
    assert results["macro_recall"] == pytest.approx(1.0)


def test_fairness_by_skin_type():
    y_true = [0, 1, 0, 1]
    y_pred = [0, 1, 1, 1]
    skin_types = ["I", "I", "VI", "VI"]

    results = fairness_by_skin_type(
        y_true,
        y_pred,
        skin_types,
    )

    assert set(results.keys()) == {"I", "VI"}
    assert results["I"]["sample_count"] == 2.0
    assert results["VI"]["sample_count"] == 2.0
    assert results["I"]["accuracy"] == pytest.approx(1.0)
    assert results["VI"]["accuracy"] == pytest.approx(0.5)


def test_confusion_matrix():
    y_true = [0, 0, 1, 1]
    y_pred = [0, 1, 1, 1]

    matrix = confusion(y_true, y_pred)

    expected = np.array(
        [
            [1, 1],
            [0, 2],
        ]
    )

    assert np.array_equal(matrix, expected)


def test_mismatched_lengths_raise_error():
    with pytest.raises(ValueError):
        classification_metrics([0, 1], [0])
