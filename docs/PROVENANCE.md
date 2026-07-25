# Data Provenance

Record of where each source dataset came from, its license, and how it was
obtained. **Read before publishing anything derived from this data.** Medical-
adjacent images are sensitive; licensing here is restrictive.

> **Image data is kept out of git** — images, raw CSVs, `manifest.csv`, splits, and
> QA reports are never committed. Metadata (the manifests, splits, label map, raw
> CSVs) is shared via the team Google Drive `DermaFace-Team-Data`. **Fitzpatrick17k
> images are NOT re-hosted anywhere** — not git, not the Drive — because the access
> agreement requires research-only use and deletion on completion; each authorized
> teammate fetches their own copy via the official form. Two small, non-image
> records stay versioned in the repo: this provenance doc (in `docs/`) and the label
> crosswalk (`data/external/label_map.csv`). Neither contains image data or PII.

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

**Image source — official access form (what we used):**

| | |
|---|---|
| **Source** | Obtained the full image set (16,577 files, each named by its `md5hash`) via the **official Fitzpatrick17k access form**, which grants a link to the complete image archive. |
| **Terms accepted (from the form)** | **Scientific / medical research use only**, and **the data will be deleted from all devices once the research is complete.** These obligations are binding and stricter than the base non-commercial license. |
| **How we use it (MD5-matching)** | Images are matched to the manifest **by content MD5** — each file's name equals the MD5 of its bytes, which is exactly the `md5hash` column in `fitzpatrick17k.csv`. Verified: content MD5 == filename for the set, and the 16,577 images map 1:1 to the 16,577 CSV rows (0 missing, 0 extra). Point the pipeline at the folder with `--from-dir <path>` — `src/dermaface/data/download.py::import_fitzpatrick_images` copies exactly the manifest's images into `data/raw/fitzpatrick17k/images/`. |
| **Fallback** | `nazmusresan/fitzpatrick17k` on Kaggle (CC0-tagged re-host) via `--from-kaggle`, for anyone awaiting form approval. ⚠️ The mirror's CC0 tag does **not** override the underlying non-commercial terms; it also missed ~231 of the images we needed (~85% coverage), so the official form is preferred. The direct clinical-atlas URLs (`url` column) are a further fallback but many are dead. |
| **Restrictions** | ❗ Research use only; do **not** redistribute the images; keep them out of git and off the shared Drive; **delete when the project is complete** (see checklist). |

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
- [x] Fitzpatrick17k images obtained via the **official access form** (research-use
      agreement), not re-hosted to git or the team Drive. Kaggle mirror kept only as
      an approval-pending fallback.
- [ ] ⏳ **Delete Fitzpatrick17k images from all devices when the project is
      complete** — required by the access agreement. (Owner: Rolando.)
- [ ] If publishing derived results: re-confirm Fitzpatrick17k non-commercial terms
      and add SCIN CC-BY attribution.
- [ ] DDI credentialized access requested before using DDI images (currently unused).
