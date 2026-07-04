# Team Roles — DermaFace AI

Five people, three weeks, run like an early-stage applied-AI startup. Titles are the real-world framing; **"Owns"** is what each person is *accountable* for. Ownership means "makes the call and it's their neck" — **not** "only person who touches it." Everyone codes.

> Fill in names in the **Person** column.

| # | Startup title | Person | Owns (accountable for) | Pipeline area |
|---|---------------|--------|------------------------|---------------|
| 1 | **CEO / Product Lead** | **Hessam** | Vision, scope control, the *"screening & education, not diagnosis"* framing, instructor/stakeholder comms, demo story, final pitch deck, ethics & disclaimer honesty | Product spec, presentation |
| 2 | **Chief Scientist / ML Research Lead** | **Iva** | Model architecture, transfer-learning choice, **severity-labeling methodology**, evaluation metrics, fairness across Fitzpatrick skin tones | Model + eval design |
| 3 | **Data Engineer / ML Data Lead** | **Aparna** | Sourcing & licensing the 3 datasets, cleaning, dedup, label harmonization, augmentation, train/val/test splits, class balance | Data pipeline |
| 4 | **ML Engineer / MLOps** | **Varsha** | Training infra, experiment tracking, **Grad-CAM implementation**, model export, inference pipeline, HF Spaces deploy, reproducibility | Training loop + serving |
| 5 | **Full-stack / UX Engineer** | **Ali** | The app (Streamlit/Gradio), UI/UX, Grad-CAM overlay rendering, consent/disclaimer flow, user-facing copy, accessibility | Frontend + demo UX |

## Shared co-ownership (where roles pair up)

- **Severity label scheme** → #2 (method) + #3 (implementation in data)
- **Grad-CAM** → #4 (compute) + #5 (display/overlay)
- **Fairness analysis** → #2 (metrics) + #3 (skin-tone stratified splits)
- **Glue work** (tests, docs, git hygiene, PR review) → coordinated by #1, done by whoever has slack

## Working agreement

- **Standup:** async daily update (what I did / doing / blocked on) in the team channel.
- **Branching:** `main` is protected; work on `feature/<area>-<short-desc>`; PRs need one review.
- **Definition of done:** code + docstring + a note in the relevant doc; no direct commits to `main`.
- **Weekly demo:** every Friday, whatever exists gets shown end-to-end.
