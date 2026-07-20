"""Dataset acquisition helpers.

Owner: Aparna (Data Lead), paired with Rolando (Data Pipeline & QA Support).

Downloads/organizes the three source datasets into ``data/raw/``:
  - Fitzpatrick17k   https://github.com/mattgroh/fitzpatrick17k
  - SKINCON          https://skincon-dataset.github.io/
  - Google SCIN      https://github.com/google-research-datasets/scin

⚠️ Verify each dataset's LICENSE before downloading (see docs/data-strategy.md)
and record provenance in data/external/PROVENANCE.md. Never commit images.

Design notes
------------
Each source has different access mechanics, so ``download_source`` is a thin
dispatcher over one handler per source. The handlers are deliberately split
into two phases:

  1. **Metadata** — the label / annotation CSVs. These are small, are what
     Sprint-1 needs, and are what the manifest builder reads. The team places
     them in ``data/raw/<source>/`` (they are gitignored). Each handler
     *validates* that the expected CSV(s) are present and records a receipt.
  2. **Images** — large, external, and (for Fitzpatrick17k / DDI) subject to a
     non-commercial / credentialized license. Only fetched when
     ``download_images=True`` so the pipeline can be exercised on metadata alone.

Image fetching is:
  * **manifest-aware** (``manifest_only=True``) — fetch only the images that made
    it into ``manifest.csv`` (~2k) instead of walking the full CSVs (~16.5k for
    Fitzpatrick17k). This is the default from the CLI.
  * **parallel** — a thread pool with a short per-request timeout, so dead
    clinical-atlas URLs (common in Fitzpatrick17k) fail fast instead of blocking.
  * **resumable** — ``data/raw/`` is immutable; existing files are never
    re-downloaded, so re-running only fills gaps.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from dermaface.config import load_config

SOURCES = ("fitzpatrick17k", "skincon", "scin")

# Candidate filenames for each source's metadata CSV(s). The first match wins,
# so both the upstream names and the names the team downloaded are accepted.
SOURCE_METADATA: dict[str, list[list[str]]] = {
    "fitzpatrick17k": [
        ["fitzpatrick17k.csv"],
    ],
    "skincon": [
        [
            "SKINCON Fitzpatrick17k annotations.csv",
            "SKINCON Fitzpatric17k annotations.csv",  # upstream filename typo
            "skincon_fitzpatrick17k.csv",
        ],
        ["SKINCON DDI annotations.csv", "skincon_ddi.csv"],
    ],
    "scin": [
        ["dataset_scin_labels.csv", "scin_labels.csv"],
        ["dataset_scin_cases.csv", "scin_cases.csv"],
    ],
}

# Public GCS bucket for SCIN images (see the SCIN repo's scin_demo.ipynb).
SCIN_GCS_BUCKET = "gs://dx-scin-public-data"
# The same bucket over public HTTPS — lets us fetch without the Google Cloud SDK.
SCIN_HTTP_BASE = "https://storage.googleapis.com/dx-scin-public-data"

# A Kaggle mirror that ships the full Fitzpatrick17k image set (no dead links).
# Any Fitzpatrick image mirror works — images are matched by content MD5, so the
# mirror's own file naming/layout does not matter. Override with --from-kaggle.
FITZPATRICK_KAGGLE_DEFAULT = "nazmusresan/fitzpatrick17k"
_IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}

_USER_AGENT = "dermaface-ai/0.1 (research; +https://github.com/neuroarcane/dermaface-ai)"

DEFAULT_WORKERS = 16
DEFAULT_TIMEOUT = 15  # seconds per image request


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def download_all(
    raw_dir: Path | None = None,
    *,
    download_images: bool = False,
    manifest_only: bool = False,
    manifest_path: Path | None = None,
    workers: int = DEFAULT_WORKERS,
    timeout: int = DEFAULT_TIMEOUT,
) -> None:
    """Download/organize every source dataset into ``raw_dir`` (default: data/raw)."""
    raw_dir = raw_dir or (load_config().data_dir / "raw")
    for source in SOURCES:
        download_source(
            source,
            raw_dir,
            download_images=download_images,
            manifest_only=manifest_only,
            manifest_path=manifest_path,
            workers=workers,
            timeout=timeout,
        )


def download_source(
    source: str,
    raw_dir: Path,
    *,
    download_images: bool = False,
    manifest_only: bool = False,
    manifest_path: Path | None = None,
    workers: int = DEFAULT_WORKERS,
    timeout: int = DEFAULT_TIMEOUT,
    fitz_source_dir: Path | None = None,
    fitz_kaggle: str | None = None,
) -> None:
    """Download/organize a single dataset by name into ``raw_dir/<source>``.

    Args:
        source: one of ``SOURCES``.
        raw_dir: the ``data/raw`` directory. ``raw_dir/<source>`` is created.
        download_images: if True, also fetch the (large, licensed) image files.
        manifest_only: fetch only the images referenced in ``manifest.csv``
            (much faster). Requires the manifest to exist.
        manifest_path: manifest location (default: config.manifest_path).
        workers: thread-pool size for parallel image downloads.
        timeout: per-request timeout in seconds (dead URLs fail fast).
        fitz_source_dir: (fitzpatrick17k only) a local folder of already-downloaded
            mirror images to import from instead of fetching external URLs.
        fitz_kaggle: (fitzpatrick17k only) a Kaggle dataset slug to download the
            image mirror from (needs the ``kaggle`` CLI + API token). Bypasses the
            dead external URLs entirely.

    Raises:
        ValueError: unknown source.
        FileNotFoundError: a required metadata CSV (or the manifest) is missing.
    """
    if source not in SOURCES:
        raise ValueError(f"Unknown source {source!r}; expected one of {SOURCES}")

    dest = Path(raw_dir) / source
    dest.mkdir(parents=True, exist_ok=True)

    keys = None
    if download_images and manifest_only:
        mp = manifest_path or load_config().manifest_path
        keys = _manifest_keys(mp, source)

    if source == "fitzpatrick17k":
        _download_fitzpatrick17k(
            dest,
            download_images=download_images,
            keys=keys,
            workers=workers,
            timeout=timeout,
            source_dir=fitz_source_dir,
            kaggle=fitz_kaggle,
        )
    elif source == "skincon":
        _download_skincon(dest, download_images=download_images, keys=keys, workers=workers, timeout=timeout)
    else:
        _download_scin(dest, download_images=download_images, keys=keys, workers=workers, timeout=timeout)


# --------------------------------------------------------------------------- #
# Per-source handlers
# --------------------------------------------------------------------------- #
def _download_fitzpatrick17k(
    dest, *, download_images, keys, workers, timeout, source_dir=None, kaggle=None
):
    """Fitzpatrick17k: a CSV of image URLs (non-commercial / research use).

    Image acquisition has two modes:
      * **mirror import** (``source_dir`` or ``kaggle``): match a folder of
        already-downloaded mirror images to the CSV by content MD5 (the
        ``md5hash`` column is the MD5 of the image bytes), sidestepping dead URLs.
      * **URL fetch** (default): parallel download from the ``url`` column.
    """
    csv_path = _require_metadata(
        dest,
        SOURCE_METADATA["fitzpatrick17k"][0],
        source="fitzpatrick17k",
        hint=(
            "Obtain fitzpatrick17k.csv from https://github.com/mattgroh/fitzpatrick17k "
            f"and place it in {dest}/ . Review the LICENSE — non-commercial use only."
        ),
    )

    n_images = 0
    note = None
    src = "external-urls"
    if download_images and (source_dir or kaggle):
        n_images = import_fitzpatrick_images(
            dest, csv_path=csv_path, keys=keys, source_dir=source_dir, kaggle=kaggle
        )
        src = f"kaggle:{kaggle}" if kaggle else f"dir:{source_dir}"
    elif download_images:
        img_dir = dest / "images"
        img_dir.mkdir(exist_ok=True)
        jobs = []
        with csv_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                url = (row.get("url") or "").strip()
                md5 = (row.get("md5hash") or "").strip()
                if not url or not md5:
                    continue
                if keys is not None and md5 not in keys:
                    continue
                out = img_dir / f"{md5}.jpg"
                if out.exists():
                    continue
                jobs.append((url, out))
        n_images = _parallel_fetch(jobs, workers=workers, timeout=timeout, label="fitzpatrick17k")

    _write_receipt(
        dest,
        source="fitzpatrick17k",
        metadata=[csv_path.name],
        images_downloaded=n_images,
        images_requested=download_images,
        license="Non-commercial / research use (see PROVENANCE.md). Images hosted externally.",
        note=(f"images imported from {src}" if download_images else None) or note,
    )


def _download_skincon(dest, *, download_images, keys, workers, timeout):
    """SKINCON: dense clinical-concept annotations (MIT-licensed annotations)."""
    found = []
    for candidates in SOURCE_METADATA["skincon"]:
        found.append(
            _require_metadata(
                dest,
                candidates,
                source="skincon",
                hint=(
                    "Download the SKINCON annotation CSVs from "
                    f"https://skincon-dataset.github.io/ and place them in {dest}/ ."
                ),
            )
        )
    ddi_note = None
    if download_images:
        ddi_note = (
            "DDI images require credentialized access (https://ddi-dataset.github.io/); "
            f"request access and place them under {dest}/ddi_images/ manually."
        )
    _write_receipt(
        dest,
        source="skincon",
        metadata=[p.name for p in found],
        images_downloaded=0,
        images_requested=download_images,
        license="Annotations: MIT. Images: inherit Fitzpatrick17k / DDI terms.",
        note=ddi_note,
    )


def _download_scin(dest, *, download_images, keys, workers, timeout):
    """Google SCIN: crowdsourced consumer images (CC-BY-4.0), stored on GCS."""
    found = []
    for candidates in SOURCE_METADATA["scin"]:
        found.append(
            _require_metadata(
                dest,
                candidates,
                source="scin",
                hint=(
                    "Download the SCIN metadata CSVs from "
                    f"https://github.com/google-research-datasets/scin and place them in {dest}/ ."
                ),
            )
        )

    n_images = 0
    note = None
    if download_images:
        if keys is not None:
            # The bucket is public, so prefer plain HTTPS (no SDK needed). Fall
            # back to gsutil if it happens to be installed (faster for bulk).
            if shutil.which("gsutil"):
                n_images = -1 if _gsutil_cp_manifest(keys, dest) else 0
            else:
                n_images = _scin_http_fetch(keys, dest, workers=workers, timeout=timeout)
        elif shutil.which("gsutil"):
            n_images = -1 if _gsutil_rsync(
                f"{SCIN_GCS_BUCKET}/dataset/images", dest / "dataset" / "images"
            ) else 0
        else:
            note = (
                "For the full image set install the Google Cloud SDK "
                "(https://cloud.google.com/sdk/docs/install), or use --manifest-only "
                "to fetch the manifest's images over HTTPS without any SDK."
            )

    _write_receipt(
        dest,
        source="scin",
        metadata=[p.name for p in found],
        images_downloaded=n_images,
        images_requested=download_images,
        license="CC-BY-4.0 (see PROVENANCE.md).",
        note=note,
    )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _manifest_keys(manifest_path: Path, source: str) -> set[str]:
    """Return the set of image keys for ``source`` present in the manifest.

    Fitzpatrick17k -> md5 hashes; SCIN -> relative image paths under raw/scin/.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"manifest not found at {manifest_path}; run `make data` first, or drop "
            "--manifest-only to walk the full CSVs."
        )
    keys: set[str] = set()
    with manifest_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("source") != source:
                continue
            p = row["path"]  # e.g. raw/fitzpatrick17k/images/<md5>.jpg or raw/scin/dataset/images/<id>.png
            if source == "fitzpatrick17k":
                keys.add(Path(p).stem)
            elif source == "scin":
                # strip the leading "raw/scin/" to get "dataset/images/<id>.png"
                parts = Path(p).parts
                keys.add(str(Path(*parts[2:])) if len(parts) > 2 else p)
    return keys


