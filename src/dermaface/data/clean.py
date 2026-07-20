"""Produce the cleaned, training-ready manifest (Sprint 2).

Owner: Rolando (Data QA), paired with Aparna (Data Lead).

Takes ``data/processed/manifest.csv`` plus the QA findings and writes
``data/processed/manifest_clean.csv`` with problem rows removed, then validates
that every surviving row has a usable class and Fitzpatrick skin type.

Rows are dropped when the QA report flags any of ``DEFAULT_DROP_REASONS``:

  * ``duplicate``          — near-identical image (perceptual hash). QA flags the
    *extra* copies only, so the first image of each group is kept.
  * ``missing_skin_type``  — unknown Fitzpatrick type (can't be placed in a
    fairness group; team decision is to drop these).
  * ``missing_image``      — the image file isn't on disk.
  * ``missing_label``      — label absent / not one of the four classes.
  * ``corrupt``            — file exists but can't be decoded.
  * ``oversized`` / ``undersized`` — outside usable dimension/size bounds.

The original ``manifest.csv`` is never modified — it stays as the audit trail.

After cleaning, re-run ``make_splits`` on the cleaned manifest to freeze a clean
test set.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from dermaface.config import CLASS_NAMES, FITZPATRICK_TYPES, load_config
from dermaface.data.manifest import MANIFEST_COLUMNS

DEFAULT_DROP_REASONS: tuple[str, ...] = (
    "duplicate",
    "missing_skin_type",
    "missing_image",
    "missing_label",
    "corrupt",
    "oversized",
    "undersized",
)


def clean_manifest(
    manifest_path: Path | None = None,
    out_path: Path | None = None,
    *,
    drop_reasons: tuple[str, ...] = DEFAULT_DROP_REASONS,
    qa_report_path: Path | None = None,
    rerun_qa: bool = True,
) -> tuple[Path, dict]:
    """Write the cleaned manifest and return (path, summary).

    Args:
        manifest_path: source manifest (default: config.manifest_path).
        out_path: destination (default: ``manifest_clean.csv`` beside the source).
        drop_reasons: QA issue prefixes that cause a row to be dropped.
        qa_report_path: existing QA report to reuse (default: config.qa_report_path).
        rerun_qa: regenerate the QA report first (needs images on disk).
    """
    cfg = load_config()
    manifest_path = Path(manifest_path) if manifest_path else cfg.manifest_path
    out_path = Path(out_path) if out_path else manifest_path.with_name("manifest_clean.csv")
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found at {manifest_path}; run `make data` first")

    # 1. Get QA findings (per-row issue flags).
    from dermaface.data import qa as qa_mod

    report_path = Path(qa_report_path) if qa_report_path else cfg.qa_report_path
    if rerun_qa or not report_path.exists():
        report_path, _ = qa_mod.run_qa(manifest_path)

    issues_by_path: dict[str, list[str]] = {}
    with report_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            raw = (row.get("issues") or "").strip()
            issues_by_path[row["path"]] = [i for i in raw.split(";") if i]

    # 2. Filter the manifest.
    with manifest_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    kept: list[dict] = []
    dropped_by_reason: Counter = Counter()
    dropped_rows = 0
    for r in rows:
        issues = issues_by_path.get(r["path"], [])
        hits = [i for i in issues if any(i.startswith(reason) for reason in drop_reasons)]
        if hits:
            dropped_rows += 1
            for h in hits:
                dropped_by_reason[h.split(":")[0]] += 1
            continue
        kept.append(r)

    # 3. Validate the surviving rows.
    bad_label = [r["path"] for r in kept if r["label"] not in CLASS_NAMES]
    bad_skin = [r["path"] for r in kept if r.get("skin_type") not in FITZPATRICK_TYPES]
    if bad_label:
        raise ValueError(f"{len(bad_label)} cleaned rows have an invalid label, e.g. {bad_label[:3]}")
    if bad_skin and "missing_skin_type" in drop_reasons:
        raise ValueError(
            f"{len(bad_skin)} cleaned rows have a non-Fitzpatrick skin_type, e.g. {bad_skin[:3]}"
        )

    # 4. Write the cleaned manifest.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(kept)

    summary = {
        "rows_in": len(rows),
        "rows_dropped": dropped_rows,
        "rows_out": len(kept),
        "dropped_by_reason": dict(dropped_by_reason),
        "by_label": dict(Counter(r["label"] for r in kept)),
        "by_skin_type": dict(Counter(r.get("skin_type", "") for r in kept)),
        "by_source": dict(Counter(r.get("source", "") for r in kept)),
    }
    return out_path, summary


def render_summary(summary: dict) -> str:
    lines = [
        f"Cleaned manifest: {summary['rows_in']} in -> {summary['rows_out']} out "
        f"({summary['rows_dropped']} dropped)",
        f"  dropped by reason: {summary['dropped_by_reason']}",
        f"  by label:          {summary['by_label']}",
        f"  by skin_type:      {summary['by_skin_type']}",
        f"  by source:         {summary['by_source']}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    from dermaface.data.splits import freeze_clean_splits

    path, summary = clean_manifest()
    print(f"Wrote {path}")
    print(render_summary(summary))

    # Re-freeze the per-split manifests from the cleaned rows. This keeps each
    # row's existing split assignment (no re-shuffling), so the frozen test set
    # stays the same images minus whatever cleaning dropped.
    counts = freeze_clean_splits(path)
    print(f"\nRe-froze split manifests from the cleaned rows: {counts}")
