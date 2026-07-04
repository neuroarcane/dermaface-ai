"""Smoke tests — verify the scaffold imports and wires together.

These pass without torch/streamlit installed and without a trained model.
Owner: shared (glue work, coordinated by Hessam).
"""

from dermaface import CLASS_NAMES, SEVERITY_BANDS, load_config
from dermaface.inference import predict


def test_config_loads():
    cfg = load_config()
    assert cfg.num_classes == len(CLASS_NAMES)
    assert cfg.image_size > 0


def test_labels_defined():
    assert "acne" in CLASS_NAMES
    assert "rosacea" in CLASS_NAMES
    assert "n/a" in SEVERITY_BANDS


def test_placeholder_prediction_runs():
    # With no trained model present, predict() returns a flagged placeholder.
    result = predict(image=None)
    assert result.placeholder is True
    assert result.condition in CLASS_NAMES
    assert abs(sum(result.condition_probs.values()) - 1.0) < 1e-6