def _parallel_fetch(jobs, *, workers: int, timeout: int, label: str) -> int:
    """Fetch (url, out) jobs concurrently. Returns count of successful downloads."""
    total = len(jobs)
    if total == 0:
        print(f"[{label}] no new images to fetch (all present or none in manifest).")
        return 0
    print(f"[{label}] fetching {total} images with {workers} workers (timeout {timeout}s)...")
    ok = 0
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(_fetch_url, url, out, timeout): out for url, out in jobs}
        for fut in as_completed(futs):
            done += 1
            if fut.result():
                ok += 1
            if done % 100 == 0 or done == total:
                print(f"  [{label}] {done}/{total} tried, {ok} ok, {done - ok} failed", flush=True)
    print(f"[{label}] done: {ok}/{total} downloaded ({total - ok} unreachable).")
    return ok


def import_fitzpatrick_images(
    dest: Path,
    *,
    csv_path: Path,
    keys: set[str] | None = None,
    source_dir: Path | None = None,
    kaggle: str | None = None,
) -> int:
    """Import Fitzpatrick17k images from a local mirror folder or a Kaggle dataset.

    Matching is naming-agnostic: images are keyed to the manifest by content MD5
    (``md5hash`` in the CSV is the MD5 of the image bytes). Files whose *stem* is
    already an md5 in the CSV are matched cheaply; the rest are matched by hashing
    their bytes. Only images whose md5 is in ``keys`` (the manifest subset) are
    kept when ``keys`` is given. Copies are write-once into ``dest/images/``.

    Returns the number of images imported.
    """
    img_dir = dest / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    md5_set, stem_to_md5 = _index_fitz_csv(csv_path)
    if keys is not None:
        md5_set = md5_set & set(keys)

    cleanup = None
    if kaggle:
        source_dir = _kaggle_download(kaggle)
        cleanup = source_dir
    if source_dir is None:
        raise ValueError("provide source_dir or kaggle to import Fitzpatrick images")
    source_dir = Path(source_dir)
    if not source_dir.exists():
        raise FileNotFoundError(f"image source dir not found: {source_dir}")

    imported = 0
    scanned = 0
    for path in source_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in _IMG_EXTS:
            continue
        scanned += 1
        stem = path.stem.lower()
        md5 = None
        if len(stem) == 32 and all(c in "0123456789abcdef" for c in stem):
            md5 = stem
        elif path.name in stem_to_md5:
            md5 = stem_to_md5[path.name]
        else:
            md5 = _md5_file(path)
        # Uniform gate: only keep images whose md5 is in the (keys-filtered) set.
        if md5 is None or md5 not in md5_set:
            continue
        out = img_dir / f"{md5}.jpg"
        if not out.exists():
            shutil.copy2(path, out)
            imported += 1
        if scanned % 500 == 0:
            print(f"  [fitzpatrick17k/import] scanned {scanned}, imported {imported}", flush=True)

    if cleanup is not None:
        shutil.rmtree(cleanup, ignore_errors=True)
    print(f"[fitzpatrick17k] imported {imported} images (of {len(md5_set)} needed) from mirror.")
    return imported


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


