# OpenLeaf-14 internal six-species holdout

Date: 2026-07-18  
Run ID: `leaf14-open-set-internal-holdout6-seed42`  
Status: completed protocol sanity check; not external OOD evidence

## Protocol

This experiment reuses the frozen features and split from the OpenLeaf-14 closed-set
pilot. It temporarily removes six of the 14 PlantVillage crop groups from the prototype
catalog and treats them as pseudo-unknown species.

Known catalog (8): Apple, Corn, Grape, Orange, Bell pepper, Potato, Strawberry, Tomato.

Held-out pseudo-unknown (6): Blueberry, Sour cherry, Peach, Raspberry, Soybean, Squash.

- Prototypes are fitted only from known training features.
- Similarity and Top-1/Top-2 margin thresholds use known and pseudo-unknown validation
  features only.
- Reported metrics use independent official-test features.
- The full experiment is still one dataset/domain and does not replace external OOD.

## Calibration correction found during the run

The first calibration objective averaged known correct acceptance, unknown rejection,
and wrong-known rejection. That counted known rejection twice and selected a gate that
accepted only `33.20%` of known test leaves. The implementation was corrected so the
optimization balances only known correct acceptance and unknown rejection; wrong-known
rejection remains a reported diagnostic. The corrected run is the result below.

## Corrected validation operating point

| Quantity | Value |
| --- | ---: |
| Similarity threshold | 0.6207 |
| Margin threshold | 0.0505 |
| Known correct accept rate | 0.5781 |
| Pseudo-unknown reject rate | 0.8125 |
| Wrong-known reject rate (diagnostic) | 0.8000 |
| Two-term balanced score | 0.6953 |

## Independent test result

| Metric | Result |
| --- | ---: |
| Known test count | 256 |
| Pseudo-unknown test count | 192 |
| Closed-set known Top-1 | 0.8945 |
| Known accept rate | 0.6328 |
| Known correct accept rate | 0.6172 |
| Accuracy among accepted known leaves | 0.9753 |
| Pseudo-unknown reject rate | 0.7917 |
| Pseudo-unknown false-accept rate | 0.2083 |
| AUROC (unknown positive) | 0.7530 |
| AUPR-Out | 0.6510 |
| FPR@95TPR | 0.6797 |
| OSCR (maximum similarity) | 0.6840 |

The high `0.9753` accuracy among accepted known leaves is accompanied by only `0.6328`
known coverage and a `0.2083` pseudo-unknown false-accept rate. Therefore the method is
selective but not yet a reliable unknown-species gate. FPR@95TPR is especially weak.

## Artifacts

Local Git-ignored directory:
`outputs/plantvillage/leaf14_open_set_holdout6_seed42/`

| Artifact | SHA-256 |
| --- | --- |
| Metrics | `4a28e9e24c070d9f0b694d3d4d02f1fbe2e0ec78157f5cd8290727dd3b5b76fd` |
| Calibration | `a498a8bc7d4194d5ec52c31a2d0322d85bebb217ed7f00e50b2af79aa698a4b0` |
| Index metadata | `b3f4a3dccb1f19ab73bb71e4a45ecf8412c637e5fba5b87ad479af3a86e3c1f2` |
| Prototypes | `9c08f257dea01494bee08d82687bf5c227e13ef79e65deaf149392068e1062c6` |

Reproduction:

```bash
HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 LOKY_MAX_CPU_COUNT=8 \
uv run python scripts/run_leaf14_open_set_pilot.py \
  --cache-dir data/huggingface \
  --pilot-dir outputs/plantvillage/leaf14_opencv_pilot_seed42 \
  --output-dir outputs/plantvillage/leaf14_open_set_holdout6_seed42
```

## Decision

Keep this as a transparent baseline. Do not deploy these thresholds as universal OOD
protection. The next comparison must use genuinely external licensed single-leaf
species and a stronger frozen encoder or learned leaf representation. The external OOD
test remains untouched until its validation split and licenses are frozen.
