"""Fitzpatrick17k image acquisition via Kaggle mirror, matched by content MD5.

Why: fitzpatrick17k.csv's own `url` column points to dermaamin.com and
atlasdermatologico.com.br. dermaamin.com has restructured its site and ~85% of
those URLs now 404 (see fitzpatrick17k-findings.md). Rather than keep fighting
dead links, this pulls a full Kaggle mirror of the same dataset and matches each
mirror image to our manifest by MD5 content hash (the `md5hash` column in
fitzpatrick17k.csv IS the MD5 of the image bytes) — so it doesn't matter how the
mirror named its files, a byte-identical match is guaranteed. Zero dead links.

Usage:
    python scripts/pull_fitzpatrick_images.py --workers 16 --timeout 10
    python scripts/pull_fitzpatrick_images.py --status
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from dermaface.config import load_config  # noqa: E402

KAGGLE_MIRROR = "nazmusresan/fitzpatrick17k"
_IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}


def _manifest_keys(manifest_path: Path, source: str) -> set[str]:
    keys: set[str] = set()
    with manifest_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("source") == source:
                keys.add(Path(row["path"]).stem)
    return keys


def _index_fitz_csv(csv_path: Path) -> tuple[set[str], dict[str, str]]:
    """Return (set of md5hashes, {url_alphanum filename -> md5})."""
    md5_set: set[str] = set()
    stem_to_md5: dict[str, str] = {}
    with csv_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            md5 = (row.get("md5hash") or "").strip().lower()
            if not md5:
                continue
            md5_set.add(md5)
            ua = (row.get("url_alphanum") or "").strip()
            if ua:
                stem_to_md5[ua] = md5
    return md5_set, stem_to_md5


def _md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _kaggle_download(dataset: str, tmp_dir: Path) -> Path:
    if shutil.which("kaggle") is None:
        raise FileNotFoundError(
            "`kaggle` CLI not installed. Run `pip install kaggle` and set up "
            "~/.kaggle/kaggle.json first."
        )
    tmp_dir.mkdir(parents=True, exist_ok=True)
    print(f"[fitzpatrick17k] downloading Kaggle mirror {dataset} -> {tmp_dir} ...")
    subprocess.run(
        ["kaggle", "datasets", "download", "-d", dataset, "-p", str(tmp_dir), "--unzip"],
        check=True,
    )
    return tmp_dir


def pull(workers: int, timeout: int) -> None:
    cfg = load_config()
    raw_dir = cfg.data_dir / "raw"
    dest = raw_dir / "fitzpatrick17k"
    dest.mkdir(parents=True, exist_ok=True)

    # Write to LOCAL disk first, not Drive directly (lesson from the SCIN fix:
    # Drive's FUSE mount doesn't handle many small concurrent writes reliably).
    local_img_dir = Path("/content/fitz_images")
    local_img_dir.mkdir(parents=True, exist_ok=True)

    csv_path = dest / "fitzpatrick17k.csv"
    if not csv_path.exists():
        print(f"error: {csv_path} not found.")
        sys.exit(1)

    md5_set, stem_to_md5 = _index_fitz_csv(csv_path)
    manifest_keys = _manifest_keys(cfg.manifest_path, "fitzpatrick17k")
    md5_set &= manifest_keys
    print(f"[fitzpatrick17k] manifest wants {len(md5_set)} images.")

    # Skip the download entirely if everything's already local
    already = {p.stem for p in local_img_dir.glob("*.jpg")}
    if md5_set <= already:
        print("[fitzpatrick17k] all images already present locally, skipping Kaggle download.")
        mirror_dir = None
    else:
        tmp_dir = Path("/content/fitz_kaggle_raw")
        mirror_dir = _kaggle_download(KAGGLE_MIRROR, tmp_dir)

    if mirror_dir is not None:
        scanned = imported = 0
        for path in mirror_dir.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in _IMG_EXTS:
                continue
            scanned += 1
            stem = path.stem.lower()
            if len(stem) == 32 and all(c in "0123456789abcdef" for c in stem):
                md5 = stem
            elif path.name in stem_to_md5:
                md5 = stem_to_md5[path.name]
            else:
                md5 = _md5_file(path)
            if md5 not in md5_set:
                continue
            out = local_img_dir / f"{md5}.jpg"
            if not out.exists():
                shutil.copy2(path, out)
                imported += 1
            if scanned % 500 == 0:
                print(f"  scanned {scanned}, imported {imported}", flush=True)
        print(f"[fitzpatrick17k] imported {imported} new images (scanned {scanned} mirror files).")
        shutil.rmtree(mirror_dir, ignore_errors=True)

    # Bulk-copy to Drive in one shot (not many small FUSE writes)
    drive_img_dir = dest / "images"
    drive_img_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for f in local_img_dir.glob("*.jpg"):
        target = drive_img_dir / f.name
        if not target.exists():
            shutil.copy2(f, target)
            copied += 1
    have_now = sum(1 for _ in drive_img_dir.glob("*.jpg"))
    print(f"[fitzpatrick17k] copied {copied} new files to Drive.")
    print(f"[fitzpatrick17k] total on disk: {have_now}/{len(md5_set)}")


def status() -> None:
    cfg = load_config()
    dest = cfg.data_dir / "raw" / "fitzpatrick17k"
    img_dir = dest / "images"
    keys = _manifest_keys(cfg.manifest_path, "fitzpatrick17k")
    have = sum(1 for _ in img_dir.glob("*.jpg")) if img_dir.exists() else 0
    print(f"manifest wants: {len(keys)}")
    print(f"on disk:        {have}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    if args.status:
        status()
    else:
        pull(args.workers, args.timeout)
