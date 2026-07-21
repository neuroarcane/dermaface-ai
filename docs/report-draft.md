# DermaFace AI — Project Report (DRAFT)

> **Status:** Living draft. This is the working skeleton for the final deliverable; it
> will be ported into the Jupyter notebook (code + descriptions) with a summary
> report at the end. Sections are marked ✅ ready · 🟡 partial · ⬜ pending as the
> sprint progresses.
>
> **Course:** Mathematics / Deep Learning (Dr. Mahdieh Khalilinezhad) — project in place of exam.
> **Team (7):** Hessam (Product Lead), Iva (ML Research), Aparna + Rolando (Data), Varsha (MLOps), Temirlan (Eval & Explainability), Ali (UI/UX).
> **Repo:** https://github.com/neuroarcane/dermaface-ai

Write each section to the team's depth standard — see [report-guide.md](report-guide.md): don't stop at *what*; cover **why**, **alternatives**, **challenges**, **meaning**, and **failures**.

---

## 0. Executive summary ✅

DermaFace AI is an **educational skin-condition screening prototype**. A user uploads a
face photo and receives: (1) a predicted condition — **acne, rosacea, redness, or clear**;
(2) *[v1: severity **de-scoped** — condition-only, see §3]*; (3) a **Grad-CAM** overlay
marking the regions that drove the prediction; and (4) confidence, limitations, and a
"see a professional" prompt.

**It is framed as screening & education, not diagnosis** — this constraint shapes every UI
and reporting decision (see [ethics-and-disclaimer.md](ethics-and-disclaimer.md)).

## 0.1 Success criteria — set up front ✅

Per the project sponsor's guidance, we defined measurable targets **before** modelling and
will report actual results against them. Full list: [requirements.md](requirements.md).
Headline targets:

- **Functional:** classify acne/rosacea/redness/clear; Grad-CAM on every prediction; severity band (or documented de-scope); screening framing.
- **Performance (frozen test set):** beat majority-class baseline; **macro-F1 ≥ 0.60**; **per-class recall ≥ 0.50**.
- **Fairness:** macro-F1 gap across Fitzpatrick skin tones **≤ 0.15** (reported even if larger).

**Target vs. Actual** is tracked in [model-card.md](model-card.md); Actual is filled after training.

---

## 1. Dataset details 🟡

**Business problem.** Common inflammatory skin conditions (acne, rosacea, redness) are
widespread; a lightweight screening/education tool could help users decide whether to seek
professional care. *Not* a diagnostic device.

**Datasets (large, publicly available skin-image collections):**

| Dataset | Link | Role |
|---|---|---|
| Fitzpatrick17k | https://github.com/mattgroh/fitzpatrick17k | Condition labels + Fitzpatrick skin-tone labels (fairness) |
| SKINCON | https://skincon-dataset.github.io/ | Dense clinical concept annotations (erythema, papules…) → severity proxy |
| Google SCIN | https://github.com/google-research-datasets/scin | Consumer/phone-quality photos, closer to deployment |

Additional sources under license review (per Day-1 report): ACNE04, DDI (for fairness/eval).

