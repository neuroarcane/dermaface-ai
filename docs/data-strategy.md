# Data Strategy

## Datasets

| Dataset | Contents | License / access | Role in DermaFace |
|---|---|---|---|
| **Fitzpatrick17k** | ~16,500 clinical images, 114 skin conditions, Fitzpatrick skin-type labels | CC-BY-NC / research use — **verify current terms** | Condition labels + skin-tone for fairness |
| **SKINCON** | ~3,230 images densely annotated with 48 clinical concepts (erythema, papule, pustule, etc.) | Built on Fitzpatrick17k + DDI — **verify terms** | Concept-level signal for severity proxies |
| **Google SCIN** | Consumer dermatology images, self-reported symptoms/context, some dermatologist labels | CC-BY 4.0 (verify) | Real-world, phone-quality photos closer to deployment |

> ⚠️ **Confirm every license before use and before publishing anything derived from it.** Medical-adjacent data is sensitive. Record provenance in `data/external/PROVENANCE.md`.

## The severity-labeling problem (read this first)

None of these datasets ship clean **acne/rosacea severity grades**. Options, roughly in order of effort:

1. **Concept-derived proxy (recommended starting point).** Use SKINCON concept annotations (count/intensity of erythema, papules, pustules) to bucket into coarse severity bands (e.g. mild / moderate / severe). Cheap, defensible, but approximate.
2. **Rule-based on lesion signals.** If lesion counts/areas are derivable, map to clinical-style grading (e.g. acne grading scales). More faithful, more work.
3. **Manual re-labeling of a small subset.** Team grades a few hundred images against a rubric for a held-out eval set only. High quality, low quantity.
4. **Condition-only, severity de-scoped.** Ship acne/rosacea/redness/clear classification; severity becomes a labeled stretch goal. **Safe fallback.**

**Decision owner:** #2 (Chief Scientist), with #3. **Deadline:** end of Week 1.

## Pipeline stages

1. **Acquire** → `data/raw/` (immutable, never edited)
2. **Clean** → dedup (perceptual hash), drop corrupt/low-quality, face-presence check
3. **Harmonize labels** → unified taxonomy across the 3 datasets (map to acne / rosacea / redness / clear + severity band)
4. **Split** → stratified train/val/test by **both class and Fitzpatrick type**; freeze the test set early
5. **Augment** (train only) → flips, mild rotation, color jitter (careful — don't distort erythema signal)
6. **Persist** → `data/processed/` + a manifest CSV (path, label, severity, skin_type, source, split)

## Data hygiene rules

- `data/raw/` is **read-only** once downloaded.
- Everything in `data/` is **gitignored** — never commit images or PII.
- No patient-identifying info in commits, issues, or the deployed app.
- Test set is frozen before modeling and never used for tuning.
