import type { ReactNode } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  ClassificationResult,
  FeatureState,
  QwenAnswer,
  QwenStatus,
} from "../api/types";
import { ClassifierPanel } from "./ClassifierPanel";
import { ImageWorkspace } from "./ImageWorkspace";
import { QwenPanel } from "./QwenPanel";

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

afterEach(cleanup);

const idle = <T,>(): FeatureState<T> => ({
  status: "idle",
  data: null,
  error: null,
});

const readyQwenRuntime = (): FeatureState<QwenStatus> => ({
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
});

function classificationResult(): ClassificationResult {
  return {
    predictions: [
      {
        class_index: 0,
        class_name: "Corn___Northern_Leaf_Blight",
        probability: 0.72,
      },
      {
        class_index: 1,
        class_name: "Corn___Common_Rust",
        probability: 0.18,
      },
    ],
    knowledge: {
      class_name: "Corn___Northern_Leaf_Blight",
      plant: "Corn",
      condition: "Northern Leaf Blight",
      is_healthy: false,
      symptoms: "Illustrative symptoms.",
      educational_note: "Educational summary only.",
    },
    model_name: "resnet50",
    checkpoint_path: "outputs/checkpoint.pt",
    checkpoint_id: "checkpoint-id",
    image_size: 224,
    input_size: [1024, 768],
    target_layer_name: "layer4.2",
    timings: {
      preprocess_ms: 1.2,
      prediction_ms: 4.4,
      gradcam_ms: 8.1,
      total_ms: 13.7,
    },
    warnings: [
      "Out-of-domain field photo.",
      "Do not generalize to field conditions.",
    ],
    gradcam: {
      target_class_index: 0,
      target_class_name: "Corn___Northern_Leaf_Blight",
      heatmap_data_url: "data:image/png;base64,heatmap",
      overlay_data_url: "data:image/png;base64,overlay",
    },
  };
}

function qwenAnswer(overrides: Partial<QwenAnswer> = {}): QwenAnswer {
  return {
    raw_answer: "The image shows elongated lesions.",
    message: "The image shows elongated lesions.",
    action: "educational_summary",
    refused: false,
    reasons: [],
    sources: ["classifier:Corn___Northern_Leaf_Blight"],
    model_id: "mlx-community/Qwen3-VL-4B-Instruct-4bit",
    scope: "exploratory_smoke",
    evidence_boundary: "Fixed smoke evidence only.",
    ...overrides,
  };
}

describe("focused Liquid Glass surfaces", () => {
  it("renders the real LiquidGlass boundary in all three production surfaces", () => {
    render(
      <>
        <ImageWorkspace
          previewUrl="blob:field-example"
          selectedFileName="field_corn_leaf.jpeg"
          hasImage
          classificationStatus="idle"
          onSelectFile={vi.fn()}
          onAnalyze={vi.fn()}
        />
        <ClassifierPanel state={idle<ClassificationResult>()} />
        <QwenPanel
          enabled={false}
          runtime={readyQwenRuntime()}
          state={idle<QwenAnswer>()}
          onAsk={vi.fn()}
          onRetryRuntime={vi.fn()}
        />
      </>,
    );

    expect(screen.getAllByTestId("liquid-glass")).toHaveLength(3);
    expect(screen.getByTestId("image-workspace-glass")).toContainElement(
      screen.getAllByTestId("liquid-glass")[0],
    );
    expect(screen.getByTestId("classifier-glass")).toContainElement(
      screen.getAllByTestId("liquid-glass")[1],
    );
    expect(screen.getByTestId("qwen-glass")).toContainElement(
      screen.getAllByTestId("liquid-glass")[2],
    );
  });
});

