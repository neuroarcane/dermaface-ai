"""Class weights for the imbalance-aware loss (Sprint 2).

Owner: Rolando (Data QA), for Iva (ML Research) to plug into training.

Team decision (Sprint 2): handle class imbalance with a **class-weighted loss**
rather than an oversampling sampler. With ~200 rosacea images, oversampling would
show the model the same handful of images repeatedly (memorisation risk), whereas
weighting the loss corrects the imbalance without duplicating data.

⚠️ Use **one** correction, not both. ``build_dataloaders(..., balance_train=True)``
enables a WeightedRandomSampler; leave it **off** (the default) when training with
these class weights, or the imbalance gets corrected twice and the model
over-predicts the rare class.

Weights are computed from the **train split only** (never eval/test — that would
leak label distribution from held-out data), and by default from the **cleaned**
manifest.

Schemes
-------
``balanced`` (default)
    ``w_c = N / (K * n_c)`` — the standard inverse-frequency rule (same as
    scikit-learn's ``class_weight="balanced"``). Fully compensates the imbalance;
    the weighted average of the weights is 1, so the loss scale stays sane.
``sqrt``
    ``w_c = sqrt(N / (K * n_c))``, renormalised to mean 1 — a **milder**
    correction. Useful if ``balanced`` over-corrects and precision on the rare
    class drops.

Usage in training:

    from dermaface.data.weights import class_weights
    import torch, torch.nn as nn

    w = class_weights()                       # aligned to config.CLASS_NAMES
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(w, dtype=torch.float))
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

from dermaface.config import CLASS_NAMES, load_config

SCHEMES = ("balanced", "sqrt")


def _resolve_manifest(cfg, manifest_path: Path | None) -> Path:
    """Prefer the cleaned manifest when present, else the raw one."""
    if manifest_path is not None:
        return Path(manifest_path)
    if cfg.clean_manifest_path.exists():
        return cfg.clean_manifest_path
    return cfg.manifest_path


def class_counts(
    manifest_path: Path | None = None, split: str | None = "train"
) -> dict[str, int]:
    """Return {class_name: count} for ``split`` (or the whole manifest if None)."""
    cfg = load_config()
    path = _resolve_manifest(cfg, manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"manifest not found at {path}; run `make data` first")
    counts: Counter = Counter()
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if split is not None and row.get("split") != split:
                continue
            counts[row["label"]] += 1
    return {name: counts.get(name, 0) for name in CLASS_NAMES}


def class_weights(
    manifest_path: Path | None = None,
    split: str | None = "train",
    scheme: str = "balanced",
) -> list[float]:
    """Return per-class loss weights, ordered to match ``config.CLASS_NAMES``.

    The returned list lines up with the label indices the DataLoader emits, so it
    can be passed straight to ``nn.CrossEntropyLoss(weight=...)``.
    """
    if scheme not in SCHEMES:
        raise ValueError(f"unknown scheme {scheme!r}; expected one of {SCHEMES}")
    counts = class_counts(manifest_path, split)
    n_total = sum(counts.values())
    if n_total == 0:
        raise ValueError(f"no rows found for split={split!r}")
    k = len(CLASS_NAMES)

    raw = []
    for name in CLASS_NAMES:
        n_c = counts[name]
        if n_c == 0:  # class absent from this split — neutral weight
            raw.append(1.0)
            continue
        w = n_total / (k * n_c)
        raw.append(math.sqrt(w) if scheme == "sqrt" else w)

    if scheme == "sqrt":  # renormalise so the mean weight is 1
        mean = sum(raw) / k
        raw = [w / mean for w in raw]
    return [round(w, 6) for w in raw]


def write_class_weights(
    out_path: Path | None = None,
    manifest_path: Path | None = None,
    split: str | None = "train",
    scheme: str = "balanced",
) -> tuple[Path, dict]:
    """Write class weights + counts to JSON for the modelling team."""
    cfg = load_config()
    out_path = Path(out_path) if out_path else (cfg.data_dir / "processed" / "class_weights.json")
    counts = class_counts(manifest_path, split)
    weights = class_weights(manifest_path, split, scheme)
    payload = {
        "classes": CLASS_NAMES,
        "split": split,
        "scheme": scheme,
        "counts": counts,
        "weights": weights,
        "source_manifest": str(_resolve_manifest(cfg, manifest_path)),
        "note": (
            "Pass to nn.CrossEntropyLoss(weight=...). Do NOT also enable the "
            "WeightedRandomSampler (build_dataloaders balance_train=True) — that "
            "double-corrects the imbalance."
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    return out_path, payload


def render(payload: dict) -> str:
    lines = [
        f"Class weights ({payload['scheme']}, split={payload['split']}) "
        f"from {Path(payload['source_manifest']).name}:"
    ]
    for name, w in zip(payload["classes"], payload["weights"]):
        n = payload["counts"][name]
        lines.append(f"  {name:<8} n={n:<6} weight={w:.3f}")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Compute class weights for a weighted loss.")
    ap.add_argument("--split", default="train", help="split to count (default: train)")
    ap.add_argument("--scheme", default="balanced", choices=SCHEMES)
    args = ap.parse_args()

    path, payload = write_class_weights(split=args.split, scheme=args.scheme)
    print(render(payload))
    print(f"\nWrote {path}")
