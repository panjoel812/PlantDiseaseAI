# OpenPlant-H: compute-efficient open-world plant and condition recognition

Status: experimental research scaffold; no dataset-scale training result is claimed.

## Research question

Can a low-compute system identify a plant before estimating its condition, reject
plants outside its catalog, and add new taxa without retraining one global disease
classifier?

“Almost every plant” is not a measurable model claim. The operational target is an
**expandable known catalog plus an explicit unknown result**. A rejected input must
not be routed to a host-specific disease model. This directly addresses the failure
mode in which an out-of-domain grape leaf is forced into the Tomato class and then
receives a high-confidence Tomato disease label.

## Architecture

```text
image
  -> quality / plant-part checks
  -> frozen image encoder
  -> family / genus / species multi-prototype retrieval
  -> similarity + top-1/top-2 margin gates
       | rejected -> unknown plant; condition withheld
       | accepted
       v
     host-specific condition model
       -> healthy / supported diseases / uncertain
       -> optional OpenCV visible-lesion evidence
       -> optional supervised lesion mask
```

The prototype index stores up to three centroids for each plant because a single
centroid is usually too restrictive for leaf, flower, fruit, field, and herbarium
views. New taxa require embedding their licensed reference images and rebuilding a
small CPU index; the frozen encoder is not retrained. For `C` plants, `K` prototypes,
and `D` float32 features, storage is approximately `C × K × D × 4` bytes. At 1,081
plants, three 512-dimensional prototypes occupy about 6.3 MiB before metadata.

## Data ladder and licensing boundary

| Purpose | Primary source | Scope | Use in this project |
| --- | --- | --- | --- |
| Plant identity | [Pl@ntNet-300K](https://github.com/plantnet/PlantNet-300K) | 306,146 images, 1,081 species, long-tailed | First frozen-encoder/prototype benchmark; preserve per-image author/license metadata |
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
2. **Pl@ntNet ResNet18** is the first domain-specific comparison because the official
   Pl@ntNet-300K repository publishes a pretrained checkpoint.
3. **DINOv2 ViT-S/14** is the stronger generic frozen-feature candidate. The official
   implementation publishes a 21M-parameter small backbone and linear/k-NN examples.
4. **MobileCLIP2-S0** is the optional mobile multimodal candidate. Code, weight, and
   training-data terms must be reviewed separately before redistribution.

No encoder wins by assumption. Selection is based on open-set validation, tail recall,
latency, peak memory, and license suitability.

## Split protocol

- Group every crop, augmentation, burst, or same observation by `entity_id`.
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
# One-time frozen feature extraction. CPU is the portable default; use mps/cuda when available.
uv run plant-openworld-embed \
  --manifest path/to/manifest.jsonl --image-root path/to/data \
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

`plant-openworld-embed` may download torchvision's ImageNet weights on its first run.
The other three commands are CPU-only NumPy/scikit-learn operations. Cached embeddings
make repeated threshold or prototype experiments fast.

## Compute tiers

| Tier | Expected hardware | Trainable parameters | Intended experiment |
| --- | --- | ---: | --- |
| Tiny | CPU or 8–16 GiB Apple Silicon | 0 | MobileNetV2 features + prototype retrieval/OOD gates |
| Small | Apple Silicon or 8–16 GiB GPU | 0 or linear head | DINOv2-S / MobileCLIP2-S0 feature comparison |
| Optional | 16–24 GiB GPU | adapters/final blocks only | Domain adaptation after frozen baselines win |

## Milestones and honest exit criteria

1. **Synthetic implementation gate:** manifest, prototype persistence, calibration,
   and “unknown plant never reaches condition model” tests pass.
2. **Pilot gate:** at least 20 known plants and 10 disjoint unknown plants; report
   open-set and efficiency metrics on a frozen split.
3. **Scale gate:** Pl@ntNet-300K benchmark with head/medium/tail results and at least
   two encoders under the same protocol.
4. **Condition gate:** only hosts with licensed condition data receive a model; missing
   hosts return `condition model unavailable` rather than a guessed disease.
5. **Field gate:** PlantWild/PlantDoc/source-held-out evaluation. Until this passes,
   no field-accuracy or universal-identification claim is allowed.

## Current implementation

- `src/plantdisease/openworld/manifest.py`: auditable JSONL manifest.
- `src/plantdisease/openworld/encoder.py`: frozen MobileNetV2 extraction.
- `src/plantdisease/openworld/index.py`: multi-prototype index and held-out OOD gates.
- `src/plantdisease/openworld/condition.py`: host-specific prototype condition model.
- `src/plantdisease/openworld/router.py`: plant-first condition routing.
- `configs/openworld_research.yaml`: protocol defaults and compute profiles.

This implementation establishes the research baseline only. It has not yet downloaded
Pl@ntNet, PlantWild, PlantSeg, or PlantDoc and reports no real-data result.
