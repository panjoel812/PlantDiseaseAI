import { useState } from "react";
import LiquidGlass from "liquid-glass-react";

import type { ClassificationResult, FeatureState } from "../api/types";

interface ClassifierPanelProps {
  state: FeatureState<ClassificationResult>;
}

function NetworkIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <circle cx="5" cy="5" r="1.5" />
      <circle cx="19" cy="5" r="1.5" />
      <circle cx="5" cy="19" r="1.5" />
      <circle cx="19" cy="19" r="1.5" />
      <path d="m6.2 6.2 11.6 11.6M17.8 6.2 6.2 17.8" />
    </svg>
  );
}

function LeafIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 48 48">
      <path d="M39 8C21 9 12 17 13 31c8 4 18 0 22-8 2.6-5 3.5-10.2 4-15Z" />
      <path d="M9 39c6-10 13-16 23-22M14 29l7 2M22 21l1-7" />
    </svg>
  );
}

function WarningIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M10.3 4.1 2.8 17a2 2 0 0 0 1.7 3h15a2 2 0 0 0 1.7-3L13.7 4.1a2 2 0 0 0-3.4 0Z" />
      <path d="M12 9v4M12 17h.01" />
    </svg>
  );
}

function EyeIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M2.5 12s3.5-5 9.5-5 9.5 5 9.5 5-3.5 5-9.5 5-9.5-5-9.5-5Z" />
      <circle cx="12" cy="12" r="2.5" />
    </svg>
  );
}

function formatClassName(value: string): string {
  const condition = value.includes("___") ? value.split("___")[1] : value;
  return condition.replaceAll("_", " ");
}

function ClassifierContent({ state }: ClassifierPanelProps) {
  const [showOverlay, setShowOverlay] = useState(false);

  if (state.status === "idle") {
    return (
      <div className="empty-state">
        <span className="empty-icon"><LeafIcon /></span>
        <strong>Ready to analyze</strong>
        <p>Top-5 predictions and Grad-CAM will appear here.</p>
      </div>
    );
  }

  if (state.status === "loading") {
    return (
      <div className="panel-message" role="status" aria-live="polite">
        <span className="progress-mark" aria-hidden="true" />
        <strong>Analyzing leaf…</strong>
        <p>Running classification and Grad-CAM.</p>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="panel-message error-message" role="alert">
        <WarningIcon />
        <strong>Analysis unavailable</strong>
        <p>{state.error}</p>
      </div>
    );
  }

  const result = state.data;
  const gradcam = result.gradcam;
  const gradcamSource = showOverlay
    ? gradcam?.overlay_data_url
    : gradcam?.heatmap_data_url;

  return (
    <div className="classifier-result" aria-live="polite">
      <p className="result-boundary">Model prediction — not ground truth</p>
      {result.warnings.length > 0 ? (
        <div className="warning-list">
          <WarningIcon />
          <div>
            {result.warnings.map((warning) => (
              <p key={warning}>{warning}</p>
            ))}
          </div>
        </div>
      ) : null}
      <p className="result-label">Top-5 predictions (PlantVillage taxonomy)</p>
      <ol className="prediction-list">
        {result.predictions.map((prediction) => {
          const percentage = Math.max(
            0,
            Math.min(100, prediction.probability * 100),
          );
          const name = formatClassName(prediction.class_name);
          return (
            <li key={`${prediction.class_index}-${prediction.class_name}`}>
              <span className="prediction-name">{name}</span>
              <span
                className="probability-track"
                role="progressbar"
                aria-label={`${name} probability`}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round(percentage)}
              >
                <span style={{ width: `${percentage}%` }} />
              </span>
              <span className="probability-value">{percentage.toFixed(1)}%</span>
            </li>
          );
        })}
      </ol>

      {gradcam && gradcamSource ? (
        <div className="gradcam-block">
          <p>
            Grad-CAM (class: {formatClassName(gradcam.target_class_name)})
          </p>
          <div className="gradcam-media">
            <img
              src={gradcamSource}
              alt={showOverlay ? "Grad-CAM overlay" : "Grad-CAM heatmap"}
            />
            <button
              className="overlay-button"
              type="button"
              onClick={() => setShowOverlay((current) => !current)}
            >
              <EyeIcon />
              {showOverlay ? "Show heatmap" : "Show overlay"}
            </button>
          </div>
        </div>
      ) : (
        <p className="gradcam-unavailable">Grad-CAM output unavailable.</p>
      )}

      <p className="timing-line">
        {result.timings.total_ms.toFixed(1)} ms total
      </p>

    </div>
  );
}

export function ClassifierPanel({ state }: ClassifierPanelProps) {
  return (
    <div
      className="glass-stage classifier-stage"
      data-testid="classifier-glass"
    >
      <LiquidGlass
        className="glass-surface panel-glass"
        cornerRadius={24}
        padding="0"
        displacementScale={24}
        blurAmount={0.08}
        saturation={120}
        elasticity={0.06}
        overLight
        style={{ position: "absolute", top: "50%", left: "50%" }}
      >
        <section className="side-panel classifier-panel" aria-labelledby="classifier-title">
          <header className="panel-header">
            <span className="panel-icon"><NetworkIcon /></span>
            <h2 id="classifier-title">Classifier</h2>
          </header>
          <ClassifierContent state={state} />
        </section>
      </LiquidGlass>
    </div>
  );
}
