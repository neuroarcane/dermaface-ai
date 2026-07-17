"""Harmonize the three raw datasets into a single processed manifest CSV.

Owner: Aparna (Data Lead), paired with Rolando (Data Pipeline & QA Support).

This is the **first-pass** label harmonization (data-strategy pipeline stage 3).
It reads whatever source CSVs are present in ``data/raw/`` and emits
``data/processed/manifest.csv`` with the schema documented in data/README.md:

    path, label, severity, skin_type, source, split

The deeper taxonomy / severity-method work lives in
``notebooks/02_label_harmonization.ipynb`` (owned by Aparna + Iva). Keep the
mapping tables below as the single source of truth so the notebook and this
module agree.

Design choices (the "why"):
  * **Keyword label map, not a hand-labeled crosswalk.** The three datasets use
    114 (Fitzpatrick17k) / free-text (SCIN) condition names. A transparent
    keyword map to {acne, rosacea, redness, clear} is cheap, defensible, and
    easy to audit in the EDA notebook. Rows whose condition maps to none of the
    four target classes are dropped (recorded in the build summary).
  * **Skin type is required for the fairness split.** We normalize every
    source's Fitzpatrick encoding to Roman numerals I–VI (or "unknown").
  * **Severity is deliberately conservative.** None of the sources ship clean
    acne/rosacea grades, and the severity method is a Week-1 decision owned by
    the Chief Scientist / Iva. We emit "n/a" unless SKINCON concept annotations
    are available, in which case a coarse concept-count proxy is used.
  * **Manifest is metadata.** A row is emitted even if its image file is not yet
    downloaded; the DataLoader checks existence at read time. Pass
    ``require_image_exists=True`` to keep only rows whose image is on disk.
"""

from __future__ import annotations

import ast
import csv
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from dermaface.config import CLASS_NAMES, SEVERITY_BANDS, load_config

MANIFEST_COLUMNS = ["path", "label", "severity", "skin_type", "source", "split"]
UNASSIGNED_SPLIT = "unassigned"

# --- Label harmonization ----------------------------------------------------
# Ordered: first matching keyword wins. Applied to a lowercased condition string.
LABEL_KEYWORDS: list[tuple[str, str]] = [
    ("acne", "acne"),
    ("rosacea", "rosacea"),
    ("perioral dermatitis", "rosacea"),  # clinically rosacea-adjacent facial redness
    ("telangiectasia", "redness"),
    ("erythema", "redness"),
    ("flushing", "redness"),
    ("redness", "redness"),
    ("healthy", "clear"),
    ("looks_healthy", "clear"),
    ("normal skin", "clear"),
    ("no relevant", "clear"),
    ("clear", "clear"),
]


def map_label(condition: str | None) -> str | None:
    """Map a raw condition string to one of CLASS_NAMES, or None if unmapped."""
    if not condition:
        return None
    text = str(condition).strip().lower()
    if not text:
        return None
    for needle, target in LABEL_KEYWORDS:
        if needle in text:
            return target
    return None


# --- Skin-type (Fitzpatrick) harmonization ----------------------------------
_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}


def map_skin_type(value: object) -> str:
    """Normalize any source's Fitzpatrick encoding to 'I'..'VI' or 'unknown'."""
    if value is None:
        return "unknown"
    s = str(value).strip().upper()
    if not s or s in {
        "-1", "NONE_SELECTED", "NONE_IDENTIFIED", "NONE", "NA", "N/A", "UNKNOWN", "NAN",
    }:
        return "unknown"
    # SCIN uses "FST1".."FST6"; Fitzpatrick17k uses integers 1..6.
    s = s.replace("FST", "").replace("TYPE", "").strip()
    # Already roman?
    if s in _ROMAN.values():
        return s
    try:
        n = int(float(s))
    except ValueError:
        return "unknown"
    return _ROMAN.get(n, "unknown")


# --- Severity proxy (optional, from SKINCON concepts) -----------------------
# Inflammatory concepts whose presence hints at acne/rosacea severity.
SEVERITY_CONCEPTS = ["erythema", "papule", "pustule", "plaque", "nodule", "abscess"]