def _kaggle_download(dataset: str) -> Path:
    """Download+unzip a Kaggle dataset to a temp dir via the ``kaggle`` CLI."""
    if shutil.which("kaggle") is None:
        raise FileNotFoundError(
            "the `kaggle` CLI is not installed. Run `pip install kaggle`, create an "
            "API token at https://www.kaggle.com/settings (kaggle.json), then retry."
        )
    tmp = Path(tempfile.mkdtemp(prefix="fitz_kaggle_"))
    print(f"[fitzpatrick17k] downloading Kaggle dataset {dataset} -> {tmp} ...")
    subprocess.run(
        ["kaggle", "datasets", "download", "-d", dataset, "-p", str(tmp), "--unzip"],
        check=True,
    )
    return tmp


def _find_metadata(dest: Path, candidates: list[str]) -> Path | None:
    for name in candidates:
        for base in (dest, dest.parent):
            p = base / name
            if p.exists():
                return p
    return None


def _require_metadata(dest: Path, candidates: list[str], *, source: str, hint: str) -> Path:
    found = _find_metadata(dest, candidates)
    if found is None:
        raise FileNotFoundError(
            f"[{source}] missing metadata CSV (looked for {candidates}). {hint}"
        )
    target = dest / found.name
    if found != target and not target.exists():
        shutil.copy2(found, target)
        return target
    return found if found == target else target


