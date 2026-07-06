# Requirements & Success Criteria

These are the targets the team commits to **before** modelling. The final report
evaluates actual results against them (see [model-card.md](model-card.md)) — a
target we miss is a valid result as long as we set it up front and analyse the
gap. Numbers are owned by Iva (ML Research Lead) and may be revised once a
baseline exists; any change is recorded here with a note.

> Status legend: ✅ met · 🟡 in progress · ⬜ not started

## 1. Functional requirements (must-do)

| # | Requirement | Target | How measured | Status |
|---|---|---|---|---|
| F1 | Classify condition | Predicts one of acne / rosacea / redness / clear from a face photo | App demo + test-set metrics | 🟡 |
| F2 | Localize affected regions | Grad-CAM overlay accompanies every prediction | Qualitative review of overlays | ✅ |
| F3 | Severity estimate | Coarse band (mild / moderate / severe) **or** a documented decision to de-scope | Iva's Week-1 methodology decision | ⬜ |
| F4 | Screening/education framing | Disclaimer shown before and alongside every result; no diagnostic language | UI review vs. ethics checklist | ✅ |

## 2. Performance targets (frozen test set)

| # | Metric | Target | Rationale |
|---|---|---|---|
| P1 | Beat majority-class baseline | Required | Sanity floor — model must learn something |
| P2 | Macro-F1 (4-class) | ≥ 0.60 | Averages over classes so rare ones (rosacea) count |
| P3 | Per-class recall | ≥ 0.50 for every class | Guards against a class being ignored |
| P4 | Severity within-1-band accuracy *(if F3 in scope)* | ≥ 0.70 | Coarse but decision-useful |

## 3. Fairness target

| # | Metric | Target |
|---|---|---|
| Fa1 | Macro-F1 gap across Fitzpatrick skin-tone groups | ≤ 0.15 — **and reported even if larger** |

Skin-tone-stratified evaluation is a core requirement, not an afterthought. If
the gap exceeds target, the report states it plainly and discusses causes
(data skew, sample sizes) rather than hiding it.

## 4. Explainability target

| # | Requirement | Target |
|---|---|---|
| E1 | Grad-CAM coverage | Heatmap available for every prediction |
| E2 | Heatmap plausibility | On correctly-classified examples, activation concentrates on skin/lesion regions (qualitative) |

## 5. Non-functional & deliverable requirements

| # | Requirement | Target |
|---|---|---|
| N1 | Reproducibility | Fixed seeds; training re-runnable from the repo; test set frozen before modelling |
| N2 | Framework | Python + Keras / PyTorch / TensorFlow |
| N3 | Notebook deliverable | Jupyter notebook (code + descriptions + end-of-notebook summary report incl. each member's contribution) **and** a PDF export |
| N4 | Report contents | Dataset link + EDA plots, preprocessing, model (pretrained + fine-tune), training/validation curves, prediction, evaluation, interpretation, hardware/memory used, next steps, lessons learned |
| N5 | Privacy | No user images stored; no PII/patient-identifying data in repo or demo |
| N6 | Analytical depth | Every section justifies choices (why), notes alternatives & challenges, and interprets results in the screening context; includes a dedicated **failure-cases / error-analysis** section. See [report-guide.md](report-guide.md) |

## How we gauge performance

For each target above, the [model card](model-card.md) reports **Target vs.
Actual** and a one-line interpretation. The presentation leads with this table —
it is the clearest evidence that the project was scoped and measured
deliberately.
