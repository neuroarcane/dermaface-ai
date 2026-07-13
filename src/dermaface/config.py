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


def _env_path(var: str, default: Path) -> Path:
    val = os.environ.get(var)
    return Path(val) if val else default


def load_config() -> Config:
    """Return a Config, reading overrides from environment variables."""
    return Config()
