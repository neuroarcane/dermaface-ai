# DermaFace AI — Project Report (DRAFT)

> **Status:** Living draft. This is the working skeleton for the final deliverable; it
> will be ported into the Jupyter notebook (code + descriptions) with a summary
> report at the end. Sections are marked ✅ ready · 🟡 partial · ⬜ pending as the
> sprint progresses.
>
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

## 0.2 Business case — why this tool 🟡

**The problem.** Acne, rosacea, and facial redness are among the most common skin complaints,
yet access to a dermatologist is slow and expensive: in many regions the wait for a routine
appointment is weeks to months, and a large share of visits are for conditions that are visually
recognisable and often self-managed. People instead self-diagnose with web searches that return
alarming, unranked results, or they do nothing. The gap is **triage**, not diagnosis: helping a
person decide *"is this worth getting looked at, and roughly what am I looking at?"*

**Who it's for and the value.** A first-line, phone-based **screening & education** aid for
non-experts. Value: (1) **reassurance or a nudge to seek care**, earlier than a booked
appointment; (2) **plain-language education** about what the condition looks like; (3) a
**Grad-CAM overlay** so the user sees *why* the tool flagged a region, building appropriate
(not blind) trust. For a course/portfolio context it also demonstrates an end-to-end applied-ML
product: data governance → model bake-off → evaluation → a deployed app.

**Why now / why feasible.** Public dermatology datasets (Fitzpatrick17k, SCIN) and mature
transfer-learning backbones make a credible prototype achievable in a short sprint on a laptop.

**Explicitly a non-goal.** This is **not a diagnostic device** and is not a substitute for a
clinician. Every screen ends in "see a professional," severity is de-scoped in v1, and the model
is measured for **fairness across skin tones** because a screening tool that works only on light
skin would do harm. This framing is a product decision, not a disclaimer bolted on at the end —
it shapes the UI, the metrics, and the scope (see §0.1, §8).

## 0.3 Project history — how our thinking evolved 🟡

*(Sponsor asked for the journey, not just the destination. Full standup log: Appendix A.)*

The project did **not** run in a straight line; several core decisions were revised as we learned,
and the schedule was gated almost entirely by **data**. The arc:

