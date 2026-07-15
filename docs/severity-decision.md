# Model Backbone & Severity Decision

> **Owners:** Iva (ML Research) + Ali (documentation). This write-up records
> decisions **Iva** made; the numbers are hers to confirm. Ali drafted the doc
> and the `severity_map.csv` template — thresholds are **proposed, pending Iva's
> validation on the real SKINCON data.**

Relates to issue #1. See also [requirements.md](requirements.md), [data-strategy.md](data-strategy.md).

## 1. Backbone decision — ResNet50 (transfer learning)

**Decision:** use a **ResNet50** pretrained on ImageNet and **fine-tune** it
(instruction option 3-2), rather than training from scratch.

**Why (Iva's rationale, from the 2026-07-13 standup):**
- Pretrained on ImageNet → already knows general visual features (edges, textures), so it learns skin conditions from far fewer images.
- Reliable, well-supported architecture with a good **accuracy-vs-compute balance** for 224×224 image classification.

**Alternatives considered:**
- *Train a CNN from scratch* (option 3-1) — kept as a **from-scratch baseline** for comparison (Varsha), but needs much more data/compute to match a pretrained model.
- *YOLO / object detection* — **rejected**: our task is whole-image *classification* + Grad-CAM localization; our datasets have no lesion bounding boxes, and YOLO would make Grad-CAM redundant.

**Where it lives:** `cfg.backbone = "resnet50"` in `src/dermaface/config.py`.

## 2. Severity decision — concept-derived proxy

**The problem:** our datasets label the *condition* (acne/rosacea/redness) but **not**
severity. So severity must be *derived*.

**Decision:** **Option 1 — concept-derived proxy** (Iva). Use **SKINCON's** clinical
concept annotations (inflammatory signs such as erythema, papules, pustules) to bucket
each image into **mild / moderate / severe**. Cheap and defensible, but approximate.

**Alternatives considered** (from [data-strategy.md](data-strategy.md)):
- Rule-based lesion counting — more faithful, much more work.
- Manual re-labelling of a subset — high quality, low quantity.
- De-scope severity to condition-only — the safe fallback if the proxy proves unreliable.

**Open question for Iva/Aparna (to confirm on real data):** SKINCON annotations are
largely **concept *presence*** (per image), which may not give fine-grained *counts*.
If only presence is available, the bands below use a **weighted concept score** rather
than lesion counts. Confirm the annotation granularity when the data lands.

## 3. Severity mapping scheme (→ `data/external/severity_map.csv`)

Proposed rulebook (a "severity score" = sum of weights of inflammatory concepts present,
then bucketed). **DRAFT — thresholds subject to Iva's tuning on SKINCON.**

| Band | Score | Meaning |
|---|---|---|
| n/a | 0 | `clear` class — no target condition |
| mild | 1–2 | few / low-intensity inflammatory concepts (e.g. mild erythema) |
| moderate | 3–4 | multiple inflammatory concepts (e.g. erythema + papules) |
| severe | 5+ | extensive / pustular involvement |

Proposed concept weights (higher = stronger severity signal):

| Concept | Weight |
|---|---|
| erythema | 1 |
| papule | 1 |
| plaque | 1 |
| scale | 1 |
| pustule | 2 |

The machine-readable version is [`data/external/severity_map.csv`](../data/external/severity_map.csv).
Aparna applies it to the manifest during data processing (`severity` column).

## 4. Definition of done (issue #1)
- [x] Backbone locked (ResNet50) — documented above.
- [x] Severity method decided (concept-derived proxy) — documented above.
- [~] `severity_map.csv` produced as a **draft**; final thresholds pending Iva's validation on SKINCON.
