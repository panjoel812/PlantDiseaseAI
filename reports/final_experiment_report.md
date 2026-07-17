# PlantDiseaseAI Final Experiment Report

## Abstract

PlantDiseaseAI studies how far a reproducible closed-set image-classification
pipeline can go on PlantVillage while keeping engineering evidence, failure
analysis, and publication claims aligned. Under the PlantVillage official split,
the selected ResNet50 candidate reached **0.9953 Accuracy and 0.9941 Macro F1 on
10,709 test images**; this is a **single seed-42 result** and the split audit found
**227 overlapping `leaf_id` values** between train and test. These conditions are
part of the result, not footnotes ([metrics](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json),
[run manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json),
[machine-readable claim ledger](release/week8_claim_evidence.json),
[split audit](data_audit.md)). Historical Week 8 runtime audits independently
re-ran clean installation, tests, static checks, packaging, a synthetic smoke,
frozen local evidence, and an Apple `container` health lane
([reproducibility report](week8_reproducibility.md)).
The system remains an educational research prototype, not a professional plant
diagnosis tool.

## Research Question and Scope

The research question is: **Can a compact, auditable workflow compare standard
vision backbones, select training improvements through controlled ablation, and
serve interpretable predictions without overstating field validity?** The scope is
leaf-image classification over the **38 PlantVillage labels** represented in the
frozen split ([split manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/split.json)).
It excludes object detection, segmentation, unknown-disease discovery, treatment
prescription, and field deployment.

## Related Methods

The project uses TorchVision image-classification backbones, ImageNet-compatible
preprocessing, cross-entropy training, controlled regularization/scheduler
ablations, Grad-CAM relevance visualization, confusion/error analysis,
calibration analysis, and a resource-limited Qwen3-VL prompt study. The selected
training knobs are recorded in a machine-readable configuration, while the full
preprocessing recipe is defined jointly by that configuration and the canonical
transform implementation ([final configuration](../configs/week3_ablation/09_combo_candidate.yaml),
[canonical transforms](../src/plantdisease/data/transforms.py)); the
release candidate records environment, checkpoint, evidence hashes, and lane
status ([release manifest](release/week8_rc1_manifest.json)).

## Dataset and Split Audit

The fixed upstream loader revision is
`9e97599868962bd0079b8db4b7f1efa9185fa1e7`. The locally audited official train
split contains **43,596 RGB images, 38 labels, 14 exact-duplicate groups, and no
invalid samples** ([machine audit](../outputs/plantvillage/audit.json),
[audit report](data_audit.md)). The selected run partitions the official train
split into **37,058 train and 6,538 validation records**, then reserves the
official **10,709-image test split** for final evaluation
([split manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/split.json)).

The official train and test splits share **227 `leaf_id` values**, although no
identical `image_path` crosses the boundary
([machine-readable claim ledger](release/week8_claim_evidence.json),
[split audit](data_audit.md)). This
means all reported classification scores are official-split evidence, not proof
of entity-isolated generalization. A leaf-entity-disjoint protocol remains future
work.

## Shared Training and Evaluation Protocol

All main comparisons use a **224-pixel input**, stratified validation split,
best-validation-Macro-F1 checkpoint selection, and seed 42. Training applies
`RandomResizedCrop(scale=(0.8, 1.0))`, `RandomHorizontalFlip`,
`RandomRotation(10)`, and `ColorJitter` with brightness, contrast, and saturation
set to `0.15`; evaluation deterministically resizes and normalizes
([canonical transforms](../src/plantdisease/data/transforms.py)). The selected
ResNet50 was trained for **5 epochs**, with batch size **16**, learning rate
**0.001**, label smoothing **0.1**, cosine scheduling, and no EMA, Mixup, CutMix,
RandAugment, or Random Erasing ([final configuration](../configs/week3_ablation/09_combo_candidate.yaml),
[run manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json)).
The test split was not used for checkpoint selection, early stopping, or tuning.

Evaluation reports Accuracy, Macro Precision, Macro Recall, Macro F1, per-class
metrics, and the confusion matrix ([final metrics](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json)).
Speed measurements use MPS float32, exclude preprocessing, use **10 warm-up and
50 measured iterations**, and record batch sizes separately
([ResNet50 benchmark](../outputs/plantvillage/benchmarks/resnet50_seed42.json)).

## Five-Model Benchmark

