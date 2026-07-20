"""Render a contact sheet of augmented training images.

Owner: Rolando (Data QA).

Purpose: *see* what augmentation does before trusting it. Each row is one real
training image — the original on the left, then N augmented variants. Use it to
sanity-check that the erythema (redness) signal survives: if the augmented
variants look noticeably less red than the original, the colour jitter in
``Config`` is too aggressive and per-class recall for redness/rosacea will suffer.

Only the PIL-stage augmentations are shown (crop/flip/rotate/jitter) — the
ToTensor + normalize steps that follow don't change what the image looks like.

    python scripts/preview_augmentation.py --rows 6 --variants 4
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from PIL import Image  # noqa: E402

from dermaface.config import load_config  # noqa: E402
from dermaface.data.preprocessing import build_augment_pil  # noqa: E402


def _train_rows(cfg, limit: int, seed: int) -> list[dict]:
    """Sample rows from the frozen train split whose images are on disk."""
    path = cfg.manifest_path.with_name("train_manifest.csv")
    if not path.exists():
        path = cfg.clean_manifest_path if cfg.clean_manifest_path.exists() else cfg.manifest_path
    with path.open(newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("split", "train") == "train"]
    rows = [r for r in rows if (cfg.data_dir / r["path"]).exists()]
    if not rows:
        raise SystemExit(
            "No train images found on disk. Download images first "
            "(see SETUP_AND_RUN.md), then re-run."
        )
    rng = random.Random(seed)
    rng.shuffle(rows)
    return rows[:limit]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows", type=int, default=6, help="how many source images")
    ap.add_argument("--variants", type=int, default=4, help="augmented copies per image")
    ap.add_argument("--cell", type=int, default=160, help="thumbnail size in px")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    cfg = load_config()
    random.seed(args.seed)
    augment = build_augment_pil(cfg)
    rows = _train_rows(cfg, args.rows, args.seed)

    cell, pad = args.cell, 6
    cols = args.variants + 1
    sheet = Image.new(
        "RGB",
        (cols * cell + (cols + 1) * pad, len(rows) * cell + (len(rows) + 1) * pad),
        (255, 255, 255),
    )

    for r_i, row in enumerate(rows):
        with Image.open(cfg.data_dir / row["path"]) as im:
            original = im.convert("RGB")
            tiles = [original.resize((cell, cell))]
            for _ in range(args.variants):
                tiles.append(augment(original).resize((cell, cell)))
        for c_i, tile in enumerate(tiles):
            x = pad + c_i * (cell + pad)
            y = pad + r_i * (cell + pad)
            sheet.paste(tile, (x, y))

    out = args.out or (cfg.data_dir / "processed" / "augmentation_preview.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"Wrote {out}")
    print(f"  {len(rows)} images x {args.variants} variants (column 1 = original)")
    print(
        "  Check: augmented variants should keep roughly the same redness as the "
        "original. If they look washed out, lower cfg.aug_brightness / aug_contrast."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
