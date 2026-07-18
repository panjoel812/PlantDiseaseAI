# OpenLeaf-14: leaf-first plant and condition recognition

Status: experimental research scaffold; no dataset-scale training result is claimed.

## Research question

Can a low-compute system isolate one clear leaf, identify its plant before estimating
its condition, reject leaves outside a small catalog, and prevent background clutter
from controlling the prediction?

“Almost every plant” is not a measurable model claim. The operational target is an
**14 known crop leaves plus an explicit unknown result**. A rejected input must
not be routed to a host-specific disease model. This directly addresses the failure
mode in which an out-of-domain grape leaf is forced into the Tomato class and then
receives a high-confidence Tomato disease label.

## Architecture

```text
image
  -> OpenCV single-leaf mask + outline quality gates
       | rejected -> ask for one clear, complete leaf
       | accepted -> neutral-background leaf cutout + shape measurements
  -> frozen leaf encoder
  -> 14-species multi-prototype retrieval
  -> similarity + top-1/top-2 margin gates
       | rejected -> unknown plant; condition withheld
       | accepted
       v
     OpenCV lesion candidates constrained to the accepted leaf mask
       -> full isolated leaf + lesion boxes/crops
       -> host-specific condition model
       -> healthy / supported diseases / uncertain
       -> optional supervised lesion mask
```

The first catalog contains the 14 PlantVillage host groups already used by this
project: apple, blueberry, sour cherry, corn, grape, orange, peach, bell pepper,
potato, raspberry, soybean, squash, strawberry, and tomato. At least six completely
different leaf species are reserved for OOD calibration/testing. The full 1,081-class
Pl@ntNet label space is explicitly out of scope.

OpenCV exports a transparent cutout, a neutral-background RGB crop, the full-resolution
leaf mask, outline measurements, lesion overlay, and lesion-region crops. Training and
inference must use the same leaf preparation. Shape is useful evidence, but shape alone
cannot reliably distinguish every closely related species and can be deformed by disease;
the encoder therefore also sees leaf texture and venation inside the isolated mask.

The prototype index stores up to three centroids for each plant. New taxa require
embedding licensed single-leaf references and rebuilding a small CPU index; the frozen
encoder is not retrained. At 14 plants, three 1,280-D float32 prototypes require only
about 210 KiB before metadata.

## Data ladder and licensing boundary

