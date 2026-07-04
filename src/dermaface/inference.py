"""Single-image inference used by the app and CLI.

Owners: Varsha (MLOps) + Ali (UI/UX).

Key design point: if no trained checkpoint is present at ``cfg.model_path``,
``predict`` returns a clearly-flagged PLACEHOLDER result so the app is runnable
from day one without a model. Never present placeholder output as real.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dermaface.config import CLASS_NAMES, Config, load_config


@dataclass
class Prediction:
    condition: str
    condition_probs: dict[str, float]
    severity: str
    confidence: float
    placeholder: bool = False
    note: str = ""
    heatmap_overlay: Any = field(default=None, repr=False)  # RGB image or None


def load_model(cfg: Config | None = None) -> Any | None:
    """Load the trained model, or return None if no checkpoint exists.

    TODO(Varsha): build_model(cfg) + load_state_dict from cfg.model_path,
    move to eval() on the right device.
    """
    cfg = cfg or load_config()
    if not cfg.model_path.exists():
        return None
    raise NotImplementedError("checkpoint loading not implemented yet")


def predict(image: Any, cfg: Config | None = None, model: Any | None = None) -> Prediction:
    """Predict condition + severity for a single PIL image.

    Falls back to a PLACEHOLDER prediction when no model is available so the
    demo runs end-to-end. Wire in the real path once training produces weights.
    """
    cfg = cfg or load_config()
    if model is None:
        model = load_model(cfg)

    if model is None:
        return _placeholder_prediction()

    # TODO(Varsha/Ali): preprocess image -> tensor, forward pass, softmax,
    # map to Prediction, and attach GradCAMExplainer(model).overlay(...).
    raise NotImplementedError("real inference path not implemented yet")


def _placeholder_prediction() -> Prediction:
    """A fixed, obviously-fake result for wiring up the UI before training."""
    probs = {name: round(1.0 / len(CLASS_NAMES), 3) for name in CLASS_NAMES}
    return Prediction(
        condition="clear",
        condition_probs=probs,
        severity="n/a",
        confidence=0.0,
        placeholder=True,
        note="PLACEHOLDER — no trained model loaded. Output is not a real prediction.",
    )
