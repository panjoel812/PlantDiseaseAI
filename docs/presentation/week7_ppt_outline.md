# Week 7 Apple Showcase Deck Outline and Speaker Notes

The final editable 12-slide deck is
`docs/presentation/week7_apple_showcase_deck.pptx`. Its reproducible source is
`scripts/build_week7_apple_showcase.mjs`, and the standalone architecture visual
exported from slide 2 is `docs/media/week7_apple_architecture.png`.

That slide and image are retained as historical Week 7 classifier-first presentation
assets. The current target-leaf and abstention architecture is documented in
`docs/media/week8_hierarchical_serving_architecture.png` and
`docs/project-architecture.md`; this outline update does not modify the existing PPTX.

All 12 slides contain speaker notes. Each notes section has a concise
`5-minute talk track`, an expanded `10-minute talk track`, and the same integrity
reminder: cite the evidence path shown on the slide and do not extend the result
to field diagnosis. Timing scaffolds appear only in notes, not in audience-facing
slide content.

## Final slide outline

### 1. Evidence before diagnosis.

- Primary claim: an attractive product moment is credible only when it follows
  an auditable evidence chain.
- Boundary: research and educational closed-set demo, not field diagnosis.
- Visual: verified synthetic-input Top-5 and Grad-CAM poster.

### 2. The model is only one link in the evidence chain.

- Primary claim: data audit, training, evaluation, explanation, and serving are
  stable classifier-first stages.
- Boundary: the VLM consumes bounded classifier context and is explicitly marked
  `Exploratory`.
- Historical visual: six-stage architecture exported as
  `docs/media/week7_apple_architecture.png`.
- Current architecture reference: target leaf, plant identity, supported-host gate,
  OpenCV morphology, Corn abiotic gate, crop-specific conditions, and downstream
  evidence/guidance gates in `docs/media/week8_hierarchical_serving_architecture.png`.
- Current boundary: the 114-class catalog is routing support rather than validated
  114-species field accuracy; OpenCV is heuristic evidence; the Corn gate does not
  confirm nitrogen deficiency.

### 3. The official split is useful—and not entity isolated.

- Primary claim: the official split supports controlled comparison but contains
  `227` overlapping `leaf_id` values across train and test.
- Boundary: the results are not strict entity-isolated or field-generalization
  evidence.

### 4. Accuracy and deployability need different winners.

- Primary claim: ResNet50 is the best accuracy candidate, while MobileNetV2 is
  the lightweight deployment candidate.
- Evidence: ResNet50 Test Accuracy `0.9830`; MobileNetV2 `2.27M` parameters and
  `0.31G` FLOPs under the shared Week 2 protocol.
- Visual: Week 2 accuracy-efficiency Pareto figure.

### 5. Controlled ablation selected the final classifier.

- Primary claim: controlled Week 3 ablation selected ResNet50 + Label Smoothing
  + Cosine Scheduler.
- Evidence: Test Accuracy `0.9953`, Macro F1 `0.9941`, seed 42, official split.
- Visual: Week 3 validation Macro F1 curves.

### 6. Grad-CAM shows relevance, not causality.

- Primary claim: the fixed Grad-CAM review supports relevance inspection, not a
  causal biological explanation.
- Evidence: 24 fixed samples spanning correct/incorrect and high/low-confidence
  groups.
- Visual: Week 4 baseline-versus-final Grad-CAM comparison.

### 7. High accuracy still needs confidence auditing.

- Primary claim: correctness and confidence quality are distinct.
- Evidence: top-label ECE `0.0965`, MCE `0.3348`, and Brier `0.0140`.
- Visual: Week 4 reliability diagram.

### 8. The same serving layer powers the product moment.

- Primary claim: shared serving contracts drive the local app and Apple
  container flow with Top-5 and Grad-CAM.
- Evidence: `129.8 ms` for one CPU-only Apple container fixed-example total;
  this is not a latency distribution or benchmark.
- Visual: verified Week 7 Apple demo poster.

### 9. Prompt constraints reduced format risk, not disease ambiguity.

- Primary claim: constrained prompts improved smoke-test answer structure but
  did not solve disease-condition recognition.
- Evidence: original `0/15`, short `10/15`, choice `11/15`, few-shot choice
  `11/15`; condition best `1/5` on 5 images / 15 questions.

### 10. A safe assistant knows when to stop.

- Primary claim: refusal is part of the prototype's capability boundary.
- Actions: educational summary, high-risk refusal, low-confidence refusal, and
  out-of-scope refusal.
