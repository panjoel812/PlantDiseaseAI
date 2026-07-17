# Upload-First Analysis Flow and Fused Vector Logo

**Date:** 2026-07-17  
**Status:** approved in conversation (Approach A)  
**Target:** public `main` React demo

## Objective

Reorganize the demo into a clear vertical analysis flow: image selection and
analysis first, complete classifier and management results second. After a
successful analysis the interface should move the user to the results without
hiding information inside card-level scroll areas. Replace the generic header
leaf with a distinctive Apple-minimal project logo derived from the supplied
Desmos Bézier artwork and the existing PlantDiseaseAI leaf.

## Information architecture

The desktop page becomes two stacked regions:

1. **Upload and analyze** — a full-width floating photography card containing
   the selected image, upload action, and Analyze action.
2. **Analysis results** — a two-column grid with the complete Classifier on the
   left and the assistant on the right. The assistant opens on Management
   guidance after classification; Visual evidence remains available as the
   secondary tab.

On mobile, the same regions remain in order and the two results stack
vertically. The page itself may scroll. Classifier and assistant surfaces use
content-driven height and do not create nested vertical scroll containers.

## Analysis transition

`App` owns a results anchor. A successful transition of classification state
from loading to success moves focus context to the results region and calls
`scrollIntoView` with smooth behavior. Reduced-motion users receive an
instant/non-animated scroll. Re-analysis repeats the transition only after the
new result succeeds, never at button press while results are unavailable.

The assistant receives the classification-success signal and selects
Management guidance as its default/result mode. The user can still switch to
Visual evidence manually. Reset returns the page to the upload-first state.

## Complete result surfaces

- Remove fixed result-rail row heights and internal `overflow: auto` from the
  classifier and assistant state bodies.
- Render all classifier warnings, crop hierarchy rows, five conditions,
  Grad-CAM, timings, provider controls, questions, and returned guidance in
  normal document flow.
- Keep long raw Qwen output collapsed under the research-audit disclosure; an
  opened disclosure expands the page rather than creating a nested scroll box.
- Preserve `liquid-glass-react` with zero elasticity on large cards so pointer
  movement cannot change geometry.

## Fused project logo

Source artwork:
`/Users/panjoel/Documents/Project/DesmosBezierRenderer/exports/desmos_remaining_functions.svg`.

The source is reference-only and is not modified. A repository-native inline
React SVG component will:

- omit the source white background and rounded-square outline;
- extract and simplify the internal Bézier gesture;
- combine it with the existing leaf silhouette and vein direction;
- use one pale-sky-to-tender-green fill gradient;
- use a restrained deep-green outline plus a soft white highlight;
- remain legible at navigation size and in monochrome/reduced-transparency
  contexts;
- expose an accessible project-name label when used without adjacent text.

The mark stays code-native, scalable, and independent of raster assets. Header
wordmark spacing, optical alignment, and stroke weight are tuned for the final
24–32 px presentation size.

## Visual system

The existing mist-white, pale-blue, and tender-green background remains. The
upload card is the dominant surface, while result cards use thinner, brighter
glass and wider low-opacity shadows. No dark page frame is introduced. Ambient
leaf/dew decoration remains non-interactive and respects reduced motion.

## Error and accessibility behavior

- Failed analysis keeps the user near the upload card and does not auto-scroll
  to an empty result region.
- The results region has a programmatic heading and temporary focus target so
  keyboard and screen-reader users receive the same navigation change.
- Automatic movement is disabled under `prefers-reduced-motion`.
- API configuration remains available directly from the assistant header.
- Existing diagnosis, field-generalization, and treatment safety boundaries
  remain unchanged.

## Acceptance criteria

- Upload/image card appears above all generated results.
- Successful Analyze moves the viewport to the results region.
- Classifier and Management guidance are visible together on desktop.
- Management guidance is the initial assistant mode after analysis.
- Classifier and assistant content have no nested vertical scrolling.
- Mobile preserves upload → classifier → management ordering.
- Header uses the fused Desmos/leaf SVG logo with the accepted Apple-minimal
  blue/green material treatment.
- Existing provider setup, Qwen visual evidence, Grad-CAM, upload, reset,
  reduced-motion, and Liquid Glass behavior remain available.

## Non-goals

- Changing classifier, Qwen, or cloud-provider inference semantics.
- Persisting API keys.
- Editing the external Desmos source SVG.
- Adding new diagnostic or treatment claims.
