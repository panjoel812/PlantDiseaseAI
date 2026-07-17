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
}: AssistantPanelProps) {
  const [mode, setMode] = useState<AssistantMode>("visual");

  return (
    <div className="assistant-switcher" data-testid="assistant-glass">
      <div className="assistant-tabs" role="tablist" aria-label="AI assistance mode">
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
    </div>
  );
}
