"""End-to-end pipeline smoke test on a synthetic slice.

Owner: Rolando (Data Pipeline & QA).

Runs the full Sprint-1 pipeline on a throwaway data dir:
    make_smoke_slice -> download_source (validate) -> build_manifest
    -> make_splits -> build_dataloaders (real batch)

If torch is installed it pulls a real batch from ``build_dataloaders`` and prints
the tensor shape (the Definition of Done). If torch is absent, it still proves
manifest/splits/Dataset by collating a batch with a numpy transform, so the data
plumbing is verified everywhere; only the DataLoader wrapper needs torch.

    python scripts/verify_slice.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _numpy_transform(img):
    """Minimal resize+normalize -> CHW float array (stand-in for torchvision)."""
    from PIL import Image

    img = img.resize((224, 224), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0  # HWC
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    arr = (arr - mean) / std
    return np.transpose(arr, (2, 0, 1))  # CHW


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="dermaface_smoke_"))
    os.environ["DERMAFACE_DATA_DIR"] = str(tmp)

    from make_smoke_slice import make_slice

    from dermaface.data import download, manifest, splits
    from dermaface.data.dataset import DermaFaceDataset, build_dataloaders

    raw_dir = tmp / "raw"
    make_slice(raw_dir, per_class=8)
    print(f"[1/5] synthetic slice -> {raw_dir}")

    # download_source should now find & validate the metadata CSVs.
    for src in download.SOURCES:
        download.download_source(src, raw_dir, download_images=False)
    print("[2/5] download_source validated all 3 sources (metadata present)")

    manifest_path, summary = manifest.build_manifest(raw_dir, require_image_exists=True)
    print(f"[3/5] manifest -> {manifest_path}")
    print("      " + summary.render().replace("\n", "\n      "))

    counts = splits.make_splits(manifest_path)
    print(f"[4/5] splits -> {counts}")

    # --- Definition of Done: a real batch -----------------------------------
    try:
        import torch  # noqa: F401

        loaders = build_dataloaders(skip_missing=True)
        train = loaders["train"]
        xb, yb = next(iter(train))
        print(f"[5/5] build_dataloaders OK (torch) — batch x={tuple(xb.shape)} y={tuple(yb.shape)}")
        assert xb.shape[1:] == (3, 224, 224), xb.shape
        assert xb.shape[0] == yb.shape[0]
    except ImportError:
        ds = DermaFaceDataset(manifest_path, "train", transform=_numpy_transform, skip_missing=True)
        n = min(len(ds), 8)
        batch = np.stack([ds[i][0] for i in range(n)])
        ys = [ds[i][1] for i in range(n)]
        print(
            f"[5/5] build_dataloaders needs torch (not installed here). "
            f"Verified Dataset path instead — collated batch x={batch.shape} y=({len(ys)},)"
        )
        assert batch.shape[1:] == (3, 224, 224), batch.shape

    print("\nPASS: pipeline produces real batches on the slice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
