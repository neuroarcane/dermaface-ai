# Model Card — DermaFace AI v1

## Model details
- **Name / version:** DermaFace AI v1 — facial skin-condition screening classifier
- **Architecture / backbone:** **VGG16** (ImageNet-pretrained, fine-tuned), selected from a
  three-model bake-off (see *Model selection* below).
- **Owner:** Varsha (MLOps, trained the selected model) · Iva (ML Research, metrics + ResNet50)
- **Date:** 2026-07-27
- **Task:** 4-class condition classification (acne / rosacea / redness / clear). **Severity
  de-scoped for v1** (too few labelled examples — 6 "severe" / 29 "mild"; see
  [severity-decision.md](severity-decision.md)); concept-derived proxy is future work.
- **Explainability:** Grad-CAM overlay on every prediction.

## Model selection — how we got here (a bake-off, not a guess)
We trained **three** models on the *same* data, splits, and metrics, then picked the best. The
progression is the point:

| Model | Macro-F1 | Beats baseline? | Passes P3? | Fairness gap | Outcome |
|---|---|---|---|---|---|
| Basic CNN (from scratch) | 0.35 | ✗ | ✗ | 0.064 | Baseline — fails; shows data is the bottleneck |
| ResNet50 (transfer) | 0.67 | ✅ | ✗ (acne 0.48) | 0.252 | Strong, but misses a recall target and is unfair |
| **VGG16 (transfer)** | **0.727** | ✅ | ✅ | **0.281** | **Selected** — best overall; fairness gap noted |

*Why VGG16:* highest macro-F1 and accuracy on the frozen test set, and the **only model to meet
every per-class recall target (P3)**. The from-scratch CNN existed to prove how far raw architecture
gets on ~1,000 images (not far) — justifying transfer learning with evidence. See report §7.

## Intended use
- **Primary:** Educational / screening demo. Helps a non-expert decide whether to seek care.
- **Out of scope:** Diagnosis, treatment decisions, any clinical use. Every screen ends in "see a
  professional."

## Training data
- **Sources:** Fitzpatrick17k (official access-form copy), SKINCON, Google SCIN. See
  [data-strategy.md](data-strategy.md) / PROVENANCE.md.
- **Cleaned set:** 1,558 images; stratified frozen splits (train 1,085 / eval 238 / test 158),
  seed 42.
- **Imbalance:** class-weighted loss (not resampling). **Severity labeling:** de-scoped v1.

## Evaluation (selected model — VGG16, frozen test set n = 158)

### Target vs. Actual

| Requirement | Target | Actual | Met? | Interpretation |
|---|---|---|---|---|
| P1 Beat majority baseline | Required | 0.74 vs 0.40 | ✅ | Comfortably beats "always predict acne" |
| P2 Macro-F1 (4-class) | ≥ 0.60 | **0.727** | ✅ | Good balanced performance across classes |
| P3 Per-class recall | ≥ 0.50 each | 0.76 / 0.68 / 0.67 / 0.88 | ✅ | Only model of the three to pass every class |
| P4 Severity within-1-band | ≥ 0.70 | — | n/a | Severity de-scoped for v1 |
| Fa1 Macro-F1 gap across skin tones | ≤ 0.15 | **0.281** | ❌ | **Fails** — weakest on darkest skin (see below) |

### Per-class results (VGG16)

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| acne | 0.76 | 0.76 | 0.76 | 63 |
| rosacea | 0.60 | 0.68 | 0.64 | 22 |
| redness | 0.89 | 0.67 | 0.76 | 48 |
| clear | 0.65 | 0.88 | 0.75 | 25 |

### By Fitzpatrick skin-tone band (fairness — primary view)

| Skin-tone band | Test support | Accuracy | Macro-F1 |
|---|---|---|---|
| I–II | 81 | 0.765 | 0.769 |
| III–IV | 61 | 0.738 | 0.707 |
| V–VI | 16 | 0.625 | **0.487** |

**Gap = 0.281 (fails Fa1 ≤ 0.15).** And note the trend across the bake-off: the gap **grew as the
models improved** (CNN 0.064 → ResNet50 0.252 → VGG16 0.281) — our best model is the least fair,
because its gains concentrated on the well-represented lighter-skin bands.

> **Limitation:** type VI = 1.9% of the dataset; darkest-skin metrics rest on only 16 test images.
> The skew originates in the source datasets, **not** our (stratified, ≤1pt drift) sampling.

### Error analysis & failure cases (VGG16)
- **Most common confusions:** acne→clear (8) and redness→acne (8); acne→rosacea (5). Balanced,
  sensible errors — no class collapse (unlike the CNN, where acne recall was 0.06).
- **Worst-performing subgroup:** **V–VI skin tones** — macro-F1 0.487 vs 0.769 on I–II (a 0.28 gap).
- **Representative failure examples:** FP/FN plates + Grad-CAM in the final report notebook
  (generated locally; not committed — Fitzpatrick license).
- **Hypothesized causes:** (1) **data-coverage skew** on dark skin; (2) the **`clear`=SCIN source
  confound** (all `clear` images are SCIN consumer photos), which flatters `clear` recall.
- **What this means for screening:** the design fails *safe* — it never issues an all-clear and
  always defers to a professional; the **fairness gap is the key real-world caveat**, reported up
  front with a remediation plan (more dark-skin data / DDI).

## Limitations & biases
- **Fairness gap on dark skin** (headline limitation) — data-coverage driven.
- **Source confound** (`clear` = SCIN only) may inflate `clear` performance and hurt transfer to
  single-source deployment photos.
- Approximate/absent severity labels; no clinical validation; sensitivity to lighting/quality.

## Ethical considerations
- Screening & education only, not diagnosis. See [ethics-and-disclaimer.md](ethics-and-disclaimer.md).
