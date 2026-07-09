# Team Roles - DermaFace AI

Seven people, three weeks, run like an early-stage applied-AI startup. Titles
are the real-world framing; **"Owns"** is what each person is accountable for.
Ownership means "makes the call" - not "only person who touches it." Everyone
codes, documents, tests, and helps unblock the demo.

The two added members are paired into existing workstreams rather than creating
new standalone scope. Original leads remain accountable; paired contributors
reduce bottlenecks and improve quality.

| # | Startup title | Person | Paired with | Owns (accountable for) | Pipeline area |
|---|---------------|--------|-------------|------------------------|---------------|
| 1 | **CEO / Product Lead** | **Hessam** | Team-wide | Vision, scope control, the "screening & education, not diagnosis" framing, instructor/stakeholder comms, GitHub tracker, demo story, final pitch deck, ethics & disclaimer honesty | Product spec, coordination, presentation |
| 2 | **Chief Scientist / ML Research Lead** | **Iva** | **Temirlan** | Model architecture, transfer-learning choice, **severity-labeling methodology**, evaluation metrics, fairness across Fitzpatrick skin tones | Model + eval design |
| 3 | **Data Engineer / ML Data Lead** | **Aparna** | **Rolando** | Sourcing & licensing the datasets, cleaning, dedup, label harmonization, augmentation, train/val/test splits, class balance | Data pipeline |
| 4 | **ML Engineer / MLOps** | **Varsha** | **Temirlan** | Training infra, experiment tracking, **Grad-CAM implementation**, model export, inference pipeline, HF Spaces deploy, reproducibility | Training loop + serving |
| 5 | **Full-stack / UX Engineer** | **Ali** | **Varsha as needed** | The Streamlit app, UI/UX, Grad-CAM overlay rendering, consent/disclaimer flow, user-facing copy, accessibility | Frontend + demo UX |
| 6 | **Data Pipeline & QA Support** | **Rolando** | **Aparna** | Data quality checks, manifest validation, image preprocessing sanity, EDA support, provenance review | Data QA + EDA support |
| 7 | **Evaluation & Explainability Support** | **Temirlan** | **Iva + Varsha** | Metrics tests, error analysis, Grad-CAM evidence set, IoU/localization evaluation when annotations support it | Evaluation + explainability evidence |

## Role Details

### Hessam - Product Lead

- Lock scope in a one-page product spec: exact classes, severity meaning for the
  demo, and what is explicitly out of scope for three weeks.
- Finalize disclaimer copy in `docs/ethics-and-disclaimer.md` and hand the
  approved string to Ali for the app.
- Turn Week-1 tasks into GitHub issues, assign owners, and maintain a simple
  board.
- Run async standup and own the Friday demo agenda.
- **Definition of done:** spec merged, disclaimer final, issues created, Friday
  demo scheduled.

### Iva - ML Research Lead

- Lock the backbone decision in `src/dermaface/config.py`; justify the choice in
  a short note.
- Decide the severity-labeling method by Friday, or formally de-scope severity
  to a stretch goal.
- Define and implement classification metrics and confusion matrix behavior.
- Pair with Varsha on loss, optimizer, schedule, class imbalance strategy, and
  evaluation design.
- **Definition of done:** backbone locked, severity decision documented, metrics
  functions pass toy-input tests.

### Aparna - Data Lead

- Acquire datasets into `data/raw/` and document access/licensing constraints.
- Build EDA covering class balance, Fitzpatrick distribution, and image quality.
- Build `data/processed/manifest.csv` and real data loaders.
- Implement stratified train/val/test splits by class and skin type.
- **Definition of done:** raw data available or access blockers documented,
  manifest CSV exists, and `build_dataloaders()` returns real batches on a small
  slice.

### Varsha - MLOps Lead

- Implement the training loop and checkpointing so `make train` runs end to end
  on Aparna's small slice.
- Wire experiment tracking through `.env`-based credentials or a local tracking
  fallback.
- Implement checkpoint loading in `src/dermaface/inference.py` so the app exits
  placeholder mode when a trained model exists.
- Keep CI green with ruff and pytest.
- **Definition of done:** a hello-world model trains, saves a checkpoint, logs a
  run, and CI stays green.

### Ali - UI/UX Lead

- Polish the Streamlit upload-to-result flow in
  `src/dermaface/app/streamlit_app.py`.
- Keep consent, disclaimer, confidence, and "see a professional" language
  front-and-center.
- Render Grad-CAM overlays cleanly in placeholder and real-checkpoint modes.
- Handle no upload, bad image, and no-face cases with friendly messaging.
- **Definition of done:** `make app` shows a clean upload -> result flow with
  the disclaimer and a working Grad-CAM panel.

### Rolando - Data Pipeline & QA Support

- Support Aparna with dataset acquisition documentation, license/provenance
  checks, and raw-data organization.
- Build quality checks for corrupt images, duplicates, image size issues,
  missing labels, missing skin-type fields, and manifest consistency.
- Help create the first `manifest.csv` and validate that `build_dataloaders()`
  returns real batches.
- Assist EDA with class balance, Fitzpatrick distribution, image quality
  summaries, and representative examples.
- **Definition of done:** manifest validation passes, EDA tables/plots exist,
  and a small clean slice can load through the data pipeline.

### Temirlan - Evaluation & Explainability Support

- Support Iva with toy-input tests for classification metrics, confusion matrix,
  and fairness-by-skin-type outputs.
- Support Varsha by validating model outputs needed by inference: logits,
  probabilities, predicted class, confidence, and checkpoint loading.
- Build the Grad-CAM evidence set for the report: correct examples, failure
  examples, and cases where heatmaps are misleading.
- Use IoU only when valid masks, bounding boxes, or defensible proxy regions are
  available; otherwise document Grad-CAM localization qualitatively.
- **Definition of done:** metrics are tested, evaluation outputs are report-ready,
  and explainability/failure-case examples are collected.

## Shared Co-ownership

- **Severity label scheme** -> #2 Iva (method) + #3 Aparna (data
  implementation) + #7 Temirlan (evaluation support)
- **Data quality and manifest readiness** -> #3 Aparna (owner) + #6 Rolando
  (QA support)
- **Grad-CAM** -> #4 Varsha (compute) + #5 Ali (display/overlay) + #7 Temirlan
  (evidence set)
- **Fairness analysis** -> #2 Iva (metrics/interpretation) + #3 Aparna
  (skin-tone stratified splits) + #7 Temirlan (tests/report outputs)
- **Glue work** (tests, docs, git hygiene, PR review) -> coordinated by #1
  Hessam, done by whoever has slack

## Working Agreement

- **Standup:** async daily update (what I did / doing / blocked on) in the team
  channel.
- **Branching:** `main` is protected; work on `feature/<area>-<short-desc>`.
- **Review:** original owners approve major changes in their area; paired
  contributors can open PRs and tag the owner.
- **Definition of done:** code + docstring + tests or evidence + a note in the
  relevant doc; no direct commits to `main`.
- **Weekly demo:** every Friday, whatever exists gets shown end-to-end.
