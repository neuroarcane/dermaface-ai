"""Model definitions and transfer-learning backbones.

Owner: Iva (ML Research Lead).
"""

from dermaface.models.classifier import build_model, get_gradcam_target_layer

__all__ = ["build_model", "get_gradcam_target_layer"]
