import { useState, type FormEvent } from "react";
import LiquidGlass from "liquid-glass-react";

import type { FeatureState, QwenAnswer, QwenStatus } from "../api/types";

interface QwenPanelProps {
  enabled: boolean;
  runtime: FeatureState<QwenStatus>;
  state: FeatureState<QwenAnswer>;
  onAsk(question: string): void;
  onRetryRuntime(): void;
}

const DEFAULT_QUESTION = "What visual symptoms are visible?";

function ChatIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M20 11.5a7.5 7.5 0 0 1-8 7.5 9 9 0 0 1-3.6-.8L4 20l1.2-4A7.8 7.8 0 0 1 4 11.5 7.5 7.5 0 0 1 12 4a7.5 7.5 0 0 1 8 7.5Z" />
      <path d="M8.5 11.5h.01M12 11.5h.01M15.5 11.5h.01" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 32 32">
      <rect x="7" y="14" width="18" height="14" rx="3" />
      <path d="M11 14V9a5 5 0 0 1 10 0v5M16 20v3" />
    </svg>
  );
}

export function QwenPanel({
  enabled,
  runtime,
  state,
  onAsk,
  onRetryRuntime,
}: QwenPanelProps) {
  const [question, setQuestion] = useState(DEFAULT_QUESTION);
  const isLoading = state.status === "loading";
  const runtimeReady = runtime.status === "success" && runtime.data.ready;
  const showSetup = runtime.status === "success" && !runtime.data.ready;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (enabled && !isLoading) onAsk(question);
  }

  return (
    <div className="glass-stage qwen-stage" data-testid="qwen-glass">
      <LiquidGlass
        className="glass-surface panel-glass"
        cornerRadius={24}
        padding="0"
        displacementScale={22}
        blurAmount={0.07}
        saturation={118}
        elasticity={0}
        overLight
        style={{ position: "absolute", top: "50%", left: "50%" }}
      >
        <section className="side-panel qwen-panel" aria-labelledby="qwen-title">
          <header className="panel-header">
            <span className="panel-icon"><ChatIcon /></span>
            <div>
              <h2 id="qwen-title">Ask Qwen</h2>
              <p>Optional local Qwen3-VL</p>
            </div>
          </header>

          <div
            className="panel-state-body qwen-state-body"
            data-testid="qwen-state-body"
          >

          {showSetup ? (
            <div className="qwen-setup" role="status">
              <strong>Local runtime not ready</strong>
              <p>{runtime.data.detail}</p>
              {!runtime.data.supported_platform ? (
                <p>Qwen local inference requires Apple Silicon macOS.</p>
              ) : !runtime.data.dependency_available ? (
                <p>Install the local runtime with <code>uv sync --group vlm</code>.</p>
              ) : !runtime.data.weights_cached ? (
                <p>
                  Explicitly cache the model with
                  <code> uv run --group vlm hf download {runtime.data.model_id}</code>.
                </p>
              ) : null}
              <p className="evidence-boundary">No automatic download from the API.</p>
              <button
                className="runtime-retry"
                type="button"
                onClick={onRetryRuntime}
              >
                Check again
              </button>
            </div>
          ) : !runtimeReady ? (
            <div className="qwen-locked" role="status">
              <span className="lock-icon"><LockIcon /></span>
              <p>
                {runtime.status === "error"
                  ? `Runtime status unavailable: ${runtime.error}`
                  : "Checking local Qwen runtime…"}
              </p>
              {runtime.status === "error" ? (
                <button
                  className="runtime-retry"
                  type="button"
                  onClick={onRetryRuntime}
                >
                  Check again
                </button>
              ) : null}
            </div>
          ) : !enabled ? (
            <div className="qwen-locked">
              <span className="lock-icon"><LockIcon /></span>
              <p>Available after classification.</p>
            </div>
          ) : null}

          {enabled && runtimeReady ? (
            <form className="qwen-form" onSubmit={handleSubmit}>
              <label htmlFor="qwen-question">Question for Qwen</label>
              <input
                id="qwen-question"
                type="text"
                value={question}
                disabled={isLoading}
                onChange={(event) => setQuestion(event.currentTarget.value)}
              />
              <button
                className="button primary-button qwen-submit"
                type="submit"
                disabled={isLoading || question.trim().length === 0}
              >
                <ChatIcon />
                {isLoading ? "Asking Qwen…" : "Ask Qwen"}
              </button>
            </form>
          ) : !showSetup ? (
            <button
              className="button qwen-submit"
              type="button"
              disabled
            >
              <ChatIcon />
              Ask Qwen
            </button>
          ) : null}

          {isLoading ? (
            <p className="qwen-live" role="status">Asking Qwen…</p>
          ) : state.status === "error" ? (
            <div className="qwen-response error-message" role="alert">
              <strong>Qwen unavailable</strong>
              <p>{state.error}</p>
            </div>
          ) : state.status === "success" ? (
            <div
              className={state.data.refused ? "qwen-response refusal" : "qwen-response"}
              role="status"
            >
              <strong>{state.data.refused ? "Request refused" : "Exploratory answer"}</strong>
              <p>{state.data.message}</p>
              {state.data.reasons.map((reason) => (
                <p key={reason}>{reason}</p>
              ))}
              <p className="evidence-boundary">{state.data.evidence_boundary}</p>
            </div>
          ) : null}
          </div>
        </section>
      </LiquidGlass>
    </div>
  );
}
