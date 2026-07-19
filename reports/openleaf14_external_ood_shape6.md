# OpenLeaf-14 external six-species outline stress test

Date: 2026-07-18  
Run ID: `leaf14-external-uci-shape6-seed42`  
Status: completed controlled outline stress test; **not field OOD evidence**

## Why the first external source was rejected

A license-audited iNaturalist candidate run used only research-grade observations and
CC0 / CC BY / CC BY-SA photos from the official open-data host. It attempted 175 photos,
the original OpenCV gate accepted 72, and the automatic acceptance rate was `0.4114`.

Visual inspection of all six contact sheets then showed that many accepted masks were
connected tree crowns, several leaves, grass, or other green background rather than one
isolated leaf. This is a real failure of the simple excess-green largest-component method
on field backgrounds. The 72 candidates were **not used for metrics**. The downloader now
names its output `candidate_manifest.jsonl` and requires a separate visual audit before it
can become evaluation data.

Local failed-candidate audit SHA-256:
`3f8b77c119a8dd437d7e9a51eba2f0cf9dc187f482ff99469fb4da6158da195c`.

## Replacement source and protocol

The replacement is the UCI One-hundred Plant Species Leaves dataset
([official page](https://archive.ics.uci.edu/dataset/241/one+hundred+plant+species+leaves+data+set),
[DOI](https://doi.org/10.24432/C5RG76)). UCI declares CC BY 4.0 and provides 16
single-leaf silhouette images per species. Archive SHA-256:
`2313a70de450a8a6b81696174f52be1c037090af53b37c6a6313f11245e5fd4c`.

This experiment uses all 16 samples for each frozen identity:

- OOD validation only: *Acer campestre*, *Betula pendula*, *Ginkgo biloba* (48).
- OOD test only: *Fagus sylvatica*, *Liquidambar styraciflua*,
  *Liriodendron tulipifera* (48).

No species identity crosses the OOD validation/test boundary. Each binary silhouette is
deterministically recolored canonical green on neutral gray so the existing RGB encoder
can consume it. This transformation preserves only outline. It contains no real color,
venation, lesion, or texture evidence.

The 14 known PlantVillage crops, split, checkpoint, and 448-leaf official test set are
unchanged from `leaf14-opencv-mobilenet-v2-frozen-pilot-seed42`. Prototypes are fitted on
known training features. Gates use known validation leaves plus the three OOD validation
species. The three OOD test species are opened once for the final result.

## Calibrated operating point

| Quantity | Value |
| --- | ---: |
| Similarity threshold | 0.6006 |
| Margin threshold | 0.00008 |
| Validation known correct accept | 0.8304 |
| Validation outline-unknown reject | 1.0000 |
| Two-term balanced score | 0.9152 |

The almost-zero margin threshold shows that this operating point is effectively a maximum
similarity gate, not a robust ambiguity detector.

## Frozen test result

| Metric | Result |
| --- | ---: |
| Known photographic test leaves | 448 |
| External outline-only test leaves | 48 |
| Prototype closed-set known Top-1 | 0.8705 |
| Known accept rate | 0.9955 |
| Known correct accept rate | 0.8661 |
| Accuracy among accepted known leaves | 0.8700 |
| Outline-unknown reject rate | 1.0000 |
| Outline-unknown false-accept rate | 0.0000 |
| AUROC (unknown positive) | 0.99995 |
| AUPR-Out | 0.99957 |
| FPR@95TPR | 0.0000 |
| OSCR (maximum similarity) | 0.8705 |

All 16 samples of each test species were rejected. Their most frequent forced known
candidates before rejection were Soybean for *Fagus*, Bell pepper for *Liquidambar*, and
Orange/Bell pepper for *Liriodendron*.

The near-perfect OOD ranking is **not evidence of a solved unknown-plant problem**. The
model can distinguish photographic PlantVillage inputs from textureless silhouette
proxies. The result is useful only as an outline/domain-shift stress test. A real color
single-leaf OOD test with masks or recorded manual audit is still required.

The independent closed-set crop head remains the relevant conditional reference:
Accuracy `0.9241`, Macro F1 `0.9230` on the same 448 accepted known test leaves. It is
carried forward, not recomputed as a disease metric in this OOD test.

## Artifacts

Local Git-ignored directories:

- `data/external_ood/uci_leaf100_leaf6_shape/`
- `outputs/plantvillage/leaf14_external_ood_shape6_seed42/`

| Artifact | SHA-256 |
| --- | --- |
| Metrics | `e6b0c506dd82cc86b1551349d7a4e4d79d0b29eaa1d376590f8d67dc03de8a39` |
| Calibration | `92c090cfc37dcc4e3c63c35d1ea7eb6397de874dbde5d89b111f2a1657780f2f` |
| Index metadata | `778e2904eb27bc6ad809bb2995ff73c8a3a2687efc642f79eb590c9a87a1b5b1` |
| Prototypes | `81a137ef5dada264f88e37f5470b76ace8ff4403f3b89d879a01c892dc75b068` |
| External dataset audit | `27a9c8d580fe2362f7ee7757320f78d453fc25015e1e4d02c425af67fe0049a9` |

Reproduction after downloading the UCI archive:

```bash
python scripts/build_uci_leaf_shape_ood.py \
  --archive /path/to/uci_leaf100.zip \
  --output-dir data/external_ood/uci_leaf100_leaf6_shape

HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 LOKY_MAX_CPU_COUNT=8 \
python scripts/run_leaf14_external_ood.py \
  --cache-dir data/huggingface \
  --pilot-dir outputs/plantvillage/leaf14_opencv_pilot_seed42 \
  --external-dir data/external_ood/uci_leaf100_leaf6_shape \
  --output-dir outputs/plantvillage/leaf14_external_ood_shape6_seed42
```

## Decision

Keep the outline result as a transparent negative/control experiment. Do not deploy its
thresholds. The next valid gate is a small, color, single-leaf external set with either
source masks or a documented two-person visual audit, followed by the frozen MobileNetV2,
DINOv2 ViT-S/14, and MobileCLIP2-S0 comparison.