- Boundary: no pesticide, dosage, regulatory, or professional diagnostic advice.

### 11. Verified, smoke-tested, and pending are different states.

- Verified: classifier pipeline, benchmark and ablation, Grad-CAM and
  calibration, local/container demo.
- Smoke-tested: Qwen3-VL prompts, safety-bounded assistant, 5-image VQA
  comparison, MLX 4-bit inference.
- Pending: LoRA/QLoRA, manual VQA audit, field validation, entity-isolated study.

### 12. Credible AI needs evidence and limits.

- Primary claim: the project's strongest contribution is its evidence chain and
  the discipline to state limits.
- Week 8 handoff: clean-environment reproduction, artifact audit, correction of
  any claim drift, and a deliberate publication decision.

## 5-minute talk track

1. **Slides 1–2 — Frame the evidence chain.** Contrast an impressive disease
   demo with a traceable research/engineering system; keep the VLM exploratory.
2. **Slide 3 — State the data boundary.** Lead with the `227` overlapping
   `leaf_id` finding and distinguish comparative official-split evidence from
   entity isolation or field generalization.
3. **Slides 4–5 — Explain model choice.** Separate the accuracy and deployment
   winners, then show that controlled ablation selected the final ResNet50 with
   `0.9953` Accuracy and `0.9941` Macro F1 under seed 42.
4. **Slides 6–7 — Audit explanation and confidence.** Use the fixed Grad-CAM
   review and calibration metrics while stating relevance-not-causality and
   top-label-only limits.
5. **Slide 8 — Show the product moment.** Connect Top-5 and Grad-CAM to the same
   serving layer; qualify `129.8 ms` as one fixed-example container total.
6. **Slides 9–10 — Draw the VLM and safety boundary.** Choice prompts reached
   `11/15`, condition recognition stayed `1/5`, and refusal remains a tested
   safety action.
7. **Slides 11–12 — Close honestly.** Separate verified, smoke-tested, and
   pending work, then hand off to Week 8 reproduction and release audit.

## 10-minute talk track

1. **Slide 1 — Project framing.** Explain why the product image is the end of
   the evidence chain rather than the proof of diagnostic readiness.
2. **Slide 2 — Architecture.** Present the historical classifier-first deck visual,
   then use the current external architecture reference to explain target-leaf,
   plant-identity, morphology, abstention, and why VLM/guidance remain experimental.
3. **Slide 3 — Data audit.** Discuss the official split and the distinction
   between sample-level comparison and entity-level isolation.
4. **Slide 4 — Benchmark.** Explain the shared protocol and why ResNet50 and
   MobileNetV2 answer different research and deployment questions.
5. **Slide 5 — Ablation.** Explain the selected Label Smoothing + Cosine
   Scheduler combination and the single-seed, official-split qualifier.
6. **Slides 6–7 — Explainability and calibration.** Cover the 24 fixed samples,
   error-analysis discipline, relevance-not-causality boundary, and the limits
   of top-label ECE/MCE/Brier.
7. **Slide 8 — Demo engineering.** Show shared serving behavior, the fixed
   synthetic input, the Apple container evidence, and the non-benchmark latency
   wording.
8. **Slide 9 — VLM exploration.** Compare the four prompt variants and explain
   why better format compliance did not resolve disease ambiguity.
9. **Slides 10–11 — Safety and integrity.** Walk through the four assistant
   actions and the verified/smoke-tested/pending evidence ledger.
10. **Slide 12 — Week 8 handoff.** End with clean-environment reproduction,
    artifact and claim auditing, and an honest release decision.

## Slide asset map

- Slides 1 and 8: `docs/media/week7_apple_demo_poster.png`
- Slide 2: native PowerPoint architecture shapes; exported to
  `docs/media/week7_apple_architecture.png`
- Current architecture supplement for Slide 2 discussion:
  `docs/media/week8_hierarchical_serving_architecture.png`
- Slide 4: `outputs/plantvillage/benchmarks/week2_accuracy_efficiency_pareto.png`
- Slide 5: `reports/figures/week3_validation_macro_f1_curves.png`
- Slide 6: `reports/figures/week4_baseline_vs_final_gradcam.png`
- Slide 7: `reports/figures/week4_reliability_diagram.png`
- Slide 9: `reports/week6_vlm_prompt_compare.md`
- Slide 12: `docs/artifact-index.md`, `docs/week7_evidence_map.md`
