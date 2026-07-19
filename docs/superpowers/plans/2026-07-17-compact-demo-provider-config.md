# Compact Demo and In-Memory Provider Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> for inline implementation. Use superpowers:subagent-driven-development only when
> the user explicitly requests subagents. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a one-viewport Apple-style desktop demo with concise structured Qwen observations, website-configurable process-memory cloud keys, restored ambient leaves, and complete English/Chinese READMEs.

**Architecture:** Keep classifier, Qwen, and cloud guidance as separate services. Normalize Qwen output at the backend audit boundary, add a locked ephemeral credential override inside `CloudAdviceService`, expose non-secret configure/clear endpoints through FastAPI, and keep password values transient inside the configuration sheet. Use viewport-derived CSS for desktop and retain document flow on mobile.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, React 19, TypeScript, Vitest, Testing Library, `liquid-glass-react`, CSS media queries, pytest, Ruff, ty.

## Global Constraints

- API keys exist only in FastAPI process memory and disappear on restart.
- Keys must never be returned, logged, stored in browser storage, placed in URLs, or committed.
- Provider selection remains manual; no automatic fallback.
- Qwen describes visible morphology only and never diagnoses or recommends treatment.
- `liquid-glass-react` remains enabled with `elasticity={0}` for large panels.
- Desktop targets are 1440×900 and 1920×1080 without document scrolling; mobile 390×844 may scroll vertically.
- Ambient motion uses transforms/opacity only and stops under `prefers-reduced-motion`.
- Existing research claims and safety boundaries remain unchanged.
- Local paper/PPT working files stay excluded from commits.

## Completion disposition

- **Tasks 1–7 — IMPLEMENTED:** shipped in `afca2d5` and published to public `main`. This includes structured Qwen observations with an auditable raw-response disclosure, locked process-memory provider credentials, configure/clear API routes, transient React data flow, the provider configuration sheet, compact viewport geometry, restored ambient leaves, and complete reciprocal English/Chinese public guides.
- **Task 8, Steps 1–4 — NOT RUN IN THE FINAL PASS:** the user explicitly requested a one-pass documentation closeout without another server start, browser inspection, automated test run, or release-manifest rebuild. These steps are waived for this pass, not reported as passing. The existing QA and `week8-rc1` manifest remain historical evidence for their recorded commits.
- **Task 8, Step 5 — COMPLETE:** implementation and documentation closeout were committed and pushed to public `main`.
- This disposition closes the implementation plan without inventing verification evidence. The unchecked boxes below preserve the original executable procedure for any future independent rerun.

---

### Task 1: Normalize Qwen into structured visual observations

**Files:**
- Modify: `src/plantdisease/vlm/interactive.py`
- Modify: `app/api.py`
- Test: `tests/vlm/test_interactive.py`
- Test: `tests/test_demo_api.py`

**Interfaces:**
- Consumes: `VLMBackend.generate(image: object, question: str) -> str`.
- Produces: `InteractiveQwenResult.observations: tuple[str, ...]`, `_build_visual_prompt(question: str) -> str`, and `_normalize_visual_observations(raw_answer: str) -> tuple[str, ...]`.

- [ ] **Step 1: Write failing Qwen normalization tests**

```python
def test_visual_answer_is_prompted_and_normalized_into_complete_observations() -> None:
    question = "What spots, colors, shapes, margins, textures, and distributions are visible?"
    expected_prompt = (
        "Inspect only visible pixels. Do not diagnose disease or recommend treatment.\n"
        "Return at most six short, complete observations about spots, colors, shapes,\n"
        "margins, textures, and distribution. Do not add an introduction.\n\n"
        f"Question: {question}"
    )
    raw = """Based on the image, here is a detailed analysis:
    **Spots:** - Numerous elongated brown lesions.
    **Colors:** - Tan centers with darker margins.
    **Spots:** - Numerous elongated brown lesions.
    **Distribution:** - Lesions follow the leaf veins."""
    backend = MockVLMBackend({expected_prompt: raw})
    result = InteractiveQwenService(
        backend=backend, status_probe=_ready_status
    ).ask(FIELD_BYTES, question, None)
    assert backend.calls[0][1] == expected_prompt
    assert result.observations == (
        "Spots: Numerous elongated brown lesions.",
        "Colors: Tan centers with darker margins.",
        "Distribution: Lesions follow the leaf veins.",
    )
    assert result.assistant_response.message == " ".join(result.observations)
    assert result.raw_answer == raw


def test_visual_observations_are_bounded() -> None:
    raw = "\n".join(f"- Observation {index}: {'x' * 300}" for index in range(10))
    observations = interactive_module._normalize_visual_observations(raw)
    assert len(observations) == 6
    assert all(len(item) <= 180 for item in observations)
```

