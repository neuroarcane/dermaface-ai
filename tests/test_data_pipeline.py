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


def test_clean_manifest_drops_flagged_rows(slice_dir):
    """Cleaning removes unknown-skin-type rows and leaves only valid fields."""
    from dermaface.config import FITZPATRICK_TYPES
    from dermaface.data import clean

    path = _built(slice_dir)
    splits.make_splits(path, seed=42)
    clean_path, summary = clean.clean_manifest(path)

    assert clean_path.exists()
    assert summary["rows_out"] > 0
    assert summary["rows_out"] + summary["rows_dropped"] == summary["rows_in"]
    # every surviving row has a valid class and a real Fitzpatrick type
    with clean_path.open(newline="", encoding="utf-8") as fh:
        rows = list(__import__("csv").DictReader(fh))
    assert rows, "cleaned manifest is empty"
    assert all(r["label"] in CLASS_NAMES for r in rows)
    assert all(r["skin_type"] in FITZPATRICK_TYPES for r in rows)
    assert all(r["skin_type"] != "unknown" for r in rows)
    # the original manifest is untouched
    assert path.exists()


def test_freeze_clean_splits_preserves_assignments(slice_dir):
    """Re-freezing from the cleaned manifest keeps split assignments (no reshuffle)."""
    import csv as _csv

    from dermaface.data import clean

    path = _built(slice_dir)
    splits.make_splits(path, seed=42)

    # remember the original test-set membership
    with path.open(newline="", encoding="utf-8") as fh:
        before = {r["path"]: r["split"] for r in _csv.DictReader(fh)}
    test_before = {p for p, s in before.items() if s == "test"}

    clean_path, summary = clean.clean_manifest(path)
    counts = splits.freeze_clean_splits(clean_path)

    frozen_test = path.with_name("test_manifest.csv")
    with frozen_test.open(newline="", encoding="utf-8") as fh:
        test_after = {r["path"] for r in _csv.DictReader(fh)}

    # the clean test set is a SUBSET of the original — nothing new moved in
    assert test_after <= test_before, "re-freezing moved new images into the test set"
    assert counts["test"] == len(test_after)
    # every surviving row kept its original split
    with clean_path.open(newline="", encoding="utf-8") as fh:
        for r in _csv.DictReader(fh):
            assert r["split"] == before[r["path"]]


def test_class_weights_from_train_split(slice_dir):
    """Weights are inverse-frequency, ordered like CLASS_NAMES, train-split only."""
    from dermaface.data import weights as W

    path = _built(slice_dir)
    splits.make_splits(path, seed=42)

    counts = W.class_counts(path, split="train")
    w = W.class_weights(path, split="train", scheme="balanced")
    assert len(w) == len(CLASS_NAMES)
    assert all(x > 0 for x in w)
    # rarer class => larger weight
    present = [(c, counts[c], wi) for c, wi in zip(CLASS_NAMES, w) if counts[c] > 0]
    rarest = min(present, key=lambda t: t[1])
    commonest = max(present, key=lambda t: t[1])
    if rarest[1] != commonest[1]:
        assert rarest[2] > commonest[2]
    # sqrt scheme is a milder correction (spread is smaller)
    w_sqrt = W.class_weights(path, split="train", scheme="sqrt")
    assert (max(w_sqrt) - min(w_sqrt)) <= (max(w) - min(w)) + 1e-9
    # json export
    out, payload = W.write_class_weights(manifest_path=path, split="train")
    assert out.exists() and payload["classes"] == CLASS_NAMES


def _face_backend() -> bool:
    from dermaface.data.preprocessing import face_backend_available

    return face_backend_available()


@pytest.mark.skipif(not _face_backend(), reason="no working OpenCV (cv2) install")
def test_has_face_rejects_non_faces_and_bad_files(tmp_path):
    """Negative paths for the face detector.

    Positive detection is verified separately against a real photograph
    (scikit-image's `astronaut` sample) — we don't ship a face image in the repo.
    """
    import numpy as np
    from PIL import Image

    from dermaface.data.preprocessing import has_face

    speckle = tmp_path / "speckle.png"
    arr = (np.random.RandomState(0).rand(224, 224, 3) * 255).astype("uint8")
    Image.fromarray(arr).save(speckle)
    assert has_face(speckle) is False

    flat = tmp_path / "flat.png"
    Image.new("RGB", (224, 224), (200, 120, 110)).save(flat)
    assert has_face(flat) is False

    corrupt = tmp_path / "bad.jpg"
    corrupt.write_bytes(b"not an image")
    assert has_face(corrupt) is False  # must not raise


def test_colour_augmentation_stays_disabled_by_default():
    """Saturation/hue jitter must stay off — it destroys the erythema signal."""
    from dermaface.config import load_config

    cfg = load_config()
    assert cfg.aug_saturation == 0.0, "saturation jitter would distort redness"
    assert cfg.aug_hue == 0.0, "hue jitter would distort redness"
    assert cfg.aug_brightness <= 0.2 and cfg.aug_contrast <= 0.2, "colour jitter too strong"


@pytest.mark.skipif(not HAS_TORCH, reason="torch/torchvision not installed")
def test_augmentation_is_train_only_and_eval_is_deterministic():
    """Train transforms vary run-to-run; eval transforms never do."""
    from PIL import Image

    from dermaface.config import load_config
    from dermaface.data.preprocessing import build_transforms

    cfg = load_config()
    img = Image.new("RGB", (300, 300), (200, 90, 90))
    # give the image structure so crops/flips actually differ
    px = img.load()
    for y in range(0, 300, 3):
        for x in range(0, 300, 3):
            px[x, y] = ((x * 7) % 256, (y * 5) % 256, 120)

    eval_tf = build_transforms(cfg, train=False)
    a, b = eval_tf(img), eval_tf(img)
    assert a.shape == (3, cfg.image_size, cfg.image_size)
    assert bool((a == b).all()), "eval transform must be deterministic"

    train_tf = build_transforms(cfg, train=True)
    outs = [train_tf(img) for _ in range(6)]
    assert all(o.shape == (3, cfg.image_size, cfg.image_size) for o in outs)
    assert any(not bool((outs[0] == o).all()) for o in outs[1:]), "train transform is not random"


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