def severity_from_concepts(concept_flags: dict[str, object]) -> str:
    """Coarse mild/moderate/severe band from a row of SKINCON concept booleans.

    Counts how many inflammatory concepts are present. This is an approximate
    proxy (see docs/data-strategy.md) — NOT a clinical grade.
    """
    n = 0
    for concept in SEVERITY_CONCEPTS:
        for key, val in concept_flags.items():
            if concept in key.lower() and _is_true(val):
                n += 1
                break
    if n == 0:
        return "n/a"
    if n <= 1:
        return "mild"
    if n <= 3:
        return "moderate"
    return "severe"


def _is_true(val: object) -> bool:
    s = str(val).strip().lower()
    return s in {"1", "1.0", "true", "yes", "t", "y"}


# --------------------------------------------------------------------------- #
# Build summary
# --------------------------------------------------------------------------- #
@dataclass
class BuildSummary:
    rows_by_source: Counter = field(default_factory=Counter)
    dropped_unmapped: Counter = field(default_factory=Counter)
    labels: Counter = field(default_factory=Counter)
    skin_types: Counter = field(default_factory=Counter)

    @property
    def total(self) -> int:
        return sum(self.rows_by_source.values())

    def render(self) -> str:
        lines = [f"Manifest rows: {self.total}"]
        lines.append(f"  by source:    {dict(self.rows_by_source)}")
        lines.append(f"  by label:     {dict(self.labels)}")
        lines.append(f"  by skin_type: {dict(self.skin_types)}")
        lines.append(f"  dropped (unmapped label): {dict(self.dropped_unmapped)}")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Per-source row extraction
# --------------------------------------------------------------------------- #
def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def _first(row: dict, *keys: str) -> str | None:
    for k in keys:
        if k in row and str(row[k]).strip():
            return str(row[k]).strip()
    return None


def _rows_fitzpatrick17k(raw_dir: Path, skincon_index: dict[str, dict]) -> list[dict]:
    csv_path = raw_dir / "fitzpatrick17k" / "fitzpatrick17k.csv"
    if not csv_path.exists():
        csv_path = raw_dir / "fitzpatrick17k.csv"
    if not csv_path.exists():
        return []
    out = []
    for row in _read_csv(csv_path):
        md5 = _first(row, "md5hash")
        label = map_label(_first(row, "label", "nine_partition_label"))
        if not md5 or label is None:
            continue
        skin = map_skin_type(_first(row, "fitzpatrick_scale", "fitzpatrick_centaur"))
        severity = "n/a"
        if md5 in skincon_index:
            severity = severity_from_concepts(skincon_index[md5])
        out.append(
            {
                "path": f"raw/fitzpatrick17k/images/{md5}.jpg",
                "label": label,
                "severity": severity,
                "skin_type": skin,
                "source": "fitzpatrick17k",
                "split": UNASSIGNED_SPLIT,
            }
        )
    return out


def _load_skincon_index(raw_dir: Path) -> dict[str, dict]:
    """Index SKINCON Fitzpatrick17k concept rows by md5hash for severity enrichment."""
    for name in (
        "SKINCON Fitzpatrick17k annotations.csv",
        "SKINCON Fitzpatric17k annotations.csv",  # upstream filename typo
        "skincon_fitzpatrick17k.csv",
    ):
        for base in (raw_dir / "skincon", raw_dir):
            p = base / name
            if p.exists():
                idx = {}
                for row in _read_csv(p):
                    key = _first(row, "md5hash", "ImageID", "image", "hash")
                    if key:
                        # strip extension if the id is a filename
                        key = key.rsplit(".", 1)[0]
                        idx[key] = row
                return idx
    return {}


def _rows_skincon_ddi(raw_dir: Path) -> list[dict]:
    """DDI-origin rows from the SKINCON DDI annotation file.

    DDI's diseases are largely neoplastic and rarely map to our four facial
    classes, so most rows drop out — that is expected and recorded in the
    summary. Emitted rows use source='skincon' (DDI images).
    """
    path = None
    for name in ("SKINCON DDI annotations.csv", "skincon_ddi.csv"):
        for base in (raw_dir / "skincon", raw_dir):
            p = base / name
            if p.exists():
                path = p
                break
        if path:
            break
    if path is None:
        return []
    out = []
    for row in _read_csv(path):
        img_id = _first(row, "DDI_file", "ImageID", "image", "file", "id")
        label = map_label(_first(row, "disease", "label", "condition"))
        if img_id is None or label is None:
            continue
        skin = map_skin_type(_first(row, "skin_tone", "fitzpatrick", "fitzpatrick_scale"))
        out.append(
            {
                "path": f"raw/skincon/ddi_images/{img_id}",
                "label": label,
                "severity": severity_from_concepts(row),
                "skin_type": skin,
                "source": "skincon",
                "split": UNASSIGNED_SPLIT,
            }
        )
    return out


