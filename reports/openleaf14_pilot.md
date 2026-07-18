# OpenLeaf-14 frozen-feature pilot

Date: 2026-07-18  
Run ID: `leaf14-opencv-mobilenet-v2-frozen-pilot-seed42`  
Status: completed low-compute closed-set pilot; OOD species evaluation not started

## Question

Does the same deterministic OpenCV single-leaf preparation work in training and
inference, and can a frozen lightweight encoder retain useful 14-crop identity
evidence after the background is removed?

## Protocol

| Item | Value |
| --- | --- |
| Dataset | Local cached PlantVillage official train/test split |
| Known leaf groups | 14 |
| Input | `opencv_exg_single_leaf_v1` neutral-background leaf cutout |
| Model | ImageNet-pretrained MobileNetV2, frozen features |
| Trainable part | Existing classifier head only |
| Seed | 42 |
| Train/validation | 80 accepted samples per crop, 16 reserved for validation |
| Test | 32 accepted samples per crop |
| Head epochs | 40 |
| Batch size | 64 |
| Device | CPU |
| Duration | 51.05 seconds |

Derived images remain grouped with their source index. The official split's known
historical `leaf_id` overlap remains a limitation. Test candidates are scanned in a
seeded order until the accepted per-crop quota is met; therefore this pilot is not
directly comparable to the earlier 128-per-crop crop checkpoint.

## Leaf preparation gate

| Selection pool | Attempted | Accepted | Rejected | Acceptance rate |
| --- | ---: | ---: | ---: | ---: |
| Train/validation | 1,188 | 1,120 | 68 | 94.28% |
| Test | 469 | 448 | 21 | 95.52% |

Corn accounted for 13 of 21 test rejections; 11 were caused by the leaf occupying
more than 90% of the image. This indicates that the fixed coverage gate is too strict
for some long corn leaves. The user-supplied multi-leaf grape image was also correctly
rejected by the current one-clear-leaf contract rather than forced into a class.

## Conditional classification result

These metrics are calculated only on the 448 accepted test leaves:

| Metric | Result |
| --- | ---: |
| Accuracy | 0.9241 |
| Macro Precision | 0.9264 |
| Macro Recall | 0.9241 |
| Macro F1 | 0.9230 |
| Best validation accuracy | 0.9330 |

The weakest class was Apple (`0.6875` recall); Grape, Peach, and Potato each had
`0.84375` recall. Corn had `1.0000` conditional recall, but its preprocessing rejection
rate was high. Reporting only conditional accuracy would hide that failure.

Counting preprocessing rejection as an unsuccessful end-to-end result, 414 of the 469
attempted test candidates were both accepted and correctly classified (`0.8827`). This
is a pipeline success rate for this seeded quota protocol, not an open-set metric.

## Inference contract verification

- The checkpoint stores `input_preprocessing=opencv_exg_single_leaf_v1`.
- `CropClassifier.from_checkpoint` restores that field and applies isolation to raw
  images automatically.
- A held-out raw test image at test index 7 was isolated and predicted as Raspberry,
  matching the label, with model probability `0.9988`. This one sample is a wiring
  check, not an additional performance result.
- Leaf isolation failures raise an input validation error before crop/disease routing.
- Lesion analysis uses the accepted full-resolution leaf mask, so candidate boxes do
  not originate from the discarded background.

## Artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| Local checkpoint | `77803bd460afa385400b551c160ff00cf15e3ecabd65bf812f32f33ea4fb9bfa` |
| Metrics JSON | `ef317ad9e18b03063a464db5924c2677dd2049a1a0e9912c81f3dd492c3ecca0` |
| Leaf audit JSON | `22f6a2532d4ae521774aa25e49b8f6a37e916775840148a404b52f253cbd5a32` |

The checkpoint and run outputs are local and Git-ignored. Recreate them with:

```bash
HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 \
uv run python scripts/train_crop_classifier.py \
  --cache-dir data/huggingface \
  --output-dir outputs/plantvillage/leaf14_opencv_pilot_seed42 \
  --selected-per-crop 80 --validation-per-crop 16 --test-per-crop 32 \
  --head-epochs 40 --batch-size 64 --device cpu --leaf-isolation
```

## Boundaries and next gate

- This is PlantVillage closed-set crop identity, not field species recognition.
- The probability is not calibrated for unknown leaves.
- No six-species OOD validation/test set exists yet; AUROC, FPR@95TPR, OSCR, and
  unknown false-accept rate remain unmeasured.
- OpenCV lesion boxes are deterministic candidates, not lesion ground truth.
- Next: freeze six licensed OOD leaf species, calibrate prototype rejection without
  touching OOD test, and compare strict single-leaf gating against a learned mask.
