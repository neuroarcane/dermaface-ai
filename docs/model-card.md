# Model Card — DermaFace AI (template)

> Fill in as the model is built. A model card is expected in the final deliverable.

## Model details
- **Name / version:**
- **Owner:** #2 Chief Scientist
- **Date:**
- **Architecture / backbone:**
- **Task:** Multi-class condition classification (acne / rosacea / redness / clear) + coarse severity band
- **Explainability:** Grad-CAM

## Intended use
- **Primary:** Educational / screening demo for a course project.
- **Out of scope:** Diagnosis, treatment decisions, any clinical use.

## Training data
- **Sources:** Fitzpatrick17k, SKINCON, Google SCIN (see [data-strategy.md](data-strategy.md))
- **Splits:** stratified by class and Fitzpatrick type
- **Severity labeling method:**

## Evaluation
- **Metrics:** accuracy, macro-F1, per-class precision/recall, confusion matrix
- **Fairness:** metrics stratified by Fitzpatrick skin type
- **Test set:** frozen before modeling

### Target vs. Actual

Targets are set up front in [requirements.md](requirements.md). Fill Actual +
Interpretation after the frozen-test-set run.

| Requirement | Target | Actual | Met? | Interpretation |
|---|---|---|---|---|
| P1 Beat majority baseline | Required | _tbd_ | _tbd_ | |
| P2 Macro-F1 (4-class) | ≥ 0.60 | _tbd_ | _tbd_ | |
| P3 Per-class recall | ≥ 0.50 each | _tbd_ | _tbd_ | |
| P4 Severity within-1-band *(if in scope)* | ≥ 0.70 | _tbd_ | _tbd_ | |
| Fa1 Macro-F1 gap across skin tones | ≤ 0.15 | _tbd_ | _tbd_ | |

### Per-class results

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| acne | _tbd_ | _tbd_ | _tbd_ | _tbd_ |
| rosacea | _tbd_ | _tbd_ | _tbd_ | _tbd_ |
| redness | _tbd_ | _tbd_ | _tbd_ | _tbd_ |
| clear | _tbd_ | _tbd_ | _tbd_ | _tbd_ |

### By Fitzpatrick skin type (fairness)

| Skin type | Accuracy | Macro-F1 | Support |
|---|---|---|---|
| I–II | _tbd_ | _tbd_ | _tbd_ |
| III–IV | _tbd_ | _tbd_ | _tbd_ |
| V–VI | _tbd_ | _tbd_ | _tbd_ |

## Limitations & biases
- Data skew, approximate severity labels, no clinical validation, sensitivity to lighting/quality.

## Ethical considerations
- See [ethics-and-disclaimer.md](ethics-and-disclaimer.md).
