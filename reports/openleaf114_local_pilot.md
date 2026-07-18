# OpenLeaf-114 local leaf identity pilot

## Outcome

The local 100+ class training path is operational. A frozen ImageNet MobileNetV2
encoder and class-balanced linear head were trained on 100 UCI Leaf100 silhouette
species plus 14 PlantVillage crop groups. This is a low-compute controlled-source
pilot, not evidence of field botanical accuracy.

Run ID: `leaf114-uci100-pv14-mobilenet-v2-frozen-seed42`

## Reproduction

```bash
uv run python scripts/train_leaf_catalog.py \
  --uci-archive /path/to/uci_leaf100.zip \
  --cache-dir data/huggingface \
  --output-dir outputs/openleaf/leaf114_uci100_pv14_balanced_seed42 \
  --head-epochs 80 --batch-size 64 --device cpu --seed 42
```

The UCI archive SHA-256 was
`2313a70de450a8a6b81696174f52be1c037090af53b37c6a6313f11245e5fd4c`.
The output checkpoint remains Git-ignored.

## Protocol

- UCI Leaf100: 100 species, 16 silhouettes per species, fixed 10/3/3
  train/validation/test split.
- PlantVillage: 14 crops, 64/16/32 accepted isolated leaves per crop from the
  existing official train/validation source and separate official test source.
- Total: 1,896 train, 524 validation, 748 test images.
- Encoder: pretrained MobileNetV2, frozen.
- Trainable component: 114-class classifier head.
- Loss: inverse-frequency class-weighted cross entropy.
- Selection: validation macro class accuracy.
- Device: CPU because the managed execution environment did not expose MPS.
- Duration: 112.31 seconds.

## Controlled-source test result

| Metric | Value |
| --- | ---: |
| Accuracy | 0.9158 |
| Macro precision | 0.9266 |
| Macro recall | 0.9138 |
| Macro F1 | 0.9117 |
| UCI Leaf100 source accuracy | 0.9133 |
| PlantVillage source accuracy | 0.9174 |

Checkpoint SHA-256:
`2ccc906155eab0b25dd392fdf1ea77f8708affc62abee95af59a8075da26ee6e`.

## Field checks

The bundled unverified corn field image ranked Corn (maize) at `0.9992`.

The user-supplied grape image `Guignardia_bidwellii_08.jpg` did **not**
generalize correctly:

| Candidate | Probability |
| --- | ---: |
| Strawberry | 0.4636 |
| Peach | 0.2401 |
| Grape | 0.2065 |

It therefore fails both the 0.60 confidence and 0.10 margin gates. The Demo
must withhold disease and management guidance for this input. Lowering the gate
to make this example pass would conceal domain shift and is not permitted.

## Interpretation

UCI Leaf100 is CC BY 4.0 and small enough for local training, but its images are
binary, controlled leaf silhouettes. PlantVillage also has controlled backgrounds.
The high held-out score mainly establishes reproducible catalog discrimination in
those sources. It does not establish robustness to outdoor illumination, multiple
leaves, severe disease, occlusion, camera noise, or unseen taxa.

Pl@ntNet remains an optional broad field identity provider. Its current Free plan
is suitable for a personal research Demo, while the local checkpoint provides an
offline and auditable fallback. Neither identity source changes the 14-host limit
of the local disease checkpoint.
