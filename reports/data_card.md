# PlantVillage Data Card for PlantDiseaseAI

## Dataset identity and access

The project loads `mohanty/PlantVillage` through the upstream loader pinned at
revision `9e97599868962bd0079b8db4b7f1efa9185fa1e7`. The adapter uses the `default`
configuration and a local Hugging Face cache, normally `data/huggingface/`
([loader implementation](../src/plantdisease/data/huggingface.py),
[audit report](data_audit.md)). Raw images and cache files are not committed.

The upstream metadata states CC BY-SA 3.0 and exposes image, path, label, crop,
disease, and `leaf_id` fields ([audit report](data_audit.md)). Users remain
responsible for respecting upstream attribution/share-alike requirements and for
checking whether a proposed use is compatible with the dataset terms.

## Composition

| Item | Audited value | Evidence |
| --- | ---: | --- |
| Official train rows | 43,596 | [machine audit](../outputs/plantvillage/audit.json) |
| Official test rows | 10,709 | [final split manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/split.json) |
| Classes | 38 | [machine audit](../outputs/plantvillage/audit.json) |
| Train image size | 256 × 256 | [machine audit](../outputs/plantvillage/audit.json) |
| Exact duplicate groups in audited train split | 14 | [machine audit](../outputs/plantvillage/audit.json) |
| Invalid audited train samples | 0 | [machine audit](../outputs/plantvillage/audit.json) |

Class frequencies are uneven: for example, common classes have thousands of
training records while several healthy/disease classes have only hundreds
([machine audit](../outputs/plantvillage/audit.json)). Macro F1 is therefore
reported alongside Accuracy.

## Project split and label mapping

The selected seed-42 run stratifies the official train split into **37,058 train
and 6,538 validation rows**, and uses all **10,709 official test rows** only for
final evaluation ([split manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/split.json),
[run manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json)).
The same split manifest stores the ordered 38-class label mapping. Training,
evaluation, inference, and Demo load the checkpoint metadata rather than
maintaining independent label orders.

## Transform policy

The selected configuration uses **224 × 224** model inputs. Training applies a
`RandomResizedCrop(scale=(0.8, 1.0))`, `RandomHorizontalFlip`,
`RandomRotation(10)`, and `ColorJitter` with brightness, contrast, and saturation
set to `0.15` before ImageNet normalization. Validation, test, inference, and
Demo deterministically resize and normalize; random augmentation is not applied
outside training
([configuration](../configs/week3_ablation/09_combo_candidate.yaml),
[canonical transforms](../src/plantdisease/data/transforms.py)). In the
selected run, RandAugment, Random Erasing, Mixup, and CutMix are disabled
([configuration](../configs/week3_ablation/09_combo_candidate.yaml)).

## Official test-set role

The test split is used for final metric reporting and post-hoc error,
calibration, and Grad-CAM analysis. It is not used for optimizer updates,
checkpoint selection, early stopping, or hyperparameter tuning. The checkpoint
selection rule is best validation Macro F1
([run manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json)).

## Overlap and duplicate risk

The official train/test boundary has **0 overlapping `image_path` values but 227
overlapping `leaf_id` values** ([split audit](data_audit.md)). Multiple views or
derived images of the same physical leaf can therefore occur across official
splits. The train audit also found **14 exact-duplicate groups** within the
official train split ([machine audit](../outputs/plantvillage/audit.json)). These
facts prohibit describing the official-split scores as strictly leakage-free or
entity-isolated.

## Biases and unsuitable generalization

PlantVillage images have controlled backgrounds, centered leaves, a closed
taxonomy, and dataset-specific acquisition patterns. The data do not represent
the full variation of farms, cultivars, growth stages, devices, lighting,
weather, occlusion, mixed infections, nutrient stress, pesticide injury,
non-leaf symptoms, or unknown conditions. Dataset accuracy is not a field
diagnosis estimate.

## React Demo field example

The bundled React example is not part of the audited PlantVillage split. Its
SHA-256 is
`0364ff44229c70666216343057f9ae77d82438a7f842b30af1ffabb786061a7e`; it is an
**out-of-domain** field image with **no verified ground truth**. It exists only
to exercise upload, preprocessing, Top-5, Grad-CAM, and warning behavior. Any
displayed class is a model prediction and must not be added to dataset metrics
or treated as a corrected label ([browser QA](week8_react_demo_qa.md)).

## Privacy, storage, and governance

The dataset contains plant images rather than intended personal data, but users
should still review cached metadata before redistribution. Raw data, cache files,
and model weights remain Git-ignored. Only code, small reports, configurations,
hashes, and approved evidence summaries belong in the release candidate
([release manifest](release/week8_rc1_manifest.json)).

## Required future evaluation

Before any field claim, create a `leaf_id`-disjoint split, repeat training across
multiple seeds, audit both official splits symmetrically, evaluate external field
images and unknown inputs, document expert review, and test calibration/refusal
under domain shift. None of these steps is complete in the current release.
