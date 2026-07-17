# Week 3 Ablation Design

## Context

Week 2 has closed the official-split model benchmark. ResNet50 is the current
best-accuracy candidate with Test Accuracy 0.9830 and Macro F1 0.9743.
MobileNetV2 is the default lightweight deployment candidate.

Week 3 will use ResNet50 as the high-accuracy baseline and run a controlled
ablation study. The goal is not to make every technique look good. The goal is
to learn which change actually helps under this project's data, metric, and
hardware constraints.

The user also wants to understand the steps and mathematical principles, so the
implementation and reports must explain both:

- what command or code change happens at each step;
- what mathematical assumption or training dynamic that step is testing.

## Goal

Build a configurable Week 3 training system and experiment matrix for
single-seed ablation experiments on ResNet50, then use real metrics to choose
the final classification model.

## Scope

The standard Week 3 budget is:

- model: ResNet50;
- seed: 42;
- epochs: 5;
- split: current PlantVillage official split protocol;
- batch size: 16, matching the Week 2 ResNet50 run;
- metric for selection: validation Macro F1;
- final comparison: official test split metrics plus efficiency context.

The first formal ablation matrix contains one-variable experiments:

| Experiment | Single changed factor |
| --- | --- |
| `label_smoothing` | CrossEntropy label smoothing = 0.1 |
| `focal_loss` | Focal Loss gamma = 2.0 |
| `randaugment` | Add RandAugment to train image transforms |
| `random_erasing` | Add RandomErasing after tensor normalization |
| `mixup` | Add batch-level Mixup, alpha = 0.2 |
| `cutmix` | Add batch-level CutMix, alpha = 1.0 |
| `cosine_scheduler` | Add per-optimizer-step cosine LR schedule |
| `ema` | Add EMA weights for validation, test, and checkpoint selection |

A combination experiment will only be selected after the one-variable results
are reviewed. The default candidate combination is:

```text
label_smoothing + randaugment + cosine_scheduler + ema
```

Mixup and CutMix will not be included in the first combination unless their
single-variable results support that choice.

## Non-Goals

- Do not start Week 4 Grad-CAM, calibration, or error-analysis work in this
  design.
- Do not change the data split protocol inside Week 3. A leaf-entity-isolated
  split would be a new protocol version and must not be mixed silently with the
  current official-split benchmark.
- Do not claim multi-seed robustness. This Week 3 version is a standard
  single-seed ablation. Reports must state that limitation.
- Do not report peak memory unless a reliable measurement method is added later.

## Architecture

Week 3 should add small focused modules instead of turning
`src/plantdisease/training/baseline.py` into a large experiment script.

Planned modules:

```text
src/plantdisease/training/losses.py
src/plantdisease/training/mix.py
src/plantdisease/training/schedulers.py
src/plantdisease/training/ema.py
src/plantdisease/data/transforms.py
src/plantdisease/config.py
src/plantdisease/training/engine.py
src/plantdisease/training/baseline.py
```

Responsibilities:

- `losses.py`: CrossEntropy with hard or soft targets, Label Smoothing, and
  Focal Loss.
- `mix.py`: Mixup and CutMix batch transforms plus validation of mutually
  exclusive settings.
- `schedulers.py`: cosine scheduler construction and schedule metadata.
- `ema.py`: EMA shadow weights, temporary weight swapping, and checkpoint
  support.
- `transforms.py`: optional RandAugment and RandomErasing while preserving
  baseline transforms when all switches are off.
- `config.py`: typed config sections for augmentation, loss, scheduler, and EMA.
- `engine.py`: minimal hooks for batch mixing, scheduler stepping, and EMA
  updates.
- `baseline.py`: orchestration, output manifests, and saving evidence files.

All new switches default to off. With every Week 3 switch disabled, training
should match the Week 2 baseline behavior as closely as possible. If a small
non-functional difference is introduced, such as extra metadata in the manifest,
it must be documented.

## Config Design

Existing configs have `data`, `model`, and `training` sections. Week 3 will add
optional sections:

```yaml
augmentation:
  randaugment_enabled: false
  randaugment_num_ops: 2
  randaugment_magnitude: 9
  random_erasing_enabled: false
  random_erasing_probability: 0.25
  mixup_alpha: 0.0
  cutmix_alpha: 0.0

loss:
  name: cross_entropy
  label_smoothing: 0.0
  focal_gamma: 2.0

scheduler:
  name: none
  eta_min: 0.0

ema:
  enabled: false
  decay: 0.999
```

Validation rules:

