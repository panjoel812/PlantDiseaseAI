# Week 8 Research Defense and Bilingual Paper Extension Design

**Date:** 2026-07-16  
**Branch:** `codex/week8-release-audit`  
**Status:** Approved for direct execution  
**Audience:** Prospective research supervisors and research-program reviewers

## Objective

Extend the evidence-first Week 8 local release candidate with a complete
15-minute research-defense presentation and synchronized Chinese/English
LaTeX papers. The presentation must use an Apple launch-event visual grammar
and smooth paired-slide motion while the paper remains an auditable academic
record of verified Week 1–8 work.

By the end of the defense, the audience should regard PlantDiseaseAI as a
reproducible and limitation-aware agricultural AI research project, rather
than as a high-accuracy Demo without evidence boundaries.

## Binding Research Boundaries

- The official split contains `227` overlapping train/test `leaf_id` values.
- Week 2 ResNet50 reports Accuracy `0.9830` and Macro F1 `0.9743`.
- MobileNetV2 is the lightweight candidate with `2.27M` parameters, `0.31G`
  FLOPs, and `644.3 img/s` under the recorded MPS protocol.
- The selected Week 3 candidate reports Accuracy `0.9953` and Macro F1
  `0.9941` for seed 42 on the official split.
- Week 4 records `50/10709` errors, ECE `0.0965`, MCE `0.3348`, and Brier
  score `0.0140`; Grad-CAM is relevance visualization, not causal evidence.
- Week 5 latency `129.8 ms` is one fixed synthetic CPU observation, not a
  general benchmark.
- Week 6 Qwen3-VL results cover five images and fifteen questions; the
  choice/few-shot result is `11/15` and condition result is `1/5`.
- LoRA/QLoRA training, multi-seed confirmation, entity-isolated evaluation,
  complete manual VQA/attention audit, and real-field validation are not done.
- The materials are educational research artifacts, not professional plant
  diagnosis or pesticide guidance.

## Deliverables

### Presentation

- `docs/presentation/plantdisease_ai_week8_research_defense.key`
- `docs/presentation/plantdisease_ai_week8_research_defense.pptx`
- `docs/presentation/week8_research_defense_animation_map.md`
- `reports/week8_presentation_qa.md`

The Keynote file is the native motion reference and uses real Magic Move. The
PowerPoint file uses paired-slide Morph semantics. Keynote playback is verified
locally. Because Microsoft PowerPoint is not installed, the PPTX is verified by
rendering, OOXML transition/object inspection, and Keynote import/export, with
the missing PowerPoint-client playback check stated explicitly.

### Bilingual paper

- `paper/zh/main.tex`
- `paper/en/main.tex`
- `paper/references.bib`
- shared files under `paper/tables/`
- `paper/out/plantdisease_ai_zh.pdf`
- `paper/out/plantdisease_ai_en.pdf`

Both papers must have equivalent structure, values, evidence boundaries,
tables, and conclusions. `Panjoel` is the author. Codex may be acknowledged as
a writing/engineering tool but is not a co-author.

## Presentation Narrative

The deck contains 20 slides for an approximately 15-minute defense. Fast
paired slides act as motion frames rather than adding extra speaking topics.

1. Minimal black title.
2. Research question: does high dataset accuracy imply trustworthy diagnosis?
3. PlantVillage 38-class scope.
4. The `227 leaf_id` overlap expands into the unavoidable data boundary.
5. Data–train–evaluate–explain–serve research loop.
6. Five model candidates appear as a family.
7. ResNet50 accuracy and MobileNetV2 efficiency separate into two decisions.
8. Frozen ResNet50 baseline enters ablation.
9. Cosine Scheduler becomes the strongest single factor.
10. Label Smoothing + Cosine converges on `0.9953 / 0.9941`.
11. `50 / 10709` error count.
12. The number opens into the dominant confusion pairs.
13. Calibration metrics and reliability diagram.
14. Grad-CAM target-layer correction and non-causal boundary.
15. Streamlit Demo becomes the visual hero.
16. MPS, Top-5, Grad-CAM, and Apple container engineering evidence.
17. Qwen3-VL appears as an exploratory branch.
18. `11/15` and `1/5` reveal the capability boundary.
19. Week 8 reproducibility and release-candidate audit.
20. Next research: entity-isolated split, multiple seeds, field data, and
    completed human review.

