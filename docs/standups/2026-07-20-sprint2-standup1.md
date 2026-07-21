# DermaFace AI — Sprint 2, Standup 1

> **Project:** DermaFace AI (mathematics / Deep Learning course) — *not* the Dental Cavity Detector.
> Project-related notes only; personal chat and other-course scheduling omitted.

**Date:** 20 July 2026
**Type:** Standup (first of Sprint 2)
**Present:** Ali, Iva, Varsha, Temirlan, Rolando
**Absent:** Hessam

## Round-table updates

**Varsha — MLOps (#5 training loop / checkpoint / tracking)** — *critical path*
- Data is done (Rolando confirmed) — **starting training today**. Finishing the other project first, so DermaFace training may slip to tomorrow. In progress.

**#20 — Real training runs + fairness logging (Iva + Temirlan + Varsha)**
- **Pairing dropped:** the 3-person pairing hasn't worked under time pressure — the team will split the work instead.
- **Plan: each person trains one model, then compare** — a **baseline CNN (6-layer, from scratch)**, **ResNet50**, and a third (**VGG16** or similar). Varsha assigns one model to each of Iva / Temirlan / herself, defines the metric set, and consolidates everyone's numbers into one file.

**#18 — load_model + output shape (Temirlan + Varsha)**
- Comes **after** a model is trained. Varsha asked what "load_model / output shape / inference contract" means — Ali to clarify.

**#22 — Full evaluation + failure analysis (Iva + Temirlan)** — after models train.

**#23 — Deploy to HF Spaces (Varsha)** — upload trained models to Hugging Face, verify.

**#10 — Final report (Iva + Hessam)** — Ali to have Claude draft it from the repo; **Iva + Hessam edit for more natural, less "machine" language.**

**#24 — Video presentation (Hessam)** — record on **Friday** (no DL class) and send to Moe; fallback next week.

**Rolando — Data** — data delivered and clear (apologised for a short delay); offered help on downloads / class-weighting / imbalance.

## Decisions
1. **Drop the 3-person pairing on #20** — each person trains one model; **compare baseline CNN vs ResNet50 vs VGG16** and consolidate metrics.
2. **Report:** Claude drafts, then Iva + Hessam humanise/edit.
3. **Video for Moe recorded Friday** (fallback next week).

## Blockers
- Varsha finishing the other project first → DermaFace training may slip to tomorrow.
- Hessam absent this standup.

## Critical path
**Varsha (training)** — the trained checkpoints gate evaluation (#22), app wiring (#21), and deploy (#23).

## Next steps
- **Varsha:** start training; assign models to Iva/Temirlan; define metrics; consolidate; deploy to HF.
- **Iva / Temirlan:** train assigned model; evaluation + failure analysis.
- **Ali:** clarify #18 for Varsha; produce the report draft.
- **Hessam:** record the video Friday.