1. **Framing first (Sprint 1 start).** Before any modelling we fixed measurable **success criteria**
   up front (sponsor's explicit requirement) — beat baseline, macro-F1 ≥ 0.60, per-class recall
   ≥ 0.50, fairness gap ≤ 0.15 — so the project would be judged target-vs-actual, not vibes.
2. **Data became the critical path — and slipped (Sprint 1, the main slowdown).** Most of
   Fitzpatrick17k's original image URLs are **dead/migrated**, so only a fraction downloaded
   directly. We lost roughly a sprint here: we emailed the authors, stood up an **interim
   Kaggle mirror** (MD5-matched so it's byte-identical) to keep moving, and later secured the
   **official copy via the access form**. The dataset **license also forbids hosting images in a
   public repo**, forcing an external-storage workflow. A teammate's ISP outage and a member
   splitting time with another course's project added drag. *Everything downstream — training,
   evaluation, the app's real predictions — waited on this*, which is why Sprints 1–2 look
   data-heavy and model-light.
3. **Framework changed: Keras → PyTorch (2026-07-17).** An early Keras baseline existed, but the
   rest of the stack (app, Grad-CAM, dataloaders) was PyTorch. Rather than maintain a split
   stack, we **unified on PyTorch** and ported the baseline over.
4. **Scope trimmed on evidence, not opinion.** **Severity was de-scoped** for v1 once the data
   showed only 6 "severe" / 29 "mild" labels — too sparse to learn. **Fairness reporting moved to
   skin-tone bands** (I-II / III-IV / V-VI) because per-Fitzpatrick-type test counts were as low as
   3. We chose **not to hard-filter to detected faces** (would have cut the set to ~293 images).
5. **Modelling plan changed: one model → a three-model bake-off.** A planned 3-person pairing on
   training was dropped under time pressure in favour of **one model per person** — a from-scratch
   **CNN** (Ali), **ResNet50** (Iva), **VGG16** (Varsha) — compared on one metric set, so we could
   show *alternatives + why* rather than a single unexplained choice.
6. **The modelling story (Sprints 2–4) — three models, one plot twist.** We trained the three in
   sequence and let each result set up the next:
   - The **from-scratch CNN** landed at **macro-F1 0.35 — below the majority-class baseline**. Not a
     failure of effort but a *diagnosis*: on ~1,000 images a fresh network only learns
     "clear vs. not-clear," not the fine differences between three red conditions. **Verdict: the
     bottleneck is data/representation → borrow pretrained features.**
   - **ResNet50** (transfer learning) nearly **doubled** that to **macro-F1 0.67** and cleared the
     accuracy bar — confirming the diagnosis. But it introduced the project's **plot twist:** it
     **failed the fairness check** (0.25 gap), scoring far worse on the darkest-skin band. The weak
     CNN had "passed" fairness only by being *uniformly* bad; the instant a competent model arrived,
     the gap it had been masking appeared. **Getting good is what exposed who the tool wasn't good
     for.**
   - **VGG16** (grid-search-tuned) took the top spot at **macro-F1 0.727 / accuracy 0.74** and was
     **selected as the final model** (§7).
7. **What the story adds up to.** The headline isn't "we reached 0.73." It's that we can **explain
   every number**: why the from-scratch baseline failed, why transfer learning fixed it, and why the
   fairness gap is a **data-coverage** problem (only 16 dark-skin test images) rather than an
   algorithm quirk — which is why *"collect more dark-skin data (DDI)"* is our **top future-work
   item, not an afterthought**. The final model ships **with that limitation stated up front**,
   because a screening tool that quietly works better on light skin would do harm. That trajectory —
   framing → data struggle → baseline → transfer learning → a fairness reckoning → an honest,
   caveated final model — *is* the project.

**How decisions were made:** measurable criteria first, then **data-driven** calls (severity,
fairness, face-filter, and the model choice itself all settled by the numbers, not opinion), with a
bias toward the *task-appropriate* choice over the fanciest one (e.g. rejecting YOLO — §3).
Reversible calls were made provisionally and flagged, not blocked on — which is what let a
7-person team keep moving while the data caught up.

---

## 1. Dataset details 🟡

**Business problem.** Common inflammatory skin conditions (acne, rosacea, redness) are
widespread; a lightweight screening/education tool could help users decide whether to seek
professional care. *Not* a diagnostic device. (Full business case: §0.2.)

**Datasets (large, publicly available skin-image collections):**

| Dataset | Link | Role |
|---|---|---|
| Fitzpatrick17k | https://github.com/mattgroh/fitzpatrick17k | Condition labels + Fitzpatrick skin-tone labels (fairness) |
| SKINCON | https://skincon-dataset.github.io/ | Dense clinical concept annotations (erythema, papules…) → severity proxy |
| Google SCIN | https://github.com/google-research-datasets/scin | Consumer/phone-quality photos, closer to deployment |

Additional sources under license review (per Day-1 report): ACNE04, DDI (for fairness/eval).

**Acquisition challenges (real, worth reporting):** most of **Fitzpatrick17k's** image
source URLs are dead/migrated, so only a small fraction was directly downloadable. The team
then **obtained the official dataset through the Fitzpatrick17k access form** (granted by the
authors, M. Groh et al.), which is now our **cited source of provenance** — not the interim
Kaggle mirror used during early development (the mirror's images are byte-identical: filenames
are content MD5s matching our manifest keys, so no retraining is needed). SCIN downloaded
cleanly over HTTPS from its public bucket; ACNE04/DDI remain under review.

**Data governance (license terms — state in the report):** the access grant restricts use to
scientific/medical research and **requires deleting the Fitzpatrick images from all devices once
the research is complete** — logged as a wrap-up compliance task. The license also **prohibits
hosting images in a public repo**, so raw data lives in external storage and is never committed
(enforced by the repo's gitignore). Full provenance + license detail: `docs/PROVENANCE.md`.
These are good "challenges + how we handled it / responsible-data" material.

### 1.1 The four classes (with examples)

The task is **4-class, single-label** condition classification. Class definitions and the
cleaned-dataset counts (1,558 images total):

| Class | What it looks like | Total | Train / Eval / Test | Main source(s) |
|---|---|---|---|---|
| **acne** | Comedones, papules, pustules — discrete lesions | 623 | 434 / 95 / 63 | Fitzpatrick (505) + SCIN (118) |
| **redness** | Diffuse erythema / inflammation, non-acne, non-rosacea | 471 | 328 / 73 / 48 | Fitzpatrick (449) + SCIN (22) |
| **rosacea** | Central-face erythema, flushing, telangiectasia | 202 | 140 / 30 / 22 | Fitzpatrick (161) + SCIN (41) |
| **clear** | No target condition present | 262 | 183 / 40 / 25 | **SCIN only (262)** |

**Example images:** a per-class example plate (a row of representative images for each class) is
generated **in the notebook** from the local data and embedded in the final PDF/Word deliverable.
It is **not committed to the repo** — the Fitzpatrick license forbids hosting images publicly
(§0.2, PROVENANCE.md). *[figure: `class_examples` — see notebook output.]*

**⚠️ Source confound (important, honest limitation).** `clear` images come **entirely from SCIN**
(consumer phone photos), while acne/redness/rosacea are **mostly Fitzpatrick** (clinical/atlas
images). The two sources differ in lighting, framing, and resolution, so a model can get
`clear`-vs-not partly right by learning **image *style*, not skin** — which likely inflates the
`clear` recall we see (§7) and would not transfer to real single-source deployment photos.
*Mitigations:* report this openly; where possible mix sources per class in future data; sanity-check
with Grad-CAM that the model attends to skin, not background/framing.

**Class balance & skew.** acne is the majority class (~40%); rosacea the minority (~13%). This
imbalance is handled by a **class-weighted loss**, not resampling (§2), and is why we report
**macro-F1** and **per-class recall**, not accuracy alone.

**Data analysis / EDA.** ✅ Data acquired and cleaned (Aparna + Rolando). EDA plots (class balance,
Fitzpatrick skin-tone distribution, source mix, image-quality summaries) are produced in the
notebook. *Depth to add:* known dataset biases (lighter-skin skew — §8), the source confound above,
and how each is expected to affect results.

## 2. Preprocessing 🟡 (Sprint-2 data work done; Rolando + Aparna)

**Cleaning:** 1,614 → **1,558** rows — dropped 35 with unknown Fitzpatrick type and 21
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
- **Primary pretrained backbone: ResNet50** (ImageNet-pretrained). *Why:* reliable for transfer
  learning, strong performance/compute balance for 224×224 classification, well-supported.
  (Decision: Iva.) The bake-off below tests it against VGG16 and the from-scratch CNN.
- **Model comparison (the bake-off):** we train and compare **three** models — one per person —
  on the **same data, splits, and metrics**, then pick the best. This gives us *alternatives + why*
  rather than one unexplained choice. **The three models (referred to by these names throughout):**

  | Model | Architecture | Type | Owner | Status |
  |---|---|---|---|---|
  | **Basic CNN** | 6-conv-block CNN | From scratch | Ali | ✅ Trained (weak baseline) |
  | **ResNet50** | ResNet-50 backbone | Transfer learning (ImageNet) | Iva | 🟡 In progress |
  | **VGG16** | VGG-16 backbone | Transfer learning (ImageNet) | Varsha | 🟡 Trained; frozen-test re-score pending |

  The Basic CNN is the deliberately-weak floor the two pretrained models must beat; if they don't
  clearly beat it, the bottleneck is data, not architecture.

- **Alternatives considered but rejected:**
  - *YOLO / object detection* — **considered and rejected; never trained** (so there are **no YOLO
    hyperparameters to report**). Our task is whole-image **classification** with Grad-CAM
    localization, and our datasets have **no lesion bounding boxes** to train a detector on; YOLO
    would also make Grad-CAM redundant. Choosing the task-appropriate model over the "fanciest" one
    is a deliberate call (see §13).
  - *Training a from-scratch CNN as the primary model* — kept only as the **baseline**, not the
    product model: too little data to learn strong features from scratch (borne out in §7).

**Severity: DE-SCOPED for v1 (condition-only).** Severity labels exist for only ~16% of images
and are heavily skewed (**6 "severe" / 29 "mild"** total), too sparse to train a reliable
severity classifier. v1 ships condition-only; the **concept-derived proxy** (SKINCON concepts →
mild/moderate/severe) is documented as **future work** in [severity-decision.md](severity-decision.md).
*Good "alternatives + honest limitation" material for the report.*

*Depth to add later:* freezing schedule, why pretrained over from-scratch, head design.

## 4. Hyperparameter tuning 🟡

**Shared configuration (all three models, from `dermaface/config.py`)** — held **fixed across
models on purpose** so the bake-off compares *architectures*, not tuning luck:

| Hyperparameter | Value | Note |
|---|---|---|
| Input size | 224 × 224 | ImageNet-standard for the pretrained backbones |
| **Batch size** | **32** | see batch-size discussion below |
| Epochs | 20 | best-val-macro-F1 checkpoint kept (early-stopping by selection) |
| Optimizer | Adam | — |
| Learning rate | 1e-4 | conservative for fine-tuning pretrained weights |
| Weight decay | 1e-4 | mild regularisation |
| Loss | Class-weighted cross-entropy | weights from `class_weights.json` (rosacea ≈ 3.1× acne) |
| Normalisation | ImageNet mean/std | matches pretrained backbones |
| Augmentation | flip / rotation / crop / mild brightness-contrast | **hue & saturation locked at 0** (erythema-safe, §2) |
| Seed | 42 | fixed for reproducibility |

**Did we evaluate different batch sizes?** Batch size was **fixed at 32** for the head-to-head so
the three models are directly comparable, and because 32 fits comfortably in laptop memory (§11).
We did **not** run a systematic batch-size sweep on the Basic CNN — a larger sweep is listed as
future work. The one place tuning *did* happen is **VGG16**, where Varsha ran a **grid search
(GridSearchCV)** over hyperparameters; that search is *why* its preliminary numbers must be
re-scored on the frozen test set before comparison (§7) — grid-search/CV scores use different data
folds and aren't comparable to a single held-out test score.

**What was tuned, per model (honest):**
- **Basic CNN** — no search; ran the shared config above. It's a baseline, so tuning effort was
  deliberately not spent here.
- **VGG16** — grid search over hyperparameters (Varsha); best configuration reported preliminarily.
- **ResNet50** — shared config; any tuning to be recorded when Iva's run lands.

*Depth to add when the pretrained runs finish:* which knob moved the metric most, and what
surprised us (e.g. whether more epochs helped or just overfit the majority class).

## 5. Training & validation 🟡

**Loop (identical for all three models):** each epoch runs train then validation; we track loss,
accuracy, and **macro-F1**, and checkpoint the **best validation macro-F1** (not the last epoch)
to `models/dermaface_best_<arch>.pt`. Metrics come from `dermaface.training.metrics` so the numbers
match evaluation. Loss/accuracy curves are plotted **in the notebook** per model.

**Basic CNN (Ali) — done.** Trained 20 epochs on the cleaned train split (1,085 images), CPU
(§11). Best **validation macro-F1 = 0.386 at epoch 20**. *Over/underfitting read:* this is
**underfitting**, not overfitting — even the *training* signal stays weak, and validation macro-F1
never rises far above chance. The from-scratch network simply lacks the capacity/data to learn the
fine-grained cues separating the three erythema conditions (§7). *Intervention that mattered:* the
**class-weighted loss** — without it the model collapses almost entirely onto the majority class;
with it, the minority `rosacea`/`redness` recalls become non-trivial (0.45 / 0.42) even though
overall accuracy stays low. The lesson carried to the pretrained models: the ceiling here is
representation quality, which is exactly what transfer learning is meant to raise.

**ResNet50 / VGG16:** curves + best-epoch to be filled in from Iva's and Varsha's runs.

## 6. Prediction 🟡 (real inference wired; **VGG16 selected** — checkpoint swap pending)

`dermaface.inference.predict` runs the full single-image path — preprocess (eval transforms,
matching training) → forward pass → softmax → `Prediction` + Grad-CAM overlay — and the Streamlit
app consumes it (PR #43, Ali). `load_model` resolves a checkpoint and rebuilds the matching
architecture (`cnn`, `resnet50`, or `vgg16`), so the selected model is a **one-file drop** into
`models/`. When no checkpoint is present the app falls back to a clearly-labelled **placeholder**
result — real output is never presented as a prediction without a model. The selected model is now
**VGG16** (§7); the app still runs the Basic CNN locally until `dermaface_best_vgg16.pt` is in hand,
at which point it's a drop-in swap (no code change) and we regenerate the Grad-CAM/FP-FN plates.

## 7. Evaluation ✅ (all three models fully scored on the frozen test set; **VGG16 selected**)

**Implemented (Iva):** `classification_metrics` (accuracy, macro-F1, macro precision/recall),
`fairness_by_skin_type`, and `confusion` (sklearn), with 5 passing unit tests. This is the
evaluation contract downstream stages use.

**Results — Basic CNN baseline (Ali):** ✅ first real numbers in. Full auto-generated report:
[eval_reports/cnn_eval_report.docx](eval_reports/cnn_eval_report.docx). Frozen test set:
**accuracy 0.35, macro-F1 0.35, macro-precision 0.33, macro-recall 0.44** (checkpoint
`dermaface_best_cnn.pt`, best val macro-F1 0.386 @ epoch 20). Per-class recall: acne 0.06,
rosacea 0.45, redness 0.42, clear 0.84. Target-vs-Actual: **P1–P3 not met**, **Fa1 met**
(band gap 0.064 ≤ 0.15).

*Error analysis (CNN):* the model sits at roughly chance and does **not** beat the majority-class
baseline (0.35 vs 0.40). The confusion matrix explains why: it reliably recognises **clear** skin
(recall 0.84) but **collapses on acne** (recall 0.06 — only 4 of 63 acne images correct),
scattering acne predictions across redness (28), clear (16) and rosacea (15); rosacea and redness
are likewise confused with each other. In effect the network learned a "clear vs. not-clear"
boundary but cannot separate the three erythema conditions — unsurprising, since acne, rosacea and
redness all present as red, inflamed skin, and a 6-layer network trained from scratch on ~1,000
images lacks the capacity and data to pick up the finer cues (papules, telangiectasia, diffuse
flushing) that distinguish them. This is the **intended role** of the Basic CNN: a weak
from-scratch baseline for the pretrained models (ResNet50, VGG16) to beat. If they don't improve
materially on the erythema classes, the bottleneck is data, not architecture.

**Basic CNN — confusion matrix (frozen test set, rows = true, cols = predicted):**

| true ↓ / pred → | acne | rosacea | redness | clear | (support) |
|---|---|---|---|---|---|
| **acne** | **4** | 15 | 28 | 16 | 63 |
| **rosacea** | 4 | **10** | 7 | 1 | 22 |
| **redness** | 5 | 19 | **20** | 4 | 48 |
| **clear** | 3 | 0 | 1 | **21** | 25 |

### 7.1 False positives / false negatives — causes and "treatment"

Reading the matrix (Basic CNN), the errors fall into three groups, ordered by how much they matter
for a **screening** tool:

1. **Condition → "clear" (false negatives — most harmful).** 16 acne, 4 redness, 1 rosacea image
   were called **clear** — i.e. a person with a condition told nothing's there (false reassurance,
   which could delay care). *Cause:* the from-scratch model only reliably learned the "clear look,"
   partly a **source confound** (`clear` = SCIN photos, §1.1). *Treatment:* **product-level** — the
   app never says "you're fine"; every screen ends in "see a professional," and low confidence is
   shown, not hidden. **Model-level** — raise recall with a pretrained backbone + more data, and add
   a confidence threshold that routes uncertain cases to *"inconclusive — seek advice."*
2. **Condition ↔ condition confusion.** acne is massively under-called (recall 0.06; 28 of 63 acne
   images predicted **redness**), and redness/rosacea trade errors. *Cause:* acne, rosacea and
   redness are all **erythematous and visually adjacent**; a shallow model can't pick up papules
   vs. telangiectasia vs. diffuse flushing. *Treatment:* transfer learning (in progress); if fine
   separation stays hard, fall back to a coarser **"inflammatory vs. clear"** decision or a **top-2**
   output rather than forcing one label.
3. **"clear" → condition (false positives — least harmful).** A few clear images were flagged as a
   condition. *Cause:* image noise/framing. *Treatment:* in a screening tool this errs the *safe*
   way (toward "get checked"); calibrate the threshold and use Grad-CAM (§9) so the user sees the
   evidence and isn't alarmed by a weak call.

**Example FP/FN plates** (a few real misclassified images per error type, with true vs. predicted
labels and Grad-CAM) are generated **in the notebook** and embedded in the final deliverable — not
committed to the repo (license, §0.2). *[figures: `fp_examples`, `fn_examples` — see notebook.]*
These will be refreshed for the **selected** model once the pretrained runs land.

**Results — ResNet50 (Iva):** ✅ **frozen-test confirmed** (same `dermaface.training.metrics`
contract as the CNN). **accuracy 0.68, macro-F1 0.67, macro-precision 0.68, macro-recall 0.73**
(checkpoint `dermaface_best_resnet50.pt`, best val macro-F1 0.586 @ epoch 20). Per-class recall:
acne 0.48, rosacea 0.77, redness 0.77, clear 0.92. Target-vs-Actual: **P1 ✅, P2 ✅** (0.67 ≥ 0.60),
**P3 ✗** (acne 0.48 — a hair under 0.50), **Fa1 ✗** (band gap **0.252** > 0.15).

**ResNet50 — confusion matrix (frozen test set):**

| true ↓ / pred → | acne | rosacea | redness | clear | (support) |
|---|---|---|---|---|---|
| **acne** | **30** | 18 | 6 | 9 | 63 |
| **rosacea** | 1 | **17** | 3 | 1 | 22 |
| **redness** | 3 | 6 | **37** | 2 | 48 |
| **clear** | 0 | 1 | 1 | **23** | 25 |

*Error analysis (ResNet50):* transfer learning closes most of the gap — macro-F1 **nearly doubles**
vs the CNN (0.67 vs 0.35) and it clears the accuracy bar. acne recovers dramatically (recall
0.06 → 0.48, 30/63 correct) but stays the hardest class, still bleeding into **rosacea**
(18 acne→rosacea); rosacea is correspondingly **over-predicted** (recall 0.77 but precision only
0.40). `clear` stays near-perfect (0.92) — consistent with the `clear`=SCIN **source confound**
(§1.1), so treat that number with caution. The real concern is **fairness**: the **V–VI band**
(darkest skin, n=16) falls to macro-F1 **0.44** vs 0.69 on III–IV — a **0.25 gap** that fails Fa1.
The model is materially weaker on the least-represented skin tones (a data-coverage problem, §8);
for a screening tool that is a **serious limitation, not a footnote**.

**Results — VGG16 (Varsha) — ✅ SELECTED FINAL MODEL:** frozen test set, same contract.
**accuracy 0.74, macro-F1 0.727, macro-precision 0.72, macro-recall 0.75** (checkpoint
`dermaface_best_vgg16.pt`, best val macro-F1 0.715 @ epoch 15; tuned via **grid search** —
winner `lr_head=3e-4, weight_decay=1e-4`, §4). Per-class recall: **acne 0.76, rosacea 0.68,
redness 0.67, clear 0.88**. Target-vs-Actual: **P1 ✅, P2 ✅** (0.727 ≥ 0.60), **P3 ✅ — the only
model to pass** (every per-class recall ≥ 0.50), **Fa1 ✗** (band gap **0.281** > 0.15 — the
*largest* of the three).

**VGG16 — confusion matrix (frozen test set):**

| true ↓ / pred → | acne | rosacea | redness | clear | (support) |
|---|---|---|---|---|---|
| **acne** | **48** | 5 | 2 | 8 | 63 |
| **rosacea** | 6 | **15** | 1 | 0 | 22 |
| **redness** | 8 | 4 | **32** | 4 | 48 |
| **clear** | 1 | 1 | 1 | **22** | 25 |

*Error analysis (VGG16):* the best model by a clear margin, and the **only one to satisfy every
per-class recall target (P3)**. acne — which the CNN collapsed on (recall 0.06) and ResNet50 half
recovered (0.48) — is now solidly classified (**0.76**, 48/63), and the residual errors are
balanced and sensible (a few acne→clear (8), redness→acne (8)) rather than a collapse. redness has
the highest precision (0.89); `clear` again tops recall (0.88), so the `clear`=SCIN **source
confound** (§1.1) still flatters every model equally. **The catch is fairness:** despite being the
best overall, VGG16 has the **largest** skin-tone gap — V–VI macro-F1 **0.487** vs I–II **0.769**,
a **0.281 gap** (§8). *The better the model got, the wider the dark-skin gap grew* — the sharpest
version of the project's central finding.

### 7.2 Model comparison & selection (progression → final)

All three models are scored the **same way** on the **same frozen test set** (`test_manifest.csv`,
158 images) with `dermaface.training.metrics`. Selection metric = **macro-F1** (chosen up front for
the class imbalance), with per-class recall and the fairness gap as tie-breakers/guards.

| Model | Accuracy | Macro-F1 | Per-class recall (acne/ros/red/clear) | Fairness gap | P1/P2/P3 |
|---|---|---|---|---|---|
| **Basic CNN** (baseline) | 0.35 | 0.35 | 0.06 / 0.45 / 0.42 / 0.84 | 0.064 ✅ | ✗ / ✗ / ✗ |
| **ResNet50** (Iva) | 0.68 | 0.67 | 0.48 / 0.77 / 0.77 / 0.92 | 0.252 ❌ | ✅ / ✅ / ✗ |
| **VGG16 (Varsha) — ✅ SELECTED** | **0.74** | **0.727** | **0.76 / 0.68 / 0.67 / 0.88** | **0.281 ❌** | ✅ / ✅ / **✅** |

All three rows are **frozen-test** scores via the same `dermaface.training.metrics`. VGG16 is the
**only model to pass P1, P2 *and* P3** — an unambiguous winner on task performance. **The tension
that must stay visible:** every model **fails the fairness guard**, and — the striking part —
**the gap grows as the model improves** (0.064 → 0.252 → 0.281). So the winner is also the *least*
fair; we ship it with that gap as a **headline limitation**, not a footnote (§8, §10).

**The progression (how we're arriving at the final model).** (1) Establish a measurable bar
(§0.1). (2) Train a **from-scratch CNN** to see how far raw architecture gets us on this data →
**it fails every performance target** (macro-F1 0.35 < 0.60), telling us the bottleneck is
representation/data, not effort. (3) Move to **transfer learning**: **ResNet50 confirms the
diagnosis** — macro-F1 jumps to **0.67** on the frozen test set (nearly 2× the CNN) and clears the
accuracy bar, **but fails the fairness guard** (gap 0.252 on the darkest-skin band). (4) **VGG16**
(Varsha), grid-search-tuned, posts the **best frozen-test macro-F1 (0.727)** and accuracy (0.74).
(5) Select on **macro-F1** → **VGG16**, then treat the fairness gap as a hard guard to report, not
hide.

**Final selection: ✅ VGG16** (accuracy 0.74, macro-F1 0.727 — highest of the three; the **only
model to clear P1, P2 *and* P3**). *Why VGG16 over ResNet50:* higher macro-F1 (0.727 vs 0.67) and
accuracy (0.74 vs 0.68) on the same frozen test set, and it satisfies **every** per-class recall
target (ResNet50 misses acne at 0.48). *Why not the Basic CNN:* it fails every performance target —
it exists to show how far from-scratch gets on this data (not far) and to prove transfer learning
was the right call.

**The honest caveat on the winner (a headline, not a footnote):** VGG16 **fails the fairness guard**
— band gap **0.281**, the *largest* of the three, driven by a V–VI macro-F1 of just 0.487.
Strikingly, **the gap grows monotonically as the models improve** (CNN 0.064 → ResNet50 0.252 →
VGG16 0.281): the better a model gets on this data, the more its gains concentrate on
well-represented lighter skin. This is a **data-coverage** problem (only 16 type-V/VI test images,
§8), not an algorithm quirk. VGG16 still ships — it is the best available and the alternatives are
both weaker *and* also unfair — but **with the fairness gap stated up front and a remediation plan**
(more dark-skin data / DDI). *Remaining task:* once `dermaface_best_vgg16.pt` is in hand it drops
straight into the app (the factory already supports `vgg16`) and we regenerate the FP/FN + Grad-CAM
plates for the selected model.

### 7.3 Beyond the test set — a real-world failure (the deployment gap)

Test-set macro-F1 of 0.727 is **in-distribution** (clinical dermatology images). Run the *deployed
app* on a **normal, well-lit face selfie** and it fails: a clear-skinned portrait is classified
**redness at 85% confidence** (probs: redness 0.85 · acne 0.08 · clear 0.04 · rosacea 0.03). This is
**expected, and arguably the most instructive result in the project:**

- **The `clear`=SCIN source confound (§1.1) bites here.** Every `clear` training image is a SCIN
  consumer photo of *body parts* (feet/arms) — **never a clean face portrait** — while the
  *conditions* are Fitzpatrick clinical *faces*. So a face portrait resembles the "condition"
  distribution and is pushed away from "clear."
- **Out-of-distribution input.** The model was trained on dermatology imagery, not selfies.
- **Grad-CAM confirms the mechanism:** the heatmap fires on **cheeks, neck, shoulders and
  background** — image *style / warmth / framing*, not any skin pathology.
- **Overconfident and wrong (85%).** The model has no calibrated sense of "I haven't seen this."

*This does not contradict the 0.727 metric* — it exposes the gap between **benchmark performance and
deployment**, which is precisely why the product is framed as *screening, not diagnosis* and always
defers to a professional. It also sharpens the top future-work item: the **`clear` class needs real,
multi-source face data**, plus **confidence calibration / an out-of-distribution guard**, before
this would be trustworthy on real users. *(Figure: `realworld_failure` — in the notebook; not
committed, license/privacy.)*

**Can't we just block bad inputs? We tried — and it backfires.** The obvious guard is a **face
detector** (reject non-face photos). But our own clinical images mostly *aren't* detectable faces
(the ~81% no-face finding, §0.3/§1) — on our four demo images, the face detector **rejects the valid
acne and clear examples while passing the failing selfie** (which *is* a face). It does the opposite
of what we need. A **confidence threshold** doesn't catch it either, because the failure is
*confident* (85%). So the app does what it honestly can — it **abstains ("Inconclusive") on
low-confidence estimates** and **states plainly that a confident answer isn't a guarantee on
out-of-distribution photos** — but there is **no clean v1 fix**. A real solution needs an
**out-of-distribution detector** (feature-distance / energy score, or a "not-a-valid-photo" class)
and **better multi-source `clear` data**. Recorded as future work (§12), not silently patched.

## 8. Fairness analysis ✅ (all three models scored by band)

**Reporting decision:** report fairness across **skin-tone bands (I-II / III-IV / V-VI)** as
the primary view (test-set n = 81 / 61 / 16), with the per-type I–VI table shown alongside
**annotated with sample sizes**. *Why bands:* the test set has only **3 Fitzpatrick VI images**
and **zero rosacea-on-VI**, so a per-type macro-F1 on n=3 is noise, not a measurement — a single
error moves it ~33 points. Bands mirror the grouping the DDI dataset uses.

**Results so far (macro-F1 by band, frozen test set):**

| Model | I-II (n=81) | III-IV (n=61) | V-VI (n=16) | Gap | Fa1 (≤0.15)? |
|---|---|---|---|---|---|
| **Basic CNN** | 0.333 | 0.367 | 0.304 | **0.064** | ✅ |
| **ResNet50** | 0.665 | 0.690 | **0.438** | **0.252** | ❌ |
| **VGG16 (selected)** | 0.769 | 0.707 | **0.487** | **0.281** | ❌ |

**The key insight (report this, don't hide it):** the Basic CNN *passed* Fa1 only because it was
**uniformly bad** — a small gap between three low scores is not fairness, it's incompetence spread
evenly. As the models get **competent**, the gap **grows monotonically** (0.064 → 0.252 →
**0.281**): each model's gains land on the well-represented lighter-skin bands (I–IV) while the
**V–VI band lags far behind** (VGG16: 0.769 on I–II but only **0.487** on V–VI). In other words,
*model skill and the fairness gap grew together, and our best model is the least fair* — a textbook
illustration of why a single accuracy number hides who a tool works for. **Root cause is data
coverage**, not the algorithm: only 16 type-V/VI images in the test set (and few in training). The
remediation is **more dark-skin data (e.g. DDI)**, reported as required future work; the selected
model ships with this gap stated as a headline limitation.

**Limitation (state plainly in the report):** type VI is 1.9% of the dataset; per-type metrics
for the darkest skin are not statistically meaningful and won't be reported as if they were.
This skew originates in the source datasets (public dermatology collections lean toward lighter
skin), **not** our sampling (stratified; ≤1pt drift). Full write-up + ready-to-paste paragraph:
Rolando's `FAIRNESS_LIMITATION.md` (on the team Drive).

## 9. Explainability — Grad-CAM 🟡 (wired to the real model; evidence pending)

**Done (Ali + Varsha):** Grad-CAM overlay renders in the Streamlit app for every prediction,
now computed on the **trained model's own weights** (PR #43) rather than the earlier random-weight
placeholder. The heatmap targets the model's last conv layer (`BasicCNN.gradcam_target_layer`, or
`layer4[-1]` for a ResNet backbone) and is best-effort — a heatmap failure never blocks the
prediction. Before a checkpoint exists the app still shows a clearly-labelled illustrative overlay.

**Pending (Temirlan):** collect the evidence set for the report — correct examples, failure
examples, and misleading heatmaps. IoU/localization scoring only if valid masks/boxes/proxy
regions exist; otherwise document qualitatively.

## 10. Interpretation of results 🟡

**What the numbers mean for a *screening* tool.** The right lens is not raw accuracy but *which
errors happen and how costly each is* (§7.1):
- **"Safe" errors** — flagging clear skin as a condition (false alarm). The tool then says "get it
  checked," which is the conservative, low-harm direction for screening.
- **Concerning errors** — telling someone with a condition they're **clear** (false reassurance),
  which could delay care. These are the errors we most want to drive down, and why the product
  **never gives an all-clear** and always routes to a professional.
- **Adjacent-condition mix-ups** (acne↔redness↔rosacea) matter less for the core "should I get
  this looked at?" decision than clear-vs-not does, though they matter for the *education* value.

**Would we trust the Basic CNN?** No — and we say so. At macro-F1 0.35 it's below the majority
baseline and would mislead users; it exists to prove the pipeline and set the floor. The product
decision is to ship **only** a model that clears the up-front bar (macro-F1 ≥ 0.60, per-class
recall ≥ 0.50) **and** holds the fairness gap — which is why selection waits on the pretrained
runs (§7.2). Until then the app shows the low-confidence warning honestly.

**Real-world constraints to state plainly:** the **source confound** (§1.1) means test numbers may
be optimistic vs. real single-source photos; **dark-skin coverage is thin** (§8), so we don't claim
equal performance there; and severity is **out of scope** in v1.

## 11. Hardware & memory 🟡

**Training environment:** Apple **M5** (10-core), **24 GB** RAM, macOS. Training ran on **CPU** —
the notebook selects `cuda` if present else CPU, and there is **no CUDA GPU** on this machine (MPS
is available but not used by the current loop, a noted future optimisation). This is a deliberate
point: the whole pipeline is **laptop-trainable**, no cloud GPU required.

**Footprint & time:** batch size 32 at 224×224 keeps memory well within 24 GB. The from-scratch
**Basic CNN** (≈1M params) trains its 20 epochs in **minutes** on CPU; the pretrained backbones
(**ResNet50** ≈25M, **VGG16** ≈138M params) are heavier and take correspondingly longer — exact
wall-clock per run to be recorded by Iva/Varsha and tabulated here.

**Reproducibility:** fixed **seed 42**, a **frozen** test split never tuned on, a versioned data
manifest, and shared config/metrics so every model is trained and scored identically.

## 12. Next steps ⬜ (to finalize)

**Immediate timeline (Sprint 4 → submission):**
- **Presentation practice:** Tue 28 or Wed 29 Jul, 5 pm.
- **Record presentation:** Thu 30 Jul (time TBD).
- **Report submission:** Fri 31 Jul.

**Future work (report continuations):** concrete, prioritized continuations (e.g., larger/curated
data, severity validation against a rubric, clinician feedback) — not just "collect more data."

## 13. Lessons learned 🟡 (in progress)

Process lessons so far:
- **Data was the critical path — and we under-estimated it.** Dead Fitzpatrick URLs + licensing
  cost us roughly a sprint and gated everything downstream (§0.3). What worked: an **interim
  MD5-matched mirror** to unblock training while the official access came through, and treating data
  acquisition as a first-class workstream, not a prerequisite assumed "done."
- **Baseline first pays off.** The deliberately-weak from-scratch CNN wasn't wasted effort — it
  **told us the bottleneck is data/representation, not tuning**, which justified moving to transfer
  learning with evidence instead of assumption.
- **Decide from the data.** Severity de-scope, fairness-by-bands, and not-face-filtering were all
  settled by **counting the data**, not by opinion — and documented as honest limitations.
- **Competence can *expose* a fairness gap, not just create one.** Our weakest model "passed" the
  fairness check by being **evenly bad**; our best model revealed a **0.25 dark-skin gap**. A single
  headline metric hides *who* a model works for — measuring per skin-tone band from the outset is
  what caught it. Root cause was **data coverage** (few dark-skin images), so we report it as a
  **headline limitation with a remediation plan**, not a footnote — the most important thing we
  learned.
- **Scope discipline** — grew from 5 → 7 members by pairing newcomers into existing workstreams rather than adding features.
- **CI-gated workflow** — self-merge once `ruff` + `pytest` pass keeps a 7-person team moving without review bottlenecks.
- **Model choice** — resisting the "use the fanciest model (YOLO)" pull in favour of the task-appropriate one (classification + Grad-CAM); YOLO was **evaluated on paper and rejected, never trained**.

*Per-person + team reflections to be completed at the end.*

## 14. Individual contributions 🟡 (running log — finalize at submission)

| Member | Contributions so far |
|---|---|
| Hessam (Product Lead) | Scope, disclaimer/ethics framing, Day-1 setup report, coordination; report editing |
| Iva (ML Research) | Backbone decision (ResNet50), severity method (concept-derived proxy), metrics implementation + tests; **trains the ResNet50 model**; report editing |
| Aparna + Rolando (Data) | Data acquisition + Sprint-2 cleaning: harmonized manifest, dedup + skin-type validation (1,614→1,558), weighted-loss imbalance handling, frozen splits (≤1pt drift), erythema-safe augmentation, QA + fairness-coverage findings; official Fitzpatrick provenance (Aparna) |
| Varsha (MLOps) | Training/MLOps infrastructure (loop, checkpointing, CI); **trains the VGG16 model** (grid search); HF Spaces deploy |
| Temirlan (Eval & Explainability) | Evaluation + failure-analysis support; Grad-CAM evidence set; metrics test support *(not a model trainer)* |
| Ali (UI/UX) | Streamlit app (upload/consent/disclaimer/UI states), Grad-CAM overlay display; **trains the Basic CNN baseline + wrote its eval report**; **wired real inference + Grad-CAM into the app**; standups/sprint tracking; severity-decision write-up |

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
- **2026-07-27 — Official Fitzpatrick17k provenance:** Aparna secured the dataset via the authors' official access form (M. Groh). We cite the official copy (not the Kaggle mirror) — the two are byte-identical (MD5-keyed), so **no retraining**. License requires deleting the images at project end (compliance to-do). Provenance recorded in `docs/PROVENANCE.md` (Rolando).
- **2026-07-17 — Framework = PyTorch:** team unified on PyTorch (the whole stack was already PyTorch; Varsha porting her Keras baseline over) to avoid a split model/dataloader stack.
- **2026-07-18 — Sprint-2 data cleaning done (Rolando + Aparna):** 1,614 → 1,558 rows (dropped unknown skin type + perceptual duplicates); class imbalance via **weighted loss** (`class_weights.json`, not oversampling); test set re-frozen with ≤1pt drift; erythema-safe train-only augmentation. See §2.
- **2026-07-18 — Fairness reporting = skin-tone bands:** report I-II / III-IV / V-VI as primary (per-type shown with sample sizes) because type-VI coverage is too thin for per-type metrics. See §8.
- **2026-07-18 — Faces (⏳ pending Iva's sign-off):** QA found ~81% of images have no *detectable* face (Fitzpatrick17k spans all body sites). Direction: **do not hard-filter** to faces (would shrink to ~293 images and drop valid facial close-ups the detector misses); instead train on the full cleaned set, tag the face flag, and report the body-site-vs-face mismatch as a **limitation**. Iva (ML lead) to confirm.
- **2026-07-21 — Severity de-scoped for v1:** the cleaned data has only **6 "severe" / 29 "mild"** labels (~16% of images labelled at all), too sparse to train a reliable severity classifier. v1 ships **condition-only**; concept-derived proxy documented as future work. App shows "Severity: Not assessed." Provisional call by Ali; Iva informed (reversible). Closes the severity part of #1 / requirement F3.

### Sprint 2, Standup 1 — 20 July 2026 (full notes: [standups/2026-07-20-sprint2-standup1.md](standups/2026-07-20-sprint2-standup1.md))
- **Training kicked off** (Varsha — critical path; full data pipeline now merged). May slip a day (other project first).
- **3-person pairing dropped** on #20 → each of Varsha / Iva / Temirlan trains one model; **compare baseline CNN vs ResNet50 vs VGG16**, consolidate metrics.
- **Report:** drafted from the repo, Iva + Hessam humanise. **Video** recorded Friday.
- Absent: Hessam.

### Sprint 4, Standup 1 — 27 July 2026 (full notes: [standups/2026-07-27-sprint4-standup1.md](standups/2026-07-27-sprint4-standup1.md))
- **Now formally in Sprint 4.** Model-training owners confirmed: **Ali, Varsha, Iva** (Temirlan is Eval & Explainability, not a trainer). Rolando / Aparna / Temirlan have no open tasks this sprint (data + pipeline complete).
- **Report pipeline:** drafted from the repo, then **Hessam + Iva** edit.
- **Schedule:** practice Tue 28 / Wed 29 Jul 5 pm · record Thu 30 Jul · **submit Fri 31 Jul**.
- **Status:** Ali's CNN done; Varsha's VGG16 trained (numbers pending frozen-test re-score); Iva's model in progress.
