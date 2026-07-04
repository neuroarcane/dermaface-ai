"""DermaFace AI — screening/education classifier for acne, rosacea, and redness.

NOT a medical device. NOT a diagnosis. See docs/ethics-and-disclaimer.md.
"""

__version__ = "0.1.0"

from dermaface.config import CLASS_NAMES, SEVERITY_BANDS, Config, load_config

__all__ = ["__version__", "CLASS_NAMES", "SEVERITY_BANDS", "Config", "load_config"]
