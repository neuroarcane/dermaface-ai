"""Image preprocessing and augmentation transforms.

Owner: Aparna (Data Lead), paired with Rolando (Data QA), with Iva
(ML Research) on augmentation choices.

Note: be careful with color augmentation — aggressive jitter can destroy the
erythema/redness signal the model needs. Keep it mild.
"""

from __future__ import annotations

from typing import Any

from dermaface.config import Config, load_config


def build_transforms(cfg: Config | None = None, *, train: bool) -> Any:
    """Return a torchvision transform pipeline.

    Args:
        cfg: configuration (defaults to ``load_config()``).
        train: if True, include augmentation; else eval-only (resize+normalize).

    Returns:
        A ``torchvision.transforms.Compose``.
    """
    cfg = cfg or load_config()
    from torchvision import transforms  # local import keeps module import cheap

    base = [
        transforms.Resize((cfg.image_size, cfg.image_size)),
    ]
    if train:
        base += [
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(degrees=10),
            # Keep color jitter MILD — see module docstring.
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
        ]
    base += [
        transforms.ToTensor(),
        transforms.Normalize(mean=cfg.norm_mean, std=cfg.norm_std),
    ]
    return transforms.Compose(base)


def has_face(image_path: str) -> bool:
    """Return True if a face is detected in the image.

    Used to filter out non-face photos during cleaning.
    TODO(Aparna/Rolando): wire up a lightweight face detector (e.g. mediapipe / haar).
    """
    raise NotImplementedError
