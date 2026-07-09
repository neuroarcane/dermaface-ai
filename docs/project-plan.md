# Project Plan - 3-Week Sprint

Roles referenced by number - see [team-roles.md](team-roles.md).

## Guiding Constraints

- **3 weeks, hard stop.** Ship something demoable over something perfect.
- **Screening/education framing** is non-negotiable and shapes every UI/report
  decision.
- **Severity labeling is the #1 risk.** If it is not decided by end of Week 1,
  de-scope severity to a stretch goal and ship condition classification.
- **No scope expansion from team growth.** Rolando and Temirlan pair into the
  heaviest existing workstreams; they do not create new must-have features.
- **IoU is conditional.** Use IoU/localization scoring only if masks, bounding
  boxes, or defensible proxy regions exist. Otherwise, evaluate Grad-CAM
  qualitatively.

---

## Week 1 - Foundation & Data

| Owner | Tasks |
|---|---|
| #1 Hessam | Lock scope; write one-page product spec; finalize disclaimer/ethics language; create GitHub issues and Friday demo agenda |
| #3 Aparna + #6 Rolando | Acquire datasets or document access blockers; record provenance/licensing; run initial EDA; start manifest and data-quality checks |
| #2 Iva + #7 Temirlan | Choose backbone; define severity/condition label scheme; implement and test core metrics on toy inputs |
| #4 Varsha + #7 Temirlan | Stand up training loop design; validate expected model outputs for inference; prepare checkpoint/tracking plan |
| #5 Ali | Keep app skeleton runnable; polish upload, consent, disclaimer, and placeholder result flow |

**Friday milestone:** scope is locked, data path is known, first manifest slice is
loading or blockers are explicit, metrics are tested, and the app accepts a
photo with clear placeholder labeling.

## Week 2 - Modeling & Integration

| Owner | Tasks |
|---|---|
| #3 Aparna + #6 Rolando | Finalize cleaned manifest; validate class/skin-type fields; handle class imbalance; freeze a clean test set |
| #2 Iva + #4 Varsha + #7 Temirlan | Run real training experiments; iterate architecture/metrics; log fairness by skin tone; confirm model output contract |
| #4 Varsha + #7 Temirlan | Make Grad-CAM work on real predictions; save checkpoint; support inference loading |
| #5 Ali + #4 Varsha | Wire real model into Streamlit; render Grad-CAM overlay; keep placeholder mode safe when no checkpoint exists |
| #1 Hessam | Draft pitch/report outline; collect demo screenshots; keep scope under control |

**Friday milestone:** end-to-end demo - upload -> prediction + severity status +
Grad-CAM overlay. Accuracy can be rough, but the path must be real.

## Week 3 - Harden, Evaluate & Ship

| Owner | Tasks |
|---|---|
| #2 Iva + #7 Temirlan | Final evaluation: confusion matrix, target-vs-actual metrics, fairness analysis, error analysis, honest limitations |
| #4 Varsha | Deploy to HF Spaces; freeze model; verify reproducibility and checkpoint loading |
| #5 Ali | UX polish; disclaimers front-and-center; edge cases for no face, bad photo, and low confidence |
| #3 Aparna + #6 Rolando | Document data provenance, preprocessing, limitations, and class/skin-tone balance |
| #1 Hessam | Final report, pitch deck, demo rehearsal, and stakeholder-ready narrative |

**Friday milestone:** deployed or locally demoable app, written report, model card
filled, failure cases prepared, and presentation rehearsed.

---

## Milestone Checklist

- [ ] W1: Product spec merged, disclaimer final, and GitHub issues created
- [ ] W1: Data access/provenance documented; first manifest slice created
- [ ] W1: Severity-labeling decision made or explicitly de-scoped
- [ ] W1: Metrics functions pass toy-input tests
- [ ] W2: Data cleaned and split; class/skin-tone balance reviewed
- [ ] W2: Baseline model trains and saves a checkpoint
- [ ] W2: End-to-end demo with Grad-CAM overlay
- [ ] W2: Fairness-by-skin-tone metrics logged
- [ ] W3: Deployed or locally reproducible demo complete
- [ ] W3: Report, model card, failure cases, deck, and rehearsal done

## Risks

| Risk | Mitigation |
|---|---|
| Severity labels do not exist in datasets | Iva decides method by Week 1; fall back to condition-only |
| Dataset access/licensing delays | Aparna starts Day 1; Rolando documents blockers and provenance |
| Class imbalance, especially rosacea | Weighted loss, augmentation, class-aware sampling, or class merge discussion |
| Skin-tone bias | Stratified splits and per-Fitzpatrick metrics; report gaps honestly |
| Grad-CAM localization lacks masks for IoU | Temirlan documents qualitative localization instead of forcing invalid IoU |
| Scope creep | Hessam guards scope; added members pair into existing workstreams only |
