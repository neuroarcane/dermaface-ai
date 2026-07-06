# Report Writing Guide

Our final report is judged on **depth of analysis**, not just whether each
section exists. The difference between a summary and a final report is *why*,
*what else*, *what went wrong*, and *what it means*. Apply the five depth checks
below to **every** section you write.

## The five depth checks

For anything you write, don't stop at *what* you did — also answer:

1. **Why** — why this dataset / model / hyperparameter / metric? Justify the choice.
2. **Alternatives** — what else did you consider, and why did you reject it?
3. **Challenges** — what was hard, surprising, or broke, and how did you handle it?
4. **Meaning** — what does this mean in the real-world context (screening a face photo for skin conditions — *not* diagnosis)?
5. **Failures** — where does it fail? Limitations, error patterns, edge cases.

> A line like *"We used ResNet50 and got 0.62 macro-F1"* fails all five checks.
>
> *"We chose ResNet50 over ResNet18 and EfficientNet-B0 because …; the main
> challenge was class imbalance (rosacea ≈ X% of samples), handled via …;
> 0.62 macro-F1 means the tool would correctly flag roughly … in a screening
> setting; it fails most on … "* passes them.

## Section-by-section

| # | Section | Owner | Baseline content | Depth to add |
|---|---|---|---|---|
| 1 | Problem & framing | Hessam | What it does; screening, not diagnosis | Why it matters, who benefits, real-world constraints, ethical stakes |
| 2 | Dataset details | Aparna | Links, EDA plots, class & skin-tone distributions | Why these 3 datasets, their known biases, licensing, what's missing, how skew will affect results |
| 3 | Preprocessing | Aparna | Normalization, dedup, splits, augmentation | Why each step; what you tried that didn't help; why color aug is kept mild (erythema signal) |
| 4 | Model | Iva | Backbone, transfer learning, head | Why this backbone vs. alternatives; freezing strategy; why pretrained over from-scratch |
| 5 | Hyperparameter tuning | Iva / Varsha | Search space + best config | What ranges you swept, what mattered most, what surprised you |
| 6 | Training / validation | Varsha | Loss & accuracy curves | Signs of over/underfitting, what the curves tell you, interventions you made |
| 7 | Prediction & evaluation | Iva | Metrics, confusion matrix, target-vs-actual | Interpret *each* metric; per-class reading; why each target was met or missed |
| 8 | Fairness analysis | Iva | Per-skin-tone metrics | Where the gaps are, likely causes, what it means for deployment, honest even if unflattering |
| 9 | Explainability (Grad-CAM) | Varsha / Ali | Overlay examples | Do heatmaps focus on skin? Show cases where they don't and what that reveals |
| 10 | Error analysis & failure cases | Iva | Misclassified examples | Patterns (which conditions get confused, which lighting/skin tones fail) + hypotheses why |
| 11 | Interpretation / real-world meaning | Hessam / Iva | What the results mean | Usefulness as a screening tool, risks, whether you'd trust it and why |
| 12 | Hardware / memory | Varsha | GPU/CPU, memory, training time | — |
| 13 | Next steps | Team | Concrete continuations | Specific, prioritized — not "collect more data" |
| 14 | Lessons learned | Team | Honest reflection | Per person + as a team; what you'd do differently |
| 15 | Individual contributions | All | Who did what | Specific and accurate |

## Report-readiness checklist

- [ ] Every major model / data / metric choice is **justified** (the "why")
- [ ] At least one **alternative** discussed per major decision
- [ ] **Challenges** and how you solved them are documented
- [ ] A dedicated **failure-cases / error-analysis** section with concrete examples
- [ ] **Limitations** stated honestly (data skew, approximate severity labels, no clinical validation)
- [ ] Results **interpreted in the screening / real-world context**, not just numbers
- [ ] **Fairness** gaps reported even if unflattering
- [ ] **Target-vs-actual** table filled in, each row with a one-line interpretation
- [ ] **Individual contributions** table complete
- [ ] Notebook exported to **PDF**; both uploaded to D2L
