"""Generate a tiny synthetic slice that mimics the three source schemas.

Owner: Rolando (Data Pipeline & QA).

Why this exists: the real images live behind external URLs (Fitzpatrick17k),
credentialized access (DDI), and a multi-GB GCS bucket (SCIN), so they cannot
be pulled in CI or on a fresh clone. This script writes small CSVs whose columns
match the *real* schemas plus a handful of solid-color JPEGs/PNGs, so the whole
pipeline — download_source validation -> build_manifest -> make_splits ->
build_dataloaders — can be exercised end-to-end offline. It is NOT training data.

Usage:
    python scripts/make_smoke_slice.py --raw-dir data_smoke/raw --per-class 8
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import random
from pathlib import Path

from PIL import Image

CLASSES = ["acne", "rosacea", "redness", "clear"]
# Raw condition strings the harmonizer's keyword map should recognize.
FITZ_CONDITIONS = {
    "acne": "acne vulgaris",
    "rosacea": "rosacea",
    "redness": "erythema",
    "clear": "healthy skin",
}
SCIN_CONDITIONS = {
    "acne": "{'Acne': 0.8, 'Folliculitis': 0.2}",
    "rosacea": "{'Rosacea': 0.9}",
    "redness": "{'Erythema': 0.7, 'Eczema': 0.3}",
    "clear": "{'Healthy': 1.0}",
}
FITZ_SCALE = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}
SKIN_TONES = list(FITZ_SCALE.keys())
CONCEPTS = ["Erythema", "Papule", "Pustule", "Plaque", "Scale", "Nodule"]


def _img(path: Path, color: tuple[int, int, int], size: int = 64) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (size, size), color).save(path)


def _color(rng: random.Random) -> tuple[int, int, int]:
    return (rng.randint(120, 255), rng.randint(40, 160), rng.randint(40, 160))


def make_slice(raw_dir: Path, per_class: int = 8, seed: int = 42) -> None:
    rng = random.Random(seed)
    fitz_dir = raw_dir / "fitzpatrick17k"
    skincon_dir = raw_dir / "skincon"
    scin_dir = raw_dir / "scin"
    for d in (fitz_dir, skincon_dir, scin_dir):
        d.mkdir(parents=True, exist_ok=True)

    # --- Fitzpatrick17k -----------------------------------------------------
    fitz_rows, skincon_fitz_rows = [], []
    for cls in CLASSES:
        for i in range(per_class):
            skin = rng.choice(SKIN_TONES)
            md5 = hashlib.md5(f"fitz-{cls}-{i}".encode()).hexdigest()
            _img(fitz_dir / "images" / f"{md5}.jpg", _color(rng))
            fitz_rows.append(
                {
                    "md5hash": md5,
                    "fitzpatrick_scale": FITZ_SCALE[skin],
                    "fitzpatrick_centaur": FITZ_SCALE[skin],
                    "label": FITZ_CONDITIONS[cls],
                    "nine_partition_label": "inflammatory",
                    "three_partition_label": "non-neoplastic",
                    "qc": "",
                    "url": f"https://example.invalid/{md5}.jpg",
                    "url_alphanum": f"{md5}.jpg",
                }
            )
            # half of them also get SKINCON concept annotations (severity proxy)
            if i % 2 == 0:
                flags = {c: int(rng.random() < 0.5) for c in CONCEPTS}
                skincon_fitz_rows.append({"md5hash": md5, **flags})

    _write_csv(fitz_dir / "fitzpatrick17k.csv", fitz_rows)
    _write_csv(skincon_dir / "SKINCON Fitzpatrick17k annotations.csv", skincon_fitz_rows)

    # --- SKINCON DDI (mostly non-facial; a few map to redness) --------------
    ddi_rows = []
    for i in range(per_class):
        cls = "redness" if i % 3 == 0 else "clear"
        img_id = f"{i:06d}.png"
        _img(skincon_dir / "ddi_images" / img_id, _color(rng))
        flags = {c: int(rng.random() < 0.4) for c in CONCEPTS}
        ddi_rows.append(
            {
                "DDI_file": img_id,
                "disease": FITZ_CONDITIONS[cls],
                "skin_tone": rng.choice([12, 34, 56]),
                **flags,
            }
        )
    _write_csv(skincon_dir / "SKINCON DDI annotations.csv", ddi_rows)

    # --- SCIN ---------------------------------------------------------------
    scin_cases, scin_labels = [], []
    for cls in CLASSES:
        for i in range(per_class):
            skin = rng.choice(SKIN_TONES)
            cid = f"scin-{cls}-{i}"
            img_rel = f"images/{cid}.png"
            _img(scin_dir / img_rel, _color(rng))
            scin_cases.append(
                {
                    "case_id": cid,
                    "source": "SCIN",
                    "fitzpatrick_skin_type": f"FST{FITZ_SCALE[skin]}",
                    "related_category": "ACNE" if cls == "acne" else "RASH",
                    "image_1_path": img_rel,
                    "image_1_shot_type": "CLOSE_UP",
                }
            )
            scin_labels.append(
                {
                    "case_id": cid,
                    "weighted_skin_condition_label": SCIN_CONDITIONS[cls],
                    "dermatologist_fitzpatrick_skin_type_label_1": f"FST{FITZ_SCALE[skin]}",
                    "monk_skin_tone_label_us": rng.randint(1, 10),
                }
            )
    _write_csv(scin_dir / "dataset_scin_cases.csv", scin_cases)
    _write_csv(scin_dir / "dataset_scin_labels.csv", scin_labels)


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-dir", type=Path, default=Path("data_smoke/raw"))
    ap.add_argument("--per-class", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    make_slice(args.raw_dir, args.per_class, args.seed)
    print(f"Wrote synthetic slice to {args.raw_dir}")
