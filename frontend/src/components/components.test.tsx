import type { ReactNode } from "react";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  AdviceProvidersResponse,
  AdviceProviderStatus,
  ClassificationResult,
  FeatureState,
  ManagementAdvice,
  LeafSelectionRequired,
  QwenAnswer,
  QwenStatus,
} from "../api/types";
import { AssistantPanel } from "./AssistantPanel";
import { ClassifierPanel } from "./ClassifierPanel";
import { ImageWorkspace } from "./ImageWorkspace";
import { ProjectLogo } from "./ProjectLogo";
import { QwenPanel } from "./QwenPanel";
import { ProviderConfigSheet } from "./ProviderConfigSheet";

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
        class_name: "Apple___Black_rot",
        probability: 0.34,
      },
      {
        class_index: 1,
        class_name: "Grape___Black_rot",
        probability: 0.21,
      },
    ],
    hierarchy: {
      method: "crop_first_rejection_v2",
      selected_crop: "Apple",
      selected_class_name: "Apple___Black_rot",
      crops: [
        { plant: "Apple", probability: 0.5 },
        { plant: "Grape", probability: 0.36 },
        { plant: "Tomato", probability: 0.14 },
      ],
      conditions: [
        {
          class_index: 0,
          class_name: "Apple___Black_rot",
          plant: "Apple",
          condition: "Black rot",
          joint_probability: 0.34,
          conditional_probability: 0.68,
        },
        {
          class_index: 2,
          class_name: "Apple___healthy",
          plant: "Apple",
          condition: "healthy",
          joint_probability: 0.16,
          conditional_probability: 0.32,
        },
      ],
      crop_confident: true,
      crop_margin: 0.14,
      confidence_threshold: 0.6,
      margin_threshold: 0.1,
      decision_reason: "Crop gate accepted.",
    },
    knowledge: {
      class_name: "Apple___Black_rot",
      plant: "Apple",
      condition: "Black rot",
      is_healthy: false,
      symptoms: "Illustrative symptoms.",
      educational_note: "Educational summary only.",
    },
    lesion_analysis: null,
    model_name: "resnet50",
    checkpoint_path: "outputs/checkpoint.pt",
    checkpoint_id: "checkpoint-id",
    image_size: 224,
    input_size: [1024, 768],
    disease_input_method: "original_image_v1",
    disease_input_size: [1024, 768],
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
      target_class_name: "Apple___Black_rot",
      heatmap_data_url: "data:image/png;base64,heatmap",
      overlay_data_url: "data:image/png;base64,overlay",
    },
  };
}