Add an API assertion:

```python
assert response.json()["observations"] == [
    "Spots: Elongated tan-brown lesions.",
    "Margins: Darker edges.",
]
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
uv run pytest -q \
  tests/vlm/test_interactive.py::test_visual_answer_is_prompted_and_normalized_into_complete_observations \
  tests/vlm/test_interactive.py::test_visual_observations_are_bounded \
  tests/test_demo_api.py::test_qwen_answer_serializes_structured_observations
```

Expected: failures because the result has no `observations`, the backend receives the original question, and the API omits the field.

- [ ] **Step 3: Implement the bounded prompt and normalizer**

Add to `interactive.py`:

```python
MAX_VISUAL_OBSERVATIONS = 6
MAX_VISUAL_OBSERVATION_CHARACTERS = 180
_VISUAL_PREFIX = """Inspect only visible pixels. Do not diagnose disease or recommend treatment.
Return at most six short, complete observations about spots, colors, shapes,
margins, textures, and distribution. Do not add an introduction.\n\nQuestion: """


def _build_visual_prompt(question: str) -> str:
    return _VISUAL_PREFIX + question.strip()


def _normalize_visual_observations(raw_answer: str) -> tuple[str, ...]:
    normalized = re.sub(r"\*\*([^*]+)\*\*", r"\n\1", raw_answer)
    fragments = normalized.splitlines()
    observations: list[str] = []
    seen: set[str] = set()
    for fragment in fragments:
        item = re.sub(r"^[\s*#•\-\d.)]+", "", fragment).strip()
        item = re.sub(r"(?i)^based on .*?(?:analysis|image)\s*:?\s*", "", item)
        item = re.sub(r"^([A-Za-z][\w /-]{1,32}:)\s*[-•]\s*", r"\1 ", item)
        item = re.sub(r"\s+", " ", item)
        if not item:
            continue
        if len(item) > MAX_VISUAL_OBSERVATION_CHARACTERS:
            item = textwrap.shorten(
                item,
                width=MAX_VISUAL_OBSERVATION_CHARACTERS,
                placeholder="…",
            )
        item = item.rstrip(" ,;:-")
        if item and item[-1] not in ".!?":
            item += "."
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        observations.append(item)
        if len(observations) == MAX_VISUAL_OBSERVATIONS:
            break
    return tuple(observations or ("No concise visual observation was returned.",))
```

Generate with `_build_visual_prompt(normalized_question)`, retain `raw_answer`, set
`observations`, and join observations for the concise assistant message. Raise the
default interactive backend budget from 96 to 192 tokens so the requested short
rows can finish cleanly, and change the existing
`test_get_qwen_service_is_cached_and_never_enables_download` assertion to
`assert first.backend.max_tokens == 192`.
Serialize `observations` in `app/api.py`.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
uv run pytest -q tests/vlm/test_interactive.py tests/test_demo_api.py -k 'qwen or visual'
uv run ruff check src/plantdisease/vlm/interactive.py app/api.py tests/vlm/test_interactive.py tests/test_demo_api.py
```

Expected: all selected tests pass and Ruff reports `All checks passed!`.

- [ ] **Step 5: Commit Task 1**

```bash
git add src/plantdisease/vlm/interactive.py app/api.py \
  tests/vlm/test_interactive.py tests/test_demo_api.py
