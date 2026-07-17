# Compact Demo, Structured Qwen Evidence, and In-Memory Provider Configuration

**Date:** 2026-07-17
**Status:** approved in conversation
**Target:** public `main` React/FastAPI demo

## 1. Objective

Make the PlantDiseaseAI demo readable within one common desktop viewport while
preserving the light Apple-style material system, restoring the visible ambient
leaf/dew decoration, turning verbose Qwen prose into concise visual evidence,
allowing cloud provider keys to be configured from the website without
persistence, and restoring a complete English/Chinese README pair.

The classifier remains the primary research path. Qwen remains an optional
local visual-observation tool, and cloud providers remain explicitly selected
educational management assistants rather than diagnosis authorities.

## 2. Root causes

1. `InteractiveQwenService` forwards the raw model string directly to the UI.
   The prompt does not require a compact response, Markdown markers are rendered
   as plain text, and the 96-token generation limit can stop mid-sentence.
2. `AmbientGarden` is absolutely positioned at the bottom of the complete page.
   Because the desktop page is taller than the viewport, its leaves are not
   visible in the initial screen.
3. The desktop workspace has a fixed `42rem` to `48rem` height below a large
   heading and header, so a normal laptop viewport necessarily scrolls.
4. Cloud providers currently read only process environment variables. There is
   no authenticated local configuration surface in the demo.
5. `README.md` is the complete English guide, while `README.zh-CN.md` is only a
   short Chinese entry page, so the public documentation is not truly bilingual.

## 3. Selected design

### 3.1 Structured Qwen visual evidence

The backend will prepend a fixed instruction to the user's visual-only question:

- describe only pixels that are visible;
- do not name a disease or recommend treatment;
- return up to six short observations;
- prefer the categories spots, colors, shapes, margins, textures, and
  distribution;
- finish every observation rather than starting a long explanation.

The service will normalize the returned text into a bounded list of observations.
Normalization will remove common Markdown headings/bullets, drop introductory
boilerplate, collapse whitespace, reject empty fragments, deduplicate repeated
phrases, and cap both item count and item length. The API will return the concise
message and a new `observations` array while retaining `raw_answer` for audit.

The React panel will render the observations as compact rows. A closed
`<details>` disclosure named **Raw response** will expose the original model
text for researchers without letting it dominate the main layout. Refusals and
runtime failures keep their existing explicit states.

### 3.2 Website provider configuration

The Management guidance panel will include a **Configure providers** control
that opens a light glass sheet. Each provider row contains:

- provider name and non-secret model identifier;
- password input for a new key;
- Save and Clear actions;
- configured/unconfigured status.

`POST /api/advice/providers/{provider}/configure` accepts one key and optional
model identifier. `DELETE /api/advice/providers/{provider}/configure` removes
the runtime override. The response is always a non-secret provider status and
never contains the key or any recoverable derivative.

Runtime overrides live only in a locked in-memory store owned by the FastAPI
process. They take precedence over environment variables for that process,
disappear on restart, and are not written to files, logs, React state after the
request, `localStorage`, `sessionStorage`, cookies, URLs, or Git. The input is
cleared immediately after a successful request. Production documentation will
state that remote deployment must use HTTPS and should prefer server-side secret
management; this UI is intended for the local demo.

No provider fallback is introduced. The user still chooses exactly one provider.

### 3.3 Compact viewport layout

For desktop widths above 760 px, the page will use a viewport-fit shell:

- header height approximately 48 px;
- display heading reduced to a restrained `clamp(2.25rem, 4vw, 3.8rem)`;
- tighter heading/subtitle spacing;
- workspace height computed from `100dvh` with a safe minimum, instead of the
  current fixed `42rem` to `48rem` range;
- classifier and assistant rail rows sized to keep their primary controls and
  result placeholders visible;
- the research boundary becomes a compact footer strip.