The frozen benchmark compared MobileNetV2, ResNet18, ResNet50,
EfficientNet-B0, and EfficientNetV2-S under the shared official-split protocol
([benchmark report](week2_benchmark_progress.md)). ResNet50 was the accuracy
candidate at **0.9830 Accuracy / 0.9743 Macro F1**
([baseline metrics](../outputs/plantvillage/baseline_resnet50_seed42/metrics.json)).
MobileNetV2 was the lightweight candidate with **2.27M parameters, 0.31G FLOPs,
and 644.3 images/s** under the recorded MPS batch-32 protocol
([machine benchmark](../outputs/plantvillage/benchmarks/mobilenet_v2_seed42.json)).
Peak memory was not measured, and model batch sizes differed because of local
resource limits; therefore the table is an engineering comparison, not a
hardware-independent ranking.

## Controlled Ablation and Model Selection

Single-variable experiments tested label smoothing, focal loss, cosine
scheduling, EMA, RandAugment, Random Erasing, Mixup, and CutMix. Focal loss,
EMA, RandAugment, and Random Erasing were negative results relative to the frozen
ResNet50 baseline; they were retained in the experiment record rather than
discarded ([ablation results](week3_ablation_results.md)). Cosine scheduling was
the strongest single-variable run. The selected combination uses label smoothing
plus cosine scheduling and reached **0.9953 Accuracy / 0.9941 Macro F1** on the
official test split ([metrics](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json),
[configuration](../configs/week3_ablation/09_combo_candidate.yaml)).

That selected score is a **single seed-42 official-split observation**, and the
same split contains the known **227-`leaf_id` overlap**. It is not a multi-seed
confidence interval or entity-isolated estimate ([run manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json),
[split audit](data_audit.md)).

## Explainability, Error Analysis, and Calibration

The frozen test predictions contain **50 errors among 10,709 images**, including
**2 errors above the 0.80 confidence threshold**
([error-analysis JSON](../outputs/plantvillage/week4_explainability/error_analysis.json)).
Frequent patterns include visually similar maize lesions, cross-crop late-blight
confusion, and similar tomato spot conditions. A fixed atlas covers **24 samples,
6 in each confidence/correctness quadrant** ([atlas manifest](../outputs/plantvillage/week4_explainability/gradcam_atlas/gradcam_atlas_manifest.json)).

The fixed prediction set reports top-label **ECE 0.0965, MCE 0.3348, and Brier
0.0140** ([calibration JSON](../outputs/plantvillage/week4_explainability/calibration.json)).
These are descriptive calibration diagnostics, not proof that confidence is safe
for high-stakes use. Grad-CAM is a **non-causal relevance visualization**: it
shows sensitivity associated with a class score and cannot establish a causal
biological explanation ([stage report](week4_stage_report.md)).

## Serving, Streamlit, and Apple Container

The service exposes Top-5 predictions, confidence warnings, knowledge-card
fallbacks, and optional Grad-CAM through a Streamlit UI. The historical Week 5
Apple-container run observed **129.8 ms total** for one fixed synthetic image on
CPU; this is one engineering observation, not a latency benchmark
([container E2E JSON](../outputs/plantvillage/week5_demo/container_e2e.json)).
Week 8 separately observed **246.92 ms total** for one fixed synthetic MPS Demo
run; it is also not a benchmark ([reproducibility report](week8_reproducibility.md)).

Week 8 also introduced a React/Vite Liquid Glass research interface. Its bundled
field example has SHA-256
`0364ff44229c70666216343057f9ae77d82438a7f842b30af1ffabb786061a7e` and is an
**out-of-domain** image with **no verified ground truth**. One representative
local ResNet-50/MPS browser request returned `Cercospora leaf spot Gray leaf
spot` with probability **0.870144**; this is a model **prediction**, not truth or
field-accuracy evidence ([browser QA](week8_react_demo_qa.md)).

The recorded Week 8 Apple `container` lane built a Linux ARM64 CPU image, returned `ok`
from the Streamlit health endpoint, and recorded image digest
`sha256:ec4f25dc57a7fdc853355ad0e0dc3cc36032ed593e291e383cb357debd48ef4d`
([reproducibility report](week8_reproducibility.md)). The refreshed delivery
manifest marks the container lane `not_run` rather than inheriting that result.
No public deployment or
user-traffic evidence exists.

## Qwen3-VL Exploration and Safety Prototype

