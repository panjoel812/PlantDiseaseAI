# Qwen Evidence and Cloud Guidance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let local Qwen describe visible morphology on any valid image while a manually selected OpenAI, Claude, or Gemini backend provides separately bounded educational management guidance.

**Architecture:** Qwen receives only visual-observation questions and no longer treats an out-of-domain classifier warning as a reason to refuse pixel-level description. A provider-neutral cloud service builds one audited management prompt and routes explicitly to one of three native HTTP adapters selected by the user; FastAPI exposes provider status and advice endpoints, and React presents both capabilities inside one fixed assistant glass stage.

**Tech Stack:** Python 3.12, FastAPI, urllib JSON transport, React 19, TypeScript 6, Vite 8, `liquid-glass-react` 1.1.1, Pytest, Vitest, Testing Library.

## Global Constraints

- Qwen only describes visible spots, colors, shapes, margins, textures, and distributions.
- Out-of-domain or low-confidence classifier context must not block a visual-only Qwen question.
- Disease identification, treatment, regulation, pesticide product, dilution, and dose questions must not reach Qwen.
- Cloud providers are manually selected; never implement automatic fallback.
- API keys remain server-side and must never be serialized, logged, committed, or stored in browser state.
- Cloud advice is educational and conditional, not a verified diagnosis or pesticide prescription.
- Exact chemical product/rate/mixing/interval claims remain locally bounded without an authoritative regional label source.
- Keep the assistant stage size stable and preserve `liquid-glass-react`, reduced motion, reduced transparency, and keyboard accessibility.
- Automated tests use injected transports and must not call paid APIs.

---

## File map

- Modify `src/plantdisease/vlm/assistant.py`: distinguish visual evidence from diagnosis/treatment policy.
- Modify `src/plantdisease/vlm/interactive.py`: allow visual-only Qwen generation regardless of classifier domain warning and return an observation-only wrapper.
- Create `src/plantdisease/vlm/cloud_advice.py`: provider configuration, prompt policy, HTTP adapters, response parsing, and sanitized errors.
- Modify `app/api.py`: dependency-injected provider status and management-advice routes.
- Modify `tests/vlm/test_assistant.py`, `tests/vlm/test_interactive.py`, and create `tests/vlm/test_cloud_advice.py`: policy and adapter coverage.
- Modify `tests/test_demo_api.py`: HTTP contract, provider routing, and secret-redaction coverage.
- Modify `frontend/src/api/types.ts` and `frontend/src/api/client.ts`: provider/advice contracts.
- Modify `frontend/src/api/client.test.ts`: exact request payload and error coverage.
- Create `frontend/src/components/AssistantPanel.tsx` and `frontend/src/components/AdvicePanel.tsx`: fixed assistant stage, mode switcher, and manual provider control.
- Modify `frontend/src/components/QwenPanel.tsx`: observation-only copy and action.
- Modify `frontend/src/App.tsx`, `frontend/src/hooks/useDemo.ts`, and `frontend/src/hooks/useDemo.test.tsx`: provider status/advice state and abort-safe requests.
- Modify `frontend/src/components/components.test.tsx`, `frontend/src/smoke.test.tsx`, and `frontend/src/styles.css`: accessible stable UI coverage and Apple-style polish.
- Create `.env.example`; modify `README.md` and `TASKS.md`: server configuration, safety boundary, and verification evidence.

---

### Task 1: Qwen visual-evidence policy

**Files:**
- Modify: `tests/vlm/test_assistant.py`
- Modify: `tests/vlm/test_interactive.py`
- Modify: `src/plantdisease/vlm/assistant.py`
- Modify: `src/plantdisease/vlm/interactive.py`

**Interfaces:**
- Produces: `is_visual_evidence_question(question: str) -> bool`.
- Produces: `build_visual_evidence_response(..., vqa_answer: str, answer_source: str) -> AssistantResponse`.

- [ ] **Step 1: Add failing policy tests**

