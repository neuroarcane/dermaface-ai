"""Sprint-1 data-pipeline tests: manifest -> label_map -> splits -> QA -> loaders.

Runs on a synthetic slice generated in a temp dir (no network, no real images).
The torch-dependent test is skipped automatically where torch is unavailable.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from make_smoke_slice import make_slice  # noqa: E402

from dermaface.config import CLASS_NAMES, SPLIT_NAMES  # noqa: E402
from dermaface.data import download, manifest, qa, splits  # noqa: E402
from dermaface.data.dataset import DermaFaceDataset, build_dataloaders  # noqa: E402

HAS_TORCH = importlib.util.find_spec("torch") is not None


def _numpy_transform(img):
    from PIL import Image

    img = img.resize((224, 224), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return np.transpose(arr, (2, 0, 1))


@pytest.fixture()
def slice_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("DERMAFACE_DATA_DIR", str(tmp_path))
    make_slice(tmp_path / "raw", per_class=16)
    return tmp_path


def _built(slice_dir):
    path, _ = manifest.build_manifest(slice_dir / "raw", require_image_exists=True)
    return path


def test_download_source_validates_metadata(slice_dir):
    for src in download.SOURCES:
        download.download_source(src, slice_dir / "raw", download_images=False)
    assert (slice_dir / "raw" / "fitzpatrick17k" / ".download_receipt.json").exists()


def test_build_manifest_schema_and_labels(slice_dir):
    path, summary = manifest.build_manifest(slice_dir / "raw", require_image_exists=True)
    assert path.read_text().splitlines()[0] == "path,label,severity,skin_type,source,split"
    assert summary.total > 0
    assert set(summary.labels) <= set(CLASS_NAMES)
    assert set(summary.rows_by_source) == {"fitzpatrick17k", "scin", "skincon"}


def test_label_map_written(slice_dir):
    path, n = manifest.build_label_map(slice_dir / "raw")
    assert path.exists() and n > 0
    header = path.read_text().splitlines()[0]
    assert header == "source,raw_label,mapped_class,action,n_rows"
    # exclusion rule: nothing containing "erythematosus" maps to a class
    assert manifest.map_label("lupus erythematosus") is None


def test_make_splits_four_way_deterministic(slice_dir):
    path = _built(slice_dir)
    a = splits.make_splits(path, seed=42)
    body_a = path.read_text()
    b = splits.make_splits(path, seed=42)
    assert a == b
    assert body_a == path.read_text()  # byte-identical for same seed
    assert set(a) == set(SPLIT_NAMES)
    assert sum(a.values()) == len(path.read_text().splitlines()) - 1
    # one frozen manifest per split
    for split in SPLIT_NAMES:
        f = path.with_name(f"{split}_manifest.csv")
        assert f.exists()
        assert len(f.read_text().splitlines()) - 1 == a[split]


def test_splits_stratified_every_class_in_test(slice_dir):
    path = _built(slice_dir)
    splits.make_splits(path, seed=42)
    test_rows = [
        r.split(",")[1]
        for r in path.read_text().splitlines()[1:]
        if r.split(",")[-1] == "test"
    ]
    assert set(test_rows) == set(CLASS_NAMES)


def test_qa_report(slice_dir):
    path = _built(slice_dir)
    splits.make_splits(path, seed=42)
    report_path, summary = qa.run_qa(path)
    assert report_path.exists()
    assert summary["total_rows"] > 0
    # images exist in the slice, so none should be flagged missing
    assert summary.get("missing_image", 0) == 0
    header = report_path.read_text().splitlines()[0]
    assert header.startswith("path,source,label,skin_type,split,")


def test_fitzpatrick_kaggle_import_matches_by_md5(tmp_path):
    """Mirror images are matched to the CSV by content MD5, regardless of naming."""
    import csv as _csv
    import hashlib

    fitz = tmp_path / "raw" / "fitzpatrick17k"
    fitz.mkdir(parents=True)
    imgs, rows = {}, []
    for i in range(3):
        content = f"IMG{i}".encode()
        md5 = hashlib.md5(content).hexdigest()
        imgs[md5] = content
        rows.append({"md5hash": md5, "url": f"http://x/{i}", "url_alphanum": f"file{i}.jpg", "label": "acne"})
    with (fitz / "fitzpatrick17k.csv").open("w", newline="") as fh:
        w = _csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    md5s = list(imgs)
    mirror = tmp_path / "mirror"
    (mirror / "sub").mkdir(parents=True)
    (mirror / f"{md5s[0]}.jpg").write_bytes(imgs[md5s[0]])   # md5-named
    (mirror / "file1.jpg").write_bytes(imgs[md5s[1]])        # url_alphanum-named
    (mirror / "sub" / "x.png").write_bytes(imgs[md5s[2]])    # content-hash match
    (mirror / "junk.jpg").write_bytes(b"nope")               # ignored

    n = download.import_fitzpatrick_images(fitz, csv_path=fitz / "fitzpatrick17k.csv", source_dir=mirror)
    assert n == 3
    assert {p.name for p in (fitz / "images").glob("*.jpg")} == {f"{m}.jpg" for m in md5s}
    # manifest-only subset respects keys
    n2 = download.import_fitzpatrick_images(
        tmp_path / "fb", csv_path=fitz / "fitzpatrick17k.csv", keys={md5s[0]}, source_dir=mirror
    )
    assert n2 == 1


def test_dataset_getitem_shape_numpy(slice_dir):
    path = _built(slice_dir)
    splits.make_splits(path, seed=42)
    ds = DermaFaceDataset(path, "train", transform=_numpy_transform, skip_missing=True)
    assert len(ds) > 0
    x, y = ds[0]
    assert x.shape == (3, 224, 224)
    assert isinstance(y, int) and 0 <= y < len(CLASS_NAMES)


@pytest.mark.skipif(not HAS_TORCH, reason="torch not installed")
def test_build_dataloaders_returns_real_batches(slice_dir):
    path = _built(slice_dir)
    splits.make_splits(path, seed=42)
    loaders = build_dataloaders(skip_missing=True)
    assert set(loaders) == set(SPLIT_NAMES)
    xb, yb = next(iter(loaders["train"]))
    assert xb.shape[1:] == (3, 224, 224)
    assert xb.shape[0] == yb.shape[0]
