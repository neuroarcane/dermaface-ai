"""Train/eval/test/demo splitting — stratified by class AND Fitzpatrick skin type.

Owner: Aparna (Data Lead), paired with Rolando (Data QA), with Iva
(ML Research) on the fairness rationale.

Stratifying by skin type is what makes the Week-2 fairness analysis possible.
Freeze the test set early and never tune on it. A small ``demo`` split is
reserved for the Streamlit app demo so we never show the app test/train images.

Implementation notes:
  * We stratify on the **joint** key (label, skin_type). Each group is shuffled
    with a fixed seed and partitioned by ``ratios`` so every (class, skin-tone)
    cell is represented in each split in the same proportion.
  * Deterministic: same manifest + same seed => identical split, every run
    (requirement N1, reproducibility).
  * In addition to writing the ``split`` column back into ``manifest.csv``, we
    persist one frozen ``<split>_manifest.csv`` per split (train/eval/test/demo).
    Modeling code loads a split from its own file so the test set stays immutable.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

from dermaface.config import DEFAULT_SPLIT_RATIOS, SPLIT_NAMES, load_config
from dermaface.data.manifest import MANIFEST_COLUMNS

DEFAULT_RATIOS = DEFAULT_SPLIT_RATIOS  # (train, eval, test, demo)


def _partition(n: int, ratios: tuple[float, ...]) -> list[int]:
    """Split ``n`` items into per-split counts matching ``ratios``.

    Uses largest-remainder rounding so the counts always sum to ``n``. For very
    small groups we guarantee the test split (index 2) is covered before eval/
    demo, so no (class, skin-tone) cell is silently absent from evaluation.
    """
    k = len(ratios)
    if n == 0:
        return [0] * k
    raw = [n * r for r in ratios]
    floors = [int(x) for x in raw]
    remainder = n - sum(floors)
    order = sorted(range(k), key=lambda i: raw[i] - floors[i], reverse=True)
    for i in range(remainder):
        floors[order[i]] += 1
    # For tiny groups, ensure the frozen test split (index 2) gets an item.
    if n >= 2 and floors[2] == 0:
        biggest = max(range(k), key=lambda i: floors[i])
        floors[biggest] -= 1
        floors[2] += 1
    return floors


def make_splits(
    manifest_path: Path | None = None,
    ratios: tuple[float, ...] = DEFAULT_RATIOS,
    seed: int | None = None,
) -> dict[str, int]:
    """Assign a ``split`` column to the manifest, stratified by (label, skin_type).

    1. Load the manifest.
    2. Group by (label, skin_type); split each group by ``ratios``.
    3. Write the ``split`` column back and persist one frozen manifest per split.

    Returns a dict of split -> row count.
    """
    cfg = load_config()
    manifest_path = Path(manifest_path) if manifest_path else cfg.manifest_path
    seed = cfg.seed if seed is None else seed
    if len(ratios) != len(SPLIT_NAMES):
        raise ValueError(f"expected {len(SPLIT_NAMES)} ratios for {SPLIT_NAMES}, got {ratios}")
    if not abs(sum(ratios) - 1.0) < 1e-6:
        raise ValueError(f"ratios must sum to 1.0, got {ratios}")
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"manifest not found at {manifest_path}; run manifest.build_manifest() first"
        )

    with manifest_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError(f"manifest at {manifest_path} is empty")

    groups: dict[tuple[str, str], list[int]] = {}
    for i, row in enumerate(rows):
        key = (row["label"], row.get("skin_type", "unknown"))
        groups.setdefault(key, []).append(i)

    rng = random.Random(seed)
    counts = {name: 0 for name in SPLIT_NAMES}
    for key in sorted(groups):  # deterministic regardless of dict order
        idxs = groups[key][:]
        rng.shuffle(idxs)
        alloc = _partition(len(idxs), ratios)
        # build split boundaries
        bounds = []
        running = 0
        for c in alloc:
            running += c
            bounds.append(running)
        for j, idx in enumerate(idxs):
            split = SPLIT_NAMES[-1]
            for s, b in enumerate(bounds):
                if j < b:
                    split = SPLIT_NAMES[s]
                    break
            rows[idx]["split"] = split
            counts[split] += 1

    # Write the split column back to the manifest.
    with manifest_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    # Persist one frozen manifest per split (train/eval/test/demo).
    for split in SPLIT_NAMES:
        out = manifest_path.with_name(f"{split}_manifest.csv")
        with out.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=MANIFEST_COLUMNS)
            writer.writeheader()
            writer.writerows([r for r in rows if r["split"] == split])

    return counts


if __name__ == "__main__":
    result = make_splits()
    print("split counts:", result)
