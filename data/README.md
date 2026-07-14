# Data

**Nothing in `data/` is committed** (except this README and `.gitkeep` files). No images, no PII — ever. See `.gitignore`.

## Layout

- `raw/` — original dataset downloads. **Immutable.** Never edit in place.
- `processed/` — cleaned, harmonized, split data ready for training + a `manifest.csv`.
- `external/` — label maps, taxonomy files, and `PROVENANCE.md` (where each dataset came from + its license).

## Get the data

- **[raw-data-sources.md](raw-data-sources.md)** — Hessam's full reference on every candidate source (contents, access/download location, license terms, canonical folder names, required provenance fields).
- **[../docs/data-strategy.md](../docs/data-strategy.md)** — sources, licensing, and the processing pipeline.

Owner: Aparna + Rolando.

## `manifest.csv` schema (target)

| column | description |
|---|---|
| `path` | relative path to the processed image |
| `label` | acne / rosacea / redness / clear |
| `severity` | mild / moderate / severe / n/a |
| `skin_type` | Fitzpatrick I–VI |
| `source` | fitzpatrick17k / skincon / scin |
| `split` | train / val / test |