Add a test where `What spots, colors, and shapes are visible?` uses a context with confidence `0.21` and warning `Out-of-domain field image.` and assert the backend is called and the response action is `visual_evidence`. Add parameterized diagnosis, treatment, pesticide-dose, and regulation questions and assert the backend is not called.

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/vlm/test_assistant.py tests/vlm/test_interactive.py -q`

Expected: the visual question is refused under the current blanket low-confidence/out-of-domain policy.

- [ ] **Step 3: Implement the minimal split policy**

Use an allowlist of observation terms plus explicit diagnosis/treatment/regulatory deny terms. In `InteractiveQwenService.ask`, validate the question first, refuse non-visual questions locally, and for visual questions call the backend without classifier-confidence/domain preflight. Wrap the raw answer directly:

```python
AssistantResponse(
    message=raw_answer,
    action="visual_evidence",
    refused=False,
    sources=[f"vqa:{self.model_id}"],
)
```

Do not append the classifier disease summary.

- [ ] **Step 4: Verify GREEN**

Run: `uv run pytest tests/vlm/test_assistant.py tests/vlm/test_interactive.py -q`

Expected: all focused tests pass.

---

### Task 2: Provider-neutral cloud advice service

**Files:**
- Create: `tests/vlm/test_cloud_advice.py`
- Create: `src/plantdisease/vlm/cloud_advice.py`

**Interfaces:**
- Produces: `CloudProvider` literal values `openai`, `anthropic`, `gemini`.
- Produces: `AdviceContext`, `CloudProviderStatus`, `ManagementAdvice`, `CloudAdviceError`.
- Produces: `CloudAdviceService.statuses() -> list[CloudProviderStatus]`.
- Produces: `CloudAdviceService.ask(provider, question, context) -> ManagementAdvice`.

- [ ] **Step 1: Add failing adapter and policy tests**

Use an injected recording transport and assert exact URLs/headers/body shapes for OpenAI Responses, Anthropic Messages, and Gemini Interactions. Assert an unconfigured provider fails before transport, an unknown provider is rejected, exact chemical-rate requests return a bounded local response without transport, and upstream error text/API keys never appear in `CloudAdviceError`.

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/vlm/test_cloud_advice.py -q`

Expected: import failure because `cloud_advice` does not exist.

- [ ] **Step 3: Implement configuration, transport, adapters, and parsing**

Read keys from `os.environ`; use overridable model IDs with defaults `gpt-5.4-mini`, `claude-sonnet-5`, and `gemini-3.5-flash`. Implement a small `UrllibJsonTransport` with a 30-second timeout and 64 KiB response limit. Parse text only from documented response fields and raise sanitized provider-specific errors for authentication, rate limiting, timeout, malformed JSON, or missing text.

- [ ] **Step 4: Verify GREEN**

Run: `uv run pytest tests/vlm/test_cloud_advice.py -q`

Expected: all adapter tests pass without network access.

---

### Task 3: FastAPI provider and advice contracts

**Files:**
- Modify: `tests/test_demo_api.py`
- Modify: `app/api.py`

**Interfaces:**
- Produces: `GET /api/advice/providers`.
- Produces: `POST /api/advice/ask` JSON request/response.
- Extends: `create_app(..., advice_provider=...)` dependency injection.

- [ ] **Step 1: Add failing API tests**

Assert provider status exposes only id, display name, configured, model id, and detail. Assert manual `anthropic` selection reaches only the fake Anthropic path, optional Qwen observation is forwarded, invalid provider/question is `422`, unconfigured provider is `503`, and no response contains configured secret strings.

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/test_demo_api.py -q`

Expected: new routes return `404`.

- [ ] **Step 3: Implement request models, routes, and serializers**

Add Pydantic request models with bounded strings/probabilities and explicit provider validation. Translate `CloudAdviceError` to sanitized JSON while keeping endpoint functions synchronous for FastAPI threadpool execution.

- [ ] **Step 4: Verify GREEN**

Run: `uv run pytest tests/test_demo_api.py -q`

Expected: all API tests pass.

---

### Task 4: React assistant modes and request state

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/client.test.ts`
- Modify: `frontend/src/hooks/useDemo.ts`
- Modify: `frontend/src/hooks/useDemo.test.tsx`
- Create: `frontend/src/components/AssistantPanel.tsx`
- Create: `frontend/src/components/AdvicePanel.tsx`
- Modify: `frontend/src/components/QwenPanel.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/components.test.tsx`
- Modify: `frontend/src/smoke.test.tsx`

