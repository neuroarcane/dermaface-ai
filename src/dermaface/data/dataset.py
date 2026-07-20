"""PyTorch Dataset + DataLoader factory backed by the processed manifest CSV.

Owner: Aparna (Data Lead), paired with Rolando (Data Pipeline & QA Support).

The manifest (data/processed/manifest.csv) columns are documented in
data/README.md: path, label, severity, skin_type, source, split.

The module stays import-light: torch / torchvision are imported lazily inside
the functions that need them, so ``import dermaface.data.dataset`` works in a
plain environment (e.g. for the manifest/split unit tests). ``DermaFaceDataset``
is duck-typed against ``torch.utils.data.Dataset`` (implements ``__len__`` /
``__getitem__``), which is all ``DataLoader`` requires — so it can also be
exercised with a non-torch transform in tests.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Callable

from dermaface.config import CLASS_NAMES, SPLIT_NAMES, Config, load_config, skin_tone_band
from dermaface.data.preprocessing import build_transforms

LABEL_TO_IDX = {name: i for i, name in enumerate(CLASS_NAMES)}
IDX_TO_LABEL = {i: name for name, i in LABEL_TO_IDX.items()}


class DermaFaceDataset:
    """Reads the manifest and yields ``(image_tensor, label_idx)`` pairs.

    Args:
        manifest_path: path to ``manifest.csv``.
        split: 'train' | 'val' | 'test'.
        cfg: configuration (defaults to ``load_config()``).
        transform: override the image transform (defaults to
            ``build_transforms``). Injectable for testing without torchvision.
        skip_missing: drop rows whose image file is absent (useful while images
            are still downloading).
    """

    def __init__(
        self,
        manifest_path: Path,
        split: str,
        cfg: Config | None = None,
        *,
        transform: Callable[[Any], Any] | None = None,
        skip_missing: bool = False,
    ) -> None:
        self.cfg = cfg or load_config()
        self.manifest_path = Path(manifest_path)
        self.split = split
        self.skip_missing = skip_missing
        self.transform = transform if transform is not None else build_transforms(
            self.cfg, train=(split == "train")
        )
        self._rows: list[dict[str, Any]] = self._load_rows()

    def _load_rows(self) -> list[dict[str, Any]]:
        """Load and filter manifest rows for this split.

        Reads the CSV, validates the schema, filters to ``self.split``, resolves
        each image to an absolute path, and maps the string label to an index.
        For the frozen test split, reads the immutable ``test_manifest.csv`` when
        present.
        """
        # Prefer the frozen per-split manifest (train/eval/test/demo) when present.
        source = self.manifest_path
        frozen = self.manifest_path.with_name(f"{self.split}_manifest.csv")
        if frozen.exists():
            source = frozen
        if not source.exists():
            raise FileNotFoundError(f"manifest not found at {source}")

        with source.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            required = {"path", "label", "skin_type", "split"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"manifest {source} missing columns: {sorted(missing)}")

            rows: list[dict[str, Any]] = []
            for r in reader:
                if r["split"] != self.split:
                    continue
                label = r["label"]
                if label not in LABEL_TO_IDX:
                    raise ValueError(f"unknown label {label!r} in {source}")
                abs_path = (self.cfg.data_dir / r["path"]).resolve()
                if self.skip_missing and not abs_path.exists():
                    continue
                rows.append(
                    {
                        "path": abs_path,
                        "label": label,
                        "label_idx": LABEL_TO_IDX[label],
                        "skin_type": r.get("skin_type", "unknown"),
                        # coarse band for fairness reporting (see config.skin_tone_band)
                        "skin_tone_band": skin_tone_band(r.get("skin_type", "unknown")),
                        "severity": r.get("severity", "n/a"),
                        "source": r.get("source", ""),
                    }
                )
        return rows

    @property
    def rows(self) -> list[dict[str, Any]]:
        return self._rows

    @property
    def labels(self) -> list[int]:
        return [r["label_idx"] for r in self._rows]

    def __len__(self) -> int:
        return len(self._rows)

    def __getitem__(self, idx: int):
        from PIL import Image  # lazy: keep module import cheap

        row = self._rows[idx]
        with Image.open(row["path"]) as img:
            image = img.convert("RGB")
            tensor = self.transform(image)
        return tensor, row["label_idx"]


def _class_weights(labels: list[int], num_classes: int) -> list[float]:
    """Inverse-frequency weight per sample, for a WeightedRandomSampler."""
    counts = [0] * num_classes
    for y in labels:
        counts[y] += 1
    freq = [c if c > 0 else 1 for c in counts]
    per_class = [1.0 / f for f in freq]
    return [per_class[y] for y in labels]


def build_dataloaders(
    cfg: Config | None = None,
    *,
    manifest_path: Path | None = None,
    skip_missing: bool = False,
    balance_train: bool = False,
) -> dict[str, Any]:
    """Return ``{"train": ..., "eval": ..., "test": ..., "demo": ...}`` DataLoaders.

    Constructs a ``DermaFaceDataset`` per split and wraps each in a
    ``torch.utils.data.DataLoader`` with ``cfg.batch_size`` / ``cfg.num_workers``.

    Class imbalance (Sprint-2 decision): handled by a **class-weighted loss**, not
    by resampling — see ``dermaface.data.weights.class_weights()``. Hence
    ``balance_train`` defaults to **False**.

    Setting ``balance_train=True`` enables a ``WeightedRandomSampler`` (inverse
    class frequency) instead. Use one or the other, never both: combining the
    sampler with weighted-loss training double-corrects the imbalance and makes
    the model over-predict rare classes.

    Raises:
        RuntimeError: if torch is not installed.
    """
    cfg = cfg or load_config()
    manifest_path = manifest_path or cfg.manifest_path
    try:
        import torch
        from torch.utils.data import DataLoader, WeightedRandomSampler
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "build_dataloaders requires torch. Install with `pip install -r requirements.txt`."
        ) from exc

    loaders: dict[str, Any] = {}
    for split in SPLIT_NAMES:
        ds = DermaFaceDataset(manifest_path, split, cfg, skip_missing=skip_missing)
        if len(ds) == 0:
            loaders[split] = None
            continue
        if split == "train" and balance_train:
            weights = _class_weights(ds.labels, cfg.num_classes)
            sampler = WeightedRandomSampler(
                torch.as_tensor(weights, dtype=torch.double),
                num_samples=len(ds),
                replacement=True,
            )
            loaders[split] = DataLoader(
                ds,
                batch_size=cfg.batch_size,
                sampler=sampler,
                num_workers=cfg.num_workers,
                drop_last=False,
            )
        else:
            loaders[split] = DataLoader(
                ds,
                batch_size=cfg.batch_size,
                shuffle=(split == "train"),
                num_workers=cfg.num_workers,
                drop_last=False,
            )
    return loaders


if __name__ == "__main__":
    dls = build_dataloaders()
    for name, dl in dls.items():
        n = len(dl.dataset) if dl is not None else 0
        print(f"{name}: {n} samples")