git commit -m "fix: structure qwen visual evidence"
```

---

### Task 2: Add locked process-memory provider credentials

**Files:**
- Modify: `src/plantdisease/vlm/cloud_advice.py`
- Test: `tests/vlm/test_cloud_advice.py`

**Interfaces:**
- Consumes: `CloudProvider`, `_ProviderConfig`, and environment configuration.
- Produces: `CloudAdviceService.configure(provider: str, api_key: str, model_id: str | None = None) -> CloudProviderStatus` and `CloudAdviceService.clear(provider: str) -> CloudProviderStatus`.

- [ ] **Step 1: Write failing in-memory configuration tests**

```python
def test_runtime_key_configures_selected_provider_without_echo_or_network() -> None:
    transport = RecordingTransport([])
    service = CloudAdviceService(transport=transport, environ={})
    status = service.configure("openai", "sk-runtime-secret", "gpt-runtime")
    assert status.configured is True
    assert status.model_id == "gpt-runtime"
    assert "sk-runtime-secret" not in repr(status)
    assert "sk-runtime-secret" not in repr(service.statuses())
    assert transport.calls == []


def test_runtime_key_takes_precedence_then_clear_restores_environment() -> None:
    service = CloudAdviceService(
        transport=RecordingTransport([]),
        environ={"OPENAI_API_KEY": "environment-key", "OPENAI_MODEL": "gpt-env"},
    )
    service.configure("openai", "runtime-key", "gpt-runtime")
    assert service.statuses()[0].model_id == "gpt-runtime"
    cleared = service.clear("openai")
    assert cleared.configured is True
    assert cleared.model_id == "gpt-env"


def test_invalid_runtime_key_does_not_mutate_existing_configuration() -> None:
    service = CloudAdviceService(transport=RecordingTransport([]), environ={})
    service.configure("openai", "valid-key")
    with pytest.raises(ValueError, match="api_key"):
        service.configure("openai", "   ")
    assert service.statuses()[0].configured is True