def _fetch_url(url: str, out: Path, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """Fetch ``url`` to ``out`` write-once. Returns True on success."""
    if out.exists():
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        if not data:
            return False
        tmp = out.with_suffix(out.suffix + ".part")
        tmp.write_bytes(data)
        tmp.replace(out)
        return True
    except (urllib.error.URLError, OSError, TimeoutError, ValueError):
        return False


def _gsutil_rsync(src: str, out_dir: Path) -> bool:
    """Mirror a GCS prefix into ``out_dir`` using gsutil. Returns True on success."""
    if shutil.which("gsutil") is None:
        return False
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["gsutil", "-m", "rsync", "-r", src, str(out_dir)], check=True)
        return True
    except (subprocess.CalledProcessError, OSError):
        return False


def _scin_http_fetch(rel_paths: set[str], dest: Path, *, workers: int, timeout: int) -> int:
    """Fetch the manifest's SCIN images from the public bucket over HTTPS.

    ``rel_paths`` are like "dataset/images/<id>.png"; each is downloaded from
    ``SCIN_HTTP_BASE/<rel>`` to ``dest/<rel>``. No Google Cloud SDK required.
    """
    jobs = []
    for rel in sorted(rel_paths):
        out = dest / rel
        if out.exists():
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        jobs.append((f"{SCIN_HTTP_BASE}/{rel}", out))
    return _parallel_fetch(jobs, workers=workers, timeout=timeout, label="scin")


