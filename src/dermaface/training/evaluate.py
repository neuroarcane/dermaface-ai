"""Evaluation entry point — runs the frozen test set and reports metrics.

Owners: Iva (ML Research Lead) + Varsha (MLOps), with Temirlan supporting
evaluation outputs and explainability evidence.

Run:
    python -m dermaface.training.evaluate
"""

from __future__ import annotations

import argparse

from dermaface.config import Config, load_config


def parse_args() -> argparse.Namespace:
    cfg = load_config()
    p = argparse.ArgumentParser(description="Evaluate DermaFace on the test split")
    p.add_argument("--model-path", type=str, default=str(cfg.model_path))
    p.add_argument("--split", type=str, default="test", choices=["val", "test"])
    return p.parse_args()


def evaluate(cfg: Config, split: str = "test") -> dict:
    """Load the checkpoint, run inference on ``split``, return a metrics dict.

    TODO(Iva/Varsha/Temirlan):
      - load model (build_model + state_dict from cfg.model_path)
      - run over the split's DataLoader collecting y_true / y_pred / skin_types
      - metrics.classification_metrics + metrics.fairness_by_skin_type
      - save confusion matrix + a metrics.json for the report
    """
    raise NotImplementedError


def main() -> None:
    args = parse_args()
    cfg = load_config()
    cfg.model_path = type(cfg.model_path)(args.model_path)
    print(evaluate(cfg, split=args.split))


if __name__ == "__main__":
    main()