| Purpose | Primary source | Scope | Use in this project |
| --- | --- | --- | --- |
| Optional leaf references/encoder | [Pl@ntNet-300K](https://github.com/plantnet/PlantNet-300K) | 306,146 images, 1,081 species, long-tailed | Use only licensed images matching the 14-leaf catalog or its pretrained encoder; do not train the full taxonomy |
| In-the-wild condition retrieval | [PlantWild / PlantWild_v2](https://tqwei05.github.io/PlantWild/) | Plant disease recognition with visual/text prototypes; v2 reports 115 classes | External condition benchmark; dataset license restricts commercial/derivative use |
| Lesion localization | [PlantSeg](https://www.nature.com/articles/s41597-025-06513-4) | Pixel masks for 115 diseases across 34 hosts | Supervised alternative to the deterministic OpenCV evidence mask |
| Small external test | [PlantDoc](https://arxiv.org/abs/1911.10317) | 2,598 field images, 13 plants, up to 17 diseases | Cross-source stress test, not training evidence |
| Existing regression set | PlantVillage | Controlled-background closed set | Keep only as a regression lane; never use its test set for threshold tuning |

Do not copy datasets into Git. Before training, produce a manifest with image-level
source and license fields and verify the upstream terms. PlantWild/PlantSeg terms are
not interchangeable with the repository code license.

## Frozen encoders, in order

1. **MobileNetV2 ImageNet** is the default smoke baseline already available through
   torchvision. It is small enough for CPU or Apple Silicon and produces 1,280-D
   features without gradients.
2. **Pl@ntNet ResNet18 features** are the first domain-specific comparison because the
   official repository publishes a pretrained checkpoint; its 1,081-way head is not
   used as this project's label space.
3. **DINOv2 ViT-S/14** is the stronger generic frozen-feature candidate. The official
   implementation publishes a 21M-parameter small backbone and linear/k-NN examples.
4. **MobileCLIP2-S0** is the optional mobile multimodal candidate. Code, weight, and
   training-data terms must be reviewed separately before redistribution.

No encoder wins by assumption. Selection is based on open-set validation, tail recall,
latency, peak memory, and license suitability.

## Split protocol

- Group every crop, augmentation, burst, or same observation by `entity_id`.
- Reject multi-leaf, truncated, tiny, non-leaf, flower, fruit, and stem-only inputs
  before species classification; keep these failures in the quality report.
- Create the OpenCV cutout before splitting, but group every derived cutout/mask/lesion
  crop with its original `entity_id` so derivatives cannot cross splits.
- When metadata exists, also isolate observer/site/time across the external test.
- The known validation split calibrates normal classification choices.
- `ood_validation` contains plant identities absent from the known catalog and is the
  only split used to choose rejection thresholds.
- `ood_test` contains disjoint unknown identities and is opened once for reporting.
- Disease evaluation is conditional on a correct, accepted plant and is also reported
  end-to-end so plant-routing errors cannot disappear from the result.

The executable manifest contract rejects duplicate `image_id` values and entity
leakage across splits. The example file is schema documentation only; its paths and
licenses must be replaced.

## Evaluation

Report all of the following instead of only closed-set accuracy:

- Plant identity: Top-1, Top-5, macro recall, and head/medium/tail recall.
- Unknown rejection: AUROC, AUPR-Out, FPR@95TPR, OSCR, and unknown false-accept rate.
- Condition: host-conditional Macro F1 and an explicit unsupported-condition rate.
- End-to-end: correct plant **and** correct condition, plus rejection/error breakdown.
- Efficiency: encoder, image size, precision, device, batch size, warm-up, latency,
  throughput, peak memory, index size, and catalog update time.
- Robustness: per-source results, multi-leaf scenes, non-leaf organs, blur, background,
  and non-plant negatives.

The current similarity/margin calibration is a transparent baseline, not a proven
optimal OOD method. An energy-score classifier is a later controlled comparison
because softmax scores can be overconfident on OOD inputs ([Energy-based OOD
detection](https://proceedings.neurips.cc/paper/2020/hash/f5496252609c43eb8a3d147ab9b9c006-Abstract.html)).

## Quick low-compute baseline

Prepare licensed images and a JSONL manifest following
`configs/openworld_manifest.example.jsonl`. Then run:

```bash
# First create leaf-only species inputs, masks, lesion overlays, and lesion crops.
uv run plant-openworld-prepare \
  --manifest path/to/raw_manifest.jsonl --image-root path/to/raw_images \
  --output-dir outputs/openworld/prepared_leaf14

# One-time frozen feature extraction. CPU is the portable default; use mps/cuda when available.
uv run plant-openworld-embed \
  --manifest outputs/openworld/prepared_leaf14/prepared_manifest.jsonl \
  --image-root outputs/openworld/prepared_leaf14 \
  --split train --device cpu --batch-size 32 \
  --output outputs/openworld/train_embeddings.npz

# No-gradient multi-prototype "training".
uv run plant-openworld-index \
  --embeddings outputs/openworld/train_embeddings.npz \
  --encoder-id torchvision/mobilenet_v2-imagenet1k-v2 \
  --max-prototypes-per-class 3 \
  --output-dir outputs/openworld/plant_index

# Extract validation and OOD-validation embeddings using the same encoder, then calibrate.
uv run plant-openworld-calibrate \
  --index-dir outputs/openworld/plant_index \
  --known outputs/openworld/validation_embeddings.npz \
  --unknown outputs/openworld/ood_validation_embeddings.npz

# Query one cached feature vector.
uv run plant-openworld-predict \
  --index-dir outputs/openworld/plant_index \
  --embedding path/to/one_embedding.npy
```

The preparation command does not modify originals. Samples whose outline is small,
truncated, fragmented, or split across multiple large green components are logged and
excluded. `plant-openworld-embed` may download torchvision's ImageNet weights on its
first run. The index/calibration/query commands are CPU-only NumPy/scikit-learn
operations. Cached embeddings make repeated experiments fast.

## Compute tiers

| Tier | Expected hardware | Trainable parameters | Intended experiment |
| --- | --- | ---: | --- |
| Tiny | CPU or 8–16 GiB Apple Silicon | 0 | MobileNetV2 features + prototype retrieval/OOD gates |
| Small | Apple Silicon or 8–16 GiB GPU | 0 or linear head | DINOv2-S / MobileCLIP2-S0 feature comparison |
| Optional | 16–24 GiB GPU | adapters/final blocks only | Domain adaptation after frozen baselines win |

## Milestones and honest exit criteria

1. **Synthetic implementation gate:** manifest, prototype persistence, calibration,
   and “unknown plant never reaches condition model” tests pass.
2. **Leaf-14 pilot gate:** 14 known crop leaves and at least six disjoint unknown leaf
   species; report segmentation acceptance/rejection errors plus
   open-set and efficiency metrics on a frozen split.
3. **Encoder gate:** compare at least two frozen encoders on the same prepared Leaf-14
   split. Full Pl@ntNet-300K training is not required.
4. **Condition gate:** only hosts with licensed condition data receive a model; missing
   hosts return `condition model unavailable` rather than a guessed disease.
5. **Field gate:** PlantWild/PlantDoc/source-held-out evaluation. Until this passes,
   no field-accuracy or universal-identification claim is allowed.

## Current implementation

- `src/plantdisease/openworld/manifest.py`: auditable JSONL manifest.
- `src/plantdisease/openworld/leaf_pipeline.py`: single-leaf cutout, shape features,
  leaf-constrained lesion boxes, and lesion crops.
- `src/plantdisease/openworld/preparation.py`: batch export without changing originals.
- `src/plantdisease/openworld/encoder.py`: frozen MobileNetV2 extraction.
- `src/plantdisease/openworld/index.py`: multi-prototype index and held-out OOD gates.
- `src/plantdisease/openworld/condition.py`: host-specific prototype condition model.
- `src/plantdisease/openworld/router.py`: plant-first condition routing.
- `configs/openworld_research.yaml`: protocol defaults and compute profiles.

The Leaf-14 PlantVillage closed-set pilot is complete: conditional Accuracy `0.9241`,
Macro F1 `0.9230`, and pipeline success `0.8827` when preprocessing rejection is
counted as failure under its seeded quota protocol. Full details and limitations are
in `reports/openleaf14_pilot.md`. Pl@ntNet, PlantWild, PlantSeg, and PlantDoc have not
been downloaded for this research line, and six-species OOD evaluation remains open.
