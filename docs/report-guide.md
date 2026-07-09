# Report Writing Guide

Our final report is judged on **depth of analysis**, not just whether each
section exists. The difference between a summary and a final report is *why*,
*what else*, *what went wrong*, and *what it means*. Apply the five depth checks
below to **every** section you write.

## The Five Depth Checks

For anything you write, do not stop at *what* you did. Also answer:

1. **Why** - why this dataset / model / hyperparameter / metric? Justify the
   choice.
2. **Alternatives** - what else did you consider, and why did you reject it?
3. **Challenges** - what was hard, surprising, or broke, and how did you handle
   it?
4. **Meaning** - what does this mean in the real-world context of screening a
   face photo for skin conditions, not diagnosis?
5. **Failures** - where does it fail? Limitations, error patterns, edge cases.

> A line like *"We used ResNet50 and got 0.62 macro-F1"* fails all five checks.
>
> A stronger version explains why ResNet50 was chosen over alternatives, how
> class imbalance affected results, what the metric means in a screening
> context, and where the model fails.

## Section-by-Section

| # | Section | Owner | Baseline content | Depth to add |
|---|---|---|---|---|
| 1 | Problem & framing | Hessam | What it does; screening, not diagnosis | Why it matters, who benefits, real-world constraints, ethical stakes |
| 2 | Dataset details | Aparna / Rolando | Links, EDA plots, class & skin-tone distributions | Why these datasets, their known biases, licensing, what is missing, how skew affects results |
| 3 | Preprocessing | Aparna / Rolando | Normalization, dedup, splits, augmentation, manifest QA | Why each step; what did not help; why color augmentation stays mild |
| 4 | Model | Iva | Backbone, transfer learning, head | Why this backbone vs. alternatives; freezing strategy; why pretrained over from-scratch |
| 5 | Hyperparameter tuning | Iva / Varsha / Temirlan | Search space + best config | What ranges you swept, what mattered most, what surprised you |
| 6 | Training / validation | Varsha / Temirlan | Loss & accuracy curves | Signs of over/underfitting, what the curves tell you, interventions you made |
| 7 | Prediction & evaluation | Iva / Temirlan | Metrics, confusion matrix, target-vs-actual | Interpret each metric; per-class reading; why each target was met or missed |
| 8 | Fairness analysis | Iva / Temirlan | Per-skin-tone metrics | Where gaps are, likely causes, what it means for deployment, honest even if unflattering |
| 9 | Explainability (Grad-CAM) | Varsha / Ali / Temirlan | Overlay examples; IoU/localization note if annotations exist | Do heatmaps focus on skin? Show cases where they do not and what that reveals |
| 10 | Error analysis & failure cases | Iva / Temirlan | Misclassified examples | Patterns, lighting/skin-tone issues, likely causes, and screening implications |
| 11 | Interpretation / real-world meaning | Hessam / Iva | What the results mean | Usefulness as a screening tool, risks, whether you would trust it and why |
| 12 | Hardware / memory | Varsha | GPU/CPU, memory, training time | Record setup, constraints, and reproducibility notes |
| 13 | Next steps | Team | Concrete continuations | Specific, prioritized steps - not just "collect more data" |
| 14 | Lessons learned | Team | Honest reflection | Per person + as a team; what you would do differently |
| 15 | Individual contributions | All | Who did what | Specific and accurate |

## Report-Readiness Checklist

- [ ] Every major model / data / metric choice is **justified**.
- [ ] At least one **alternative** is discussed per major decision.
- [ ] **Challenges** and how you solved them are documented.
- [ ] A dedicated **failure-cases / error-analysis** section includes concrete
  examples.
- [ ] **Limitations** are stated honestly: data skew, approximate severity
  labels, no clinical validation.
- [ ] Results are **interpreted in the screening / real-world context**, not just
  reported as numbers.
- [ ] **Fairness** gaps are reported even if unflattering.
- [ ] **IoU/localization** is discussed only if valid annotations or defensible
  proxy regions exist.
- [ ] **Target-vs-actual** table is filled in, each row with a one-line
  interpretation.
- [ ] **Individual contributions** table is complete.
- [ ] Notebook is exported to **PDF**; both notebook and PDF are uploaded to D2L.
