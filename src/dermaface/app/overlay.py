"""UI-side image helpers: preprocessing, face check, and demo Grad-CAM overlay.

Owner: Ali (UI/UX).

These are the display-layer utilities the Streamlit app needs. The demo overlay
runs Grad-CAM on a *random-weight* model so the heatmap panel works before
training produces real weights — clearly illustrative, never a real prediction.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np

from dermaface.config import Config, load_config

# Lazily-built random-weight model, reused across calls (cheap to keep around).
_DEMO_MODEL: Any = None


def prepare_image(image: Any, cfg: Config | None = None) -> tuple[np.ndarray, Any]:
    """Turn a PIL image into (rgb_float HxWx3 in [0,1], input_tensor 1xCxHxW).

    ``rgb_float`` is the resized, un-normalized image used as the overlay base;
    ``input_tensor`` is normalized for the model.
    """
    cfg = cfg or load_config()
    from dermaface.data.preprocessing import build_transforms

    resized = image.resize((cfg.image_size, cfg.image_size))
    rgb_float = np.asarray(resized, dtype=np.float32) / 255.0

    tensor = build_transforms(cfg, train=False)(image).unsqueeze(0)
    return rgb_float, tensor


def detect_face(image: Any) -> bool:
    """Best-effort face check using OpenCV's Haar cascade.

    Returns True if a face is found (or if detection is unavailable — we don't
    want to block the demo on a missing cascade). Used only to warn the user.
    """
    try:
        import cv2

        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(cascade_path)
        if cascade.empty():
            return True
        gray = cv2.cvtColor(np.asarray(image.convert("RGB")), cv2.COLOR_RGB2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        return len(faces) > 0
    except Exception:
        return True  # never block on detector issues


def build_demo_overlay(image: Any, cfg: Config | None = None) -> np.ndarray:
    """Grad-CAM overlay from a random-weight model (illustrative only).

    Lets the UI show a working heatmap before a trained checkpoint exists.
    """
    cfg = cfg or load_config()
    global _DEMO_MODEL
    if _DEMO_MODEL is None:
        from dermaface.models import build_model

        # No pretrained download needed — random weights are fine to demo the UI.
        _DEMO_MODEL = build_model(replace(cfg, pretrained=False))

    from dermaface.explain import GradCAMExplainer

    rgb_float, tensor = prepare_image(image, cfg)
    explainer = GradCAMExplainer(_DEMO_MODEL, cfg)
    return explainer.overlay(rgb_float, tensor)