function qwenAnswer(overrides: Partial<QwenAnswer> = {}): QwenAnswer {
  return {
    raw_answer: "The image shows elongated lesions.",
    observations: ["The image shows elongated lesions."],
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

function leafSelectionRequired(): LeafSelectionRequired {
  return {
    code: "leaf_selection_required",
    message: "Select one target leaf before analysis.",
    leaf_isolation: {
      method: "opencv_target_leaf_v2",
      selection_mode: "automatic",
      target_point: null,
      purity: {
        accepted: false,
        coverage_percent: 31.2,
        border_touch_ratio: 0,
        fragment_count: 2,
        click_contained: null,
        probable_foreground_retention: null,
        principal_axis_aspect_ratio: 1.7,
        axis_band_retention: null,
        coverage_range: [3, 85],
        max_border_touch_ratio: 0.18,
        min_probable_foreground_retention: 0.6,
        min_axis_band_retention: 0.8,
        reason: "Select one target leaf before analysis.",
      },
      accepted: false,
      reason: "Select one target leaf before analysis.",
      image_size: [400, 200],
      bounding_box: [20, 30, 120, 150],
      shape: null,
      cutout_data_url: null,
    },
  };
}

describe("ProjectLogo", () => {
  it("renders the fused project mark without the source frame", () => {
    render(<ProjectLogo labelled />);
    const logo = screen.getByRole("img", { name: "PlantDiseaseAI" });
    expect(logo).toHaveAttribute("viewBox", "0 0 480 480");
    expect(
      logo.querySelector('[data-logo-layer="leaf"]'),
    ).toBeInTheDocument();
    expect(
      logo.querySelector('[data-logo-layer="desmos-gesture"]'),
    ).toBeInTheDocument();
    expect(logo.querySelector("rect")).not.toBeInTheDocument();
    expect(
      logo.querySelector('[data-source-path="expr-003"]'),
    ).not.toBeInTheDocument();
    expect(
      logo.querySelector('[data-source-path="expr-019"]'),
    ).toBeInTheDocument();
    expect(
      logo.querySelector('[data-source-path="expr-054"]'),
    ).toBeInTheDocument();
  });
});

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

describe("AssistantPanel", () => {
  it("keeps one glass stage while manually switching to a configured provider", async () => {
    const user = userEvent.setup();
    const onAskAdvice = vi.fn();
    const providers: FeatureState<AdviceProvidersResponse> = {
      status: "success",
      data: {
        providers: [
          {
            provider: "openai",
            display_name: "OpenAI",
            configured: true,
            model_id: "gpt-test",
            detail: "Ready",
          },
          {
            provider: "anthropic",
            display_name: "Claude",
            configured: true,
            model_id: "claude-test",
            detail: "Ready",
          },
          {
            provider: "gemini",
            display_name: "Gemini",
            configured: false,
            model_id: "gemini-test",
            detail: "Set GEMINI_API_KEY on the API server.",
          },
        ],
      },
      error: null,
    };
    render(
      <AssistantPanel
        guidanceEnabled
        qwenEnabled
        qwenRuntime={readyQwenRuntime()}
        qwenState={idle<QwenAnswer>()}
        providers={providers}
        adviceState={idle<ManagementAdvice>()}
        onAskQwen={vi.fn()}
        onRetryQwenRuntime={vi.fn()}
        onAskAdvice={onAskAdvice}
        onConfigureProvider={vi.fn()}
        onClearProvider={vi.fn()}
      />,
    );

    expect(screen.getByTestId("assistant-glass")).toBeVisible();
    expect(screen.getByRole("tab", { name: /management guidance/i })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("radio", { name: /gemini/i })).toBeDisabled();
    await user.click(screen.getByRole("radio", { name: /claude/i }));
    await user.click(screen.getByRole("button", { name: /ask for guidance/i }));

    expect(onAskAdvice).toHaveBeenCalledWith(
      "anthropic",
      "What management steps should I consider while the diagnosis remains uncertain?",
    );
    expect(screen.getAllByTestId("liquid-glass")).toHaveLength(1);
  });
});

describe("ImageWorkspace", () => {
  it("maps a target click to source coordinates and keeps a fixed keyboard crosshair", async () => {
    const user = userEvent.setup();
    const onTargetPointChange = vi.fn();
    const common = {
      previewUrl: "blob:wide-leaf",
      selectedFileName: "wide-leaf.jpeg",
      hasImage: true,
      classificationStatus: "idle" as const,
      targetSelectionActive: true,
      leafSelection: leafSelectionRequired(),
      onSelectFile: vi.fn(),
      onAnalyze: vi.fn(),
      onTargetPointChange,
    };
    const { rerender } = render(
      <ImageWorkspace {...common} targetPoint={null} />,
    );
    const image = screen.getByRole("img");
    Object.defineProperties(image, {
      naturalWidth: { configurable: true, value: 400 },
      naturalHeight: { configurable: true, value: 200 },
    });
    vi.spyOn(image, "getBoundingClientRect").mockReturnValue({
      left: 0,
      top: 0,
      width: 200,
      height: 200,
      right: 200,
      bottom: 200,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });

    expect(screen.getByRole("button", { name: /select a leaf first/i })).toBeDisabled();
    fireEvent.pointerDown(image, { clientX: 0, clientY: 100 });
    expect(onTargetPointChange).toHaveBeenLastCalledWith({ x: 0.25, y: 0.5 });

    rerender(
      <ImageWorkspace {...common} targetPoint={{ x: 0.25, y: 0.5 }} />,
    );
    const crosshair = screen.getByTestId("target-crosshair");
    expect(crosshair).toHaveStyle({ left: "25%", top: "50%" });
    fireEvent.pointerMove(image, { clientX: 160, clientY: 30 });
    expect(onTargetPointChange).toHaveBeenCalledTimes(1);
    fireEvent.keyDown(crosshair, { key: "ArrowRight" });
    expect(onTargetPointChange).toHaveBeenLastCalledWith({ x: 0.26, y: 0.5 });
    await user.click(screen.getByRole("button", { name: /use image centre/i }));
    expect(onTargetPointChange).toHaveBeenLastCalledWith({ x: 0.5, y: 0.5 });
  });

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
  it("renders Corn abiotic evidence and labels disease candidates counterfactual", async () => {
    const user = userEvent.setup();
    const onSelectAnotherLeaf = vi.fn();
    const result = classificationResult();
    result.hierarchy.selected_crop = "Corn (maize)";
    result.hierarchy.selected_class_name = null;
    result.hierarchy.disease_confident = false;
    result.hierarchy.disease_decision_reason = "Abiotic evidence withheld disease.";
    result.hierarchy.conditions = result.hierarchy.conditions.map((condition) => ({
      ...condition,
      plant: "Corn (maize)",
    }));
    result.knowledge = null;
    result.gradcam = null;
    result.abiotic_evidence = {
      method: "opencv_corn_midrib_stress_v1",
      status: "suspected_abiotic_nutrient_stress",
      suspected: true,
      abnormal_coverage_percent: 18,
      central_axis_share: 0.72,
      longitudinal_continuity: 0.81,
      bilateral_similarity: 0.68,
      off_axis_lesion_coverage_percent: 1.2,
      abnormal_coverage_threshold: 8,
      central_axis_share_threshold: 0.55,
      longitudinal_continuity_threshold: 0.6,
      bilateral_similarity_threshold: 0.5,
      off_axis_lesion_coverage_threshold: 5,
      reason: "Morphology evidence only; cannot identify a specific nutrient.",
      evidence_boundary: "Soil or tissue testing may be required.",
      overlay_data_url: "data:image/png;base64,abiotic",
    };

    render(
      <ClassifierPanel
        state={{ status: "success", data: result, error: null }}
        onSelectAnotherLeaf={onSelectAnotherLeaf}
      />,
    );

    expect(
      screen.getByRole("heading", { name: /suspected abiotic.*nutrient stress/i }),
    ).toBeVisible();
    expect(
      screen.getByText(/not a confirmed nitrogen deficiency/i),
    ).toBeVisible();
    expect(screen.getByText(/abnormal coverage/i)).toBeVisible();
    expect(screen.getByText(/central-axis share/i)).toBeVisible();
    expect(screen.getByText(/longitudinal continuity/i)).toBeVisible();
    expect(screen.getByText(/bilateral similarity/i)).toBeVisible();
    expect(screen.getByText(/off-axis lesion coverage/i)).toBeVisible();
    expect(
      screen.getByText(/closed-set infectious candidates.*counterfactual only/i),
    ).toBeVisible();
    expect(screen.queryByRole("img", { name: /grad-cam/i })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /select another leaf/i }));
    expect(onSelectAnotherLeaf).toHaveBeenCalledOnce();
  });

  it("shows a calm empty state before classification", () => {
    render(<ClassifierPanel state={idle<ClassificationResult>()} />);

    expect(screen.getByRole("heading", { name: /classifier/i })).toBeVisible();
    expect(screen.getByText(/ready to analyze/i)).toBeVisible();
    expect(screen.getByText(/top-5 predictions and grad-cam/i)).toBeVisible();
    expect(screen.getByTestId("classifier-state-body")).toBeVisible();
  });

  it("renders crop-first conditions, Grad-CAM assets, timings, and warnings", async () => {
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
    expect(screen.getByText(/step 3.*plant identity/i)).toBeVisible();
    expect(screen.getByText("Apple")).toBeVisible();
    expect(screen.getByText(/crop confidence/i)).toBeVisible();
    expect(screen.getByText(/fallback crop gate comes from the joint disease model/i)).toBeVisible();
    const conditions = screen.getByRole("list", {
      name: /conditions within apple/i,
    });
    expect(within(conditions).getAllByText(/black rot/i)).toHaveLength(1);
    expect(within(conditions).queryByText(/grape/i)).not.toBeInTheDocument();
    expect(screen.getByText("68.0%")).toBeVisible();
    expect(screen.getByRole("progressbar", { name: /black rot/i }))
      .toHaveAttribute("aria-valuenow", "68");
    expect(screen.getByTestId("classifier-state-body")).toBeVisible();
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

  it("discloses when disease inference uses the isolated leaf", () => {
    const result = classificationResult();
    result.disease_input_method =
      "opencv_isolated_leaf_neutral_background_v1";
    result.disease_input_size = [640, 480];

    render(
      <ClassifierPanel
        state={{ status: "success", data: result, error: null }}
      />,
    );

    expect(
      screen.getByText(/background-suppressed disease input/i),
    ).toBeVisible();
    expect(
      screen.getByText(/not the original scene/i),
    ).toBeVisible();
  });

  it("labels lesion-focused reranking as uncalibrated candidate evidence", () => {
    const result = classificationResult();
    result.disease_input_method = "opencv_isolated_leaf_plus_lesion_rois_v2";
    result.lesion_focus = {
      method: "opencv_healthy_veto_roi_ensemble_v1",
      applied: true,
      selected_crop: "Grape",
      reason: "Visible lesions contradict healthy.",
      lesion_coverage_percent: 12.42,
      healthy_coverage_threshold: 1.2959,
      lesion_count: 25,
      roi_count: 2,
      full_healthy_probability: 0.616,
      focused_predictions: [],
      evidence_boundary: "Candidate evidence only.",
    };

    render(
      <ClassifierPanel
        state={{ status: "success", data: result, error: null }}
      />,
    );

    expect(
      screen.getByText(/healthy candidate contradicted by visible lesions/i),
    ).toBeVisible();
    expect(screen.getByText(/12\.42% lesion coverage/i)).toBeVisible();
    expect(screen.getByText(/not calibrated field probabilities/i)).toBeVisible();
  });

  it("owns classifier progress and error announcements", () => {
    const { rerender } = render(
      <ClassifierPanel
        state={{ status: "loading", data: null, error: null }}
      />,
    );
    expect(screen.getByTestId("classifier-state-body")).toBeVisible();
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
    expect(screen.getByTestId("classifier-state-body")).toBeVisible();
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

    expect(screen.getByRole("heading", { name: /visual evidence/i })).toBeVisible();
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

    const question = screen.getByRole("textbox", { name: /visual evidence prompt/i });
    expect(question).toHaveValue(
      "What spots, colors, shapes, margins, textures, and distributions are visible?",
    );
    expect(question).toHaveAttribute("readonly");
    await user.click(screen.getByRole("button", { name: /ask qwen/i }));
    expect(onAsk).toHaveBeenCalledWith(
      "What spots, colors, shapes, margins, textures, and distributions are visible?",
    );
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
    expect(screen.getByRole("status")).toHaveTextContent(/inspecting visible evidence/i);
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
    expect(screen.getAllByText(/elongated lesions/i)[0]).toBeVisible();
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

  it("clears a temporary provider key after a successful save", async () => {
    const user = userEvent.setup();
    const onConfigure = vi.fn().mockResolvedValue(undefined);
    const providers: AdviceProviderStatus[] = [{
      provider: "openai",
      display_name: "OpenAI",
      configured: false,
      model_id: "gpt-test",
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

    expect(onConfigure).toHaveBeenCalledWith("openai", "sk-transient", "gpt-test");
    expect(input).toHaveValue("");
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
      screen.queryByRole("textbox", { name: /visual evidence prompt/i }),
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
