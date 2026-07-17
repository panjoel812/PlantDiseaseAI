# Week 7 Showcase Architecture

This architecture diagram is intended for README, blog, and PPT use. It shows
the relationship between the verified classifier line, explainability, demo
deployment, and the exploratory VLM branch.

![PlantDiseaseAI Apple showcase architecture](media/week7_apple_architecture.png)

*The PlantVillage classifier is the verified main line; Qwen3-VL is a
secondary, exploratory smoke branch and does not replace classifier evidence.*

```mermaid
flowchart LR
    data["PlantVillage data\nHF cache + audit"] --> split["Official split\nleakage caveat recorded"]
    split --> train["Training pipeline\nconfigs, seeds, checkpoints"]
    train --> benchmark["Week 2 benchmark\n5 models, shared protocol"]
    train --> ablation["Week 3 ablation\nloss, scheduler, aug, EMA"]
    benchmark --> select["Frozen classifier\nResNet50 combo candidate"]
    ablation --> select
    select --> eval["Evaluation\nmetrics + calibration"]
    select --> explain["Week 4 explainability\nGrad-CAM + error analysis"]
    select --> serve["Serving layer\nTop-5 + Grad-CAM + knowledge cards"]
    serve --> streamlit["Week 5 Streamlit demo\neducational UI"]
    serve --> container["Apple container\nCPU-only demo image"]
    select --> vlmdata["Week 6 VQA seed\n24 images / 72 questions"]
    vlmdata --> qwen["Qwen3-VL MLX smoke\nprompt comparison"]
    qwen --> assistant["Safety-bounded assistant prototype\nsource + refusal rules"]
```

## How to explain the branches

- The classifier branch is the project core. It owns the measured classification
  metrics, Grad-CAM, error analysis, and demo inference.
- The deployment branch reuses the same serving layer so Streamlit and Apple
  `container` do not drift from offline inference.
- The VLM branch is exploratory. It uses source-grounded VQA data and Qwen3-VL
  smoke runs to test capability boundaries, not to replace the classifier.
- The assistant prototype is safety-bounded: it uses classifier context,
  provenance, and refusal behavior instead of presenting itself as a professional
  diagnosis system.

## Diagram caption

“PlantDiseaseAI keeps the verified classifier as the central system and routes
explainability, demo deployment, and VLM exploration through auditable evidence
paths. The VLM branch is explicitly exploratory and does not override classifier
results.”
