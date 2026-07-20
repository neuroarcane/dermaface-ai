"""Data QA — flag problems in the manifest and its images.

Owner: Rolando (Data QA), paired with Aparna (Data Lead).

Produces ``data/processed/qa/data_quality_report.csv``: one row per manifest
entry with QA flags, plus a printed summary. Checks:

  * **missing_image**   — the image file is not on disk yet
  * **corrupt**         — the file exists but PIL cannot decode it
  * **oversized**       — file bytes over ``MAX_BYTES`` or dimension over ``MAX_DIM``
  * **undersized**      — smaller than ``MIN_DIM`` (too low-res to be useful)
  * **duplicate**       — same perceptual hash as another image (near-duplicate)
  * **missing_label**   — label absent / not one of the four classes
  * **missing_skin_type** — skin_type absent or "unknown" (breaks fairness split)

The report runs on whatever is present: with a metadata-only manifest it still
flags missing images and missing/unknown fields, so it's useful before the
images are downloaded. Image checks (corrupt/size/duplicate) activate once the
images are on disk.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from dermaface.config import CLASS_NAMES, load_config

REPORT_COLUMNS = [
    "path", "source", "label", "skin_type", "split",
    "image_exists", "corrupt", "width", "height", "filesize_kb",
    "oversized", "undersized", "is_duplicate", "phash",
    "missing_label", "missing_skin_type", "issues",
]

MAX_BYTES = 8 * 1024 * 1024   # 8 MB
MAX_DIM = 4000                # px on the long side
MIN_DIM = 64                  # px on the short side


def run_qa(
    manifest_path: Path | None = None,
    raw_dir: Path | None = None,
    out_path: Path | None = None,
) -> tuple[Path, dict]:
    """Scan the manifest, write the QA report CSV, and return (path, summary)."""
    cfg = load_config()
    manifest_path = Path(manifest_path) if manifest_path else cfg.manifest_path
    out_path = Path(out_path) if out_path else cfg.qa_report_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found at {manifest_path}; run `make data` first")

    with manifest_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    # Try to load PIL / imagehash; degrade gracefully if unavailable.
    try:
        from PIL import Image
    except ImportError:
        Image = None
    try:
        import imagehash
    except ImportError:
        imagehash = None

    seen_hashes: dict[str, str] = {}
    out_rows: list[dict] = []
    summary: Counter = Counter()

    for r in rows:
        rel = r["path"]
        abs_path = (cfg.data_dir / rel)
        rec = {c: "" for c in REPORT_COLUMNS}
        rec.update(
            {
                "path": rel,
                "source": r.get("source", ""),
                "label": r.get("label", ""),
                "skin_type": r.get("skin_type", ""),
                "split": r.get("split", ""),
            }
        )
        issues = []

        # Field checks (work without images).
        if r.get("label") not in CLASS_NAMES:
            rec["missing_label"] = "1"
            issues.append("missing_label")
            summary["missing_label"] += 1
        if not r.get("skin_type") or r.get("skin_type") == "unknown":
            rec["missing_skin_type"] = "1"
            issues.append("missing_skin_type")
            summary["missing_skin_type"] += 1

        exists = abs_path.exists()
        rec["image_exists"] = "1" if exists else "0"
        if not exists:
            issues.append("missing_image")
            summary["missing_image"] += 1
        elif Image is not None:
            try:
                size = abs_path.stat().st_size
                rec["filesize_kb"] = f"{size / 1024:.1f}"
                with Image.open(abs_path) as im:
                    im.verify()  # detect truncation/corruption
                with Image.open(abs_path) as im:
                    w, h = im.size
                    rec["width"], rec["height"] = str(w), str(h)
                    if imagehash is not None:
                        ph = str(imagehash.phash(im.convert("RGB")))
                        rec["phash"] = ph
                        if ph in seen_hashes:
                            rec["is_duplicate"] = "1"
                            issues.append("duplicate")
                            summary["duplicate"] += 1
                        else:
                            seen_hashes[ph] = rel
                if size > MAX_BYTES or max(w, h) > MAX_DIM:
                    rec["oversized"] = "1"
                    issues.append("oversized")
                    summary["oversized"] += 1
                if min(w, h) < MIN_DIM:
                    rec["undersized"] = "1"
                    issues.append("undersized")
                    summary["undersized"] += 1
            except Exception as exc:  # corrupt / unreadable
                rec["corrupt"] = "1"
                issues.append(f"corrupt:{type(exc).__name__}")
                summary["corrupt"] += 1

        rec["issues"] = ";".join(issues)
        if issues:
            summary["rows_with_issues"] += 1
        out_rows.append(rec)

    summary["total_rows"] = len(rows)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(out_rows)
    return out_path, dict(summary)


def render_summary(summary: dict) -> str:
    total = summary.get("total_rows", 0)
    lines = [f"QA report — {total} rows, {summary.get('rows_with_issues', 0)} with issues"]
    for k in ("missing_image", "corrupt", "oversized", "undersized",
              "duplicate", "missing_label", "missing_skin_type"):
        if summary.get(k):
            lines.append(f"  {k}: {summary[k]}")
    return "\n".join(lines)


if __name__ == "__main__":
    path, summary = run_qa()
    print(f"Wrote {path}")
    print(render_summary(summary))
