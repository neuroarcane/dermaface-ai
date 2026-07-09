"""Evaluation metrics, including fairness-by-skin-tone.

Owner: Iva (ML Research Lead), paired with Temirlan (Evaluation &
Explainability Support).

The fairness breakdown is a graded deliverable — see docs/model-card.md.
"""

from __future__ import annotations

from typing import Any, Sequence


def classification_metrics(y_true: Sequence[int], y_pred: Sequence[int]) -> dict[str, float]:
    """Return accuracy + macro-F1 (and room for per-class P/R).

    TODO(Iva/Temirlan): use sklearn.metrics; add confusion matrix export for the report.
    """
    raise NotImplementedError


def fairness_by_skin_type(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    skin_types: Sequence[str],
) -> dict[str, dict[str, float]]:
    """Return metrics stratified by Fitzpatrick skin type {"I": {...}, ...}.

    This is the core fairness analysis. Call out gaps honestly in the report.
    TODO(Iva/Temirlan): group by skin_type and compute classification_metrics per group.
    """
    raise NotImplementedError


def confusion(y_true: Sequence[int], y_pred: Sequence[int]) -> Any:
    """Return a confusion matrix (for plotting in the report).

    TODO(Iva/Temirlan): sklearn.metrics.confusion_matrix.
    """
    raise NotImplementedError
