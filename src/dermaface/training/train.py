"""Training entry point.

Owners: Varsha (MLOps, infra/tracking) + Iva (ML Research, loss/schedule),
with Temirlan validating model outputs needed for evaluation and inference.

Run:
    python -m dermaface.training.train            # uses defaults from config
    python -m dermaface.training.train --epochs 5

The CLI wiring, seeding, and checkpoint plumbing are scaffolded. The training
loop body is a TODO so the owners can make the modelling decisions.
"""

from __future__ import annotations

import argparse

from dermaface.config import Config, load_config


def parse_args() -> argparse.Namespace:
    cfg = load_config()
    p = argparse.ArgumentParser(description="Train DermaFace classifier")
    p.add_argument("--epochs", type=int, default=cfg.epochs)
    p.add_argument("--batch-size", type=int, default=cfg.batch_size)
    p.add_argument("--lr", type=float, default=cfg.learning_rate)
    p.add_argument("--backbone", type=str, default=cfg.backbone)
    p.add_argument("--seed", type=int, default=cfg.seed)
    return p.parse_args()


def set_seed(seed: int) -> None:
    """Seed python, numpy, and torch for reproducibility."""
    import random

    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def train(cfg: Config) -> None:
    """Full training run.

    TODO(Varsha/Iva/Temirlan):
      - build_dataloaders(cfg)  (dermaface.data.dataset)
      - build_model(cfg)        (dermaface.models)
      - loss (weighted CE for class imbalance), optimizer (AdamW), scheduler
      - epoch loop w/ train + val, log metrics (dermaface.training.metrics)
      - track with W&B/MLflow; checkpoint best val macro-F1 -> cfg.model_path
    """
    set_seed(cfg.seed)
    raise NotImplementedError("training loop not implemented yet")


def main() -> None:
    args = parse_args()
    cfg = load_config()
    cfg.epochs = args.epochs
    cfg.batch_size = args.batch_size
    cfg.learning_rate = args.lr
    cfg.backbone = args.backbone
    cfg.seed = args.seed
    train(cfg)


if __name__ == "__main__":
    main()
