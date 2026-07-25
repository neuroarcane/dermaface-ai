"""From-scratch baseline CNN (architecture comparison).

Owner: Ali.

``build_model`` (see ``classifier.py``) is the torchvision-backbone registry —
resnet18 / resnet50 / efficientnet_b0. This standalone 6-layer CNN is the
*from-scratch* baseline those pretrained models are measured against. It lives in
the package (not only in the training notebook) so the app and ``inference`` can
rebuild the architecture to load its checkpoint.
"""

from __future__ import annotations

from typing import Any

import torch.nn as nn


class BasicCNN(nn.Module):
    """Six conv blocks -> global average pool -> linear head.

    The layer definitions must stay byte-compatible with the checkpoints trained
    in ``notebooks/Basic_CNN.ipynb`` (``dermaface_best_cnn.pt``); changing them
    invalidates ``load_state_dict``.
    """

    def __init__(self, num_classes: int) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(128, 256, kernel_size=3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(256, 256, kernel_size=3, padding=1), nn.ReLU(),
        )
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(256, num_classes)

    def forward(self, x: Any) -> Any:
        x = self.features(x)
        x = self.pool(x).flatten(1)
        return self.classifier(x)

    @property
    def gradcam_target_layer(self) -> Any:
        """The last conv layer — the spatial feature map Grad-CAM hooks."""
        convs = [m for m in self.features if isinstance(m, nn.Conv2d)]
        return convs[-1]
