"""Image preprocessing and augmentation transforms.

Owner: Aparna (Data Lead), paired with Rolando (Data QA), with Iva
(ML Research) on augmentation choices.

Two pipelines, and the split decides which one you get:

* **train** — augmented: random resized crop, horizontal flip, small rotation,
  *mild* brightness/contrast jitter (optionally random erasing), then
  ToTensor + ImageNet normalize.
* **eval / test / demo** — deterministic: resize + ToTensor + normalize. No
  randomness, so metrics are stable and comparable across runs.

Why augmentation is applied here (at load time) and never baked into the
manifest: augmenting *before* splitting would let a flipped copy of an image
land in a different split from its original — textbook leakage that silently
inflates test scores. Doing it on the fly, gated on ``train``, makes that
impossible by construction.

⚠️ **Colour augmentation is deliberately restrained.** Erythema — redness — is
the feature separating `redness`/`rosacea` from `clear`. Saturation and hue
jitter degrade exactly that signal, so they are pinned to 0.0 in ``Config`` and
brightness/contrast are kept mild. All knobs live in ``Config`` (``aug_*``); tune
them there, and re-check per-class recall for redness and rosacea afterwards.
"""

from __future__ import annotations

from typing import Any

from dermaface.config import Config, load_config


def _pil_stage_ops(cfg: Config, transforms: Any) -> list:
    """The PIL-stage (pre-tensor) train augmentations, in order."""
    ops: list = []
    if cfg.aug_scale_min < 1.0:
        # Random crop-and-rescale gives scale/translation invariance. The lower
        # bound is conservative so we don't crop the lesion out of frame.
        ops.append(
            transforms.RandomResizedCrop(
                cfg.image_size,
                scale=(cfg.aug_scale_min, 1.0),
                ratio=(0.9, 1.1),
            )
        )
    else:
        ops.append(transforms.Resize((cfg.image_size, cfg.image_size)))

    if cfg.aug_hflip_p > 0:
        ops.append(transforms.RandomHorizontalFlip(p=cfg.aug_hflip_p))
    if cfg.aug_rotation_deg > 0:
        ops.append(transforms.RandomRotation(degrees=cfg.aug_rotation_deg))

    if any((cfg.aug_brightness, cfg.aug_contrast, cfg.aug_saturation, cfg.aug_hue)):
        ops.append(
            transforms.ColorJitter(
                brightness=cfg.aug_brightness,
                contrast=cfg.aug_contrast,
                saturation=cfg.aug_saturation,  # 0.0 by design
                hue=cfg.aug_hue,                # 0.0 by design
            )
        )
    return ops


def build_augment_pil(cfg: Config | None = None) -> Any:
    """Return only the PIL-stage train augmentations (no tensor conversion).

    Handy for previewing/debugging what augmentation actually does to an image —
    see ``scripts/preview_augmentation.py``.
    """
    cfg = cfg or load_config()
    from torchvision import transforms

    return transforms.Compose(_pil_stage_ops(cfg, transforms))


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

    to_tensor = [
        transforms.ToTensor(),
        transforms.Normalize(mean=cfg.norm_mean, std=cfg.norm_std),
    ]

    if not train:
        # Deterministic: identical output every time for stable metrics.
        return transforms.Compose(
            [transforms.Resize((cfg.image_size, cfg.image_size)), *to_tensor]
        )

    ops = [*_pil_stage_ops(cfg, transforms), *to_tensor]
    if cfg.aug_erasing_p > 0:
        # Operates on tensors, so it goes last. Small patches only — a large
        # erase could remove the lesion entirely.
        ops.append(transforms.RandomErasing(p=cfg.aug_erasing_p, scale=(0.02, 0.08)))
    return transforms.Compose(ops)


_CASCADES: dict[str, Any] = {}

_OPENCV_HINT = (
    "Face detection needs an OpenCV build that provides CascadeClassifier.\n"
    "OpenCV 5.0 MOVED CascadeClassifier out of `objdetect` into `xobjdetect` "
    "(opencv_contrib), so plain `opencv-python>=5` does not have it.\n"
    "Fix with either:\n"
    "  pip install 'opencv-python<5'            # simplest — Haar cascades work\n"
    "  pip install opencv-contrib-python        # keeps 5.x, adds cv2.xobjdetect"
)


def _cascade_api() -> Any:
    """Return this OpenCV version's CascadeClassifier class, or None.

    OpenCV 4.x exposes it at ``cv2.CascadeClassifier``. OpenCV 5.0 moved it to
    ``cv2.xobjdetect.CascadeClassifier`` (only present with opencv_contrib).
    """
    try:
        import cv2
    except Exception:
        return None
    cls = getattr(cv2, "CascadeClassifier", None)
    if cls is not None:
        return cls
    xobj = getattr(cv2, "xobjdetect", None)
    return getattr(xobj, "CascadeClassifier", None) if xobj is not None else None


def face_backend_available() -> bool:
    """True if OpenCV is importable *and* usable for Haar cascade detection.

    Checking the attributes matters: a `cv2` can import perfectly (OpenCV 5.0
    does) and still lack the cascade API, blowing up only on first use.
    """
    try:
        import cv2
    except Exception:
        return False
    return _cascade_api() is not None and hasattr(cv2, "data")


def _cascade(name: str) -> Any:
    """Load (and cache) an OpenCV Haar cascade that ships with opencv-python."""
    import cv2

    api = _cascade_api()
    if api is None or not hasattr(cv2, "data"):
        raise RuntimeError(_OPENCV_HINT)
    if name not in _CASCADES:
        _CASCADES[name] = api(cv2.data.haarcascades + name)
    return _CASCADES[name]


def has_face(image_path: str, *, min_size: int = 60, max_side: int = 640) -> bool:
    """Return True if a face is detected in the image.

    Used to distinguish facial photos from other body sites: Fitzpatrick17k covers
    every body site, but DermaFace is a *face* screening tool, so training largely
    on arms and torsos is a train/deploy mismatch.

    Uses OpenCV Haar cascades (frontal + profile, and the profile cascade re-run on
    a mirrored copy since it only detects one direction). No model download needed —
    the cascades ship with ``opencv-python``.

    ⚠️ **This is a lower bound, not ground truth.** Haar cascades miss faces that
    are rotated, partially cropped, or shot very close up — and many clinical
    photos are tight crops of a cheek or chin, which are *facial skin* without a
    detectable face. Treat the result as "images where a face is clearly visible"
    and calibrate against a manual spot-check before acting on it.

    Args:
        image_path: path to the image.
        min_size: ignore detections smaller than this many pixels on a side.
        max_side: downscale the long side to this before detecting (speed).

    Returns:
        True if any cascade detects a face.
    """
    if not face_backend_available():
        raise RuntimeError(_OPENCV_HINT)

    import cv2

    img = cv2.imread(str(image_path))
    if img is None:  # unreadable/corrupt
        return False

    h, w = img.shape[:2]
    if max(h, w) > max_side:  # downscale for speed; Haar is scale-invariant
        scale = max_side / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    gray = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    kwargs = dict(scaleFactor=1.1, minNeighbors=4, minSize=(min_size, min_size))

    for name in ("haarcascade_frontalface_default.xml", "haarcascade_frontalface_alt2.xml"):
        if len(_cascade(name).detectMultiScale(gray, **kwargs)):
            return True

    # Profile cascade only fires on one facing direction — try both.
    profile = _cascade("haarcascade_profileface.xml")
    if len(profile.detectMultiScale(gray, **kwargs)):
        return True
    if len(profile.detectMultiScale(cv2.flip(gray, 1), **kwargs)):
        return True

    return False