**Acquisition challenges (real, worth reporting):** most of **Fitzpatrick17k's** image
source URLs are dead/migrated, so only a small fraction was directly downloadable — the team
requested the images from the authors and is leaning on additional sources (SCIN downloaded
cleanly; ACNE04/DDI under review) to compensate. The dataset **license also prohibits hosting
images in a public repo**, so raw data is kept in external storage and never committed
(consistent with the repo's gitignore). These are good "challenges + how we handled it" material.

**Data analysis / EDA.** ⬜ *Pending data acquisition (Aparna + Rolando).* For images we will
plot: class balance, Fitzpatrick skin-tone distribution, and image-quality summaries.

*Depth to add later:* why these datasets, their known biases, licensing constraints, what's
missing, and how class/skin-tone skew is expected to affect results.

## 2. Preprocessing 🟡 (Sprint-2 data work done; Rolando + Aparna)

**Cleaning:** 1,614 → **1,559** rows — dropped 35 with unknown Fitzpatrick type and 21
perceptual-hash duplicate images. Every surviving row validates (real class + real skin type,
no unknowns).

**Class imbalance → weighted loss** (not oversampling). With only ~200 rosacea images,
resampling would show the model the same few images repeatedly; instead, class weights are
exported to `class_weights.json` (rosacea ≈ 3.1× acne) and applied in the loss. The sampler is
off by default so we don't double-correct. *Why this over oversampling:* avoids overfitting to
a handful of rare-class images.

**Splits:** re-frozen from the cleaned rows with **original assignments preserved** (no
reshuffle) — the frozen test set is the same images minus what cleaning removed; measured drift
is **≤ 1 point** on every class and skin type, so stratification held. (seed 42)

**Augmentation (train split only):** crop / flip / rotation + mild brightness/contrast.
**Saturation and hue are locked at 0 on purpose** — jittering them washes out the erythema,
which is the whole signal for redness/rosacea. A test fails if anyone raises them.

*Depth to add later:* why each step; what didn't help; effect of augmentation choices.

## 3. Model 🟡 (decided; implementation in progress)

**Approach chosen: pretrained model + fine-tune (instruction option 3-2).**

- **Framework: PyTorch** (decided 2026-07-17). *Why:* the rest of the stack is already
  PyTorch — the package scaffold, the Streamlit app, Grad-CAM (pytorch-grad-cam), and the data
  pipeline's `torch` dataloaders. A brief Keras baseline existed, but the team **unified on
  PyTorch** to avoid a split model/dataloader stack; Varsha is porting her model to torchvision.
- **Backbone: ResNet50** (ImageNet-pretrained). *Why:* reliable for transfer learning, strong
  performance/compute balance for 224×224 classification, well-supported. (Decision: Iva.)
- **Alternatives considered:**
  - *Train a CNN from scratch* (option 3-1) — kept as a **from-scratch baseline** for comparison.
- **Model comparison (Sprint 2):** we train and compare **three** models — a baseline **CNN (6-layer, from scratch)**, **ResNet50** (fine-tuned), and **VGG16** — one per team member (Varsha / Iva / Temirlan), then pick the best on a common metric set. Reporting a from-scratch baseline vs. two pretrained backbones is good "alternatives + why" evidence.
  - *YOLO / object detection* — **rejected**: our task is whole-image *classification* with
    Grad-CAM localization, and our datasets have no lesion bounding boxes; YOLO would also make
    Grad-CAM redundant. (Good "alternatives considered" material for the report.)

**Severity: DE-SCOPED for v1 (condition-only).** Severity labels exist for only ~16% of images
and are heavily skewed (**6 "severe" / 29 "mild"** total), too sparse to train a reliable
severity classifier. v1 ships condition-only; the **concept-derived proxy** (SKINCON concepts →
mild/moderate/severe) is documented as **future work** in [severity-decision.md](severity-decision.md).
*Good "alternatives + honest limitation" material for the report.*

*Depth to add later:* freezing schedule, why pretrained over from-scratch, head design.

## 4. Hyperparameter tuning ⬜ (planned, "good to have")

Planned search over learning rate, batch size, and augmentation strength; report what
mattered most and what surprised us.

## 5. Training & validation ⬜ (pending)

Will track **training loss & accuracy** and analyze train/validation via history/TensorBoard;
include loss/accuracy curves and note over/underfitting signs and interventions.
*Blocked on:* the processed manifest (Aparna + Rolando) → training loop (Varsha).

## 6. Prediction ⬜ (pending)

`model.predict` on held-out images; the Streamlit app already performs single-image inference
(placeholder mode until a checkpoint exists).

## 7. Evaluation 🟡 (metrics implemented; results pending)

**Implemented (Iva):** `classification_metrics` (accuracy, macro-F1, macro precision/recall),
`fairness_by_skin_type`, and `confusion` (sklearn), with 5 passing unit tests. This is the
evaluation contract downstream stages use.

**Results:** ⬜ pending training. Will report accuracy, macro-F1, per-class precision/recall,
confusion matrix, and the **Target-vs-Actual** table with a one-line interpretation per row.

## 8. Fairness analysis 🟡 (method decided; results pending)

**Reporting decision:** report fairness across **skin-tone bands (I-II / III-IV / V-VI)** as
the primary view (test-set n = 81 / 61 / 16), with the per-type I–VI table shown alongside
**annotated with sample sizes**. *Why bands:* the test set has only **3 Fitzpatrick VI images**
and **zero rosacea-on-VI**, so a per-type macro-F1 on n=3 is noise, not a measurement — a single
error moves it ~33 points. Bands mirror the grouping the DDI dataset uses.

**Limitation (state plainly in the report):** type VI is 1.9% of the dataset; per-type metrics
for the darkest skin are not statistically meaningful and won't be reported as if they were.
This skew originates in the source datasets (public dermatology collections lean toward lighter
skin), **not** our sampling (stratified; ≤1pt drift). Full write-up + ready-to-paste paragraph:
Rolando's `FAIRNESS_LIMITATION.md` (on the team Drive).

## 9. Explainability — Grad-CAM 🟡 (app done; evidence pending)

**Done (Ali + Varsha):** Grad-CAM overlay renders in the Streamlit app for every prediction
(currently on a random-weight model in placeholder mode, clearly labelled as illustrative).

**Pending (Temirlan):** collect the evidence set for the report — correct examples, failure
examples, and misleading heatmaps. IoU/localization scoring only if valid masks/boxes/proxy
regions exist; otherwise document qualitatively.

## 10. Interpretation of results ⬜ (pending)

What the metrics mean for a *screening* tool (not diagnosis): which errors are "safe" vs.
concerning, whether we'd trust it and why, real-world constraints.

## 11. Hardware & memory ⬜ (pending)

Record training environment (GPU/TPU/CPU), memory used, and training time; note reproducibility
(fixed seeds, frozen test set).

## 12. Next steps ⬜ (to finalize)

Concrete, prioritized continuations (e.g., larger/curated data, severity validation against a
rubric, clinician feedback) — not just "collect more data."

## 13. Lessons learned 🟡 (in progress)

Process lessons so far:
- **Scope discipline** — grew from 5 → 7 members by pairing newcomers into existing workstreams rather than adding features.
- **CI-gated workflow** — self-merge once `ruff` + `pytest` pass keeps a 7-person team moving without review bottlenecks.
- **Model choice** — resisting the "use the fanciest model (YOLO)" pull in favour of the task-appropriate one (classification + Grad-CAM).

*Per-person + team reflections to be completed at the end.*

## 14. Individual contributions 🟡 (running log — finalize at submission)

| Member | Contributions so far |
|---|---|
| Hessam (Product Lead) | Scope, disclaimer/ethics framing, Day-1 setup report, coordination |
| Iva (ML Research) | Backbone decision (ResNet50), severity method (concept-derived proxy), metrics implementation + tests |
| Aparna + Rolando (Data) | Data acquisition + Sprint-2 cleaning: harmonized manifest, dedup + skin-type validation (1,614→1,559), weighted-loss imbalance handling, frozen splits (≤1pt drift), erythema-safe augmentation, QA + fairness-coverage findings |
| Varsha (MLOps) | Baseline **CNN + ResNet** (PyTorch); leads training + model comparison (assigns models, defines metrics, consolidates); HF Spaces deploy; CI |
| Temirlan (Eval & Explainability) | Trains one comparison model; metrics test support; Grad-CAM evidence set; evaluation + failure analysis |
| Ali (UI/UX) | Streamlit app (upload/consent/disclaimer/UI states), Grad-CAM overlay display, standups/sprint tracking; #1 decision write-up (`severity-decision.md` + draft `severity_map`) |

---

## Appendix A — Progress log / standups

### Sprint 1, Standup 1 — 13 July 2026 (full notes: [standups/2026-07-13-standup1.md](standups/2026-07-13-standup1.md))
- **Decisions:** backbone = **ResNet50**; severity = **concept-derived proxy**; data acquisition owned by **Aparna + Rolando**; some of Temirlan's tasks reshuffled to Ali.
- **Done:** Iva — backbone/severity decisions + metrics toy test; Ali — Streamlit app + consent flow.
- **Blockers:** everything downstream (training, benchmarks, evaluation) waits on the dataset/manifest; a git branch-sync issue (since resolved).

### Sprint 1, Standup 2 — 15 July 2026 (full notes: [standups/2026-07-15-standup2.md](standups/2026-07-15-standup2.md))
- **Data trouble:** Fitzpatrick17k source URLs mostly dead → only a small portion downloaded; authors emailed; SCIN fine; may need ACNE04/DDI. **License forbids public-repo image hosting** → external storage only.
- **Varsha (async):** baseline CNN + ResNet models ready; not yet trained (waiting on data).
- **Unblock plan:** Aparna to share a partial dataset with Varsha so she can start a baseline.
- **Blockers:** Fitzpatrick dead URLs; dataset licensing; Temirlan's ISP outage (resolved). **Data is the critical path and is slipping past this sprint.**

### Sprint 1, Standup 3 — 17 July 2026 (full notes: [standups/2026-07-17-standup3.md](standups/2026-07-17-standup3.md))
- **End of Sprint 1.** Data pipeline delivered (Aparna + Rolando); Aparna now on a Sprint-3 report task (~1 day). Varsha's one remaining task carried to the next sprint (failure-case analysis).
- **Submission decision:** DermaFace is submitted to the sponsor as a **recorded video presentation** (online, not in person) — planned to record during next Friday's class.
- **Absent:** Iva (internet issues — severity thresholds still pending), Temirlan (no update).

### Decisions after Standup 2
- **2026-07-17 — Data pipeline delivered:** Rolando's PR acquires all 3 datasets (1,614 images via an MD5-matched Kaggle mirror, dodging the dead URLs), with harmonized manifest, label map, stratified frozen splits, QA report, and passing tests. Raw data stays out of git (license) — hosted on a shared team Google Drive.
- **2026-07-17 — Framework = PyTorch:** team unified on PyTorch (the whole stack was already PyTorch; Varsha porting her Keras baseline over) to avoid a split model/dataloader stack.
- **2026-07-18 — Sprint-2 data cleaning done (Rolando + Aparna):** 1,614 → 1,559 rows (dropped unknown skin type + perceptual duplicates); class imbalance via **weighted loss** (`class_weights.json`, not oversampling); test set re-frozen with ≤1pt drift; erythema-safe train-only augmentation. See §2.
- **2026-07-18 — Fairness reporting = skin-tone bands:** report I-II / III-IV / V-VI as primary (per-type shown with sample sizes) because type-VI coverage is too thin for per-type metrics. See §8.
- **2026-07-18 — Faces (⏳ pending Iva's sign-off):** QA found ~81% of images have no *detectable* face (Fitzpatrick17k spans all body sites). Direction: **do not hard-filter** to faces (would shrink to ~293 images and drop valid facial close-ups the detector misses); instead train on the full cleaned set, tag the face flag, and report the body-site-vs-face mismatch as a **limitation**. Iva (ML lead) to confirm.
- **2026-07-21 — Severity de-scoped for v1:** the cleaned data has only **6 "severe" / 29 "mild"** labels (~16% of images labelled at all), too sparse to train a reliable severity classifier. v1 ships **condition-only**; concept-derived proxy documented as future work. App shows "Severity: Not assessed." Provisional call by Ali; Iva informed (reversible). Closes the severity part of #1 / requirement F3.

### Sprint 2, Standup 1 — 20 July 2026 (full notes: [standups/2026-07-20-sprint2-standup1.md](standups/2026-07-20-sprint2-standup1.md))
- **Training kicked off** (Varsha — critical path; full data pipeline now merged). May slip a day (other project first).
- **3-person pairing dropped** on #20 → each of Varsha / Iva / Temirlan trains one model; **compare baseline CNN vs ResNet50 vs VGG16**, consolidate metrics.
- **Report:** Claude drafts, Iva + Hessam humanise. **Video** for Moe recorded Friday.
- Absent: Hessam.
