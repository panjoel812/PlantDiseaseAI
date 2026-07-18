/// <reference types="node" />

import { readFileSync } from "node:fs";
import type { ReactNode } from "react";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import type { DemoState } from "./hooks/useDemo";
import { useDemo } from "./hooks/useDemo";

vi.mock("liquid-glass-react", () => ({
  default: ({
    children,
    className,
  }: {
    children: ReactNode;
    className?: string;
  }) => (
    <div className={className} data-testid="liquid-glass">
      {children}
    </div>
  ),
}));

vi.mock("./hooks/useDemo", () => ({ useDemo: vi.fn() }));

afterEach(cleanup);

const styles = readFileSync("src/styles.css", "utf8");

function demoState(): DemoState {
  return {
    classification: { status: "idle", data: null, error: null },
    qwen: { status: "idle", data: null, error: null },
    qwenRuntime: {
      status: "success",
      data: {
        supported_platform: true,
        dependency_available: true,
        weights_cached: true,
        ready: true,
        model_id: "mlx-community/Qwen3-VL-4B-Instruct-4bit",
        detail: "ready",
      },
      error: null,
    },
    adviceProviders: {
      status: "success",
      data: {
        providers: [
          {
            provider: "openai",
            display_name: "OpenAI",
            configured: false,
            model_id: "gpt-5.4-mini",
            detail: "Set OPENAI_API_KEY on the API server.",
          },
          {
            provider: "anthropic",
            display_name: "Claude",
            configured: false,
            model_id: "claude-sonnet-5",
            detail: "Set ANTHROPIC_API_KEY on the API server.",
          },
          {
            provider: "gemini",
            display_name: "Gemini",
            configured: false,
            model_id: "gemini-3.5-flash",
            detail: "Set GEMINI_API_KEY on the API server.",
          },
        ],
      },
      error: null,
    },
    advice: { status: "idle", data: null, error: null },
    plantIdentity: {
      status: "success",
      data: {
        provider: "plantnet",
        display_name: "Pl@ntNet",
        configured: false,
        scope: "Broad field species identity (100+ species)",
        detail: "Optional: add a Pl@ntNet API key for broader field identity beyond the local 114-class pilot.",
      },
      error: null,
    },
    selectedFile: new File(["example"], "field_corn_leaf.jpeg", {
      type: "image/jpeg",
    }),
    previewUrl: "blob:field-example",
    targetPoint: null,
    leafSelection: null,
    targetSelectionActive: false,
    selectFile: vi.fn(),
    setTargetPoint: vi.fn(),
    beginTargetSelection: vi.fn(),
    clearTargetPoint: vi.fn(),
    classify: vi.fn().mockResolvedValue(undefined),
    ask: vi.fn().mockResolvedValue(undefined),
    askAdvice: vi.fn().mockResolvedValue(undefined),
    configureProvider: vi.fn().mockResolvedValue(undefined),
    clearProvider: vi.fn().mockResolvedValue(undefined),
    configurePlantIdentity: vi.fn().mockResolvedValue(undefined),
    clearPlantIdentity: vi.fn().mockResolvedValue(undefined),
    refreshQwenRuntime: vi.fn().mockResolvedValue(undefined),
    reset: vi.fn(),
  };
}

