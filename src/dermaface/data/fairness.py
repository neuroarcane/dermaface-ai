"""Fairness coverage — how reliably can we measure per-skin-tone performance?

Owner: Rolando (Data QA), for Iva (ML Research) ahead of the fairness analysis.

**Read this before interpreting any per-skin-tone metric.** Public dermatology
datasets skew heavily toward lighter skin, so some Fitzpatrick groups in our
splits are far too small to estimate a per-group F1 from. A macro-F1 computed on
3 images is noise, not a finding.

This module reports, for a given split:

  * counts per Fitzpatrick type (I–VI) and per **band** (I-II / III-IV / V-VI)
  * the class x band crosstab
  * which groups fall below ``config.MIN_GROUP_N`` (too noisy to report bare)
  * which (class, group) cells are empty (that combination is unmeasurable)

Recommended reporting: use **bands** as the primary fairness view, and show the
per-type table alongside with sample sizes attached, so a tiny-n group is never
mistaken for a real result.

    python -m dermaface.data.fairness --split test
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from dermaface.config import (
    CLASS_NAMES,
    FITZPATRICK_TYPES,
    MIN_GROUP_N,
    SKIN_TONE_BAND_NAMES,
    load_config,
    skin_tone_band,
)


def _rows(split: str, manifest_path: Path | None = None) -> list[dict]:
    cfg = load_config()
    if manifest_path is None:
        frozen = cfg.manifest_path.with_name(f"{split}_manifest.csv")
        manifest_path = (
            frozen
            if frozen.exists()
            else (cfg.clean_manifest_path if cfg.clean_manifest_path.exists() else cfg.manifest_path)
        )
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found at {manifest_path}")
    with manifest_path.open(newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("split", split) == split]
    return rows


def coverage(split: str = "test", manifest_path: Path | None = None) -> dict:
    """Return per-type / per-band coverage plus the groups that are too small."""
    rows = _rows(split, manifest_path)
    by_type = Counter(r["skin_type"] for r in rows)
    by_band = Counter(skin_tone_band(r["skin_type"]) for r in rows)
    class_by_band = Counter((r["label"], skin_tone_band(r["skin_type"])) for r in rows)
    class_by_type = Counter((r["label"], r["skin_type"]) for r in rows)

    thin_types = [t for t in FITZPATRICK_TYPES if by_type.get(t, 0) < MIN_GROUP_N]
    thin_bands = [b for b in SKIN_TONE_BAND_NAMES if by_band.get(b, 0) < MIN_GROUP_N]
    empty_cells = [
        (c, b) for c in CLASS_NAMES for b in SKIN_TONE_BAND_NAMES if class_by_band[(c, b)] == 0
    ]
    return {
        "split": split,
        "n": len(rows),
        "by_type": {t: by_type.get(t, 0) for t in FITZPATRICK_TYPES},
        "by_band": {b: by_band.get(b, 0) for b in SKIN_TONE_BAND_NAMES},
        "class_by_band": {f"{c}|{b}": class_by_band[(c, b)] for c in CLASS_NAMES for b in SKIN_TONE_BAND_NAMES},
        "class_by_type": {f"{c}|{t}": class_by_type[(c, t)] for c in CLASS_NAMES for t in FITZPATRICK_TYPES},
        "thin_types": thin_types,
        "thin_bands": thin_bands,
        "empty_class_band_cells": empty_cells,
        "min_group_n": MIN_GROUP_N,
    }


def render(cov: dict) -> str:
    lines = [f"Fairness coverage — split={cov['split']} ({cov['n']} rows)", ""]

    lines.append("By band (primary fairness view):")
    lines.append(f"  {'band':<10}{'n':>6}  status")
    for b in SKIN_TONE_BAND_NAMES:
        n = cov["by_band"][b]
        status = "OK" if n >= cov["min_group_n"] else f"TOO SMALL (< {cov['min_group_n']})"
        lines.append(f"  {b:<10}{n:>6}  {status}")

    lines.append("")
    lines.append("By Fitzpatrick type (report only with sample sizes attached):")
    lines.append(f"  {'type':<10}{'n':>6}  status")
    for t in FITZPATRICK_TYPES:
        n = cov["by_type"][t]
        status = "OK" if n >= cov["min_group_n"] else f"TOO SMALL (< {cov['min_group_n']})"
        lines.append(f"  {t:<10}{n:>6}  {status}")

    lines.append("")
    lines.append("Class x band:")
    lines.append(f"  {'':<10}" + "".join(f"{b:>9}" for b in SKIN_TONE_BAND_NAMES))
    for c in CLASS_NAMES:
        row = f"  {c:<10}"
        for b in SKIN_TONE_BAND_NAMES:
            row += f"{cov['class_by_band'][f'{c}|{b}']:>9}"
        lines.append(row)

    if cov["empty_class_band_cells"]:
        lines.append("")
        lines.append("UNMEASURABLE (class, band) combinations — no samples at all:")
        for c, b in cov["empty_class_band_cells"]:
            lines.append(f"  - {c} on {b}")

    lines.append("")
    lines.append(
        "Interpretation: groups marked TOO SMALL cannot support a trustworthy "
        "per-group metric. Report them with n attached, or fall back to bands."
    )
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Report fairness coverage for a split.")
    ap.add_argument("--split", default="test")
    args = ap.parse_args()
    cov = coverage(args.split)
    print(render(cov))
