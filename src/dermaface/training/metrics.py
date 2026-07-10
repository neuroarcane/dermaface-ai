\"""Evaluation metrics, including fairness-by-skin-tone.

Owner: Iva (ML Research Lead), paired with Temirlan
(Evaluation & Explainability Support).

The fairness breakdown is a graded deliverable — see docs/model-card.md.
"""

from __future__ import annotations

from typing import Any, Sequence

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def _validate_inputs(
    y_true: Sequence[int],
    y_pred: Sequence[int],
) -> None:
    """Check that labels are present and have matching lengths."""

    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length.")

    if len(y_true) == 0:
        raise ValueError("y_true and y_pred cannot be empty.")


def classification_metrics(
    y_true: Sequence[int],
    y_pred: Sequence[int],
) -> dict[str, float]:
    """Return the main classification evaluation metrics.

    Macro averaging gives every class equal importance, even when the
    dataset is imbalanced.
    """

    _validate_inputs(y_true, y_pred)

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(
            f1_score(
                y_true,
                y_pred,
                average="macro",
                zero_division=0,
            )
        ),
        "macro_precision": float(
            precision_score(
                y_true,
                y_pred,
                average="macro",
                zero_division=0,
            )
        ),
        "macro_recall": float(
            recall_score(
                y_true,
                y_pred,
                average="macro",
                zero_division=0,
            )
        ),
    }


def fairness_by_skin_type(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    skin_types: Sequence[str],
) -> dict[str, dict[str, float]]:
    """Return classification metrics for each Fitzpatrick skin type.

    Each skin-type group is evaluated separately so performance differences
    can be reported honestly.
    """

    _validate_inputs(y_true, y_pred)

    if len(y_true) != len(skin_types):
        raise ValueError(
            "y_true, y_pred, and skin_types must have the same length."
        )

    results: dict[str, dict[str, float]] = {}

    for skin_type in sorted(set(skin_types)):
        indices = [
            index
            for index, value in enumerate(skin_types)
            if value == skin_type
        ]

        group_y_true = [y_true[index] for index in indices]
        group_y_pred = [y_pred[index] for index in indices]

        group_metrics = classification_metrics(
            group_y_true,
            group_y_pred,
        )

        group_metrics["sample_count"] = float(len(indices))
        results[skin_type] = group_metrics

    return results


def confusion(
    y_true: Sequence[int],
    y_pred: Sequence[int],
) -> Any:
    """Return the confusion matrix used for evaluation and reporting."""

    _validate_inputs(y_true, y_pred)

    return confusion_matrix(y_true, y_pred)
