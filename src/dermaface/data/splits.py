"""Train/val/test splitting — stratified by class AND Fitzpatrick skin type.

Owner: Aparna (Data Lead), with Iva (ML Research) on the fairness rationale.

Stratifying by skin type is what makes the Week-2 fairness analysis possible.
Freeze the test set early and never tune on it.
"""

from __future__ import annotations

from pathlib import Path

from dermaface.config import load_config

DEFAULT_RATIOS = (0.70, 0.15, 0.15)  # train, val, test


def make_splits(
    manifest_path: Path | None = None,
    ratios: tuple[float, float, float] = DEFAULT_RATIOS,
    seed: int | None = None,
) -> None:
    """Assign a ``split`` column to the manifest, stratified by (label, skin_type).

    TODO(Aparna):
      1. Load the manifest.
      2. Group by (label, skin_type); split each group by ``ratios``.
      3. Write the ``split`` column back. Persist a copy of the frozen test set.
    """
    cfg = load_config()
    manifest_path = manifest_path or cfg.manifest_path
    seed = cfg.seed if seed is None else seed
    if not abs(sum(ratios) - 1.0) < 1e-6:
        raise ValueError(f"ratios must sum to 1.0, got {ratios}")
    raise NotImplementedError