describe("ImageWorkspace", () => {
  it("labels the field example and binds upload and analysis actions", async () => {
    const user = userEvent.setup();
    const onSelectFile = vi.fn();
    const onAnalyze = vi.fn();
    render(
      <ImageWorkspace
        previewUrl="blob:field-example"
        selectedFileName="field_corn_leaf.jpeg"
        hasImage
        classificationStatus="idle"
        onSelectFile={onSelectFile}
        onAnalyze={onAnalyze}
      />,
    );

    expect(screen.getByText(/user-supplied field corn leaf/i)).toBeVisible();
    expect(screen.getByText(/no verified ground truth/i)).toBeVisible();
    expect(screen.getByRole("img", { name: /field corn leaf/i })).toHaveAttribute(
      "src",
      "blob:field-example",
    );
    const analyze = screen.getByRole("button", { name: /analyze leaf/i });
    expect(analyze).toBeEnabled();
    await user.click(analyze);
    expect(onAnalyze).toHaveBeenCalledOnce();

    const file = new File(["leaf"], "leaf.png", { type: "image/png" });
    await user.upload(screen.getByLabelText(/choose image/i), file);
    expect(onSelectFile).toHaveBeenCalledWith(file);
  });

  it("accepts an image dropped onto the workspace", () => {
    const onSelectFile = vi.fn();
    render(
      <ImageWorkspace
        previewUrl="blob:field-example"
        selectedFileName="field_corn_leaf.jpeg"
        hasImage
        classificationStatus="idle"
        onSelectFile={onSelectFile}
        onAnalyze={vi.fn()}
      />,
    );
    const file = new File(["leaf"], "replacement.webp", { type: "image/webp" });

    fireEvent.drop(screen.getByTestId("image-drop-zone"), {
      dataTransfer: { files: [file] },
    });

    expect(onSelectFile).toHaveBeenCalledWith(file);
  });

  it("leaves classifier loading and error announcements to ClassifierPanel", () => {
    const { rerender } = render(
      <>
        <ImageWorkspace
          previewUrl="blob:field-example"
          selectedFileName="field_corn_leaf.jpeg"
          hasImage
          classificationStatus="loading"
          onSelectFile={vi.fn()}
          onAnalyze={vi.fn()}
        />
        <ClassifierPanel
          state={{ status: "loading", data: null, error: null }}
        />
      </>,
    );

    expect(screen.getAllByRole("status")).toHaveLength(1);
    expect(screen.getByRole("status")).toHaveTextContent(/analyzing leaf/i);
    expect(screen.getByRole("button", { name: /analyzing leaf/i })).toBeDisabled();
    rerender(
      <>
        <ImageWorkspace
          previewUrl="blob:field-example"
          selectedFileName="field_corn_leaf.jpeg"
          hasImage
          classificationStatus="error"
          onSelectFile={vi.fn()}
          onAnalyze={vi.fn()}
        />
        <ClassifierPanel
          state={{
            status: "error",
            data: null,
            error: "Classifier unavailable",
          }}
        />
      </>,
    );
    expect(screen.getAllByRole("alert")).toHaveLength(1);
    expect(screen.getByRole("alert")).toHaveTextContent(
      /classifier unavailable/i,
    );
    expect(screen.getByRole("img", { name: /field corn leaf/i })).toBeVisible();
  });

  it("keeps reset state within the accepted copy boundary", () => {
    render(
      <ImageWorkspace
        previewUrl={null}
        selectedFileName={null}
        hasImage={false}
        classificationStatus="idle"
        onSelectFile={vi.fn()}
        onAnalyze={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: /analyze leaf/i })).toBeDisabled();
    expect(
      screen.queryByRole("heading", { name: /field corn leaf/i }),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.queryByText(/choose an image to begin/i)).not.toBeInTheDocument();
  });

  it("uses the uploaded filename instead of corn provenance for custom files", () => {
    render(
      <ImageWorkspace
        previewUrl="blob:custom"
        selectedFileName="backyard-bean.png"
        hasImage
        classificationStatus="idle"
        onSelectFile={vi.fn()}
        onAnalyze={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "backyard-bean.png" }),
    ).toBeVisible();
    expect(screen.getByRole("img")).toHaveAccessibleName(
      /selected upload: backyard-bean\.png/i,
    );
    expect(screen.queryByText(/field corn leaf/i)).not.toBeInTheDocument();
    expect(screen.getByText(/no verified ground truth/i)).toBeVisible();
  });
});

