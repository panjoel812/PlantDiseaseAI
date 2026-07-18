# PlantDiseaseAI ResNet50 Model Card

## Model identity

| Field | Value | Evidence |
| --- | --- | --- |
| Model | TorchVision ResNet50 closed-set classifier | [run manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json) |
| Output space | 38 PlantVillage labels | [split manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/split.json) |
| Logical checkpoint | `outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt` | [release manifest](release/week8_rc1_manifest.json) |
| Checkpoint SHA-256 | `d53c09ab7fd3e0d1e93fdfbbcac307ebde2d2ee40adfa66440068486374486cf` | [release manifest](release/week8_rc1_manifest.json) |
| Checkpoint size | 94,660,305 bytes | [release manifest](release/week8_rc1_manifest.json) |
| Training seed | 42 | [run manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json) |

The checkpoint is deliberately excluded from Git. Retrieve it from the local
logical path above (or an explicitly authorized artifact store in a future
release), then verify both byte size and SHA-256 against the tracked
[release manifest](release/week8_rc1_manifest.json). There is currently no public
checkpoint download claim.

## Architecture and preprocessing

The model replaces the ResNet50 classification head with a linear layer for the
PlantVillage closed set. Inputs are RGB leaf images resized to **224 × 224** and
normalized with ImageNet statistics; validation, test, inference, and Demo use
deterministic preprocessing ([configuration](../configs/week3_ablation/09_combo_candidate.yaml),
[transform implementation](../src/plantdisease/data/transforms.py)). Training uses
`RandomResizedCrop(scale=(0.8, 1.0))`, `RandomHorizontalFlip`,
`RandomRotation(10)`, and `ColorJitter` with brightness, contrast, and saturation
set to `0.15`; optional RandAugment and Random Erasing are disabled in the
selected recipe. Label smoothing is **0.1**, the scheduler is cosine, and EMA is
disabled ([configuration](../configs/week3_ablation/09_combo_candidate.yaml),
[canonical transforms](../src/plantdisease/data/transforms.py)).

## Training and evaluation

The official train split is stratified into **37,058 train and 6,538 validation
records**, with the official **10,709-record test split** reserved for final
evaluation ([split manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/split.json)).
The best validation-Macro-F1 checkpoint was selected at epoch **5**
([run manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json)).

The candidate produced **0.9953 Accuracy, 0.9951 Macro Precision, 0.9932 Macro
Recall, and 0.9941 Macro F1** on that official test split
([metrics](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json)).
These values are one seed 42 official split observation. The official train/test
split shares **227 `leaf_id` values**, so the result is not entity-isolated evidence
([split audit](data_audit.md)).

## Per-class behavior, errors, and calibration

The lowest observed class F1 was **0.9573** for maize Cercospora/gray leaf spot,
and common errors involved visually similar maize, late-blight, and tomato-spot
classes ([metrics](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json),
[error analysis](../outputs/plantvillage/week4_explainability/error_analysis.json)).
There were **50 errors**, including **2 above confidence 0.80**, among the official
test predictions ([error analysis](../outputs/plantvillage/week4_explainability/error_analysis.json)).

Top-label calibration diagnostics were **ECE 0.0965, MCE 0.3348, and Brier
0.0140** ([calibration JSON](../outputs/plantvillage/week4_explainability/calibration.json)).
No calibrated risk threshold has been validated for professional decisions.

## Explainability

The Demo targets ResNet50 layer `layer4.2` for Grad-CAM. The Week 8 audit
completed a **24-sample** fixed atlas covering **6 samples in each of four
correctness/confidence groups** ([reproducibility report](week8_reproducibility.md)).
Grad-CAM is a non-causal relevance visualization. It does not prove that a
highlighted region is a causal disease feature or a biologically valid diagnosis.

## Hardware and performance context

Training and frozen benchmarking were performed on Apple Silicon with MPS and
float32. The ResNet50 efficiency record reports **23.59M parameters, 4.11G FLOPs,
7.42 ms batch-1 mean latency, and 165.9 images/s at batch 32**, after **10 warm-up
and 50 measured iterations**, excluding preprocessing
([benchmark JSON](../outputs/plantvillage/benchmarks/resnet50_seed42.json)). These
are protocol- and hardware-specific measurements; peak memory was not measured.

The historical Week 5 container run observed **129.8 ms** for one fixed synthetic
CPU image ([container E2E](../outputs/plantvillage/week5_demo/container_e2e.json)).
The Week 8 local lane observed **246.92 ms** for one fixed synthetic MPS Demo
image ([reproducibility report](week8_reproducibility.md)). Neither single image
observation is a latency benchmark.

## React field-example boundary

The React research interface includes the user-supplied example
`app/examples/field_corn_leaf.jpeg`, SHA-256
`0364ff44229c70666216343057f9ae77d82438a7f842b30af1ffabb786061a7e`.
It is an **out-of-domain** field image with **no verified ground truth**. One
representative local MPS run returned the `Cercospora leaf spot Gray leaf spot`
class at **0.870144**; this is a closed-set model **prediction**, not a validated
label or field-performance result ([browser QA](week8_react_demo_qa.md)).

## Hierarchical demo addendum

The React/FastAPI demo now places a separately trained 14-class MobileNetV2
crop head before the frozen 38-class disease model. The crop head is trained
with balanced PlantVillage crop sampling and has local sampled official-test
Accuracy `0.977121` / Macro F1 `0.977101`; this is not an external field result.
Crop and disease confidence/margin gates independently abstain. OpenCV lesion
geometry is measured on the original upload but is not treated as a disease
label. The user-supplied multi-leaf grape image does not pass the crop gate, so
the demo correctly withholds diagnosis rather than asserting the expected file
label. See [hierarchical crop QA](week8_hierarchical_crop_qa.md).

## Intended uses

- Reproducibility, teaching, and research demonstrations.
- Closed-set PlantVillage experimentation and software integration tests.
- Human-reviewed exploration of model errors and non-causal visual relevance.

## Excluded uses

- Professional or autonomous crop diagnosis.
- Unknown disease, non-leaf, or field-scene recognition.
- Pesticide selection, dosage, treatment, insurance, or regulatory decisions.
- Any claim of multi-seed stability, field validation, or entity-isolated
  generalization.

## Biases and limitations

PlantVillage has controlled backgrounds and a restricted label vocabulary. The
official split has known leaf-entity overlap, class frequencies are uneven, and
the selected model has only a single formal seed. External field data, unknown
classes, local cultivars, varied acquisition devices, weather, occlusion, and
expert diagnostic agreement have not been validated. Predictions must be shown
with educational-use and domain-limit warnings.

## Dependencies and licenses

Project code is MIT-licensed ([license](../LICENSE)). The upstream data is
described as CC BY-SA 3.0 ([data audit](data_audit.md)). TorchVision pretrained
weights and their source datasets retain upstream terms; users must verify
suitability for their deployment. The locked Python environment and its hash are
recorded in the [release manifest](release/week8_rc1_manifest.json).
