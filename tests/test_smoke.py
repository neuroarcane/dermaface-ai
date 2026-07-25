"""Smoke tests — verify the scaffold imports and wires together.

These pass without torch/streamlit installed and without a trained model.
Owner: shared (glue work, coordinated by Hessam).
"""

from dataclasses import replace

import pytest

from dermaface import CLASS_NAMES, SEVERITY_BANDS, load_config
from dermaface.inference import predict, resolve_checkpoint


def test_config_loads():
    cfg = load_config()
    assert cfg.num_classes == len(CLASS_NAMES)
    assert cfg.image_size > 0


def test_labels_defined():
    assert "acne" in CLASS_NAMES
    assert "rosacea" in CLASS_NAMES
    assert "n/a" in SEVERITY_BANDS


def test_placeholder_prediction_runs(tmp_path):
    # Point at an empty model dir so we deterministically get the placeholder
    # path regardless of any checkpoint sitting in the real models/ dir. This
    # path stays torch-free (load_model returns None before importing torch).
    cfg = replace(load_config(), model_path=tmp_path / "none.pt")
    result = predict(image=None, cfg=cfg)
    assert result.placeholder is True
    assert result.condition in CLASS_NAMES
    assert abs(sum(result.condition_probs.values()) - 1.0) < 1e-6


def test_real_prediction_when_checkpoint_present():
    # Runs only where a trained checkpoint exists (e.g. a dev machine); skipped
    # in CI, which has no weights. Uses a synthetic image — no dataset needed.
    cfg = load_config()
    if resolve_checkpoint(cfg) is None:
        pytest.skip("no trained checkpoint present")
    pytest.importorskip("torch")
    from PIL import Image

    img = Image.new("RGB", (256, 256), (200, 120, 120))
    result = predict(img, cfg=cfg)
    assert result.placeholder is False
    assert result.condition in CLASS_NAMES
    assert abs(sum(result.condition_probs.values()) - 1.0) < 1e-5
    assert 0.0 <= result.confidence <= 1.0