Magic Move/Morph groups are 3→4, 6→7, 8→9→10, 11→12, 13→14, 15→16, and
17→18. Every slide must remain meaningful with transitions disabled.

## Visual System

- 16:9 canvas with alternating full black and off-white scenes.
- SF Pro Display/Text and PingFang for Chinese.
- Black, white, and neutral gray dominate; Apple blue marks verified evidence
  and amber marks risk or exploratory status.
- One claim and one primary visual per slide; large evidence-led titles replace
  dense academic bullet lists.
- Use only project-owned screenshots, plots, Grad-CAM images, leaf samples, and
  architecture evidence. Do not copy Apple product imagery, logos, Bilibili
  watermarks, or subtitle overlays from the visual references.
- Use a single rounded Bento overview only where it clarifies the whole research
  system; avoid turning the remaining deck into a dashboard.
- Visible copy is Chinese-first with precise English technical terms.

## Motion System

- Preserve stable object names, crop geometry, z-order, and visual identity
  across paired slides.
- Motion is limited to position, scale, crop, and opacity changes.
- Keynote transitions use native `magic move`, click-triggered, generally
  `0.8–1.0 s`.
- PPTX transitions use Morph-compatible paired objects and validated transition
  XML where available.
- Avoid bounce, spin, decorative fly-ins, and motion that hides evidence.
- Keep speaker timing in notes, never in audience-facing slide copy.

## Paper Structure

1. Introduction.
2. Related Work.
3. Dataset, Task, and Split Audit.
4. Unified Training and Evaluation Protocol.
5. Five-Model Benchmark.
6. Controlled Ablation and Model Selection.
7. Explainability, Error Analysis, and Calibration.
8. Demo, MPS Serving, and Apple Container.
9. Qwen3-VL Exploration and Safety.
10. Week 8 Reproducibility Audit.
11. Discussion and Negative Results.
12. Limitations, Ethics, and Intended Use.
13. Conclusion and Future Work.

The papers add Week 5–8 engineering and exploratory evidence, an error and
calibration table, a VLM comparison table, a reproducibility-audit table, and
selected real project figures. Shared BibTeX replaces duplicated manual
bibliographies. Numerical claims must remain linked to tracked reports or the
Week 8 release manifest/claim ledger.

## Verification

### Presentation

- Exactly 20 slides and 20 speaker-note parts in both presentation forms where
  the format exposes notes.
- Render and inspect every slide at full size; contact sheets are overview only.
- No overflow, clipping, accidental overlap, title wrapping, missing images, or
  unresolved placeholders.
- Keynote opens, applies native Magic Move to every mapped group, and exports a
  motion preview for visual inspection.
- PPTX contains the mapped paired objects and Morph-compatible transition data;
  inability to play it in Microsoft PowerPoint locally is recorded.
- Every visible metric matches the claim ledger and uses its required boundary.

### Paper

- XeLaTeX/BibTeX builds complete without undefined citations or references.
- Chinese and English section/table/value parity checks pass.
- Render and inspect every PDF page for missing figures, table overflow, bad
  breaks, or font failures.
- Claim/link audit passes over both papers and the presentation text/notes.

### Repository

- The authorized cross-cutting type-hardening work makes the locked
  `ty check src/plantdisease app scripts` command pass without blanket ignores
  or behavior changes.
- The eight-command clean-install lane passes in a repository-external temporary
  environment.
- Full pytest, Ruff, ty, media/deck QA, paper builds, safety scans, and evidence
  synchronization pass before Week 8 is marked complete.
- Existing untracked Week 7 legacy deck artifacts remain untouched.
- No push, tag, release, PR, or publication occurs without separate authority.
