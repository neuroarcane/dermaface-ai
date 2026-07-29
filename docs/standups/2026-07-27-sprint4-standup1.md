# DermaFace AI — Sprint 4, Standup 1

> **Project:** DermaFace AI — *not* the Dental Cavity Detector.
> Project-related notes only; personal chat and other-course scheduling omitted.

**Date:** 27 July 2026 (Monday)
**Type:** Standup (first of Sprint 4)
**Attendance:** not recorded in the minutes; the task allocation below covers the whole team.

## Task allocation
- **Model training:** **Ali, Varsha, Iva** each train a model (three-model bake-off — pick the best on a common metric set).
- **Report:** drafted from the repo, then **Hessam + Iva** edit for natural language.
- **Rolando, Aparna, Temirlan:** **no open tasks this sprint** — data acquisition + pipeline work is complete. ("Please chill.")

## Schedule (to submission)
- **Presentation practice:** Tue 28 or Wed 29 July, 5:00 pm.
- **Record presentation:** Thu 30 July (time TBD).
- **Report submission:** Fri 31 July.

## Decisions
1. Team is **formally in Sprint 4**.
2. **Model-training owners = Ali, Varsha, Iva** (Temirlan not a trainer — he's Eval & Explainability).
3. **Report editing pipeline:** drafted from the repo, then Hessam + Iva humanise/edit.

## Status going in
- **Ali** — Basic CNN done (eval report written; real inference + Grad-CAM wired into the app, merged).
- **Varsha** — VGG16 trained (grid-searched; numbers pending a **frozen-test** re-score before they enter the comparison table).
- **Iva** — model in progress (SCIN data now unblocked via the Team Drive copy).

## Next steps
- **Varsha:** confirm the VGG numbers on the frozen test set (`dermaface.training.metrics`); share the checkpoint for the app.
- **Iva:** finish training; run the evaluation + failure analysis.
- **Ali:** consolidate the three models' metrics once in; keep the report draft current; swap the app to the winning checkpoint.
- **Hessam + Iva:** edit the report ahead of Friday's submission.
