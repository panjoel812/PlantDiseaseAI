import {
  useEffect,
  useRef,
  useState,
  type DragEvent,
  type KeyboardEvent,
  type PointerEvent,
} from "react";
import LiquidGlass from "liquid-glass-react";

import type {
  FeatureState,
  LeafSelectionRequired,
  TargetPoint,
} from "../api/types";
import { coverPointToNormalizedImage } from "../lib/imageCoordinates";

interface ImageWorkspaceProps {
  previewUrl: string | null;
  selectedFileName: string | null;
  hasImage: boolean;
  classificationStatus: FeatureState<unknown>["status"];
  targetPoint?: TargetPoint | null;
  leafSelection?: LeafSelectionRequired | null;
  targetSelectionActive?: boolean;
  onSelectFile(file: File): void;
  onAnalyze(): void;
  onTargetPointChange?(point: TargetPoint): void;
}

function clampCoordinate(value: number): number {
  return Math.min(1, Math.max(0, Number(value.toFixed(2))));
}

function UploadIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M12 16V4" />
      <path d="m7.5 8.5 4.5-4.5 4.5 4.5" />
      <path d="M5 14v4.5A1.5 1.5 0 0 0 6.5 20h11a1.5 1.5 0 0 0 1.5-1.5V14" />
    </svg>
  );
}

function AnalyzeIcon({ again = false }: { again?: boolean }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      {again ? (
        <>
          <path d="M18.5 8.5A7 7 0 1 0 19 15" />
          <path d="M18.5 4v4.5H14" />
          <path d="m19.5 17.5.8.8" />
        </>
      ) : (
        <>
          <circle cx="10.5" cy="10.5" r="6.5" />
          <path d="m15.3 15.3 4.2 4.2" />
          <path d="M9 13c2.7-1 4-3.3 3.8-6-2.9.5-4.7 2.2-5 5.2" />
        </>
      )}
    </svg>
  );
}

export function ImageWorkspace({
  previewUrl,
  selectedFileName,
  hasImage,
  classificationStatus,
  targetPoint = null,
  leafSelection = null,
  targetSelectionActive = false,
  onSelectFile,
  onAnalyze,
  onTargetPointChange,
}: ImageWorkspaceProps) {
  const [isDragging, setIsDragging] = useState(false);
  const imageRef = useRef<HTMLImageElement>(null);
  const selectionPromptRef = useRef<HTMLDivElement>(null);
  const isLoading = classificationStatus === "loading";
  const analyzed = classificationStatus === "success";
  const imageTitle = selectedFileName
    ? selectedFileName === "field_corn_leaf.jpeg"
      ? "User-supplied field corn leaf"
      : selectedFileName
    : null;
  const imageAlt = imageTitle
    ? selectedFileName === "field_corn_leaf.jpeg"
      ? imageTitle
      : `Selected upload: ${selectedFileName}`
    : "";
  const actionLabel = isLoading
    ? "Analyzing leaf…"
    : targetSelectionActive && !targetPoint
      ? "Select a leaf first"
      : targetSelectionActive
        ? "Analyze selected leaf"
    : analyzed
      ? "Analyze again"
      : "Analyze leaf";
  const updateFromPointer = (event: PointerEvent<HTMLImageElement>) => {
    if (!targetSelectionActive || !onTargetPointChange) return;
    const image = imageRef.current;
    if (!image) return;
    const point = coverPointToNormalizedImage(
      event,
      image.getBoundingClientRect(),
      { width: image.naturalWidth, height: image.naturalHeight },
    );
    if (point) onTargetPointChange(point);
  };
  const moveCrosshair = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (!targetPoint || !onTargetPointChange) return;
    const next = { ...targetPoint };
    if (event.key === "ArrowLeft") next.x = clampCoordinate(next.x - 0.01);
    else if (event.key === "ArrowRight") next.x = clampCoordinate(next.x + 0.01);
    else if (event.key === "ArrowUp") next.y = clampCoordinate(next.y - 0.01);
    else if (event.key === "ArrowDown") next.y = clampCoordinate(next.y + 0.01);
    else return;
    event.preventDefault();
    onTargetPointChange(next);
  };

  useEffect(() => {
    if (targetSelectionActive) selectionPromptRef.current?.focus();
  }, [targetSelectionActive]);

  return (
    <div
      className="glass-stage image-workspace-stage"
      data-testid="image-workspace-glass"
    >
      <LiquidGlass
        className="glass-surface image-workspace-glass"
        cornerRadius={24}
        padding="0"
        displacementScale={30}
        blurAmount={0.08}
        saturation={125}
        elasticity={0}
        style={{ position: "absolute", top: "50%", left: "50%" }}
      >
        <section
          className={isDragging ? "image-workspace is-dragging" : "image-workspace"}
          aria-label="Image workspace"
          data-testid="image-drop-zone"
          onDragEnter={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragOver={(event) => event.preventDefault()}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(event: DragEvent<HTMLElement>) => {
            event.preventDefault();
            setIsDragging(false);
            const file = event.dataTransfer.files[0];
            if (file?.type.startsWith("image/")) onSelectFile(file);
          }}
        >
          {previewUrl && imageTitle ? (
            <img
              ref={imageRef}
              className={`field-image ${targetSelectionActive ? "is-targetable" : ""}`}
              src={previewUrl}
              alt={imageAlt}
              onPointerDown={updateFromPointer}
            />
          ) : (
            <div className="image-placeholder" aria-hidden="true" />
          )}

          {imageTitle ? (
            <div className="image-caption">
              <h2>{imageTitle}</h2>
              <p>No verified ground truth · out-of-domain example</p>
            </div>
          ) : null}

          {targetSelectionActive ? (
            <div
              ref={selectionPromptRef}
              className="target-selection-prompt"
              role="status"
              tabIndex={-1}
            >
              <strong>Select one clear leaf</strong>
              <span>
                {leafSelection?.message ??
                  "Click near the centre of the leaf you want to analyze."}
              </span>
              <button
                type="button"
                onClick={() => onTargetPointChange?.({ x: 0.5, y: 0.5 })}
              >
                Use image centre
              </button>
            </div>
          ) : null}

          {targetSelectionActive && targetPoint ? (
            <button
              className="target-crosshair"
              data-testid="target-crosshair"
              type="button"
              aria-label="Selected target leaf"
              style={{ left: `${targetPoint.x * 100}%`, top: `${targetPoint.y * 100}%` }}
              onKeyDown={moveCrosshair}
            >
              <span aria-hidden="true" />
            </button>
          ) : null}

          <div className="image-actions">
            <label className="button secondary-button upload-button">
              <UploadIcon />
              <span>Choose image</span>
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                aria-label="Choose image"
                onChange={(event) => {
                  const file = event.currentTarget.files?.[0];
                  if (file) onSelectFile(file);
                  event.currentTarget.value = "";
                }}
              />
            </label>
            <button
              className="button primary-button"
              type="button"
              disabled={
                !hasImage ||
                isLoading ||
                (targetSelectionActive && !targetPoint)
              }
              onClick={onAnalyze}
            >
              <AnalyzeIcon again={analyzed} />
              {actionLabel}
            </button>
          </div>

        </section>
      </LiquidGlass>
    </div>
  );
}
