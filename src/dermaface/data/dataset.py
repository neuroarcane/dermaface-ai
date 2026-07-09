"""PyTorch Dataset + DataLoader factory backed by the processed manifest CSV.

Owner: Aparna (Data Lead), paired with Rolando (Data Pipeline & QA Support).

The manifest (data/processed/manifest.csv) columns are documented in
data/README.md: path, label, severity, skin_type, source, split.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dermaface.config import CLASS_NAMES, Config, load_config
from dermaface.data.preprocessing import build_transforms

LABEL_TO_IDX = {name: i for i, name in enumerate(CLASS_NAMES)}
IDX_TO_LABEL = {i: name for name, i in LABEL_TO_IDX.items()}


class DermaFaceDataset:
    """Reads the manifest and yields (image_tensor, label_idx) pairs.

    TODO(Aparna/Rolando): subclass ``torch.utils.data.Dataset`` and implement
    ``__len__`` / ``__getitem__`` (load image via PIL, apply transform,
    map label -> index). Kept framework-light here so the module imports
    without torch installed.
    """

    def __init__(self, manifest_path: Path, split: str, cfg: Config | None = None) -> None:
        self.cfg = cfg or load_config()
        self.manifest_path = Path(manifest_path)
        self.split = split
        self.transform = build_transforms(self.cfg, train=(split == "train"))
        self._rows: list[dict[str, Any]] = self._load_rows()

    def _load_rows(self) -> list[dict[str, Any]]:
        """Load and filter manifest rows for this split.

        TODO(Aparna/Rolando): read CSV, filter by split, validate columns.
        """
        raise NotImplementedError

    def __len__(self) -> int:
        return len(self._rows)


def build_dataloaders(cfg: Config | None = None) -> dict[str, Any]:
    """Return {"train": ..., "val": ..., "test": ...} DataLoaders.

    TODO(Aparna/Rolando): construct DermaFaceDataset per split and wrap in
    torch.utils.data.DataLoader with cfg.batch_size / cfg.num_workers.
    Consider a WeightedRandomSampler for class imbalance (rosacea is rare).
    """
    cfg = cfg or load_config()
    raise NotImplementedError
