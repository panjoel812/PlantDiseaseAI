# PlantDiseaseAI — One-Page Mentor Summary

## Question

This project asks whether an agricultural image-classification study can be made
useful for research applications by connecting model comparison, controlled
ablation, error analysis, explainability, serving, and reproducibility—without
turning a controlled-dataset score into a field-diagnosis claim.

## What was built

I implemented a shared PlantVillage data/training/evaluation pipeline, compared
five standard backbones, and selected a ResNet50 recipe through controlled
single-variable and combination ablations. The final system provides Top-5
inference, confidence/domain warnings, Grad-CAM, a Streamlit UI, and Apple
`container` packaging. Week 8 added an isolated locked install, complete tests,
static checks, package/CLI smoke, evidence hashes, frozen local recomputation,
and container health verification
([reproducibility report](../../reports/week8_reproducibility.md)).

## Measured result and its boundary

The selected label-smoothing + cosine-schedule ResNet50 reached **0.9953 Accuracy
and 0.9941 Macro F1 on 10,709 official-test images**
([metrics](../../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json)).
This is one **seed 42 official split** run
([run manifest](../../outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json)).
The data audit found **227 `leaf_id` values shared across official train and test
splits**, so this is not evidence of strict leaf-entity isolation or field
generalization ([split audit](../../reports/data_audit.md)).

Error analysis found **50 errors**, including **2 above confidence 0.80**, with
strong recurring confusions among visually similar maize, late-blight, and
tomato-spot classes
([error-analysis JSON](../../outputs/plantvillage/week4_explainability/error_analysis.json)).
Calibration diagnostics were **ECE 0.0965, MCE 0.3348, and Brier 0.0140**
([calibration JSON](../../outputs/plantvillage/week4_explainability/calibration.json)).
A fixed **24-sample** Grad-CAM atlas was reproduced, but Grad-CAM is treated only
as non-causal relevance visualization ([reproducibility report](../../reports/week8_reproducibility.md)).

## Negative results and engineering evidence

Focal loss, EMA, RandAugment, and Random Erasing underperformed the frozen
ResNet50 baseline; these negative experiments were retained
([ablation report](../../reports/week3_ablation_results.md)). The clean Week 8
lane passed **226 tests**, Ruff, `ty`, claim/link audit, package build, CLI help,
and a synthetic CPU smoke ([reproducibility report](../../reports/week8_reproducibility.md)).
Apple-container health passed, while the reported **129.8 ms CPU** and **246.92
ms MPS** values are each one fixed synthetic observation—not performance
benchmarks ([Week 5 E2E](../../outputs/plantvillage/week5_demo/container_e2e.json),
[Week 8 reproducibility report](../../reports/week8_reproducibility.md)).

The Qwen3-VL extension remains a small smoke study: choice/few-shot prompts scored
**11/15** overall but only **1/5** for condition recognition on **5 images**
([choice result](../../outputs/plantvillage/week6_vlm/qwen3_vl_choice_smoke.json),
[few-shot result](../../outputs/plantvillage/week6_vlm/qwen3_vl_few_shot_choice_smoke.json)).
No LoRA/QLoRA training or broad human validation was completed.

The Week 8 React interface was also browser-audited with the supplied image
(SHA-256 `0364ff44229c70666216343057f9ae77d82438a7f842b30af1ffabb786061a7e`).
It is an **out-of-domain** field example with **no verified ground truth**;
`0.870144` is a model **prediction**, not a validated label. The optional
`mlx-community/Qwen3-VL-4B-Instruct-4bit` runtime had no default-cache weights,
so `ready=false` and the UI unavailable state were verified. Browser/API
requests perform **no automatic download**
([browser QA](../../reports/week8_react_demo_qa.md)).

## Next experiments

The highest-value next step is a `leaf_id`-disjoint protocol with repeated seeds,
followed by external field/unknown-class evaluation and expert review. I would
then study calibration and refusal under domain shift before considering any VLM
fine-tuning. Peak-memory measurement and a pre-registered latency protocol are
also needed. Until those experiments exist, the project is an educational
research prototype and not professional agricultural diagnosis.
