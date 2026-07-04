"""Explainability: Grad-CAM heatmaps over the model's prediction.

Owners: Varsha (MLOps, compute) + Ali (UI/UX, overlay rendering).
"""

from dermaface.explain.gradcam import GradCAMExplainer

__all__ = ["GradCAMExplainer"]
