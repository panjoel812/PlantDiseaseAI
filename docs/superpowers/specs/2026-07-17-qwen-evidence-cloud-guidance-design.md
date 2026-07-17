# Qwen Evidence and Cloud Guidance Design

Date: 2026-07-17
Status: approved by the user (方案 A)

## Goal

Separate image-grounded observation from educational management guidance. Local Qwen3-VL describes only visible spots, colors, shapes, margins, texture, and distribution. A separately selected OpenAI, Claude, or Gemini API may use the classifier hierarchy and optional Qwen observation to answer management questions without presenting the result as a verified diagnosis.

## Product structure

- The existing assistant glass card gains two explicit modes: **Visual evidence** and **Management guidance**.
- Visual evidence uses only the optional local Qwen runtime and defaults to “What spots, colors, shapes, margins, textures, and distributions are visible?”
- Management guidance presents a manual OpenAI / Claude / Gemini selector. There is no automatic fallback and the chosen provider is always visible before submission.
- Provider availability and configured model IDs come from the backend. API keys never appear in response payloads, browser storage, React state, logs, or Git.
- The assistant card keeps one fixed outer size; switching modes and request states changes only its internal scrollable body.

## Qwen boundary

Qwen may answer visual-observation questions even when the classifier is low-confidence, unknown, or warns that the image is out of domain. Those warnings affect disease claims, not the ability to describe visible pixels.

Qwen refuses questions that ask it to:

- name or confirm a disease;
- recommend treatment or chemicals;
- interpret regulations;
- provide pesticide product, rate, dilution, or dose instructions.

The Qwen response is displayed as raw visual evidence with local-model provenance. The wrapper must not append a classifier disease summary that could contaminate the observation.

## Cloud provider boundary

The backend exposes one provider-neutral service with three native adapters:

- OpenAI Responses API;
- Anthropic Messages API;
- Gemini Interactions API.

Each request includes the manually selected provider, question, crop-first classifier context, warnings, and optional Qwen visual observation. The system instruction requires uncertainty-aware integrated pest-management guidance, separates observations from hypotheses, and states that the PlantVillage result is not ground truth.

General management questions are allowed. The answer may discuss monitoring, sanitation, moisture management, isolation, sampling, and conditional next steps. Exact pesticide products, concentrations, mixing ratios, application rates, re-entry intervals, pre-harvest intervals, or local regulatory claims are not supplied without an authoritative region-specific label source. Such questions receive a local bounded response that asks the user to follow the registered product label and consult local extension or plant-health professionals.

## Configuration

The FastAPI process reads:

- `OPENAI_API_KEY` and optional `OPENAI_MODEL`;
- `ANTHROPIC_API_KEY` and optional `ANTHROPIC_MODEL`;
- `GEMINI_API_KEY` and optional `GEMINI_MODEL`.

Documented defaults are pinned, currently supported model IDs, but every model ID is overridable. A provider without a key remains visible as “Not configured” and cannot be submitted.

## API contract

- `GET /api/advice/providers` returns provider id, display name, configured boolean, model id, and non-secret detail.
- `POST /api/advice/ask` accepts JSON with provider, question, selected crop, selected condition, probabilities, warnings, and optional visual observation.
- Successful advice returns provider, model id, message, scope, evidence boundary, and source identifiers.
- Provider authentication, rate-limit, timeout, malformed response, and upstream service errors return sanitized errors; upstream bodies and secrets are never forwarded.

## Visual and interaction design

- Use a compact Apple-style segmented control for Visual evidence / Management guidance and a second three-option provider selector inside the management mode.
- Keep the current mist-white, pale-blue, and fresh-green background and real `liquid-glass-react` material.
- Use restrained opacity and color transitions only. No panel translation, pointer-following refraction, or geometry-changing animation.
- Disabled providers remain readable and explain which server environment variable is missing.
- Status, error, and answer regions use stable minimum heights and accessible `role="status"` / `role="alert"` behavior.
- `prefers-reduced-motion`, `prefers-reduced-transparency`, keyboard focus, and 44px minimum targets remain supported.

## Verification

- Python tests prove that out-of-domain visual questions reach Qwen while diagnosis/treatment questions do not.
- Adapter tests use injected fake HTTP transports; no paid API is contacted in the automated suite.
- FastAPI tests verify provider status, manual routing, sanitized failures, and absence of API keys.
- React tests verify the two modes, manual provider selection, disabled provider behavior, request payload, stable glass boundary, and no secret fields.
- Full Python tests, Ruff, type checking, frontend tests, lint, production build, and browser QA must pass before completion.

## Out of scope

- Automatic provider fallback or hidden provider routing.
- Sending API keys from the browser.
- Claiming that cloud advice is a professional diagnosis.
- Region-specific pesticide label retrieval, prescription, or regulatory compliance verification.
- Live paid-provider verification without user-supplied credentials.
