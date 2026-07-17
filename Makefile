.PHONY: help install dev-install lint format test app train eval clean data qa slice verify-data

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

slice:
	python scripts/make_smoke_slice.py --raw-dir data_smoke/raw --per-class 12

verify-data:
	python scripts/verify_slice.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
