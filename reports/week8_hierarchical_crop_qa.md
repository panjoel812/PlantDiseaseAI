# Week 8 independent crop hierarchy QA

Date: 2026-07-18

## Implemented path

The interactive serving path is now:

1. OpenCV estimates visible leaf/lesion geometry, size, coarse colour, and
   distribution on the original image resolution.
2. A separate 14-class MobileNetV2 checkpoint estimates PlantVillage crop
   identity at 224 × 224.
3. Crop confidence must be at least 60% with a 10 percentage-point margin.
4. The frozen 38-class ResNet50 outputs are restricted to the accepted crop.
5. The leading crop-specific disease must reach 65% conditional probability
   and a 15 percentage-point margin. Otherwise diagnosis, Grad-CAM, and cloud
   management guidance are withheld.

OpenCV measurements are visual evidence, not a disease classifier. Both learned
models remain closed-set PlantVillage models.

## Crop checkpoint run

- Run ID: `crop-mobilenet-v2-frozen-seed42`
- Architecture: ImageNet-pretrained MobileNetV2, frozen feature extractor,
  trained crop-only linear head
- Seed: 42
- Balanced samples: 3,473 train, 896 validation, 1,792 official-test samples
- Device: CPU
- Best validation accuracy: 0.986607
- Official-test accuracy: 0.977121
- Official-test macro F1: 0.977101
- Checkpoint SHA-256:
  `5d7192ffa3bab24d0d12a91e6210e7bc89f86f0b0d16b6df81ab6110d6605390`
- Local evidence directory:
  `outputs/plantvillage/crop_mobilenet_v2_seed42/`

The generated checkpoint is intentionally Git-ignored. The public repository
contains the deterministic training command and implementation, not model
weights.

## User-supplied grape image

- File: `Guignardia_bidwellii_08.jpg`
- SHA-256:
  `efd397fbbb7fa2867ca566b21e10591b4b71ae8632a0b4ef37b2d2195abe62ad`
- Independent crop output: Tomato 47.99%, Cherry 46.45%, Grape 1.40%
- Crop margin: 1.54 percentage points
- Gate result: rejected
- Disease result: withheld
- Grad-CAM: withheld
- Management guidance: disabled

This multi-leaf external image still lies outside the reliable PlantVillage
crop distribution. The new crop head therefore does not turn the filename or
the user's expected label into ground truth. Its correct product behavior is to
abstain instead of presenting the prior incorrect Tomato/Late blight cascade.
External grape data and an entity-isolated field evaluation are required before
claiming that this specific image is recognized reliably.

## Verification

- Targeted Python service/API suite: 51 passed.
- Ruff on affected Python files: passed.
- React component/API tests and production build: recorded in the final commit
  verification for this change.
