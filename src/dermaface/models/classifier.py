"""Transfer-learning classifier for DermaFace.

Owner: Iva (ML Research Lead).

``build_model`` swaps the final layer of a torchvision backbone for a
``num_classes`` head. This part is standard boilerplate and is implemented;
the research decisions (which backbone, freezing schedule, whether to add a
separate severity head) are TODOs for Iva.
"""

from __future__ import annotations

from typing import Any

from dermaface.config import Config, load_config

_SUPPORTED = {"resnet18", "resnet50", "efficientnet_b0"}


def build_model(cfg: Config | None = None) -> Any:
    """Build a pretrained backbone with a fresh classification head.

    Args:
        cfg: configuration (defaults to ``load_config()``).

    Returns:
        A ``torch.nn.Module`` producing ``cfg.num_classes`` logits.
    """
    cfg = cfg or load_config()
    if cfg.backbone not in _SUPPORTED:
        raise ValueError(f"backbone {cfg.backbone!r} not in {_SUPPORTED}")

    import torch.nn as nn
    from torchvision import models

    weights = "DEFAULT" if cfg.pretrained else None

    if cfg.backbone.startswith("resnet"):
        model = getattr(models, cfg.backbone)(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, cfg.num_classes)
    elif cfg.backbone == "efficientnet_b0":
        model = models.efficientnet_b0(weights=weights)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, cfg.num_classes)
    else:  # pragma: no cover - guarded above
        raise ValueError(cfg.backbone)

    # TODO(Iva): optionally freeze early layers for the first few epochs.
    # TODO(Iva): decide if severity gets its own head or is folded into classes.
    return model


def get_gradcam_target_layer(model: Any, cfg: Config | None = None) -> Any:
    """Return the conv layer Grad-CAM should hook (last conv block).

    Kept next to the model so it stays in sync with backbone changes.
    """
    cfg = cfg or load_config()
    if cfg.backbone.startswith("resnet"):
        return model.layer4[-1]
    if cfg.backbone == "efficientnet_b0":
        return model.features[-1]
    raise ValueError(f"no target layer configured for {cfg.backbone!r}")