The target is no horizontal overflow and no document scrolling at 1440×900 and
1920×1080 after classification. A small internal scroll area is allowed only
inside a long raw response or long cloud answer. Below 760 px the existing
single-column document flow remains scrollable and touch friendly.

Large photo and result surfaces keep `liquid-glass-react` with zero elasticity,
so pointer movement cannot deform or shift layout.

### 3.4 Ambient leaf/dew layer

`AmbientGarden` will be anchored to the initial viewport background instead of
the bottom of the whole document. It remains behind interactive content with
`pointer-events: none`, light opacity, and transform/opacity-only animation.
The lowest leaves will remain visibly peeking into the bottom corners without
covering buttons or text. `prefers-reduced-motion` disables movement;
`prefers-reduced-transparency` makes the shapes more solid and subdued.

### 3.5 Complete bilingual README

`README.md` remains the complete English public guide. `README.zh-CN.md` will be
expanded to mirror its practical structure: project boundary, architecture,
platform support, smoke path, PlantVillage training/evaluation, React/FastAPI,
Streamlit, Docker, Qwen and cloud provider configuration, reproducibility,
limitations, repository map, licensing, and citations.

Both files will start with reciprocal language links. Claims and limitations
must remain evidence-backed and pass the existing Week 8 claim/link audit.

## 4. Interfaces and data flow

```text
Browser password input
  -> HTTPS/localhost POST configure endpoint
  -> validated provider + bounded key/model
  -> locked process-memory override store
  -> non-secret provider status response
  -> input cleared

Image + fixed visual-only question
  -> Qwen prompt instruction
  -> raw local model output
  -> bounded observation normalizer
  -> observations + concise message + retained raw_answer
  -> compact rows + optional Raw response disclosure
```

Existing environment variables remain supported. Provider status merges the
in-memory override with environment configuration but never exposes which key
was supplied or its length/prefix.

## 5. Error handling and security

- Empty or oversized keys/models return 422 without mutating configuration.
- Unknown provider identifiers return 404 or 422 before mutation.
- Clear is idempotent and returns the resulting non-secret status.
- Provider network/authentication failures remain sanitized and cannot include
  the submitted key.
- A configuration request never triggers a paid provider call.
- Qwen normalization failure falls back to one bounded plain-text observation;
  it never replaces a model answer with a fabricated disease label.
- The UI labels in-memory keys as temporary and provides an explicit Clear
  control.

## 6. Testing and acceptance criteria

Implementation follows red-green-refactor.

Backend tests must prove:

- Qwen Markdown/boilerplate is normalized into complete, deduplicated,
  length-bounded observations;
- the constrained prompt reaches the backend;
- configure/clear changes provider status and routing;
- keys never appear in responses, exceptions, repr output, or logs captured by
  tests;
- invalid configuration does not mutate existing state;
- no provider call occurs during configuration.

Frontend tests must prove:

- observations render as rows and raw output is closed by default;
- the configuration sheet saves and clears one provider;
- key inputs use `type=password`, are cleared after success, and are never sent
  to browser storage;
- provider choice remains manual;
- the ambient garden remains present and non-interactive.

Browser QA must verify 1440×900, 1920×1080, and 390×844 layouts, including
classified/Qwen/provider-configured states. Desktop targets must show the core
image, classifier, assistant selector, and ambient corner leaves within one
viewport without horizontal overflow. Mobile may scroll vertically.

Release verification includes the complete Python suite, Ruff, scoped `ty`,
React tests, frontend lint/build, claim/link audit, README language-link checks,
secret scan, `git diff --check`, and confirmation that local paper/PPT working
files remain excluded from the commit.

## 7. Non-goals

- Persisting API keys across FastAPI restarts.
- Browser-side provider API calls.
- Automatic provider fallback.
- Diagnosing disease or prescribing chemical products/doses through Qwen.
- Replacing the classifier with a VLM.
- Removing the safety boundary to make the page shorter.
