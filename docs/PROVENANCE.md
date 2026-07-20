# Data Provenance

Record of where each source dataset came from, its license, and how it was
obtained. **Read before publishing anything derived from this data.** Medical-
adjacent images are sensitive; licensing here is restrictive.

> **Image data is kept out of git** — images, raw CSVs, `manifest.csv`, splits, and
> QA reports are never committed (shared via the team Google Drive
> `DermaFace-Team-Data`), to respect dataset licensing, especially Fitzpatrick17k's
> non-commercial terms. Two small, non-image records stay versioned in the repo:
> this provenance doc (in `docs/`) and the label crosswalk
> (`data/external/label_map.csv`). Neither contains image data or PII.

Last verified: **2026-07-17** (Aparna, Data Lead / Rolando, Data QA). Re-verify
license terms at each source before any external release.

---

## 1. Fitzpatrick17k

| | |
|---|---|
| **Dataset** | Groh et al., "Evaluating Deep Neural Networks Trained on Clinical Images in Dermatology with the Fitzpatrick 17k Dataset", CVPR ISIC Workshop 2021 — https://github.com/mattgroh/fitzpatrick17k |
| **Contents** | ~16,577 clinical images, 114 skin conditions, Fitzpatrick skin type I–VI |
| **Dataset license** | **Non-commercial / research use only** (derivatives typically CC BY-NC-SA 4.0). These terms govern the **images** regardless of where we obtain the files. |
| **Metadata** | `fitzpatrick17k.csv` (from the official repo) — columns `md5hash, fitzpatrick_scale, fitzpatrick_centaur, label, nine_partition_label, three_partition_label, qc, url, url_alphanum`. The `md5hash` column is the **MD5 of each image's bytes**. |

**Actual image source — Kaggle mirror (what we used):**

| | |
|---|---|
| **Mirror** | `nazmusresan/fitzpatrick17k` on Kaggle — https://www.kaggle.com/datasets/nazmusresan/fitzpatrick17k |
| **Mirror license** | **CC0-1.0** (public domain dedication *by the uploader*). ⚠️ The mirror's CC0 tag does **not** override the underlying dataset's non-commercial terms — we still treat the **images as non-commercial / research-only** and do not redistribute them. |
| **Why a mirror** | The official dataset ships only external clinical-atlas URLs (dermaamin.com, atlasdermatologico.com.br); many are dead and downloading is slow/unreliable. |
| **How we obtained it (MD5-matching)** | We download the mirror via the `kaggle` CLI, then match its images to our manifest **by content MD5**: for every mirror image we take its filename stem (if already an md5) or hash its bytes, and keep it only if that hash is in `fitzpatrick17k.csv`'s `md5hash` set. This is naming-agnostic (mirror file names don't matter) and immune to dead links. Implemented in `src/dermaface/data/download.py` (`import_fitzpatrick_images`, `--from-kaggle`). Result: **1,141** manifest images, full coverage. A local mirror folder works too via `--from-dir` (same MD5 match). The direct-URL fetch remains available as a fallback. |
| **Restrictions** | ❗ Non-commercial only; do not redistribute the images; keep them out of git. |

## 2. SKINCON

| | |
|---|---|
| **Source** | https://skincon-dataset.github.io/ · Daneshjou et al., NeurIPS 2022 Datasets & Benchmarks |
| **Contents** | 3,230 Fitzpatrick17k images + 656 DDI images, densely annotated with 48 clinical concepts |
| **License** | **Annotations & code: MIT.** Underlying **images inherit source terms** — Fitzpatrick17k (non-commercial) and DDI (credentialized). |
| **How we obtained it** | Downloaded the two annotation CSVs. We use them for a coarse **severity proxy** (concept counts) joined onto Fitzpatrick17k by `md5hash`. DDI images require credentialized access (https://ddi-dataset.github.io/) and are **not** auto-downloaded. |
| **Files** | `SKINCON Fitzpatric17k annotations.csv`, `SKINCON DDI annotations.csv` |

## 3. Google SCIN (Skin Condition Image Network)

| | |
|---|---|
| **Source** | https://github.com/google-research-datasets/scin · Google Health + Stanford Medicine (2024) |
| **Contents** | 10,000+ crowdsourced consumer dermatology images (informed consent); dermatologist labels, estimated Fitzpatrick skin type + Monk Skin Tone |
| **License** | **CC BY-4.0** (verify at source). Attribution required. |
| **How we obtained it** | Metadata CSVs from the repo. Images live in the **public** bucket `gs://dx-scin-public-data`; we fetch just the manifest's images over **plain HTTPS** (`https://storage.googleapis.com/dx-scin-public-data/dataset/images/<id>.png`) — **no Google Cloud SDK required** (uses `gsutil` if present). Result: **473** images. Implemented in `src/dermaface/data/download.py` (`_scin_http_fetch`). |
| **Restrictions** | Attribution required (CC BY-4.0). Treat as sensitive: no re-identification, no PII in commits or the demo. |
| **Files** | `dataset_scin_cases.csv`, `dataset_scin_labels.csv` |

---

## Label harmonization note

The four classes (`acne`, `rosacea`, `redness`, `clear`) are mapped from each
source's native condition names by a transparent keyword map in
`src/dermaface/data/manifest.py` (`LABEL_KEYWORDS`), with an `EXCLUDE_KEYWORDS`
guard (e.g. `lupus erythematosus` must not fall into `redness`). Full crosswalk is
generated to `data/external/label_map.csv` (committed in the repo — non-image
taxonomy only). This is a
**first pass** for Sprint 1; finalized taxonomy + severity method are worked out in
`notebooks/02_label_harmonization.ipynb` (Aparna + Iva). Fitzpatrick encodings are
normalized to Roman numerals I–VI (or `unknown`) so splits can stratify by skin tone.

## Compliance checklist

- [x] Every source's license reviewed and recorded above.
- [x] **Image data kept out of git** (images, raw CSVs, manifest, splits, QA report)
      — shared via the team Google Drive (`DermaFace-Team-Data`).
- [x] Non-image records versioned in repo: `docs/PROVENANCE.md` +
      `data/external/label_map.csv` (taxonomy crosswalk, no image data/PII).
- [x] Kaggle mirror documented as the actual Fitzpatrick image source, with the
      caveat that non-commercial terms still govern the images.
- [ ] If publishing derived results: re-confirm Fitzpatrick17k non-commercial terms
      and add SCIN CC-BY attribution.
- [ ] DDI credentialized access requested before using DDI images (currently unused).
