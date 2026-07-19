# Open-World Architecture Evidence Sync Design

**Status:** approved

**Date:** 2026-07-19

## Purpose

Synchronize the bilingual paper, bilingual presentation outline, public architecture
documentation, and evidence index with the implemented target-leaf and abiotic-stress
gates. The edited materials must explain the new serving sequence without changing the
frozen benchmark results or presenting heuristic image analysis as a verified diagnosis.

The PowerPoint and Keynote binaries are explicitly out of scope. They remain unchanged.

## Communication job

By the end, a research reviewer or defense audience should understand that the verified
PlantVillage classifier remains the measured core, while the React/FastAPI demo now adds
pre-inference target-leaf selection, plant-identity routing, OpenCV morphology evidence,
and safety gates that can abstain before a crop-condition claim or management guidance is
shown.

## Canonical architecture

The synchronized materials will use one serving sequence:

1. Upload a leaf image.
2. Isolate one target leaf automatically or from one source-image click.
3. Estimate plant identity with the local 114-class catalog; use optional Pl@ntNet only
   when the local identity result is uncertain and a configured key is available.
4. Continue only when the identified plant is supported by the PlantVillage disease
   classifier.
5. Measure OpenCV morphology on the selected leaf and lesion candidates.
6. For accepted Corn inputs, apply the central-axis abiotic-stress gate before infectious
   disease selection.
7. Otherwise route the accepted crop to its crop-specific PlantVillage conditions.
8. Show Grad-CAM, local Qwen visual evidence, or cloud management guidance only when their
   respective evidence and safety gates permit it.

The architecture must distinguish three evidence levels:

- **Verified experimental core:** frozen PlantVillage benchmark, ablation, calibration,
  error analysis, and Grad-CAM relevance artifacts.
- **Implemented serving gates:** target-leaf selection, local plant routing, crop support
  checks, OpenCV morphology summaries, and guidance suppression.
- **Experimental extensions:** broad plant identity, Grape lesion focus, local Qwen visual
  descriptions, and external management providers.

## Scientific boundaries

- OpenCV outputs are heuristic region and morphology evidence, not pathological lesion
  masks or causal explanations.
- The Corn gate may output `suspected_abiotic_nutrient_stress`; it must not claim confirmed
  nitrogen deficiency or identify a nutrient without validated labels.
- The 114-class plant catalog expands identity routing but is not evidence of validated
  open-world accuracy across 114 species.
- PlantVillage disease probabilities remain closed-set model outputs and must not be
  described as field accuracy or ground truth.
- Grad-CAM remains a non-causal relevance visualization.
- Qwen is limited to visible morphology; management guidance remains optional,
  provider-selected, educational, and suppressed when upstream gates do not support a
  disease claim.
- The original user-supplied nitrogen-deficiency image is not available in the repository;
  the recorded QA therefore demonstrates gate behavior and synthetic/proxy checks rather
  than a completed external-image benchmark.

## Deliverables

### Bilingual paper

Update `paper/en/main.tex` and `paper/zh/main.tex` symmetrically:

- revise the abstract and contribution framing so the React/FastAPI hierarchy is part of
  the engineering evidence;
- add a concise hierarchical-serving subsection to the demo section;
- describe target-leaf isolation, plant identity, crop support, OpenCV morphology, the Corn
  abiotic gate, disease routing, and downstream guidance gating;
- extend limitations and future work without changing frozen metrics;
- add or update one architecture figure and caption when the derived asset is ready;
- rebuild the English and Chinese PDFs.

### Presentation outline

Update only `docs/presentation/plantdisease_ai_complete_bilingual_outline.md` and, where its
architecture references would otherwise conflict, `docs/presentation/week7_ppt_outline.md`.
The outline should revise the architecture, demo, limitations, and future-work material and
map the updated architecture asset to the relevant slides. No `.pptx` or `.key` file may be
modified.

### Architecture and evidence documentation

Update:

- `docs/project-architecture.md`
- `docs/week7_showcase_architecture.md`
- the shared architecture visual in `docs/media/`
- `docs/artifact-index.md`
- the README architecture summary or links only where they would otherwise contradict the
  new canonical flow

The text-readable Mermaid diagram remains the maintainable architecture source. A derived
PNG is regenerated for paper and outline references without rebuilding the existing slide
decks.

## Validation

- Confirm `git diff --name-only` contains no `.pptx` or `.key` files.
- Run the paper claim audit and rebuild both paper PDFs.
- Render every page of both PDFs and inspect page-level contact sheets.
- Validate all Markdown links touched by the change.
- Confirm the architecture diagram and paper captions preserve all scientific boundaries.
- Run the project documentation/claim tests affected by the edits.
- Commit the synchronized evidence set on the feature branch, then merge it into local
  `main` without pushing or deleting the feature branch.

