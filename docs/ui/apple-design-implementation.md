# Apple-inspired interface implementation rules

This project uses web design guidance installed from `emilkowalski/skills` as a
craft reference. It does not claim Apple affiliation and does not copy Apple
product assets or proprietary interface content.

## Guidance reviewed

The controller installed the requested skill collection locally with
`npx skills@latest add emilkowalski/skills`. The installed guidance was reviewed
before creating the React shell, but the skill sources themselves are local tool
inputs and are not redistributed in the public repository. See
[`docs/release/publication_decisions.md`](../release/publication_decisions.md)
for the publication boundary.

The reviewed guidance covered Apple-inspired interface foundations, Emil
Kowalski-style design engineering polish, animation vocabulary, animation
opportunity finding, motion improvement, and motion review.

## Rules for Tasks 5–7

1. Use glass as a functional hierarchy layer around the image and result
   workspaces. Do not blur the entire page or stack pale translucent surfaces.
2. Keep text on glass high contrast and slightly stronger in weight. Safety,
   availability, and out-of-domain warnings must remain readable over every
   background and cannot depend on color alone.
3. Prefer the platform system font. Tighten tracking and leading only for large
   display headings; keep body copy comfortably spaced and size layout in
   scalable units.
4. Give pointer and touch actions immediate press feedback. Keep frequent
   controls crisp and reserve noticeable motion for occasional state changes
   such as the Qwen panel or result arrival.
5. Keep reversible state changes spatially consistent: panels return toward
   their source, and loading, success, warning, and error states must not make
   surrounding content jump without a visual bridge.
6. Use short, interruptible transitions for interface state. Animate compositor-
   friendly `transform` and `opacity`; use a spring only for a genuinely
   gesture-driven interaction that must inherit velocity.
7. Avoid decorative looping motion, exaggerated bounce, and delayed keyboard
   interactions in the research workspace. Motion must provide feedback,
   orientation, state explanation, or continuity.
8. Preserve user agency: uploads can be replaced or reset, failures retain the
   selected image, and classifier and Qwen progress remain independent.
9. Implement `prefers-reduced-motion` with gentle fades or immediate state
   changes, `prefers-reduced-transparency` with solid surfaces, and
   `prefers-contrast` with stronger boundaries.
10. Verify desktop and mobile layouts, keyboard focus, touch targets, text
    scaling, loading/error states, and actual `liquid-glass-react` rendering in
    the browser before claiming visual completion.

## Current slice

Task 1 intentionally contains only a tested semantic research shell. It renders
`liquid-glass-react` around the identity and safety boundary so the dependency is
exercised now; the complete four-region interface and browser fidelity work are
owned by later tasks.
