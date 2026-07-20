"""How many of our images actually show a face?

Owner: Rolando (Data QA), for Aparna (Data Lead) + Iva (ML Research).

**Why this exists.** DermaFace is a *face* screening tool, but Fitzpatrick17k is a
general dermatology dataset covering every body site — arms, torso, legs. An
augmentation preview showed 4 of 6 randomly sampled training images were not
faces. Training largely on non-facial skin and then deploying on face photos is a
train/deploy mismatch, so before deciding what to do about it we need a number.

This scans the (cleaned) manifest with ``preprocessing.has_face`` and reports the
face-detection rate overall and broken down by class, source and split. It writes
a per-image result to ``data/processed/face_check.csv`` so rows can be filtered
later without re-scanning.

⚠️ **The number is a LOWER BOUND on facial images.** Haar cascades miss rotated,
partially-cropped and very-close-up faces — and many clinical photos are tight
crops of a cheek or chin, which are facial *skin* without a detectable face. Use
``--sample N`` to eyeball a random subset and calibrate the detector against your
own judgement before anyone acts on the number.

    python -m dermaface.data.facecheck                 # scan the clean manifest
    python -m dermaface.data.facecheck --limit 200     # quick estimate
    python -m dermaface.data.facecheck --sample 40     # copy a sample out to look at
"""

from __future__ import annotations

import csv
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from dermaface.config import load_config
from dermaface.data.preprocessing import has_face


def _resolve_manifest(cfg, manifest_path: Path | None) -> Path:
    if manifest_path is not None:
        return Path(manifest_path)
    return cfg.clean_manifest_path if cfg.clean_manifest_path.exists() else cfg.manifest_path


def scan(
    manifest_path: Path | None = None,
    out_path: Path | None = None,
    limit: int | None = None,
    progress_every: int = 100,
) -> tuple[Path, dict]:
    """Run face detection over the manifest; write per-image results + return summary."""
    cfg = load_config()
    manifest_path = _resolve_manifest(cfg, manifest_path)
    out_path = Path(out_path) if out_path else (cfg.data_dir / "processed" / "face_check.csv")
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found at {manifest_path}")

    with manifest_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if limit:
        rows = rows[:limit]

    results: list[dict] = []
    faces = 0
    missing = 0
    by_class: dict[str, Counter] = defaultdict(Counter)
    by_source: dict[str, Counter] = defaultdict(Counter)
    by_split: dict[str, Counter] = defaultdict(Counter)

    for i, r in enumerate(rows, 1):
        abs_path = cfg.data_dir / r["path"]
        if not abs_path.exists():
            missing += 1
            detected = False
        else:
            detected = has_face(abs_path)
        faces += int(detected)
        key = "face" if detected else "no_face"
        by_class[r["label"]][key] += 1
        by_source[r.get("source", "")][key] += 1
        by_split[r.get("split", "")][key] += 1
        results.append({
            "path": r["path"],
            "label": r["label"],
            "skin_type": r.get("skin_type", ""),
            "source": r.get("source", ""),
            "split": r.get("split", ""),
            "face_detected": int(detected),
        })
        if progress_every and i % progress_every == 0:
            print(f"  scanned {i}/{len(rows)} — {faces} faces so far", flush=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["path", "label", "skin_type", "source", "split", "face_detected"]
        )
        writer.writeheader()
        writer.writerows(results)

    summary = {
        "manifest": str(manifest_path),
        "scanned": len(rows),
        "faces": faces,
        "no_face": len(rows) - faces,
        "missing_images": missing,
        "rate": (faces / len(rows)) if rows else 0.0,
        "by_class": {k: dict(v) for k, v in by_class.items()},
        "by_source": {k: dict(v) for k, v in by_source.items()},
        "by_split": {k: dict(v) for k, v in by_split.items()},
    }
    return out_path, summary


def render(summary: dict) -> str:
    n = summary["scanned"]
    lines = [
        f"Face detection over {Path(summary['manifest']).name} — {n} images scanned",
        f"  face detected : {summary['faces']:>5}  ({100*summary['rate']:.1f}%)",
        f"  no face       : {summary['no_face']:>5}  ({100*(1-summary['rate']):.1f}%)",
    ]
    if summary["missing_images"]:
        lines.append(f"  (images missing from disk: {summary['missing_images']})")

    def block(title: str, data: dict) -> None:
        lines.append("")
        lines.append(f"{title}:")
        lines.append(f"  {'':<16}{'face':>7}{'no face':>9}{'rate':>8}")
        for k in sorted(data):
            f_, nf = data[k].get("face", 0), data[k].get("no_face", 0)
            tot = f_ + nf
            rate = f"{100*f_/tot:.0f}%" if tot else "-"
            lines.append(f"  {k:<16}{f_:>7}{nf:>9}{rate:>8}")

    block("By class", summary["by_class"])
    block("By source", summary["by_source"])
    block("By split", summary["by_split"])

    lines.append("")
    lines.append(
        "NOTE: this is a LOWER BOUND. Haar cascades miss rotated/cropped/close-up "
        "faces, and tight crops of a cheek or chin are facial skin without a "
        "detectable face. Calibrate with --sample before acting on these numbers."
    )
    return "\n".join(lines)


def sample_out(n: int, face: bool, out_dir: Path | None = None, results_path: Path | None = None) -> Path:
    """Copy N images with a given detection result somewhere you can eyeball them."""
    import random

    cfg = load_config()
    results_path = Path(results_path) if results_path else (cfg.data_dir / "processed" / "face_check.csv")
    if not results_path.exists():
        raise FileNotFoundError(f"{results_path} not found — run the scan first")
    out_dir = Path(out_dir) if out_dir else (cfg.data_dir / "processed" / f"face_sample_{'face' if face else 'noface'}")
    out_dir.mkdir(parents=True, exist_ok=True)

    with results_path.open(newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if int(r["face_detected"]) == int(face)]
    random.Random(0).shuffle(rows)
    for r in rows[:n]:
        src = cfg.data_dir / r["path"]
        if src.exists():
            shutil.copy2(src, out_dir / f"{r['label']}_{Path(r['path']).name}")
    return out_dir


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Measure how many manifest images show a face.")
    ap.add_argument("--limit", type=int, default=None, help="scan only the first N rows (quick estimate)")
    ap.add_argument("--sample", type=int, default=0, help="after scanning, copy N of each outcome out to eyeball")
    args = ap.parse_args()

    path, summary = scan(limit=args.limit)
    print(render(summary))
    print(f"\nWrote {path}")

    if args.sample:
        d1 = sample_out(args.sample, face=True)
        d2 = sample_out(args.sample, face=False)
        print(f"\nSampled images to eyeball:\n  faces   -> {d1}\n  no face -> {d2}")
        print("Open both folders and check whether the detector agrees with you.")