- `mixup_alpha` and `cutmix_alpha` cannot both be positive in this version.
- `loss.name` must be `cross_entropy` or `focal`.
- `label_smoothing` must be in `[0.0, 1.0)`.
- `focal_gamma` must be non-negative.
- `scheduler.name` must be `none` or `cosine`.
- `ema.decay` must be in `[0.0, 1.0)`.

## Mathematical Learning Notes

### Baseline CrossEntropy

For logits `z`, softmax probabilities are:

```text
p_k = exp(z_k) / sum_j exp(z_j)
```

For a hard class label `y`, CrossEntropy is:

```text
L = -log(p_y)
```

This asks the model to put as much probability as possible on the true class.
It is a strong baseline, but it can become over-confident on controlled datasets
like PlantVillage.

### Label Smoothing

Label smoothing replaces the one-hot target with a softened target
distribution. With `K` classes and smoothing value `epsilon`, the target is
approximately:

```text
q_y = 1 - epsilon
q_k = epsilon / (K - 1), for k != y
L = -sum_k q_k log(p_k)
```

The intuition: the model is still rewarded most for the true class, but it is
discouraged from assigning probability 1.0 to a single class. This can improve
generalization and calibration, especially when labels are noisy or classes are
visually similar.

### Focal Loss

Focal Loss changes CrossEntropy by down-weighting easy examples:

```text
p_t = p_y
L = -(1 - p_t)^gamma log(p_t)
```

If the model already predicts the right class with high confidence, `p_t` is
large and `(1 - p_t)^gamma` is small. The loss contribution shrinks. If the
example is hard, `p_t` is small and the loss stays large.

The intuition: training spends relatively more gradient budget on hard or
minority examples. The risk is that it can over-focus on noisy samples or make
optimization less stable.

### Mixup

Mixup forms a convex combination of two images and two labels:

```text
lambda ~ Beta(alpha, alpha)
x' = lambda x_i + (1 - lambda) x_j
y' = lambda onehot(y_i) + (1 - lambda) onehot(y_j)
L = lambda CE(model(x'), y_i) + (1 - lambda) CE(model(x'), y_j)
```

The intuition: the model learns smoother decision boundaries between classes.
Instead of treating every training image as an isolated point, it learns that
linear blends should have blended labels. This can reduce memorization, but for
fine-grained plant disease patterns it may sometimes create unnatural examples.

### CutMix

CutMix pastes a rectangle from one image into another and mixes labels according
to the pasted area:

```text
x' = x_i with a patch from x_j
lambda_adjusted = 1 - patch_area / image_area
y' = lambda_adjusted onehot(y_i) + (1 - lambda_adjusted) onehot(y_j)
```

The intuition: the model cannot rely on one small discriminative region or a
background shortcut. It must learn from partial evidence. The risk is that leaf
disease images may become visually implausible if the pasted patch cuts through
the most important lesion pattern.

### RandAugment

RandAugment samples a fixed number of image operations, such as rotation,
contrast, or color changes, using a fixed magnitude:

```text
N = number of operations
M = shared magnitude
```

The intuition: it exposes the model to plausible visual variation without
hand-tuning many augmentation probabilities. It tests whether the Week 2
baseline is too specialized to the training image appearance.

### Random Erasing

Random Erasing removes or overwrites a random rectangle after the image has been
converted to a tensor:

```text
x' = x with rectangle R replaced by a constant or random value
```

The intuition: it simulates occlusion and forces the model to distribute
attention across more of the leaf. The risk is that erasing disease lesions can
make the training label partially inconsistent with the image.

### Cosine Scheduler

The cosine learning-rate schedule changes the learning rate over optimizer
steps:

```text
lr_t = eta_min + 0.5 * (lr_max - eta_min) * (1 + cos(pi * t / T))
```

Here `t` is the optimizer step index and `T = epochs * train_batches`. There is
no warmup in the first Week 3 version. The scheduler steps after each optimizer
update.

The intuition: training begins with the same learning rate as the baseline, then
gradually lowers it. This can help the model settle into a better minimum near
the end of training. Because Week 3 uses only 5 epochs, per-step scheduling is
preferred over per-epoch scheduling for smoother decay.

### EMA

EMA keeps a smoothed copy of model weights:

```text
theta_ema <- decay * theta_ema + (1 - decay) * theta_model
```

The training model still receives gradient updates normally. The EMA model is a
running average of recent model states. Validation, test evaluation, and
checkpoint selection use the EMA weights when EMA is enabled.

The intuition: individual SGD/AdamW steps can be noisy. Averaging weights over
time often produces a model that generalizes better. The risk is that if decay
is too high or training is too short, EMA can lag behind the trained model.

