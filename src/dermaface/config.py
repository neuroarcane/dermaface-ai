"""Central configuration for DermaFace AI.

Keep all magic numbers, paths, and label definitions here so every module
(data, models, training, app) agrees. Owner: shared, coordinated by MLOps (Varsha).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# --- Labels -----------------------------------------------------------------
# Condition classes. "clear" = no target condition detected.
CLASS_NAMES: list[str] = ["acne", "rosacea", "redness", "clear"]

# Coarse severity bands. "n/a" applies to the "clear" class.
SEVERITY_BANDS: list[str] = ["mild", "moderate", "severe", "n/a"]

# Fitzpatrick skin types tracked for fairness analysis.
FITZPATRICK_TYPES: list[str] = ["I", "II", "III", "IV", "V", "VI"]

# --- Skin-tone bands (fairness reporting) -----------------------------------
# The public dermatology datasets are heavily skewed toward lighter skin, so the
# individual dark-skin types are too sparse to estimate per-group metrics from
# (type VI is ~2% of our data). We therefore report fairness primarily on coarse
# BANDS — the same I-II / III-IV / V-VI grouping the DDI dataset uses — and show
# the per-type table alongside it with explicit sample sizes.
SKIN_TONE_BANDS: dict[str, str] = {
    "I": "I-II", "II": "I-II",
    "III": "III-IV", "IV": "III-IV",
    "V": "V-VI", "VI": "V-VI",
}
SKIN_TONE_BAND_NAMES: list[str] = ["I-II", "III-IV", "V-VI"]

# Below this many samples, a per-group metric is too noisy to report unqualified.
MIN_GROUP_N: int = 30


def skin_tone_band(skin_type: str) -> str:
    """Map a Fitzpatrick type ('I'..'VI') to its reporting band, else 'unknown'."""
    return SKIN_TONE_BANDS.get(str(skin_type).strip().upper(), "unknown")

# --- Dataset splits ---------------------------------------------------------
# Four-way split. "eval" is the tuning/validation split; "test" is frozen and
# never tuned on; "demo" is a tiny curated set reserved for the app demo.
SPLIT_NAMES: list[str] = ["train", "eval", "test", "demo"]
DEFAULT_SPLIT_RATIOS: tuple[float, float, float, float] = (0.70, 0.15, 0.10, 0.05)

# --- Paths ------------------------------------------------------------------
REPO_ROOT: Path = Path(__file__).resolve().parents[2]
_DEFAULT_DATA_DIR = REPO_ROOT / "data"


@dataclass
class Config:
    """Runtime configuration. Load via ``load_config()``."""

    # Paths
    data_dir: Path = field(default_factory=lambda: _env_path("DERMAFACE_DATA_DIR", _DEFAULT_DATA_DIR))
    model_path: Path = field(
        default_factory=lambda: _env_path("DERMAFACE_MODEL_PATH", REPO_ROOT / "models" / "dermaface_best.pt")
    )

    # Data
    image_size: int = 224
    num_workers: int = 4
    # ImageNet normalization (matches pretrained backbones).
    norm_mean: tuple[float, float, float] = (0.485, 0.456, 0.406)
    norm_std: tuple[float, float, float] = (0.229, 0.224, 0.225)

    # --- Augmentation (TRAIN SPLIT ONLY) ------------------------------------
    # Applied on the fly at load time; eval/test/demo always get the
    # deterministic resize+normalize pipeline so metrics stay comparable.
    #
    # ⚠️ COLOUR IS DELIBERATELY CONSTRAINED. Erythema (redness) is the visual
    # signal that separates `redness`/`rosacea` from `clear`. Saturation and hue
    # jitter attack exactly that signal, so both are pinned at 0.0 and
    # brightness/contrast are kept small. Do not raise these without re-checking
    # per-class recall for redness and rosacea.
    aug_hflip_p: float = 0.5        # faces are roughly symmetric; safe
    aug_rotation_deg: float = 10.0  # clinical photos are near-upright
    aug_brightness: float = 0.10    # mild
    aug_contrast: float = 0.10      # mild
    aug_saturation: float = 0.0     # keep 0 — would distort erythema
    aug_hue: float = 0.0            # keep 0 — would distort erythema
    aug_scale_min: float = 0.85     # RandomResizedCrop lower bound (1.0 = no crop)
    aug_erasing_p: float = 0.0      # optional occlusion robustness; off by default

    # Model
    # ResNet50 v1 baseline: ImageNet-pretrained, reliable for transfer learning.
    backbone: str = "resnet50"
    pretrained: bool = True
    num_classes: int = len(CLASS_NAMES)

    # Training
    batch_size: int = 32
    epochs: int = 20
    learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    seed: int = 42

    @property
    def manifest_path(self) -> Path:
        """CSV manifest of the processed dataset (see data/README.md)."""
        return self.data_dir / "processed" / "manifest.csv"

    @property
    def clean_manifest_path(self) -> Path:
        """Cleaned, training-ready manifest (QA-flagged rows removed)."""
        return self.data_dir / "processed" / "manifest_clean.csv"

    @property
    def label_map_path(self) -> Path:
        """Crosswalk of raw source condition names -> the four classes."""
        return self.data_dir / "external" / "label_map.csv"

    @property
    def qa_report_path(self) -> Path:
        """Per-image data-quality report (see data/processed/qa/)."""
        return self.data_dir / "processed" / "qa" / "data_quality_report.csv"


def _env_path(var: str, default: Path) -> Path:
    val = os.environ.get(var)
    return Path(val) if val else default


def load_config() -> Config:
    """Return a Config, reading overrides from environment variables."""
    return Config()