The resource-limited Qwen3-VL study used
`mlx-community/Qwen3-VL-4B-Instruct-4bit` on **5 images / 15 questions**. Choice
and few-shot-choice prompts each scored **11/15 exact matches**, but fine-grained
condition recognition remained **1/5**
([choice JSON](../outputs/plantvillage/week6_vlm/qwen3_vl_choice_smoke.json),
[few-shot JSON](../outputs/plantvillage/week6_vlm/qwen3_vl_few_shot_choice_smoke.json)).
This is smoke exploration only. It is not evidence of LoRA/QLoRA training, broad
VQA quality, field diagnosis, or completed human audit.

The optional React panel targets the same
`mlx-community/Qwen3-VL-4B-Instruct-4bit` runtime. The platform and MLX
dependency were available during browser QA, but default-cache weights were
absent, so `ready=false` and only the UI unavailable state was verified. The API
and browser perform **no automatic download**; a real browser response remains
unverified until the user explicitly caches the weights.

The safety prototype blocks high-risk treatment requests, low-confidence
classifier context, and out-of-scope input. It supplies educational wording only
([assistant evidence](week6_vlm_assistant.md)).

## Reproducibility Audit

The clean lane installed locked dependencies into a repository-external virtual
environment and passed **226 tests**, Ruff, `ty`, claim/link audit, synthetic
smoke, package build, and CLI help. It used CPU synthetic data and did not load
PlantVillage or the final checkpoint
([machine-readable claim ledger](release/week8_claim_evidence.json),
[reproducibility report](week8_reproducibility.md)).

The local lane then hashed the frozen checkpoint
(`d53c09ab7fd3e0d1e93fdfbbcac307ebde2d2ee40adfa66440068486374486cf`,
**94,660,305 bytes**), recomputed equality for metrics/error/calibration,
completed Top-5 and MPS Grad-CAM checks, and passed Apple-container health
([reproducibility report](week8_reproducibility.md)). Historical results and
Week 8 recomputation are distinguished in the audit report.

## Limitations and Agricultural Safety

- The best classifier result is single-seed and uses an official split with
  known `leaf_id` overlap; multi-seed and entity-isolated tests are incomplete.
- PlantVillage has controlled backgrounds and a closed label set; unknown
  diseases, non-leaf inputs, local cultivars, lighting, weather, and field clutter
  are outside validated scope.
- Peak memory, external field validation, full expert review, and prospective
  user evaluation are incomplete.
- Grad-CAM is non-causal, and confidence is not calibrated for professional
  decisions.
- VLM evidence is smoke-only; LoRA/QLoRA is incomplete.
- Outputs are educational. Consult qualified local plant-health or extension
  professionals and follow local regulation before treatment decisions.

## Ethics, Licenses, and Intended Use

The code is released under the repository MIT license ([project license](../LICENSE)).
The upstream PlantVillage loader states CC BY-SA 3.0 for the data
([data audit](data_audit.md)); raw data is cached locally and not committed.
TorchVision pretrained weights retain their upstream terms, and the project does
not claim ownership of them. Intended uses are reproducibility research,
coursework, model-comparison demonstrations, and educational prototyping.
Excluded uses include autonomous diagnosis, pesticide/dosage advice, regulatory
decisions, or claims of clinical/agronomic validation.

## Future Work

Priority experiments are: create a `leaf_id`-disjoint protocol; run repeated
seeds with uncertainty estimates; add field and unknown-class data; evaluate
calibration/refusal under domain shift; complete expert human audit; measure peak
memory consistently; and, only if resources permit, run a separately specified
LoRA/QLoRA experiment. None is represented as completed work.

## Evidence Index

| Evidence | Role |
| --- | --- |
| [Week 8 release manifest](release/week8_rc1_manifest.json) | Current source, environment, lock/checkpoint identities, tracked delivery hashes, and explicit `not_run` runtime lanes |
| [Week 8 claim evidence](release/week8_claim_evidence.json) | Locked claims, boundaries, and local-link audit status |
| [Final configuration](../configs/week3_ablation/09_combo_candidate.yaml) | Selected training protocol |
| [Final metrics](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json) | Test metrics and per-class results |
| [Final run manifest](../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json) | Seed, split sizes, environment, selection rule |
| [Error analysis](../outputs/plantvillage/week4_explainability/error_analysis.json) | Confusions and high-confidence errors |
| [Calibration](../outputs/plantvillage/week4_explainability/calibration.json) | ECE, MCE, Brier, reliability bins |
| [Qwen choice smoke](../outputs/plantvillage/week6_vlm/qwen3_vl_choice_smoke.json) | Small VLM prompt result |