## Experiment Flow

### Step 1: Freeze the baseline

Use the Week 2 ResNet50 result as the baseline row. Do not rerun it unless code
changes make baseline equivalence questionable.

Evidence:

```text
outputs/plantvillage/baseline_resnet50_seed42/
```

### Step 2: Implement switches with tests

Before running expensive training, unit tests must prove:

- Label Smoothing and Focal Loss produce finite losses and gradients.
- Soft-label CrossEntropy works for Mixup and CutMix labels.
- Mixup creates convex image/label combinations.
- CutMix adjusts lambda based on patch area.
- Scheduler hits expected learning-rate boundary behavior.
- EMA updates shadow weights and can temporarily swap them into the model.
- Disabling all switches preserves baseline transform and loss behavior.

### Step 3: Run smoke checks

Each new config family should run on a small sample before formal training:

```bash
uv run plant-train \
  --config configs/week3/resnet50_label_smoothing.yaml \
  --cache-dir data/huggingface \
  --output-dir outputs/plantvillage/week3_ablation/smoke_label_smoothing_resnet50_seed42 \
  --samples-per-class 2 \
  --log-every 5
```

Smoke checks prove the pipeline runs. They do not count as final evidence.

### Step 4: Run one-variable formal experiments

Each formal output directory follows:

```text
outputs/plantvillage/week3_ablation/<experiment>_resnet50_seed42/
```

Each experiment must save the same core artifacts as Week 2:

- `config.yaml`;
- `split.json`;
- `checkpoint.pt`;
- `metrics.json`;
- `validation_metrics.json`;
- `training_curve.json`;
- `training_curve.png`;
- `run_manifest.json`.

### Step 5: Compare results

The report compares each experiment against the frozen ResNet50 baseline:

```text
delta_macro_f1 = experiment_test_macro_f1 - baseline_test_macro_f1
delta_accuracy = experiment_test_accuracy - baseline_test_accuracy
```

It must also compare:

- validation Macro F1;
- test Macro F1;
- training time;
- per-class F1 changes;
- whether the method adds inference cost;
- whether the method adds training-only complexity.

### Step 6: Select one combination experiment

Only after one-variable results exist, select one combination. The combination
must be justified by evidence. A method that did not help alone should not be
included merely because it is popular.

### Step 7: Choose the final classification model

The final model decision should consider:

- highest Macro F1;
- stability of validation curve;
- per-class improvements or regressions;
- extra training complexity;
- inference efficiency from Week 2;
- whether the method is understandable and maintainable.

## Reporting

Create or update:

```text
reports/week3_ablation_plan.md
reports/week3_ablation_results.md
docs/artifact-index.md
TASKS.md
README.md
```

The plan report records the experiment matrix before formal runs. The results
report records all runs, including failures and no-improvement experiments.

Every table row must point to an output directory and machine-readable metrics.

## Teaching Style During Execution

For each implementation chunk, explain:

1. the plain-language purpose;
2. the exact file being changed;
3. the mathematical object being implemented, such as a target distribution,
   mixed-label loss, or moving average;
4. the test that proves the behavior;
5. the command the user can run independently.

The explanation should be concise enough not to interrupt coding flow, but
explicit enough that the user can reconstruct the idea without memorizing it.

## Validation

Development validation:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
```

Formal experiment validation:

- every formal run has `status = completed` in `run_manifest.json`;
- every run uses seed 42 and official test `sample_count = 10709`;
- every config differs from baseline in exactly the intended factor;
- all final metrics come from `metrics.json`;
- negative and neutral results are retained.

## Risks and Mitigations

- Single-seed results can be noisy. Mitigation: explicitly label them as
  single-seed and avoid claims of statistical robustness.
- PlantVillage official split has known `leaf_id` overlap. Mitigation: keep the
  official-split limitation in every report.
- Mixup and CutMix can create visually unnatural plant disease samples.
  Mitigation: evaluate them as single-variable experiments before including
  either in a combination.
- EMA can lag if decay is too high. Mitigation: use decay 0.999 for formal
  ResNet50 runs because there are many optimizer steps, and record the value.
- More augmentation may improve validation but hurt a rare class. Mitigation:
  compare per-class F1, not only aggregate Macro F1.

## Exit Criteria

Week 3 can close when:

- all planned switches are implemented and tested;
- formal single-variable experiments are run or explicitly marked failed with
  reason;
- one combination experiment is selected and run when evidence supports it;
- the final classification model is chosen with a written decision record;
- reports and task state are updated with machine-readable evidence paths.
