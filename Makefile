.PHONY: help install dev-install lint format test app train eval clean data qa clean-manifest weights fairness facecheck slice verify-data

help:
	@echo "DermaFace AI — common tasks"
	@echo "  make install       Install runtime deps"
	@echo "  make dev-install   Install package (editable) + dev deps"
	@echo "  make lint          Ruff lint"
	@echo "  make format        Black format"
	@echo "  make test          Run pytest"
	@echo "  make app           Launch the Streamlit demo"
	@echo "  make train         Run training (see src/dermaface/training/train.py)"
	@echo "  make eval          Run evaluation"
	@echo "  --- data pipeline ---"
	@echo "  make data          Build manifest + label_map from data/raw/, then stratified splits"
	@echo "  make qa            Write data/processed/qa/data_quality_report.csv"
	@echo "  make clean-manifest  Write data/processed/manifest_clean.csv (drops QA-flagged rows)"
	@echo "  make weights       Write data/processed/class_weights.json (weighted-loss)"
	@echo "  make fairness      Report per-skin-tone coverage of the test split"
	@echo "  make facecheck     Measure how many manifest images actually show a face"
	@echo "  make slice         Generate a synthetic smoke slice under data_smoke/"
	@echo "  make verify-data   Run the end-to-end pipeline smoke test"

install:
	pip install -r requirements.txt

dev-install:
	pip install -e ".[dev]"
	pip install -r requirements.txt

lint:
	ruff check src tests

format:
	black src tests

test:
	pytest -q

app:
	streamlit run src/dermaface/app/streamlit_app.py

train:
	python -m dermaface.training.train

eval:
	python -m dermaface.training.evaluate

data:
	python -m dermaface.data.manifest
	python -m dermaface.data.splits

qa:
	python -m dermaface.data.qa

clean-manifest:
	python -m dermaface.data.clean

weights:
	python -m dermaface.data.weights

fairness:
	python -m dermaface.data.fairness --split test

facecheck:
	python -m dermaface.data.facecheck

slice:
	python scripts/make_smoke_slice.py --raw-dir data_smoke/raw --per-class 12

verify-data:
	python scripts/verify_slice.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