def _gsutil_cp_manifest(rel_paths: set[str], dest: Path) -> bool:
    """Copy only the manifest's SCIN images via `gsutil -m cp -I`.

    ``rel_paths`` are like "dataset/images/<id>.png"; they are copied to
    ``dest/dataset/images/`` preserving filenames. Skips files already present.
    """
    out_dir = dest / "dataset" / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    uris = []
    for rel in sorted(rel_paths):
        if (dest / rel).exists():
            continue
        uris.append(f"{SCIN_GCS_BUCKET}/{rel}")
    if not uris:
        print("[scin] no new images to fetch (all present or none in manifest).")
        return True
    print(f"[scin] copying {len(uris)} images from GCS via gsutil...")
    try:
        proc = subprocess.run(
            ["gsutil", "-m", "cp", "-I", str(out_dir)],
            input="\n".join(uris),
            text=True,
            check=True,
        )
        return proc.returncode == 0
    except (subprocess.CalledProcessError, OSError):
        return False


def _write_receipt(dest, *, source, metadata, images_downloaded, images_requested, license, note=None):
    receipt = {
        "source": source,
        "acquired_at": datetime.now(timezone.utc).isoformat(),
        "metadata_files": metadata,
        "images_requested": images_requested,
        "images_downloaded": images_downloaded,
        "license": license,
    }
    if note:
        receipt["note"] = note
    (dest / ".download_receipt.json").write_text(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Acquire DermaFace source datasets.")
    parser.add_argument("source", nargs="?", choices=SOURCES, help="single source (default: all)")
    parser.add_argument("--images", action="store_true", help="also fetch image files")
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="fetch only images referenced in manifest.csv (much faster)",
    )
    parser.add_argument("--all-images", action="store_true", help="walk full CSVs (opposite of --manifest-only)")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="parallel download threads")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="per-request timeout (s)")
    parser.add_argument(
        "--from-kaggle",
        nargs="?",
        const=FITZPATRICK_KAGGLE_DEFAULT,
        default=None,
        metavar="SLUG",
        help="(fitzpatrick17k) import images from a Kaggle mirror instead of URLs "
        f"(default slug: {FITZPATRICK_KAGGLE_DEFAULT}); needs the kaggle CLI + token",
    )
    parser.add_argument(
        "--from-dir",
        type=str,
        default=None,
        metavar="PATH",
        help="(fitzpatrick17k) import images from a local mirror folder (matched by content MD5)",
    )
    args = parser.parse_args()

    # Default to manifest-only when fetching images, unless --all-images is given.
    manifest_only = args.images and not args.all_images
    if args.manifest_only:
        manifest_only = True

    raw = load_config().data_dir / "raw"
    kwargs = dict(
        download_images=args.images,
        manifest_only=manifest_only,
        workers=args.workers,
        timeout=args.timeout,
    )
    fitz_kwargs = dict(
        fitz_source_dir=Path(args.from_dir) if args.from_dir else None,
        fitz_kaggle=args.from_kaggle,
    )
    try:
        if args.source == "fitzpatrick17k":
            download_source(args.source, raw, **kwargs, **fitz_kwargs)
        elif args.source:
            download_source(args.source, raw, **kwargs)
        else:
            download_all(raw, **kwargs)
            if args.from_kaggle or args.from_dir:
                download_source("fitzpatrick17k", raw, **kwargs, **fitz_kwargs)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
