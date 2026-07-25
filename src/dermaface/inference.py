"""Single-image inference used by the app and CLI.

Owners: Varsha (MLOps) + Ali (UI/UX), with Temirlan validating model outputs
needed for evaluation and explainability.

Key design point: if no trained checkpoint is present, ``predict`` returns a
clearly-flagged PLACEHOLDER result so the app is runnable from day one without a
model. Never present placeholder output as real.

Checkpoint format (see ``notebooks/Basic_CNN.ipynb``): a dict with
``model_state_dict``, ``arch`` (``"cnn"`` or a torchvision backbone name), and
``class_names``. ``load_model`` rebuilds the matching architecture and loads the
weights, so whichever model the team ships (CNN now, ResNet50/VGG16 later) is
picked up as long as it saves this format.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import numpy as np

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


def prepare_image(image: Any, cfg: Config | None = None) -> tuple[np.ndarray, Any]:
    """Turn a PIL image into ``(rgb_float HxWx3 in [0,1], tensor 1xCxHxW)``.

    ``rgb_float`` is the resized, un-normalized image used as the Grad-CAM overlay
    base; ``tensor`` is normalized exactly like the eval/test pipeline the model
    was trained against, so inference matches training.
    """
    cfg = cfg or load_config()
    from dermaface.data.preprocessing import build_transforms

    resized = image.resize((cfg.image_size, cfg.image_size))
    rgb_float = np.asarray(resized.convert("RGB"), dtype=np.float32) / 255.0
    tensor = build_transforms(cfg, train=False)(image).unsqueeze(0)
    return rgb_float, tensor


def resolve_checkpoint(cfg: Config) -> Path | None:
    """Find a checkpoint to load, or None (-> placeholder mode).

    Prefers the explicit ``cfg.model_path``. Otherwise, by convention the training
    notebooks save ``dermaface_best_<arch>.pt``; if exactly one such file exists
    we use it, so the app "just works" once training drops a checkpoint into
    ``models/``. If several exist we can't know which is best, so we defer to an
    explicit ``DERMAFACE_MODEL_PATH`` and fall back to placeholder mode.
    """
    if cfg.model_path.exists():
        return cfg.model_path
    candidates = sorted(cfg.model_path.parent.glob("dermaface_best_*.pt"))
    if len(candidates) == 1:
        return candidates[0]
    return None


def _build_for_arch(arch: str, cfg: Config) -> Any:
    """Instantiate the architecture named by a checkpoint's ``arch`` field."""
    if arch == "cnn":
        from dermaface.models import BasicCNN

        return BasicCNN(cfg.num_classes)
    from dermaface.models import build_model

    # Random init here — the state_dict supplies the trained weights.
    return build_model(replace(cfg, backbone=arch, pretrained=False))


def load_model(cfg: Config | None = None) -> Any | None:
    """Load the trained model, or return None if no checkpoint exists."""
    cfg = cfg or load_config()
    ckpt_path = resolve_checkpoint(cfg)
    if ckpt_path is None:
        return None

    import torch

    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    # Support both the dict checkpoint format and a bare state_dict.
    if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
        state, arch = ckpt["model_state_dict"], ckpt.get("arch", cfg.backbone)
    else:
        state, arch = ckpt, cfg.backbone

    model = _build_for_arch(arch, cfg)
    model.load_state_dict(state)
    model.eval()
    model._dermaface_arch = arch  # for the prediction note / debugging
    return model


def predict(image: Any, cfg: Config | None = None, model: Any | None = None) -> Prediction:
    """Predict condition (+ Grad-CAM overlay) for a single PIL image.

    Falls back to a PLACEHOLDER prediction when no model is available so the demo
    runs end-to-end. Severity is de-scoped for v1 (see docs/severity-decision.md).
    """
    cfg = cfg or load_config()
    if model is None:
        model = load_model(cfg)
    if model is None:
        return _placeholder_prediction()

    import torch

    rgb_float, tensor = prepare_image(image, cfg)
    model.eval()
    with torch.no_grad():
        probs_t = torch.softmax(model(tensor), dim=1)[0]

    probs = {name: float(probs_t[i]) for i, name in enumerate(CLASS_NAMES)}
    top_idx = int(torch.argmax(probs_t))
    condition = CLASS_NAMES[top_idx]
    confidence = float(probs_t[top_idx])

    # Grad-CAM is best-effort: a heatmap failure must never sink the prediction.
    overlay = None
    try:
        from dermaface.explain import GradCAMExplainer

        overlay = GradCAMExplainer(model, cfg).overlay(rgb_float, tensor, target_class=top_idx)
    except Exception:
        overlay = None

    arch = getattr(model, "_dermaface_arch", cfg.backbone)
    return Prediction(
        condition=condition,
        condition_probs=probs,
        severity="n/a",  # de-scoped for v1
        confidence=confidence,
        placeholder=False,
        note=f"Screening only — not a diagnosis. Model: {arch}.",
        heatmap_overlay=overlay,
    )


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
