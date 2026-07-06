"""Grad-CAM wrapper around the ``grad-cam`` package.

Owners: Varsha (MLOps, compute) + Ali (UI/UX, overlay display).

``heatmap`` computes the class-activation map; ``overlay`` blends it onto the
original image for the app. Works with any model built by
``dermaface.models.build_model`` — including a random-weight model, so the UX
can be developed and demoed before training produces real weights.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from dermaface.config import Config, load_config
from dermaface.models import get_gradcam_target_layer


class GradCAMExplainer:
    """Produces a Grad-CAM heatmap for a given model + input tensor."""

    def __init__(self, model: Any, cfg: Config | None = None) -> None:
        self.cfg = cfg or load_config()
        self.model = model
        self.model.eval()
        self.target_layer = get_gradcam_target_layer(model, self.cfg)

    def heatmap(self, input_tensor: Any, target_class: int | None = None) -> np.ndarray:
        """Return a HxW float array in [0, 1] highlighting influential regions.

        Args:
            input_tensor: preprocessed image tensor, shape (1, C, H, W).
            target_class: class index to explain; None -> model's top class.
        """
        from pytorch_grad_cam import GradCAM
        from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

        targets = None
        if target_class is not None:
            targets = [ClassifierOutputTarget(target_class)]

        with GradCAM(model=self.model, target_layers=[self.target_layer]) as cam:
            # grayscale_cam has shape (batch, H, W); take the first image.
            grayscale_cam = cam(input_tensor=input_tensor, targets=targets)[0]
        return grayscale_cam

    def overlay(
        self,
        rgb_image: np.ndarray,
        input_tensor: Any,
        target_class: int | None = None,
    ) -> np.ndarray:
        """Return the original image with the heatmap blended on top (RGB uint8).

        Args:
            rgb_image: HxWx3 array in [0, 1] (float) matching the model input size.
            input_tensor: preprocessed image tensor, shape (1, C, H, W).
            target_class: class index to explain; None -> model's top class.
        """
        from pytorch_grad_cam.utils.image import show_cam_on_image

        rgb_image = np.asarray(rgb_image, dtype=np.float32)
        if rgb_image.max() > 1.0:  # accept uint8 [0,255] too
            rgb_image = rgb_image / 255.0

        cam = self.heatmap(input_tensor, target_class)
        overlay = show_cam_on_image(rgb_image, cam, use_rgb=True)
        return overlay  # HxWx3 uint8
