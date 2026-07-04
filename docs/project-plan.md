# Project Plan — 3-Week Sprint

Roles referenced by number — see [team-roles.md](team-roles.md).

## Guiding constraints

- **3 weeks, hard stop.** Ship something demoable over something perfect.
- **Screening/education framing** is non-negotiable and shapes every UI/report decision.
- **Severity labeling is the #1 risk.** If it isn't decided by end of Week 1, de-scope severity to a stretch goal and ship condition classification.

---

## Week 1 — Foundation & Data  *(get to a baseline)*

| Owner | Tasks |
|---|---|
| #1 | Lock scope; write one-page product spec; draft disclaimer/ethics language |
| #3 | Acquire all 3 datasets; EDA; dedup; first cleaned split |
| #2 | Choose backbone; **define the severity/condition label scheme** |
| #4 | Stand up training repo + experiment tracking; "hello world" model trains end-to-end on a slice |
| #5 | App skeleton: image upload + placeholder output |

**Friday milestone:** data pipeline runs, a dumb model trains, app accepts a photo.

## Week 2 — Modeling & Integration  *(get it working)*

| Owner | Tasks |
|---|---|
| #2 + #4 | Real training runs; iterate architecture/metrics; log fairness by skin tone |
| #4 | Grad-CAM working on real predictions |
| #3 | Finalize splits; handle class imbalance; freeze a clean test set |
| #5 | Wire real model into app; render Grad-CAM overlay |
| #1 | Draft pitch/report outline; collect demo screenshots |

**Friday milestone:** end-to-end demo — upload → prediction + severity + Grad-CAM overlay (accuracy can be rough).

## Week 3 — Harden, Evaluate & Ship  *(make it presentable)*

| Owner | Tasks |
|---|---|
| #2 | Final evaluation: confusion matrices, fairness analysis, honest limitations |
| #4 | Deploy to HF Spaces; freeze model; reproducibility check |
| #5 | UX polish; disclaimers front-and-center; edge cases (no face / bad photo) |
| #3 | Document data provenance & licenses |
| #1 | Final report + pitch deck + demo rehearsal |

**Friday milestone:** deployed app, written report, rehearsed presentation.

---

## Milestone checklist

- [ ] W1: Data cleaned & split, baseline model trains, app skeleton accepts upload
- [ ] W1: Severity-labeling decision made (or explicitly de-scoped)
- [ ] W2: End-to-end demo with Grad-CAM overlay
- [ ] W2: Fairness-by-skin-tone logged
- [ ] W3: Deployed to HF Spaces
- [ ] W3: Report + deck + rehearsal done

## Risks

| Risk | Mitigation |
|---|---|
| Severity labels don't exist in datasets | Decide method W1; fall back to condition-only |
| Class imbalance (rosacea rare) | Weighted loss / augmentation / merge rare classes |
| Skin-tone bias | Stratified eval; report per-Fitzpatrick metrics |
| Scope creep | #1 guards scope; stretch goals labeled as such |
| Dataset access/licensing delays | #3 starts downloads Day 1 |