describe("App", () => {
  let demo: DemoState;

  beforeEach(() => {
    demo = demoState();
    vi.mocked(useDemo).mockImplementation(() => demo);
  });

  it("composes the accepted default state and fixed research boundary", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: /evidence before diagnosis/i }),
    ).toBeVisible();
    expect(screen.getByText(/not a professional diagnosis/i)).toBeVisible();
    expect(screen.getByText(/user-supplied field corn leaf/i)).toBeVisible();
    expect(screen.getByText(/no verified ground truth/i)).toBeVisible();
    expect(screen.getByRole("button", { name: /analyze leaf/i })).toBeEnabled();
    expect(screen.getByRole("button", { name: /ask qwen/i })).toBeDisabled();
    expect(screen.getByText(/choice.*11\/15/i)).toBeVisible();
    expect(screen.getByText(/condition.*1\/5/i)).toBeVisible();
    expect(screen.getAllByTestId("liquid-glass")).toHaveLength(3);
    expect(screen.getByTestId("ambient-garden")).toHaveAttribute(
      "aria-hidden",
      "true",
    );
    const upload = screen.getByRole("region", { name: "Upload and analyze" });
    const results = screen.getByRole("region", { name: "Analysis results" });
    expect(upload.compareDocumentPosition(results)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
    expect(results).toHaveAttribute("tabindex", "-1");
    expect(
      results.querySelector('[data-testid="classifier-glass"]'),
    ).toBeInTheDocument();
    expect(
      results.querySelector('[data-testid="assistant-glass"]'),
    ).toBeInTheDocument();
  });

  it("binds reset, analyze, and Qwen actions to useDemo", async () => {
    const user = userEvent.setup();
    const { rerender } = render(<App />);

    await user.click(screen.getByRole("button", { name: /reset/i }));
    expect(demo.reset).toHaveBeenCalledOnce();
    await user.click(screen.getByRole("button", { name: /analyze leaf/i }));
    expect(demo.classify).toHaveBeenCalledWith({
      topK: 5,
      includeGradcam: true,
    });

    demo = {
      ...demo,
      classification: {
        status: "success",
        data: {
          predictions: [],
          hierarchy: {
            method: "crop_first_rejection_v2",
            selected_crop: "Corn",
            selected_class_name: "Corn___healthy",
            crops: [{ plant: "Corn", probability: 1 }],
            conditions: [
              {
                class_index: 0,
                class_name: "Corn___healthy",
                plant: "Corn",
                condition: "healthy",
                joint_probability: 1,
                conditional_probability: 1,
              },
            ],
            crop_confident: true,
            crop_margin: 1,
            confidence_threshold: 0.6,
            margin_threshold: 0.1,
            decision_reason: "Crop gate accepted.",
          },
          knowledge: {
            class_name: "",
            plant: "",
            condition: "",
            is_healthy: false,
            symptoms: "",
            educational_note: "",
          },
          lesion_analysis: null,
          model_name: "resnet50",
          checkpoint_path: "checkpoint.pt",
          checkpoint_id: "checkpoint-id",
          image_size: 224,
          input_size: [1024, 768],
          disease_input_method: "original_image_v1",
          disease_input_size: [1024, 768],
          target_layer_name: null,
          timings: {
            preprocess_ms: 1,
            prediction_ms: 2,
            gradcam_ms: 0,
            total_ms: 3,
          },
          warnings: [],
          gradcam: null,
        },
        error: null,
      },
    };
    rerender(<App />);
    await user.click(screen.getByRole("tab", { name: /visual evidence/i }));
    await user.click(screen.getByRole("button", { name: /ask qwen/i }));
    expect(demo.ask).toHaveBeenCalledWith(
      "What spots, colors, shapes, margins, textures, and distributions are visible?",
    );
  });

  it("binds image provenance to the selected file", () => {
    const { rerender } = render(<App />);

    expect(
      screen.getByRole("heading", { name: /user-supplied field corn leaf/i }),
    ).toBeVisible();

    demo = {
      ...demo,
      selectedFile: new File(["custom"], "garden-sample.webp", {
        type: "image/webp",
      }),
      previewUrl: "blob:custom",
    };
    rerender(<App />);
    expect(
      screen.getByRole("heading", { name: "garden-sample.webp" }),
    ).toBeVisible();
    expect(screen.getByRole("img")).toHaveAccessibleName(
      /selected upload: garden-sample\.webp/i,
    );

    demo = { ...demo, selectedFile: null, previewUrl: null };
    rerender(<App />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.queryByText(/field corn leaf/i)).not.toBeInTheDocument();
  });

  it("defines responsive and accessibility material fallbacks", () => {
    expect(styles).not.toMatch(/--page-graphite|#191a18/i);
    expect(styles).toMatch(/\.ambient-garden\s*\{[\s\S]*?pointer-events:\s*none/);
    expect(styles).toMatch(/\.ambient-shape/);
    expect(styles).toMatch(
      /@media \(prefers-reduced-motion: reduce\) \{[\s\S]*?animation-duration: 0\.01ms !important;[\s\S]*?transition-duration: 0\.01ms !important;/,
    );
    expect(styles).toMatch(/@media \(prefers-reduced-transparency: reduce\)/);
    expect(styles).toMatch(/@media \(prefers-contrast: more\)/);
    expect(styles).toMatch(/@media \(max-width: 760px\)/);
    expect(styles).not.toMatch(/display:\s*contents/);
    expect(styles).not.toMatch(/grid-row\s*:/);
    expect(styles).toMatch(
      /@media \(max-width: 760px\) \{[\s\S]*?\.results-grid \{[\s\S]*?grid-template-columns:\s*minmax\(0, 1fr\);/,
    );
    expect(styles).toMatch(/\.results-grid[\s\S]*?align-items:\s*start/);
    expect(styles).toMatch(
      /\.results-grid \.panel-state-body\s*\{[\s\S]*?overflow:\s*visible/,
    );
    expect(styles).toMatch(/min-height:\s*44px/);
    expect(styles).toMatch(/:focus-visible/);
    expect(styles).toMatch(
      /@media \(prefers-reduced-motion: reduce\) \{[\s\S]*?\.ambient-shape[\s\S]*?animation:\s*none !important;/,
    );
    expect(styles).toMatch(
      /\.side-panel\s*\{[^}]*background:\s*rgb\(255 255 255 \/ 68%\)/s,
    );
    expect(styles).toMatch(/\.side-panel\s*\{[^}]*backdrop-filter:\s*blur\(24px\)/s);
    expect(styles).toMatch(
      /\.glass-surface \.glass__warp\s*\{[^}]*filter:\s*none !important/s,
    );
  });

  it("uses distinct readable amber ink for small warning text", () => {
    expect(styles).toMatch(/--amber-ink:\s*#70400b;/);
    expect(styles).toMatch(
      /\.safety-title \{[\s\S]*?color:\s*var\(--amber-ink\);/,
    );
    expect(styles).toMatch(
      /\.safety-title svg \{[\s\S]*?color:\s*var\(--amber\);/,
    );
    expect(styles).toMatch(
      /\.warning-list \{[\s\S]*?color:\s*var\(--amber-ink\);/,
    );
  });
});