**Interfaces:**
- Produces: `AdviceProviderStatus`, `AdviceProvidersResponse`, `ManagementAdvice`, and `AdviceProviderId` TypeScript contracts.
- Produces: `fetchAdviceProviders()` and `askForAdvice()` clients.
- Extends: `DemoState` with provider-status and advice feature states plus abort-safe `askAdvice()`.

- [ ] **Step 1: Add failing client, hook, and component tests**

Assert the provider status loads once, stale requests abort, selecting Claude sends `provider: "anthropic"`, classification/Qwen evidence is serialized, Visual evidence remains the default mode, unconfigured providers are disabled, and switching modes retains one fixed `data-testid="assistant-glass"` stage.

- [ ] **Step 2: Verify RED**

Run: `cd frontend && npm test -- --run`

Expected: missing types, clients, hook state, and components fail.

- [ ] **Step 3: Implement clients and reducer state**

Follow the existing abort-controller pattern. Keep derived provider selection in component state, do not store API keys, and reset advice/Qwen answers when a different image is selected or classification reruns.

- [ ] **Step 4: Implement the fixed assistant stage**

Render an accessible two-option segmented control, then Qwen visual evidence or cloud management guidance inside the same scrollable state body. Provider choices are explicit radio buttons with 44px targets. Use `LiquidGlass` only on the outer assistant stage with `elasticity={0}`.

- [ ] **Step 5: Verify GREEN**

Run: `cd frontend && npm test -- --run`

Expected: all frontend tests pass.

---

### Task 5: Styling, configuration, documentation, and complete verification

**Files:**
- Modify: `frontend/src/styles.css`
- Create: `.env.example`
- Modify: `README.md`
- Modify: `TASKS.md`

- [ ] **Step 1: Add contract assertions for non-secret configuration and UI copy**

Extend integration tests to require all six environment-variable names in `.env.example`, require the README to explain server-only keys/manual provider selection, and require the UI to contain the educational/non-prescriptive boundary.

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/integration/test_react_demo_contract.py -q`

Expected: configuration/documentation assertions fail.

- [ ] **Step 3: Apply Apple-style stable material rules**

Add segmented controls, provider cards, answer typography, stable body sizing, high-contrast focus, disabled status, and reduced-motion/transparency rules. Limit animation to opacity/background/color; never transition assistant width, height, or transform.

- [ ] **Step 4: Document setup and evidence boundaries**

Explain optional provider keys, model overrides, no automatic fallback, expected paid API/network behavior, Qwen local-only setup, exact run commands, and the untested-without-credentials limitation. Record the completed verification path in `TASKS.md` only after tests pass.

- [ ] **Step 5: Run complete verification**

Run:

```bash
uv run pytest -q
uv run ruff check .
uv run ty check
cd frontend && npm test -- --run
cd frontend && npm run lint
cd frontend && npm run build
```

Expected: every command exits `0`; no paid provider is contacted.

- [ ] **Step 6: Browser QA**

Start the API and Vite app, then verify desktop and narrow layouts, both assistant modes, disabled provider states, Qwen visual evidence copy, stable geometry, keyboard focus, reduced-motion behavior, and absence of console errors. Live cloud answers remain unverified until the user configures a key.

- [ ] **Step 7: Commit and push**

Stage only files in this plan, preserving unrelated presentation and paper files. Commit with a scoped message and push the current branch after verification.
