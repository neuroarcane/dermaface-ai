# Raw Data Sources Reference

This file documents the candidate raw datasets and image sources for DermaFace AI.
It is intended for documentation, reporting, and provenance tracking before any
data is downloaded into `data/raw/`.

No raw images or restricted dataset files should be committed to Git. Store local
downloads under `data/raw/<source>/` and record access details in
`data/external/PROVENANCE.md`.

## Source Summary

| Source | Type | Primary project use | Raw data contents | Access / download location | License and use notes | Project handling |
|---|---|---|---|---|---|---|
| Google SCIN | Open-access dermatology image dataset | Consumer-style skin photos, condition labels, metadata, skin-tone fields, realistic app-like images | 10,000+ dermatology images from 5,000+ consented US internet-user contributions; includes self-reported demographics/symptoms, dermatologist condition labels, estimated Fitzpatrick Skin Type, and Monk Skin Tone | GitHub: <https://github.com/google-research-datasets/scin>; data bucket: `dx-scin-public-data`; use the repository demo notebook and schema docs | Released under the SCIN Data Use License. Medical images may be sensitive. Verify license terms before training or redistribution | Candidate primary source. Ingest into `data/raw/scin/`; map labels to `acne`, `rosacea`, `redness`, `clear`; preserve source labels and skin-tone metadata |
| Fitzpatrick17k | Clinical dermatology image dataset with skin-type annotations | Main disease-label source and fairness analysis by Fitzpatrick type | 16,577 clinical images across 114 skin conditions; annotations include Fitzpatrick skin type and image source URLs | GitHub CSV: <https://github.com/mattgroh/fitzpatrick17k>; images are referenced by source URL in `fitzpatrick17k.csv`; alternative full-image link may require contacting maintainers through their form | Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported. Some source links are broken. Use is non-commercial; do not redistribute images through the repo | Candidate primary source. Ingest into `data/raw/fitzpatrick17k/`; use only mapped target classes; keep original labels and URL/provenance fields |
| SKINCON | Dermatology concept-annotation dataset | Severity proxy, explainability/error analysis, redness/erythema and lesion-concept support | Dermatologist concept annotations for 3,230 Fitzpatrick17k images and 656 DDI images; 48 clinical concepts such as plaque, scale, erosion, erythema-related features, papules, and pustules | Website: <https://skincon-dataset.github.io/>; annotation downloads are linked from the site; underlying images must be obtained through Fitzpatrick17k and DDI | Annotation layer depends on source dataset rights. Must track whether each row came from Fitzpatrick17k or DDI | Use as annotation overlay, not standalone image source. Store annotations under `data/raw/skincon/`; join to source images through stable IDs |
| ACNE04 / acne grading data | Acne-specific image dataset used by acne severity research | Acne class support and possible severity labels | Facial acne classification/detection files and metadata used by acne grading papers; includes classification and detection archives in referenced workflows | Reference implementation: <https://github.com/openface-io/acne-lds>; linked ACNE04 dataset repository and Google Drive/Baidu-style downloads from related work | Verify dataset license and permitted academic use before download. The reference code is MIT, but dataset rights must be checked separately | Optional source for acne/severity only. Ingest into `data/raw/acne04/`; do not let acne-only data distort the four-class balance |
| DDI | Diverse Dermatology Images dataset | Supplemental fairness/evaluation benchmark, especially skin-tone robustness | 656 biopsy-proven dermatology images from 570 unique patients; labels and skin tone curated by dermatologists | Website: <https://ddi-dataset.github.io/>; access through Stanford AIMI shared datasets portal after agreement | Personal, non-commercial research use only. Do not distribute, publish, reproduce, or share the download link. Research use only; not for diagnosis or patient care | Use sparingly for evaluation/fairness, not as dominant training data. Ingest into `data/raw/ddi/` only after individual access approval |
| DermNet image library | Clinical image library/reference site | Reference for documentation and clinical framing; possible source only if licensing is explicitly approved | Dermatology image galleries with filters for skin of colour, body location, lesion type, colour, condition, and related clinical topics | Image library: <https://dermnetnz.org/images> | Treat as reference unless explicit license/permission supports ML training. Do not scrape casually | Do not include in v1 training by default. Use for background research and report language only unless Hessam approves licensed use |

