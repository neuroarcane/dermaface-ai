"""Dataset acquisition helpers.

Owner: Aparna (Data Lead).

Downloads/organizes the three source datasets into ``data/raw/``:
  - Fitzpatrick17k   https://github.com/mattgroh/fitzpatrick17k
  - SKINCON          https://skincon-dataset.github.io/
  - Google SCIN      https://github.com/google-research-datasets/scin

⚠️ Verify each dataset's LICENSE before downloading (see docs/data-strategy.md)
and record provenance in data/external/PROVENANCE.md. Never commit images.
"""

from __future__ import annotations

from pathlib import Path

from dermaface.config import load_config

SOURCES = ("fitzpatrick17k", "skincon", "scin")


def download_all(raw_dir: Path | None = None) -> None:
    """Download every source dataset into ``raw_dir`` (default: data/raw)."""
    raw_dir = raw_dir or (load_config().data_dir / "raw")
    for source in SOURCES:
        download_source(source, raw_dir)


def download_source(source: str, raw_dir: Path) -> None:
    """Download a single dataset by name into ``raw_dir/<source>``.

    TODO(Aparna): implement per-source fetch. Each dataset has different
    access mechanics (git-lfs, gsutil, manual form). Keep raw/ immutable.
    """
    if source not in SOURCES:
        raise ValueError(f"Unknown source {source!r}; expected one of {SOURCES}")
    raise NotImplementedError(f"download for {source!r} not implemented yet")


if __name__ == "__main__":
    download_all()
