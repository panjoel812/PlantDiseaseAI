import { useState, type FormEvent } from "react";
import LiquidGlass from "liquid-glass-react";

import type {
  AdviceProviderId,
  AdviceProvidersResponse,
  FeatureState,
  ManagementAdvice,
} from "../api/types";

interface AdvicePanelProps {
  enabled: boolean;
  providers: FeatureState<AdviceProvidersResponse>;
  state: FeatureState<ManagementAdvice>;
  onAsk(provider: AdviceProviderId, question: string): void;
}

const DEFAULT_ADVICE_QUESTION =
  "What management steps should I consider while the diagnosis remains uncertain?";

function GuidanceIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M12 3a7 7 0 0 0-4 12.7V19h8v-3.3A7 7 0 0 0 12 3Z" />
      <path d="M9 22h6M9.5 15.5h5M12 7v5M9.5 9.5 12 12l2.5-2.5" />
    </svg>
  );
}
export function AdvicePanel({
  enabled,
  providers,
  state,
  onAsk,
}: AdvicePanelProps) {
  const [provider, setProvider] = useState<AdviceProviderId>("openai");
  const [question, setQuestion] = useState(DEFAULT_ADVICE_QUESTION);
  const isLoading = state.status === "loading";
  const selectedProvider =
    providers.status === "success"
      ? providers.data.providers.find((item) => item.provider === provider)
      : undefined;
  const canSubmit = Boolean(
    enabled && selectedProvider?.configured && question.trim() && !isLoading,
  );

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (canSubmit) onAsk(provider, question.trim());
  }

  return (
    <div className="glass-stage advice-stage" data-testid="advice-glass">
      <LiquidGlass
        className="glass-surface panel-glass"
        cornerRadius={24}
        padding="0"
        displacementScale={22}
        blurAmount={0.07}
        saturation={118}
        elasticity={0}
        overLight
        style={{ position: "relative", width: "100%" }}
      >
        <section className="side-panel advice-panel" aria-labelledby="advice-title">
          <header className="panel-header">
            <span className="panel-icon advice-icon"><GuidanceIcon /></span>
            <div>
              <h2 id="advice-title">Management guidance</h2>
              <p>Optional cloud AI · manually selected</p>
            </div>
          </header>

          <div className="panel-state-body advice-state-body">
            {providers.status === "loading" || providers.status === "idle" ? (
              <p className="qwen-live" role="status">Checking cloud providers…</p>
            ) : providers.status === "error" ? (
              <div className="qwen-response error-message" role="alert">
                <strong>Provider status unavailable</strong>
                <p>{providers.error}</p>
              </div>
            ) : (
              <form className="advice-form" onSubmit={handleSubmit}>
                <fieldset className="provider-fieldset">
                  <legend>Choose one provider</legend>
                  <div className="provider-options">
                    {providers.data.providers.map((item) => (
                      <label
                        className={`provider-option${item.configured ? "" : " unavailable"}`}
                        key={item.provider}
                      >
                        <input
                          type="radio"
                          name="advice-provider"
                          value={item.provider}
                          checked={provider === item.provider}
                          disabled={!item.configured || isLoading}
                          onChange={() => setProvider(item.provider)}
                        />
                        <span>
                          <strong>{item.display_name}</strong>
                          <small>{item.configured ? item.model_id : "Not configured"}</small>
                        </span>
                      </label>
                    ))}
                  </div>
                </fieldset>
                {selectedProvider && !selectedProvider.configured ? (
                  <p className="provider-detail">{selectedProvider.detail}</p>
                ) : null}
                <label htmlFor="advice-question">Question for management guidance</label>
                <textarea
                  id="advice-question"
                  rows={2}
                  value={question}
                  disabled={isLoading}
                  onChange={(event) => setQuestion(event.currentTarget.value)}
                />
                <button
                  className="button primary-button advice-submit"
                  type="submit"
                  disabled={!canSubmit}
                >
                  <GuidanceIcon />
                  {isLoading ? "Asking provider…" : "Ask for guidance"}
                </button>
              </form>
            )}

            {!enabled ? (
              <p className="provider-detail">
                Guidance unlocks only after the plant identity passes the crop gate.
              </p>
            ) : null}
            {isLoading ? (
              <p className="qwen-live" role="status">Requesting conditional guidance…</p>
            ) : state.status === "error" ? (
              <div className="qwen-response error-message" role="alert">
                <strong>Guidance unavailable</strong>
                <p>{state.error}</p>
              </div>
            ) : state.status === "success" ? (
              <div
                className={state.data.refused ? "qwen-response refusal" : "qwen-response"}
                role="status"
              >
                <strong>{state.data.refused ? "Request bounded" : "Conditional guidance"}</strong>
                <p>{state.data.message}</p>
                {state.data.reasons.map((reason) => <p key={reason}>{reason}</p>)}
                <p className="evidence-boundary">{state.data.evidence_boundary}</p>
              </div>
            ) : null}
          </div>
        </section>
      </LiquidGlass>
    </div>
  );
}
