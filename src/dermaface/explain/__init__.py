"""Explainability: Grad-CAM heatmaps over the model's prediction.

Owners: Varsha (MLOps, compute) + Ali (UI/UX, overlay rendering), with Temirlan
supporting explainability evidence.
"""

from dermaface.explain.gradcam import GradCAMExplainer

__all__ = ["GradCAMExplainer"]
