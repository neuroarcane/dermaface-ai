# DermaFace AI

**Screening & education tool** that classifies **acne**, **rosacea**, and **redness / inflammation severity** from face photos, with **Grad-CAM** heatmaps highlighting the affected areas.

> ⚠️ **Not a medical device. Not a diagnosis.** DermaFace AI is an educational / screening prototype built for a course project. It does **not** provide medical advice. Always consult a licensed dermatologist for any skin concern. See [docs/ethics-and-disclaimer.md](docs/ethics-and-disclaimer.md).

---

## What it does

1. You upload a face photo.
2. The model predicts the likely **condition** (acne / rosacea / redness / clear) and a coarse **severity** band.
3. A **Grad-CAM** overlay shows *which regions of the face* drove the prediction.
4. The UI surfaces confidence, limitations, and a "see a professional" prompt.

## Datasets

| Dataset | Use |
|---|---|
| [Fitzpatrick17k](https://github.com/mattgroh/fitzpatrick17k) | Condition labels + Fitzpatrick skin-tone labels (fairness analysis) |
| [SKINCON](https://skincon-dataset.github.io/) | Dense clinical concept annotations (erythema, papules, etc.) |
| [Google SCIN](https://github.com/google-research-datasets/scin) | Consumer-quality photos + self-reported context |

See [docs/data-strategy.md](docs/data-strategy.md) for licensing, harmonization, and the **severity-labeling plan** (the project's hardest problem).

## Tech stack (planned)

- **Modeling:** PyTorch + a pretrained CNN backbone (transfer learning)
- **Explainability:** Grad-CAM
- **App:** Streamlit or Gradio
- **Deploy:** Hugging Face Spaces
- **Tracking:** Weights & Biases or MLflow

> Stack is a proposal, not locked. Final choice is the Chief Scientist / MLOps call in Week 1.

## Repository layout

```
dermaface-ai/
├── docs/                  # Project docs (roles, plan, data, ethics, model card)
├── data/                  # Datasets (gitignored — see data/README.md)
│   ├── raw/               # Original downloads, never edited
│   ├── processed/         # Cleaned + split, ready for training
│   └── external/          # Third-party metadata / label maps
├── src/dermaface/         # Python package (implementation lands here)
│   ├── data/              # Loading, cleaning, augmentation, splits
│   ├── models/            # Architectures, transfer learning
│   ├── training/          # Train / eval loops, metrics, fairness
│   ├── explain/           # Grad-CAM
│   └── app/               # Streamlit / Gradio front-end
├── notebooks/             # EDA & experiments
├── models/                # Saved weights (gitignored)
├── tests/                 # Unit tests
└── assets/                # Screenshots, demo images, diagrams
```

## Getting started

The package scaffold is in place: modules import, smoke tests pass, and the app
runs in **placeholder mode** (dummy predictions) until a model is trained. Each
owner fills in the `TODO(...)`/`NotImplementedError` stubs in their area.

```bash
git clone https://github.com/neuroarcane/dermaface-ai
cd dermaface-ai
python -m venv .venv && source .venv/bin/activate
make dev-install          # editable install + dev + runtime deps

make test                 # smoke tests (no model/torch needed)
make app                  # launch the Streamlit demo (placeholder mode)
make train                # NotImplementedError until the loop is written
```

See the `Makefile` for all tasks. Module ownership is noted at the top of each
file and in [docs/team-roles.md](docs/team-roles.md).

## Team & timeline

Five-person team, three-week sprint, run like a small startup. See **[docs/team-roles.md](docs/team-roles.md)** and **[docs/project-plan.md](docs/project-plan.md)**.

**Success criteria** (targets set up front, measured in the report): **[docs/requirements.md](docs/requirements.md)** → results tracked in **[docs/model-card.md](docs/model-card.md)**.

## License

Code under the MIT License (see [LICENSE](LICENSE)). **Datasets carry their own licenses/usage terms** — review each before use; see [docs/data-strategy.md](docs/data-strategy.md).