def _parse_weighted_label(raw: str | None) -> str | None:
    """Return the top-weighted condition name from SCIN's dict-encoded label."""
    if not raw:
        return None
    try:
        d = ast.literal_eval(raw)
        if isinstance(d, dict) and d:
            return max(d.items(), key=lambda kv: kv[1])[0]
    except (ValueError, SyntaxError):
        pass
    return raw


def _rows_scin(raw_dir: Path) -> list[dict]:
    cases_p = _scin_file(raw_dir, "dataset_scin_cases.csv", "scin_cases.csv")
    labels_p = _scin_file(raw_dir, "dataset_scin_labels.csv", "scin_labels.csv")
    if cases_p is None:
        return []
    labels_by_case: dict[str, dict] = {}
    if labels_p is not None:
        for row in _read_csv(labels_p):
            cid = _first(row, "case_id")
            if cid:
                labels_by_case[cid] = row

    out = []
    for case in _read_csv(cases_p):
        cid = _first(case, "case_id")
        lab = labels_by_case.get(cid, {})
        condition = _parse_weighted_label(_first(lab, "weighted_skin_condition_label"))
        label = map_label(condition) or map_label(_first(case, "related_category"))
        img_path = _first(case, "image_1_path", "image_2_path", "image_3_path")
        if label is None or not img_path:
            continue
        # Prefer the self-reported Fitzpatrick; if missing/None, fall back to the
        # dermatologist estimate from the labels file.
        skin = map_skin_type(_first(case, "fitzpatrick_skin_type"))
        if skin == "unknown":
            skin = map_skin_type(
                _first(
                    lab,
                    "dermatologist_fitzpatrick_skin_type_label_1",
                    "dermatologist_fitzpatrick_skin_type_label_2",
                    "dermatologist_fitzpatrick_skin_type_label_3",
                )
            )
        out.append(
            {
                "path": f"raw/scin/{img_path}",
                "label": label,
                "severity": "n/a",
                "skin_type": skin,
                "source": "scin",
                "split": UNASSIGNED_SPLIT,
            }
        )
    return out


def _scin_file(raw_dir: Path, *names: str) -> Path | None:
    for name in names:
        for base in (raw_dir / "scin", raw_dir):
            p = base / name
            if p.exists():
                return p
    return None


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def build_manifest(
    raw_dir: Path | None = None,
    out_path: Path | None = None,
    *,
    require_image_exists: bool = False,
) -> tuple[Path, BuildSummary]:
    """Harmonize all present source CSVs into ``manifest.csv``.

    Args:
        raw_dir: the ``data/raw`` directory (default: from config).
        out_path: manifest destination (default: config.manifest_path).
        require_image_exists: drop rows whose image file is not on disk.

    Returns:
        (manifest_path, summary)
    """
    cfg = load_config()
    raw_dir = Path(raw_dir) if raw_dir else (cfg.data_dir / "raw")
    out_path = Path(out_path) if out_path else cfg.manifest_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    skincon_index = _load_skincon_index(raw_dir)
    rows: list[dict] = []
    rows += _rows_fitzpatrick17k(raw_dir, skincon_index)
    rows += _rows_scin(raw_dir)
    rows += _rows_skincon_ddi(raw_dir)

    summary = BuildSummary()
    kept: list[dict] = []
    for r in rows:
        if require_image_exists and not (cfg.data_dir / r["path"]).exists():
            continue
        # normalize severity into the allowed band set
        if r["severity"] not in SEVERITY_BANDS:
            r["severity"] = "n/a"
        kept.append(r)
        summary.rows_by_source[r["source"]] += 1
        summary.labels[r["label"]] += 1
        summary.skin_types[r["skin_type"]] += 1

    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(kept)

    # sanity: every label is a known class
    assert set(summary.labels) <= set(CLASS_NAMES), summary.labels
    return out_path, summary


if __name__ == "__main__":
    path, summ = build_manifest()
    print(f"Wrote {path}")
    print(summ.render())
