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
(2) a coarse **severity** estimate (mild / moderate / severe); (3) a **Grad-CAM** overlay
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

**Data analysis / EDA.** ⬜ *Pending data acquisition (Aparna + Rolando).* For images we will
plot: class balance, Fitzpatrick skin-tone distribution, and image-quality summaries.

*Depth to add later:* why these datasets, their known biases, licensing constraints, what's
missing, and how class/skin-tone skew is expected to affect results.

## 2. Preprocessing ⬜ (planned)

Planned pipeline (see [data-strategy.md](data-strategy.md)): dedup (perceptual hash),
drop corrupt/low-quality images, face-presence check, unify labels → {acne, rosacea,
redness, clear}, stratified train/val/test/demo splits by **class and Fitzpatrick type**,
frozen test set. Normalization uses ImageNet statistics.

*Note:* color augmentation is kept **mild** on purpose — aggressive jitter would destroy the
erythema/redness signal the model needs.

*Depth to add later:* why each step; what didn't help; effect of augmentation choices.

## 3. Model 🟡 (decided; implementation in progress)

**Approach chosen: pretrained model + fine-tune (instruction option 3-2).**

- **Backbone: ResNet50** (ImageNet-pretrained). *Why:* reliable for transfer learning, strong
  performance/compute balance for 224×224 classification, well-supported. (Decision: Iva.)
- **Alternatives considered:**
  - *Train a CNN from scratch* (option 3-1) — kept as the from-scratch baseline for comparison (Varsha).
  - *YOLO / object detection* — **rejected**: our task is whole-image *classification* with
    Grad-CAM localization, and our datasets have no lesion bounding boxes; YOLO would also make
    Grad-CAM redundant. (Good "alternatives considered" material for the report.)

**Severity method: concept-derived proxy** (decision: Iva) — use SKINCON concept annotations
(erythema/papule/pustule intensity) to bucket into mild/moderate/severe. Cheap and defensible,
but approximate; a `severity_map.csv` will document the mapping. ⬜ *severity_map.csv pending.*

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

## 8. Fairness analysis ⬜ (pending)

Metrics stratified by Fitzpatrick skin type; report the macro-F1 gap honestly even if it
exceeds the ≤ 0.15 target, and discuss likely causes (data skew, small subgroup sizes).

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
| Aparna + Rolando (Data) | Data acquisition, manifest, QA, EDA (starting) |
| Varsha (MLOps) | Training loop / backbone code (Keras), benchmarking plan, CI |
| Temirlan (Eval & Explainability) | Metrics test support, Grad-CAM evidence set, evaluation validation |
| Ali (UI/UX) | Streamlit app (upload/consent/disclaimer/UI states), Grad-CAM overlay display, standups/sprint tracking |

---

## Appendix A — Progress log / standups

### Sprint 1, Standup 1 — 13 July 2026 (full notes: [standups/2026-07-13-standup1.md](standups/2026-07-13-standup1.md))
- **Decisions:** backbone = **ResNet50**; severity = **concept-derived proxy**; data acquisition owned by **Aparna + Rolando**; some of Temirlan's tasks reshuffled to Ali.
- **Done:** Iva — backbone/severity decisions + metrics toy test; Ali — Streamlit app + consent flow.
- **Blockers:** everything downstream (training, benchmarks, evaluation) waits on the dataset/manifest; a git branch-sync issue (since resolved).
