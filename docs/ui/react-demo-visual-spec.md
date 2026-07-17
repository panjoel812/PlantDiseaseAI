# React Demo Visual Specification

## Accepted concept references

- Default state: `docs/ui/concepts/react-demo-default.png` (1586 × 992)
- Analyzed state: `docs/ui/concepts/react-demo-analyzed.png` (1586 × 992)
- Primary media: `app/examples/field_corn_leaf.jpeg`; preserve its natural color and
  crop without a tint or color overlay.

These concepts extend the approved React/FastAPI design. The implementation must
preserve their information architecture, visual hierarchy, container model, and
state transition while keeping all interface text and controls code-native.

## Composition and container model

1. A quiet graphite page contains a compact brand/reset header.
2. One warm-ivory application field holds the title, description, workspace, and
   research boundary.
3. The workspace is a two-column grid at desktop size: the image occupies roughly
   two thirds; a narrower result rail holds classifier above Qwen.
4. Only the image workspace, classifier panel, and Qwen panel use Liquid Glass.
   Do not add nested glass or turn the layout into a bento grid.
5. The amber research boundary is a single full-width band below the workspace.
6. At 760 px and below, order is title, image, classifier, Qwen, research boundary.
   No horizontal scroll is permitted; the composer must remain inside the viewport.

## State anatomy

### Default

- The supplied field image is already selected and clearly labeled as user supplied,
  out of domain, and without verified ground truth.
- `Analyze leaf` is the primary action.
- Classifier shows a calm empty state for Top-5 and Grad-CAM.
- Qwen is present but disabled until classification succeeds.

### Analyzed

- The photo remains unchanged.
- Classifier leads with `Model prediction — not ground truth`, then Top-5 rows,
  Grad-CAM output, and field-generalization warnings.
- Qwen exposes its bounded composer only after classification. It remains labeled
  local, optional, and exploratory; unavailable runtime state must stay legible.
- Classification and Qwen errors stay in their owning panel.

## Design tokens

| Role | Token | Intended value |
| --- | --- | --- |
| Page | `--page-graphite` | `#191a18` |
| App field | `--field-ivory` | `#f2f0ec` |
| Primary text | `--ink` | `#20221f` |
| Muted text | `--muted` | `#61645f` |
| Leaf accent | `--leaf` | `#326f39` |
| Leaf active | `--leaf-strong` | `#245c2d` |
| Risk | `--amber` | `#a45f0a` |
| Risk surface | `--amber-wash` | `rgba(246, 224, 188, 0.35)` |
| Glass border | `--glass-edge` | `rgba(255, 255, 255, 0.72)` |
| Hairline | `--hairline` | `rgba(32, 34, 31, 0.14)` |
| Small radius | `--radius-control` | `14px` |
| Panel radius | `--radius-panel` | `24px` |
| Field radius | `--radius-field` | `28px` |
| Fast response | `--press` | `100ms` |
| Material response | `--materialize` | `240ms` |

Glass surfaces use restrained blur/saturation, a bright top edge, and one soft shadow.
They need solid high-contrast fallbacks for reduced transparency and increased
contrast. A larger panel may be visually heavier than a small control, but light
glass must not be stacked over light glass.

## Typography

- Family: platform system stack (`-apple-system`, `BlinkMacSystemFont`, `Segoe UI`,
  sans-serif).
- Display: `clamp(2.25rem, 4vw, 4.25rem)`, weight 700, line-height 0.98–1.04,
  tracking `-0.035em`.
- Section title: 1.05–1.2rem, weight 650, line-height 1.2.
- Body: 0.95–1rem, weight 450, line-height 1.5.
- UI control: 0.92–1rem, weight 600, deliberate line-height; never browser default.
- Caption: 0.78–0.86rem with slightly positive tracking for legibility.

## Allowed first-viewport copy

- `PlantDiseaseAI`
- `Evidence before diagnosis.`
- `Educational research demo — not a professional diagnosis.`
- `User-supplied field corn leaf`
- `No verified ground truth · out-of-domain example`
- `Choose image`
- `Analyze leaf` / `Analyze again`
- `Classifier`
- `Ready to analyze`
- `Top-5 predictions and Grad-CAM will appear here.`
- `Model prediction — not ground truth`
- `Ask Qwen`
- `Optional local Qwen3-VL`
- `Available after classification.`
- `What visual symptoms are visible?`
- `Research boundary`
- `PlantVillage performance does not establish field accuracy.`
- `Qwen fixed smoke: choice/few-shot 11/15; fine-grained condition 1/5.`

Dynamic class names, probabilities, server warnings, timing values, Qwen status,
and bounded answers may appear only when supplied by real application state.

## Component and icon inventory

- `Hero`: brand/reset header plus title and educational boundary.
- `ImageWorkspace`: image, upload input, primary analyze action, progress/error live
  region. Upload, analyze, and reset use simple 1.75–2 px rounded-line SVG icons.
- `ClassifierPanel`: classifier/network icon, leaf empty state, Top-5 probability
  bars, Grad-CAM image, timings, warnings.
- `QwenPanel`: rounded chat icon, lock/unavailable state, labeled question field,
  submit action, scope/evidence boundary, answer and refusal state.
- `SafetyNotice`: amber outlined warning triangle and the two fixed boundaries.

Icons must use `currentColor`, a consistent rounded stroke, clean `viewBox`, and
optical alignment. Do not add a general icon library solely for this screen.

## Interaction and accessibility

- Controls respond on press with a subtle scale change; no bouncy decoration.
- Material panels may enter with a short opacity/blur materialization only.
- Every target is at least 44 × 44 px, has a visible `:focus-visible` ring, and is
  keyboard reachable. The file input has an explicit accessible label.
- Loading and errors use panel-local `aria-live` regions.
- Progress, warning, refusal, and disabled status cannot rely on color alone.
- Reduced motion changes motion to near-static opacity feedback. Reduced
  transparency uses solid surfaces; increased contrast adds defined borders.

## Prohibited deviations

- No fabricated disease label, field accuracy, or Qwen result.
- No decorative eyebrow, kicker, badge, pill row, fake metric, or extra navigation.
- No color wash over the supplied photo, neon, glow, orb, or gradient-heavy backdrop.
- No nested cards for every datum, generic stock imagery, Apple logo, or watermark.