describe("ClassifierPanel", () => {
  it("shows a calm empty state before classification", () => {
    render(<ClassifierPanel state={idle<ClassificationResult>()} />);

    expect(screen.getByRole("heading", { name: /classifier/i })).toBeVisible();
    expect(screen.getByText(/ready to analyze/i)).toBeVisible();
    expect(screen.getByText(/top-5 predictions and grad-cam/i)).toBeVisible();
  });

  it("renders real predictions, Grad-CAM assets, timings, and warnings", async () => {
    const user = userEvent.setup();
    render(
      <ClassifierPanel
        state={{
          status: "success",
          data: classificationResult(),
          error: null,
        }}
      />,
    );

    expect(screen.getByText(/model prediction.*not ground truth/i)).toBeVisible();
    expect(screen.getAllByText(/northern leaf blight/i)).toHaveLength(2);
    expect(screen.getByText("72.0%")).toBeVisible();
    expect(screen.getByRole("progressbar", { name: /northern leaf blight/i }))
      .toHaveAttribute("aria-valuenow", "72");
    expect(screen.getByRole("img", { name: /grad-cam heatmap/i })).toHaveAttribute(
      "src",
      "data:image/png;base64,heatmap",
    );
    expect(screen.getByText(/13\.7 ms total/i)).toBeVisible();
    expect(screen.getByText(/out-of-domain field photo/i)).toBeVisible();
    const warningList = screen.getByText(/out-of-domain field photo/i).closest(
      ".warning-list",
    );
    const predictionList = screen.getByRole("list");
    expect(
      warningList?.compareDocumentPosition(predictionList) ?? 0,
    ).toBe(Node.DOCUMENT_POSITION_FOLLOWING);

    await user.click(screen.getByRole("button", { name: /show overlay/i }));
    expect(screen.getByRole("img", { name: /grad-cam overlay/i })).toHaveAttribute(
      "src",
      "data:image/png;base64,overlay",
    );
  });

  it("owns classifier progress and error announcements", () => {
    const { rerender } = render(
      <ClassifierPanel
        state={{ status: "loading", data: null, error: null }}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent(/analyzing leaf/i);

    rerender(
      <ClassifierPanel
        state={{
          status: "error",
          data: null,
          error: "Checkpoint unavailable",
        }}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      /checkpoint unavailable/i,
    );
  });
});

describe("QwenPanel", () => {
  it("keeps the bounded composer disabled before classification", () => {
    render(
      <QwenPanel
        enabled={false}
        runtime={readyQwenRuntime()}
        state={idle<QwenAnswer>()}
        onAsk={vi.fn()}
        onRetryRuntime={vi.fn()}
      />,
    );

    expect(screen.getByRole("heading", { name: /ask qwen/i })).toBeVisible();
    expect(screen.getByText(/optional local qwen3-vl/i)).toBeVisible();
    expect(screen.getByText(/available after classification/i)).toBeVisible();
    expect(
      screen.queryByRole("textbox", { name: /question for qwen/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ask qwen/i })).toBeDisabled();
  });

  it("submits the fixed bounded question after classification", async () => {
    const user = userEvent.setup();
    const onAsk = vi.fn();
    render(
      <QwenPanel
        enabled
        runtime={readyQwenRuntime()}
        state={idle<QwenAnswer>()}
        onAsk={onAsk}
        onRetryRuntime={vi.fn()}
      />,
    );

    const question = screen.getByRole("textbox", { name: /question for qwen/i });
    expect(question).toHaveValue("What visual symptoms are visible?");
    await user.click(screen.getByRole("button", { name: /ask qwen/i }));
    expect(onAsk).toHaveBeenCalledWith("What visual symptoms are visible?");
  });

  it("announces loading, unavailable, answers, and refusals in its own panel", () => {
    const { rerender } = render(
      <QwenPanel
        enabled
        runtime={readyQwenRuntime()}
        state={{ status: "loading", data: null, error: null }}
        onAsk={vi.fn()}
        onRetryRuntime={vi.fn()}
      />,
    );
    expect(screen.getAllByRole("status")).toHaveLength(1);
    expect(screen.getByRole("status")).toHaveTextContent(/asking qwen/i);
    expect(screen.getByRole("status").closest("[aria-live]")).toBeNull();

    rerender(
      <QwenPanel
        enabled
        runtime={readyQwenRuntime()}
        state={{ status: "error", data: null, error: "Qwen unavailable" }}
        onAsk={vi.fn()}
        onRetryRuntime={vi.fn()}
      />,
    );
    expect(screen.getAllByRole("alert")).toHaveLength(1);
    expect(screen.getByRole("alert")).toHaveTextContent(/qwen unavailable/i);
    expect(screen.getByRole("alert").closest("[aria-live]")).toBeNull();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();

    rerender(
      <QwenPanel
        enabled
        runtime={readyQwenRuntime()}
        state={{ status: "success", data: qwenAnswer(), error: null }}
        onAsk={vi.fn()}
        onRetryRuntime={vi.fn()}
      />,
    );
    expect(screen.getAllByRole("status")).toHaveLength(1);
    expect(screen.getByRole("status").closest("[aria-live]")).toBeNull();
    expect(screen.getByText(/elongated lesions/i)).toBeVisible();
    expect(screen.getByText(/fixed smoke evidence only/i)).toBeVisible();

    rerender(
      <QwenPanel
        enabled
        runtime={readyQwenRuntime()}
        state={{
          status: "success",
          data: qwenAnswer({
            raw_answer: null,
            message: "I cannot provide treatment instructions.",
            refused: true,
            reasons: ["Treatment advice is outside the bounded demo."],
          }),
          error: null,
        }}
        onAsk={vi.fn()}
        onRetryRuntime={vi.fn()}
      />,
    );
    expect(screen.getAllByRole("status")).toHaveLength(1);
    expect(screen.getByRole("status").closest("[aria-live]")).toBeNull();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByText(/cannot provide treatment instructions/i)).toBeVisible();
    expect(screen.getByText(/outside the bounded demo/i)).toBeVisible();
  });

  it("shows the real local setup boundary and disables Qwen when weights are absent", () => {
    render(
      <QwenPanel
        enabled
        runtime={{
          status: "success",
          data: {
            supported_platform: true,
            dependency_available: true,
            weights_cached: false,
            ready: false,
            model_id: "mlx-community/Qwen3-VL-4B-Instruct-4bit",
            detail: "Model weights are not in the local cache. The API never downloads them automatically.",
          },
          error: null,
        }}
        state={idle<QwenAnswer>()}
        onAsk={vi.fn()}
        onRetryRuntime={vi.fn()}
      />,
    );

    expect(screen.getByText(/model weights are not in the local cache/i)).toBeVisible();
    expect(screen.getByText(/hf download.*qwen3-vl-4b-instruct-4bit/i)).toBeVisible();
    expect(screen.getByText(/no automatic download/i)).toBeVisible();
    expect(
      screen.queryByRole("button", { name: /ask qwen/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("textbox", { name: /question for qwen/i }),
    ).not.toBeInTheDocument();
  });

  it("does not offer an unusable download path off Apple Silicon and can retry", async () => {
    const user = userEvent.setup();
    const onRetryRuntime = vi.fn();
    render(
      <QwenPanel
        enabled={false}
        runtime={{
          status: "success",
          data: {
            supported_platform: false,
            dependency_available: false,
            weights_cached: false,
            ready: false,
            model_id: "mlx-community/Qwen3-VL-4B-Instruct-4bit",
            detail: "Unsupported platform.",
          },
          error: null,
        }}
        state={idle<QwenAnswer>()}
        onAsk={vi.fn()}
        onRetryRuntime={onRetryRuntime}
      />,
    );

    expect(screen.getByText(/requires apple silicon macos/i)).toBeVisible();
    expect(screen.queryByText(/hf download/i)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /check again/i }));
    expect(onRetryRuntime).toHaveBeenCalledOnce();
  });

  it("offers dependency setup without a model download off-ramp", () => {
    render(
      <QwenPanel
        enabled={false}
        runtime={{
          status: "success",
          data: {
            supported_platform: true,
            dependency_available: false,
            weights_cached: false,
            ready: false,
            model_id: "mlx-community/Qwen3-VL-4B-Instruct-4bit",
            detail: "MLX-VLM dependency is unavailable.",
          },
          error: null,
        }}
        state={idle<QwenAnswer>()}
        onAsk={vi.fn()}
        onRetryRuntime={vi.fn()}
      />,
    );

    expect(screen.getByText(/uv sync --group vlm/i)).toBeVisible();
    expect(screen.queryByText(/hf download/i)).not.toBeInTheDocument();
  });

  it("retries after a runtime status request fails", async () => {
    const user = userEvent.setup();
    const onRetryRuntime = vi.fn();
    render(
      <QwenPanel
        enabled={false}
        runtime={{ status: "error", data: null, error: "Status unavailable" }}
        state={idle<QwenAnswer>()}
        onAsk={vi.fn()}
        onRetryRuntime={onRetryRuntime}
      />,
    );

    expect(screen.getByText(/runtime status unavailable/i)).toBeVisible();
    await user.click(screen.getByRole("button", { name: /check again/i }));
    expect(onRetryRuntime).toHaveBeenCalledOnce();
  });
});