## Source-Specific Notes

### Google SCIN

- Best fit for realistic user-uploaded image style.
- Useful metadata fields include dermatologist condition labels, estimated
  Fitzpatrick Skin Type, Monk Skin Tone, self-reported symptoms, and image
  quality information.
- Known source issues include duplicates and some missing/ambiguous labels.
- Required QA:
  - check duplicate IDs and perceptual duplicates
  - verify labels map cleanly to project classes
  - flag non-face or non-target body-location examples
  - preserve skin-tone metadata for fairness analysis

### Fitzpatrick17k

- Best fit for broad dermatology labels and skin-type-aware evaluation.
- Images come from source URLs listed in the CSV, so availability may vary.
- License is non-commercial ShareAlike; this must be explicit in the report.
- Required QA:
  - record broken links
  - store original disease label
  - map only defensible labels into the four project classes
  - exclude ambiguous diseases from v1 training unless approved as `clear/other`

### SKINCON

- Best fit for concept-derived severity and explainability support.
- SKINCON is not a raw image source by itself for this project; it is an
  annotation layer over Fitzpatrick17k and DDI images.
- Required QA:
  - confirm each annotation row can be joined to an available image
  - document whether concepts support severity strongly or only qualitatively
  - keep severity assumptions in `data/external/severity_map.csv`

### ACNE04

- Best fit for acne grading/severity if access and rights are confirmed.
- It does not help rosacea, redness, or clear classes directly.
- Required QA:
  - verify dataset license separately from code license
  - map acne grades/counts into `mild`, `moderate`, `severe` only if defensible
  - monitor class imbalance so acne does not dominate model training

### DDI

- Best fit for fairness analysis because it was designed around diverse skin
  tone representation and biopsy-proven labels.
- Access terms are restrictive and individual-user based.
- Required QA:
  - do not share download links or copied images
  - use only after access agreement is completed
  - keep DDI-derived rows clearly marked in `source=ddi`
  - do not use DDI output for clinical claims

### DermNet

- Best treated as a reference library unless explicit training permission is
  obtained.
- It can support product wording, report context, and visual understanding of
  conditions, but should not be treated as a default dataset.

## Canonical Raw Folder Names

Use these folder names so notebooks and scripts can rely on stable paths:

| Source | Raw folder |
|---|---|
| Google SCIN | `data/raw/scin/` |
| Fitzpatrick17k | `data/raw/fitzpatrick17k/` |
| SKINCON | `data/raw/skincon/` |
| ACNE04 | `data/raw/acne04/` |
| DDI | `data/raw/ddi/` |
| DermNet, only if licensed | `data/raw/dermnet/` |

## Required Provenance Fields

Every source used in the project must have a provenance entry with:

| Field | Description |
|---|---|
| `source_name` | Human-readable source name |
| `source_key` | Stable key used in `manifest.csv`, such as `scin` |
| `source_url` | Official dataset or access URL |
| `access_date` | Date the team accessed or downloaded the data |
| `download_method` | Manual portal, public bucket, CSV URLs, form request, or other method |
| `license_or_terms` | License name or short summary of terms |
| `redistribution_allowed` | Whether images or metadata can be redistributed |
| `approved_for_training` | Yes/no/pending decision for this class project |
| `approved_by` | Team member who confirmed use |
| `notes` | Known constraints, broken links, missing labels, or special handling |

## Recommended Priority

1. Start with SCIN and Fitzpatrick17k because they provide the broadest fit for
   condition classification and fairness metadata.
2. Add SKINCON as an annotation overlay for severity and explainability.
3. Add ACNE04 only if acne severity remains in scope and license/access is clear.
4. Use DDI mainly for fairness/evaluation because of restrictive access terms.
5. Treat DermNet as reference-only unless the team secures explicit permission.

## Reporting Notes

- State clearly that dataset labels and model outputs are for educational
  screening only, not diagnosis.
- Separate "training data", "evaluation data", "demo holdout", and "reference
  material" in the report.
- Document label-mapping decisions, excluded labels, and severity assumptions.
- Document known bias risks by source, skin-tone coverage, image quality, and
  class imbalance.