def test_runtime_secret_is_absent_from_logs_and_sanitized_failures(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FailingTransport:
        def post_json(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
            raise HTTPTransportError(
                status_code=401,
                detail="authentication failed for sk-never-echo",
            )

    transport = FailingTransport()
    service = CloudAdviceService(transport=transport, environ={})
    service.configure("openai", "sk-never-echo")
    with pytest.raises(CloudAdviceError) as captured:
        service.ask("openai", "What should I monitor?", _context())
    assert "sk-never-echo" not in str(captured.value)
    assert "sk-never-echo" not in caplog.text
    assert service.clear("openai") == service.clear("openai")
```

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run pytest -q tests/vlm/test_cloud_advice.py -k runtime_key`

Expected: `AttributeError` because `configure` and `clear` do not exist.

- [ ] **Step 3: Implement the locked override store**

Add a `threading.RLock`, an internal frozen credential record, and bounded validation:

```python
MAX_API_KEY_CHARACTERS = 8_192
MAX_MODEL_ID_CHARACTERS = 200

@dataclass(frozen=True)
class _RuntimeCredential:
    api_key: str
    model_id: str | None


def configure(self, provider: str, api_key: str, model_id: str | None = None) -> CloudProviderStatus:
    config = _lookup_provider(provider)
    key = api_key.strip()
    model = model_id.strip() if model_id else None
    if not key or len(key) > MAX_API_KEY_CHARACTERS:
        raise ValueError("api_key must be non-empty and at most 8192 characters")
    if model is not None and len(model) > MAX_MODEL_ID_CHARACTERS:
        raise ValueError("model_id must be at most 200 characters")
    with self._credential_lock:
        self._runtime_credentials[config.provider] = _RuntimeCredential(key, model)
    return self._status(config)


def clear(self, provider: str) -> CloudProviderStatus:
    config = _lookup_provider(provider)
    with self._credential_lock:
        self._runtime_credentials.pop(config.provider, None)
    return self._status(config)
```

Resolve `(api_key, model_id)` through one `_credentials(config)` helper used by both `_status` and `ask`; never include the key in status/detail/repr.

- [ ] **Step 4: Run Task 2 tests and verify GREEN**

Run:

```bash
uv run pytest -q tests/vlm/test_cloud_advice.py
uv run ruff check src/plantdisease/vlm/cloud_advice.py tests/vlm/test_cloud_advice.py
```

Expected: all cloud advice tests pass and Ruff is clean.

- [ ] **Step 5: Commit Task 2**

```bash
git add src/plantdisease/vlm/cloud_advice.py tests/vlm/test_cloud_advice.py
git commit -m "feat: configure cloud providers in memory"
```

---

### Task 3: Expose non-secret provider configure and clear endpoints

**Files:**
- Modify: `app/api.py`
- Test: `tests/test_demo_api.py`

**Interfaces:**
- Consumes: Task 2 `configure` and `clear` methods.
- Produces: `POST /api/advice/providers/{provider}/configure` and `DELETE /api/advice/providers/{provider}/configure`.

- [ ] **Step 1: Write failing API contract tests**

```python
def test_provider_can_be_configured_and_cleared_without_key_echo() -> None:
    service = FakeAdviceService()
    client = TestClient(create_app(advice_provider=lambda: service))
    configured = client.post(
        "/api/advice/providers/openai/configure",
        json={"api_key": "sk-browser-secret", "model_id": "gpt-runtime"},
    )
    assert configured.status_code == 200
    assert configured.json()["configured"] is True
    assert configured.json()["model_id"] == "gpt-runtime"
    assert "sk-browser-secret" not in configured.text
    assert service.configure_calls == [("openai", "sk-browser-secret", "gpt-runtime")]

    cleared = client.delete("/api/advice/providers/openai/configure")
    assert cleared.status_code == 200
    assert "sk-browser-secret" not in cleared.text
    assert service.clear_calls == ["openai"]


def test_invalid_provider_configuration_does_not_mutate_service() -> None:
    response = client.post(
        "/api/advice/providers/openai/configure", json={"api_key": ""}
    )
    assert response.status_code == 422
    assert service.configure_calls == []
```

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run pytest -q tests/test_demo_api.py -k 'provider_can_be_configured or invalid_provider_configuration'`

Expected: 404 for the new routes.

- [ ] **Step 3: Implement request model, protocol, routes, and DELETE CORS**

```python
class ProviderConfigureRequest(BaseModel):
    api_key: str = Field(min_length=1, max_length=8_192)
    model_id: str | None = Field(default=None, max_length=200)

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("api_key must not be blank")
        return value


@app.post("/api/advice/providers/{provider}/configure")
def configure_advice_provider(
    provider: Literal["openai", "anthropic", "gemini"],
    request: ProviderConfigureRequest,
) -> dict[str, object]:
    status = _get_advice_service(app).configure(
        provider, request.api_key, request.model_id
    )
    return _serialize_advice_provider_status(status)


@app.delete("/api/advice/providers/{provider}/configure")
def clear_advice_provider(
    provider: Literal["openai", "anthropic", "gemini"],
) -> dict[str, object]:
    return _serialize_advice_provider_status(
        _get_advice_service(app).clear(provider)
    )
```

Extend `AdviceService` and set `allow_methods=["GET", "POST", "DELETE"]`.

- [ ] **Step 4: Run API tests and verify GREEN**

Run:

```bash
uv run pytest -q tests/test_demo_api.py
uv run ty check app/api.py src/plantdisease/vlm/cloud_advice.py
```

Expected: all API tests pass and ty reports `All checks passed!`.

- [ ] **Step 5: Commit Task 3**

```bash
git add app/api.py tests/test_demo_api.py
git commit -m "feat: expose temporary provider configuration"
```

---

### Task 4: Add transient React configuration data flow

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/client.test.ts`
- Modify: `frontend/src/hooks/useDemo.ts`
- Modify: `frontend/src/hooks/useDemo.test.tsx`
- Modify: `frontend/src/api/types.ts`

**Interfaces:**
- Consumes: Task 3 endpoints.
- Produces: `configureAdviceProvider`, `clearAdviceProvider`, `DemoState.configureProvider`, and `DemoState.clearProvider`.

- [ ] **Step 1: Write failing client and hook tests**

```typescript
it("configures one provider without browser storage", async () => {
  const storageSpy = vi.spyOn(Storage.prototype, "setItem");
  await configureAdviceProvider("openai", "sk-transient", "gpt-runtime");
  expect(fetch).toHaveBeenCalledWith(
    "/api/advice/providers/openai/configure",
    expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ api_key: "sk-transient", model_id: "gpt-runtime" }),
    }),
  );
  expect(storageSpy).not.toHaveBeenCalled();
});

it("refreshes non-secret status after configure and clear", async () => {
  const { result } = renderHook(() => useDemo());
  await act(async () => {
    await result.current.configureProvider("openai", "secret", "gpt");
  });
  expect(result.current.adviceProviders).toMatchObject({ status: "success" });
  await act(async () => {
    await result.current.clearProvider("openai");
  });
  expect(clearAdviceProvider).toHaveBeenCalledWith("openai", expect.any(AbortSignal));
});
```

- [ ] **Step 2: Run tests and verify RED**

Run: `cd frontend && npm test -- --run src/api/client.test.ts src/hooks/useDemo.test.tsx`

Expected: import/type failures because the functions do not exist.

- [ ] **Step 3: Implement client functions and abort-safe hook callbacks**

```typescript
export function configureAdviceProvider(
  provider: AdviceProviderId,
  apiKey: string,
  modelId?: string,
  signal?: AbortSignal,
): Promise<AdviceProviderStatus> {
  return requestJson(`/api/advice/providers/${provider}/configure`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      api_key: apiKey,
      ...(modelId?.trim() ? { model_id: modelId.trim() } : {}),
    }),
    signal,
  });
}

export function clearAdviceProvider(
  provider: AdviceProviderId,
  signal?: AbortSignal,
): Promise<AdviceProviderStatus> {
  return requestJson(`/api/advice/providers/${provider}/configure`, {
    method: "DELETE",
    signal,
  });
}
```

Extend the response type so the UI can render normalized rows while retaining the
auditable raw model output:

```typescript
export interface QwenAnswer {
  raw_answer: string | null;
  observations: string[];
  message: string;
  action: string;
  refused: boolean;
  reasons: string[];
  sources: string[];
  model_id: string;
  scope: string;
  evidence_boundary: string;
}
```

The hook must pass the key directly from event callback to the client, discard it after `await`, replace only the returned provider status, and abort prior configuration requests on reset/unmount.

- [ ] **Step 4: Run frontend data-flow tests and verify GREEN**

Run: `cd frontend && npm test -- --run src/api/client.test.ts src/hooks/useDemo.test.tsx`

Expected: both files pass with no storage writes.

- [ ] **Step 5: Commit Task 4**

```bash
git add frontend/src/api/client.ts frontend/src/api/client.test.ts \
  frontend/src/hooks/useDemo.ts frontend/src/hooks/useDemo.test.tsx \
  frontend/src/api/types.ts
git commit -m "feat: connect temporary provider configuration"
```

---

### Task 5: Build compact Qwen rows and provider configuration sheet

**Files:**
- Create: `frontend/src/components/ProviderConfigSheet.tsx`
- Modify: `frontend/src/components/AdvicePanel.tsx`
- Modify: `frontend/src/components/AssistantPanel.tsx`
- Modify: `frontend/src/components/QwenPanel.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/components.test.tsx`
- Modify: `frontend/src/styles.css`

**Interfaces:**
- Consumes: Task 1 `QwenAnswer.observations` and Task 4 provider callbacks.
- Produces: an accessible temporary-key sheet and compact evidence rows.

Add `AdviceProviderStatus` to the type imports and import
`ProviderConfigSheet` in `components.test.tsx`. Extend the existing `qwenAnswer`
helper with `observations: ["The image shows elongated lesions."]` so every
existing fixture remains type-complete.

- [ ] **Step 1: Write failing component tests**

```typescript
it("renders concise observations and keeps raw qwen output collapsed", () => {
  const qwenSuccess: FeatureState<QwenAnswer> = {
    status: "success",
    data: qwenAnswer({
      raw_answer: "**Spots:** elongated lesions. **Colors:** tan centers.",
      observations: [
        "Elongated lesions run parallel to the veins.",
        "The centers are tan to brown.",
        "Darker margins surround several lesions.",
      ],
    }),
    error: null,
  };
  render(
    <QwenPanel
      enabled
      runtime={readyQwenRuntime()}
      state={qwenSuccess}
      onAsk={vi.fn()}
      onRetryRuntime={vi.fn()}
    />,
  );
  expect(screen.getAllByRole("listitem")).toHaveLength(3);
  const disclosure = screen.getByText("Raw response").closest("details");
  expect(disclosure).not.toHaveAttribute("open");
  expect(screen.getByText(/\*\*Spots:\*\*/)).not.toBeVisible();
});

it("clears the password field immediately after a successful save", async () => {
  const user = userEvent.setup();
  const onConfigure = vi.fn().mockResolvedValue(undefined);
  const providers: AdviceProviderStatus[] = [{
    provider: "openai",
    display_name: "OpenAI",
    configured: false,
    model_id: "gpt-4.1-mini",
    detail: "Not configured",
  }];
  render(
    <ProviderConfigSheet
      providers={providers}
      onConfigure={onConfigure}
      onClear={vi.fn().mockResolvedValue(undefined)}
      onClose={vi.fn()}
    />,
  );
  const input = screen.getByLabelText(/openai api key/i);
  expect(input).toHaveAttribute("type", "password");
  await user.type(input, "sk-transient");
  await user.click(screen.getByRole("button", { name: /save openai/i }));
  expect(onConfigure).toHaveBeenCalledWith("openai", "sk-transient", "");
  expect(input).toHaveValue("");
});
```

- [ ] **Step 2: Run component tests and verify RED**

Run: `cd frontend && npm test -- --run src/components/components.test.tsx`

Expected: missing `ProviderConfigSheet`, missing `observations`, and raw response rendered as the primary paragraph.

- [ ] **Step 3: Implement the sheet and observation rows**

`ProviderConfigSheet` keeps key/model inputs in component-local state only:

```tsx
<section className="provider-config-sheet" aria-label="Temporary provider configuration">
  <header>
    <div><strong>Configure providers</strong><p>Temporary · cleared on API restart</p></div>
    <button type="button" aria-label="Close provider configuration" onClick={onClose}>×</button>
  </header>
  {providers.map((provider) => (
    <form key={provider.provider} onSubmit={(event) => void save(event, provider.provider)}>
      <label htmlFor={`${provider.provider}-key`}>{provider.display_name} API key</label>
      <input
        id={`${provider.provider}-key`}
        type="password"
        autoComplete="off"
        value={keys[provider.provider] ?? ""}
        onChange={(event) => setKeys((current) => ({
          ...current,
          [provider.provider]: event.target.value,
        }))}
      />
      <label htmlFor={`${provider.provider}-model`}>{provider.display_name} model</label>
      <input
        id={`${provider.provider}-model`}
        value={models[provider.provider] ?? provider.model_id}
        onChange={(event) => setModels((current) => ({
          ...current,
          [provider.provider]: event.target.value,
        }))}
      />
      <button type="submit">Save {provider.display_name}</button>
      <button type="button" onClick={() => onClear(provider.provider)}>Clear</button>
    </form>
  ))}
</section>
```

Qwen success state becomes:

```tsx
<ul className="observation-list">
  {state.data.observations.map((observation) => <li key={observation}>{observation}</li>)}
</ul>
{state.data.raw_answer ? (
  <details className="raw-response"><summary>Raw response</summary><p>{state.data.raw_answer}</p></details>
) : null}
```

Pass callbacks through `App -> AssistantPanel -> AdvicePanel`. Keep real `LiquidGlass`, zero elasticity, focus-visible states, and a non-blocking sheet without a dark scrim.

- [ ] **Step 4: Run component tests and verify GREEN**

Run:

```bash
cd frontend
npm test -- --run src/components/components.test.tsx src/smoke.test.tsx
npm run lint
```

Expected: component/smoke tests and oxlint pass.

- [ ] **Step 5: Commit Task 5**

```bash
git add frontend/src/components/ProviderConfigSheet.tsx \
  frontend/src/components/AdvicePanel.tsx \
  frontend/src/components/AssistantPanel.tsx \
  frontend/src/components/QwenPanel.tsx frontend/src/App.tsx \
  frontend/src/components/components.test.tsx frontend/src/styles.css
git commit -m "feat: add compact assistant configuration UI"
```

---

### Task 6: Fit desktop into one viewport and restore ambient leaves

**Files:**
- Modify: `frontend/src/styles.css`
- Modify: `frontend/src/components/AmbientGarden.tsx`
- Modify: `frontend/src/smoke.test.tsx`
- Test evidence: `reports/week8_react_demo_qa.md`

**Interfaces:**
- Consumes: existing `.page-shell`, `.hero`, `.workspace-grid`, `.result-rail`, and `.ambient-garden` DOM contracts.
- Produces: viewport-fit desktop geometry and initial-viewport ambient decoration.

- [ ] **Step 1: Write failing static contract tests**

```typescript
expect(screen.getByTestId("ambient-garden")).toHaveAttribute("aria-hidden", "true");
expect(screen.getByTestId("ambient-garden")).toHaveClass("ambient-garden");
expect(document.querySelectorAll(".ambient-shape.leaf")).toHaveLength(3);
```

Extend `tests/integration/test_react_demo_contract.py`:

```python
styles = (FRONTEND / "src/styles.css").read_text(encoding="utf-8")
ambient_rule = styles.split(".ambient-garden", 1)[1].split("}", 1)[0]
qwen_source = (FRONTEND / "src/components/QwenPanel.tsx").read_text(encoding="utf-8")
advice_source = (FRONTEND / "src/components/AdvicePanel.tsx").read_text(encoding="utf-8")

assert "100dvh" in styles
assert "position: fixed" in ambient_rule
assert "prefers-reduced-motion" in styles
assert "prefers-reduced-transparency" in styles
assert "elasticity={0}" in qwen_source
assert "elasticity={0}" in advice_source
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
cd frontend
npm test -- --run src/smoke.test.tsx
cd ..
uv run pytest -q tests/integration/test_react_demo_contract.py
```

Expected: contract fails because ambient positioning is absolute and the desktop grid uses the fixed `42rem`–`48rem` clamp.

- [ ] **Step 3: Implement viewport-derived desktop geometry**

Use these desktop rules first. If browser geometry later requires a correction,
record the exact CSS change and measured before/after geometry in the QA report:

```css
.page-shell { min-height: 100dvh; height: 100dvh; padding-bottom: .65rem; }
.site-header { min-height: 3rem; margin-bottom: .35rem; }
.app-field { height: calc(100dvh - 4.1rem); padding-block: .55rem .35rem; }
.hero { height: 100%; display: grid; grid-template-rows: auto minmax(0, 1fr) auto; }
.hero h1 { font-size: clamp(2.25rem, 4vw, 3.8rem); line-height: .96; }
.hero p { margin-top: .28rem; }
.workspace-grid { height: auto; min-height: 0; margin-top: .65rem; }
.result-rail { grid-template-rows: minmax(17rem, 1.08fr) minmax(15rem, .92fr); }
.ambient-garden { position: fixed; bottom: 0; height: 10rem; }
```

Under `@media (max-width: 760px)`, restore `height: auto`, `min-height: 100dvh`, absolute ambient placement, and normal vertical flow. Ensure the safety strip has compact padding and no content is clipped. Add an explicit `prefers-reduced-transparency` rule that removes backdrop blur and renders the ambient shapes more solid and subdued.

- [ ] **Step 4: Verify automated contracts and frontend build**

Run:

```bash
cd frontend
npm test -- --run
npm run lint
npm run build
cd ..
uv run pytest -q tests/integration/test_react_demo_contract.py
```

Expected: all commands pass.

- [ ] **Step 5: Commit Task 6**

```bash
git add frontend/src/styles.css frontend/src/components/AmbientGarden.tsx \
  frontend/src/smoke.test.tsx tests/integration/test_react_demo_contract.py \
  reports/week8_react_demo_qa.md
git commit -m "style: fit demo within desktop viewport"
```

---

### Task 7: Restore complete bilingual public documentation

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `.env.example`
- Modify: `tests/release/test_public_readme_contract.py`
- Modify: `docs/artifact-index.md`

**Interfaces:**
- Consumes: final endpoint names and UI copy from Tasks 1–6.
- Produces: reciprocal full English/Chinese guides and temporary-key security documentation.

- [ ] **Step 1: Write failing bilingual README contract**

```python
def test_readmes_are_reciprocal_and_cover_all_public_run_paths() -> None:
    english = Path("README.md").read_text(encoding="utf-8")
    chinese = Path("README.zh-CN.md").read_text(encoding="utf-8")
    assert "[简体中文](README.zh-CN.md)" in english
    assert "[English](README.md)" in chinese
    for english_term, chinese_term in (
        ("React + FastAPI demo", "React + FastAPI Demo"),
        ("Docker on Linux", "Linux、macOS 与 Windows Docker"),
        ("Optional Qwen panel", "可选 Qwen 面板"),
        ("Reproducibility and evidence", "复现与证据"),
        ("Known limitations", "已知限制"),
    ):
        assert english_term in english
        assert chinese_term in chinese
    assert len(chinese) >= 12_000
    assert "process memory" in english
    assert "进程内存" in chinese
```

- [ ] **Step 2: Run test and verify RED**

Run: `uv run pytest -q tests/release/test_public_readme_contract.py`

Expected: failure because the Chinese README is approximately 3 KB and lacks the complete run sections.

- [ ] **Step 3: Expand both guides and provider security copy**

Mirror the existing English structure in Chinese. Add exact configure endpoint behavior, the temporary/restart-cleared boundary, HTTPS warning for remote deployment, compact Qwen observations/raw disclosure, viewport behavior, and reciprocal language links. Keep all locked values and their required boundary wording unchanged.

Update `.env.example` comments to say environment keys remain the recommended deployment path while the local website can set temporary process-memory overrides.

- [ ] **Step 4: Run documentation and claim audits**

Run:

```bash
uv run pytest -q tests/release/test_public_readme_contract.py tests/release/test_claims.py
uv run python scripts/audit_week8_claims.py \
  --config configs/week8_claims.yaml \
  --output reports/release/week8_claim_evidence.json \
  --check-links
```

Expected: language contract and all claim/link audits pass.

- [ ] **Step 5: Commit Task 7**

```bash
git add README.md README.zh-CN.md .env.example \
  tests/release/test_public_readme_contract.py docs/artifact-index.md \
  reports/release/week8_claim_evidence.json
git commit -m "docs: restore complete bilingual demo guide"
```

---

### Task 8: Browser QA, release manifest, and main publication

**Files:**
- Modify: `reports/week8_react_demo_qa.md`
- Modify: `reports/release/week8_rc1_manifest.json`
- Modify: `TASKS.md`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: browser evidence, fresh release hashes, clean verified `main`.

- [ ] **Step 1: Start the local API and Vite servers**

```bash
uv run python scripts/run_demo_api.py \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --device mps --host 127.0.0.1 --port 8000

cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Expected: API and Vite report ready without loading any cloud provider key.

- [ ] **Step 2: Run browser QA at three viewports**

Use the in-app Browser plugin. At 1440×900 and 1920×1080 verify:

```text
scrollWidth == clientWidth
scrollHeight <= clientHeight + 2
image, classifier, assistant tabs, safety strip visible
at least two ambient leaves intersect the viewport
Qwen observations visible; raw response details closed
configuration sheet opens without a dark scrim
password field empties after configure
provider status changes without any key text in DOM
```

At 390×844 verify no horizontal overflow, usable touch targets, reduced single-column layout, and allowed vertical scrolling. Record exact geometry and console errors in `reports/week8_react_demo_qa.md`.

- [ ] **Step 3: Run fresh full verification**

```bash
uv run pytest -q
uv run ruff check .
uv run ty check src/plantdisease app scripts
cd frontend && npm test -- --run && npm run lint && npm run build && cd ..
git diff --check
git grep -n '/''Users/' -- ':!*.pptx' ':!*.key' ':!*.pdf' || test $? -eq 1
```

Expected: all commands exit 0; pytest and React test counts are reported in the handoff.

- [ ] **Step 4: Rebuild and validate release evidence**

```bash
uv run python scripts/build_release_candidate.py \
  --candidate-id week8-rc1 \
  --source-commit bc5edecda055d40c1eb075c77326fb42549eea13 \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --output reports/release/week8_rc1_manifest.json \
  --claims-output reports/release/week8_claim_evidence.json
uv run pytest -q tests/test_week8_release_cli.py tests/release/test_claims.py
```

Expected: candidate status `passed` and release tests pass.

- [ ] **Step 5: Commit final evidence and push main**

```bash
git add reports/week8_react_demo_qa.md reports/release/week8_rc1_manifest.json TASKS.md
git commit -m "chore: finalize compact demo evidence"
git status -sb
git push origin HEAD:main
git ls-remote origin refs/heads/main
```

Expected: clean local branch, fast-forward push, and remote `main` SHA equals local `HEAD`.
