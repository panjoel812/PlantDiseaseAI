import { useState } from "react";

import type {
  AdviceProviderId,
  AdviceProvidersResponse,
  FeatureState,
  ManagementAdvice,
  QwenAnswer,
  QwenStatus,
} from "../api/types";
import { AdvicePanel } from "./AdvicePanel";
import { ProviderConfigSheet } from "./ProviderConfigSheet";
import { QwenPanel } from "./QwenPanel";

interface AssistantPanelProps {
  classificationReady: boolean;
  qwenEnabled: boolean;
  qwenRuntime: FeatureState<QwenStatus>;
  qwenState: FeatureState<QwenAnswer>;
  providers: FeatureState<AdviceProvidersResponse>;
  adviceState: FeatureState<ManagementAdvice>;
  onAskQwen(question: string): void;
  onRetryQwenRuntime(): void;
  onAskAdvice(provider: AdviceProviderId, question: string): void;
  onConfigureProvider(
    provider: AdviceProviderId,
    apiKey: string,
    modelId?: string,
  ): Promise<void>;
  onClearProvider(provider: AdviceProviderId): Promise<void>;
}

type AssistantMode = "visual" | "guidance";

export function AssistantPanel({
  classificationReady,
  qwenEnabled,
  qwenRuntime,
  qwenState,
  providers,
  adviceState,
  onAskQwen,
  onRetryQwenRuntime,
  onAskAdvice,
  onConfigureProvider,
  onClearProvider,
}: AssistantPanelProps) {
  const [mode, setMode] = useState<AssistantMode>("visual");
  const [configOpen, setConfigOpen] = useState(false);
  const canConfigure = providers.status === "success";

  return (
    <div className="assistant-switcher" data-testid="assistant-glass">
      <div className="assistant-tabs" role="tablist" aria-label="AI assistance mode">
        <div className="assistant-mode-tabs">
          <button
            role="tab"
            type="button"
            aria-selected={mode === "visual"}
            onClick={() => setMode("visual")}
          >
            Visual evidence
          </button>
          <button
            role="tab"
            type="button"
            aria-selected={mode === "guidance"}
            onClick={() => setMode("guidance")}
          >
            Management guidance
          </button>
        </div>
        <button
          className="assistant-config-button"
          type="button"
          disabled={!canConfigure}
          onClick={() => setConfigOpen(true)}
        >
          API setup
        </button>
      </div>
      <div className="assistant-tab-panel" role="tabpanel">
        {mode === "visual" ? (
          <QwenPanel
            enabled={qwenEnabled}
            runtime={qwenRuntime}
            state={qwenState}
            onAsk={onAskQwen}
            onRetryRuntime={onRetryQwenRuntime}
          />
        ) : (
          <AdvicePanel
            enabled={classificationReady}
            providers={providers}
            state={adviceState}
            onAsk={onAskAdvice}
          />
        )}
      </div>
      {configOpen && providers.status === "success" ? (
        <ProviderConfigSheet
          providers={providers.data.providers}
          onConfigure={onConfigureProvider}
          onClear={onClearProvider}
          onClose={() => setConfigOpen(false)}
        />
      ) : null}
    </div>
  );
}
