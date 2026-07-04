"""Grad-CAM wrapper around the ``grad-cam`` package.

Owners: Varsha (MLOps, compute) + Ali (UI/UX, overlay display).

Structure is scaffolded against the pytorch-grad-cam API. Fill in the two
TODOs (invoke CAM, blend overlay) to make it live.
"""

from __future__ import annotations

from typing import Any

from dermaface.config import Config, load_config
from dermaface.models import get_gradcam_target_layer


class GradCAMExplainer:
    """Produces a Grad-CAM heatmap for a given model + input tensor."""

    def __init__(self, model: Any, cfg: Config | None = None) -> None:
        self.cfg = cfg or load_config()
        self.model = model
        self.target_layer = get_gradcam_target_layer(model, self.cfg)

    def heatmap(self, input_tensor: Any, target_class: int | None = None) -> Any:
        """Return a HxW float array in [0, 1] highlighting influential regions.

        Args:
            input_tensor: preprocessed image tensor, shape (1, C, H, W).
            target_class: class index to explain; None -> model's top class.

        TODO(Varsha): use pytorch_grad_cam.GradCAM(model, [target_layer]);
        return the grayscale cam for the chosen target.
        """
        raise NotImplementedError

    def overlay(self, rgb_image: Any, input_tensor: Any, target_class: int | None = None) -> Any:
        """Return the original image with the heatmap blended on top (RGB uint8).

        TODO(Ali): use pytorch_grad_cam.utils.image.show_cam_on_image to blend
        self.heatmap(...) onto the normalized rgb_image for the app.
        """
        raise NotImplementedError
