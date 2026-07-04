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

| Metric | Overall | By skin type (I–VI) |
|---|---|---|
| Accuracy | _tbd_ | _tbd_ |
| Macro-F1 | _tbd_ | _tbd_ |

## Limitations & biases
- Data skew, approximate severity labels, no clinical validation, sensitivity to lighting/quality.

## Ethical considerations
- See [ethics-and-disclaimer.md](ethics-and-disclaimer.md).
