import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  LeafSelectionRequiredError,
  askQwen,
  askForAdvice,
  classifyImage,
  clearAdviceProvider,
  configureAdviceProvider,
  fetchAdviceProviders,
  fetchExampleImage,
  fetchHealth,
  fetchQwenStatus,
} from "./client";
import type { ClassificationResult, QwenAnswer } from "./types";

const file = new File(["leaf"], "leaf.jpeg", { type: "image/jpeg" });

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function classification(): ClassificationResult {
  return {
    predictions: [
      {
        class_index: 7,
        class_name: "Corn___Northern_Leaf_Blight",
        probability: 0.91,
      },
    ],
    hierarchy: {
      method: "crop_first_rejection_v2",
      selected_crop: "Corn",
      selected_class_name: "Corn___Northern_Leaf_Blight",
      crops: [
        { plant: "Corn", probability: 0.96 },
        { plant: "Tomato", probability: 0.04 },
      ],
      conditions: [
        {
          class_index: 7,
          class_name: "Corn___Northern_Leaf_Blight",
          plant: "Corn",
          condition: "Northern Leaf Blight",
          joint_probability: 0.91,
          conditional_probability: 0.9479166667,
        },
      ],
      crop_confident: true,
      crop_margin: 0.92,
      confidence_threshold: 0.6,
      margin_threshold: 0.1,
      decision_reason: "Crop gate accepted.",
    },
    knowledge: {
      class_name: "Corn___Northern_Leaf_Blight",
      plant: "Corn",
      condition: "Northern Leaf Blight",
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
      preprocess_ms: 1,
      prediction_ms: 2,
      gradcam_ms: 3,
      total_ms: 6,
    },
    warnings: ["Educational demo only.", "Field generalization is unknown."],
    gradcam: null,
  };
}

describe("API client", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  it("configures and clears a provider without browser storage", async () => {
    const storageSpy = vi.spyOn(Storage.prototype, "setItem");
    fetchMock
      .mockResolvedValueOnce(jsonResponse({
        provider: "openai",
        display_name: "OpenAI",
        configured: true,
        model_id: "gpt-runtime",
        detail: "Ready",
      }))
      .mockResolvedValueOnce(jsonResponse({
        provider: "openai",
        display_name: "OpenAI",
        configured: false,
        model_id: "gpt-test",
        detail: "Not configured",
      }));

    await configureAdviceProvider("openai", "sk-transient", "gpt-runtime");
    await clearAdviceProvider("openai");

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "/api/advice/providers/openai/configure",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ api_key: "sk-transient", model_id: "gpt-runtime" }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/advice/providers/openai/configure",
      expect.objectContaining({ method: "DELETE" }),
    );
    expect(storageSpy).not.toHaveBeenCalled();
  });

  it("sends the selected image and exact Grad-CAM controls", async () => {
    fetchMock.mockResolvedValue(jsonResponse(classification()));

    await classifyImage(file, {
      topK: 5,
      includeGradcam: true,
      device: "mps",
      targetLayer: "layer4.2",
      targetPoint: { x: 0.25, y: 0.75 },
    });

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0];
    const body = init?.body as FormData;
    expect(url).toBe("/api/classify");
    expect(init?.method).toBe("POST");
    expect(body.get("image")).toBe(file);
    expect(body.get("top_k")).toBe("5");
    expect(body.get("include_gradcam")).toBe("true");
    expect(body.get("device")).toBe("mps");
    expect(body.get("target_layer")).toBe("layer4.2");
    expect(body.get("target_x")).toBe("0.25");
    expect(body.get("target_y")).toBe("0.75");
  });

  it("omits optional classifier controls instead of sending undefined text", async () => {
    fetchMock.mockResolvedValue(jsonResponse(classification()));

    await classifyImage(file, { topK: 3, includeGradcam: false });

    const body = fetchMock.mock.calls[0][1]?.body as FormData;
    expect(body.get("include_gradcam")).toBe("false");
    expect(body.has("device")).toBe(false);
    expect(body.has("target_layer")).toBe(false);
    expect(body.has("target_x")).toBe(false);
    expect(body.has("target_y")).toBe(false);
  });

  it("preserves structured leaf-selection evidence from a 409 response", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        {
          detail: {
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
              image_size: [320, 220],
              bounding_box: [20, 30, 120, 150],
              shape: null,
              cutout_data_url: null,
            },
          },
        },
        409,
      ),
    );

    const request = classifyImage(file, { topK: 5, includeGradcam: true });

    await expect(request).rejects.toBeInstanceOf(LeafSelectionRequiredError);
    await expect(request).rejects.toMatchObject({
      detail: {
        code: "leaf_selection_required",
        leaf_isolation: {
          selection_mode: "automatic",
          purity: {
            reason: "Select one target leaf before analysis.",
          },
        },
      },
    });
  });

  it("sends Qwen classifier context with repeated warning fields", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({
        raw_answer: "diseased",
        observations: ["Visible lesions."],
        message: "Educational summary only.",
        action: "educational_summary",
        refused: false,
        reasons: [],
        sources: ["classifier:Corn___Northern_Leaf_Blight"],
        model_id: "mlx-community/Qwen3-VL-4B-Instruct-4bit",
        scope: "exploratory_smoke",
        evidence_boundary: "Fixed smoke evidence only.",
      }),
    );

    const hierarchicalClassification = classification();
    hierarchicalClassification.hierarchy.selected_class_name =
      "Corn___Common_Rust";
    hierarchicalClassification.hierarchy.conditions[0] = {
      class_index: 8,
      class_name: "Corn___Common_Rust",
      plant: "Corn",
      condition: "Common Rust",
      joint_probability: 0.63,
      conditional_probability: 0.65625,
    };

    await askQwen(
      file,
      "What symptoms are visible?",
      hierarchicalClassification,
    );

    const [url, init] = fetchMock.mock.calls[0];
    const body = init?.body as FormData;
    expect(url).toBe("/api/qwen/ask");
    expect(init?.method).toBe("POST");
    expect(body.get("image")).toBe(file);
    expect(body.get("question")).toBe("What symptoms are visible?");
    expect(body.get("classifier_top_class_name")).toBe(
      "Corn___Common_Rust",
    );
    expect(body.get("classifier_confidence")).toBe("0.63");
    expect(body.getAll("classifier_warnings")).toEqual([
      "Educational demo only.",
      "Field generalization is unknown.",
    ]);
  });

  it("omits partial classifier context when no prediction is available", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ refused: true }));
    const current = classification();
    const withoutPrediction = {
      ...current,
      predictions: [],
      hierarchy: { ...current.hierarchy, conditions: [] },
    };

    await askQwen(file, "What can you safely say?", withoutPrediction);

    const body = fetchMock.mock.calls[0][1]?.body as FormData;
    expect(body.has("classifier_top_class_name")).toBe(false);
    expect(body.has("classifier_confidence")).toBe(false);
    expect(body.has("classifier_warnings")).toBe(false);
  });

  it("carries FastAPI JSON detail and status in ApiError", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ detail: "classifier checkpoint is unavailable" }, 503),
    );

    const request = classifyImage(file, {
      topK: 5,
      includeGradcam: true,
    });

    await expect(request).rejects.toMatchObject({
      status: 503,
      detail: "classifier checkpoint is unavailable",
      message: "classifier checkpoint is unavailable",
    });
    await expect(request).rejects.toBeInstanceOf(ApiError);
  });

  it("preserves human-readable messages from FastAPI validation detail arrays", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        {
          detail: [
            {
              type: "missing",
              loc: ["body", "image"],
              msg: "Field required",
              input: null,
            },
            {
              type: "less_than_equal",
              loc: ["body", "top_k"],
              msg: "Input should be less than or equal to 10",
              input: 11,
            },
          ],
        },
        422,
      ),
    );

    await expect(fetchHealth()).rejects.toMatchObject({
      status: 422,
      detail:
        "body.image: Field required; body.top_k: Input should be less than or equal to 10",
    });
  });

  it("turns a non-JSON error response into ApiError instead of a parse failure", async () => {
    fetchMock.mockResolvedValue(
      new Response("backend offline", {
        status: 502,
        statusText: "Bad Gateway",
        headers: { "content-type": "text/plain" },
      }),
    );

    const request = fetchHealth();

    await expect(request).rejects.toMatchObject({
      status: 502,
      detail: "backend offline",
    });
    await expect(request).rejects.toBeInstanceOf(ApiError);
  });

  it("uses the health and Qwen status endpoints with the supplied abort signal", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ status: "degraded" }))
      .mockResolvedValueOnce(jsonResponse({ ready: false }));
    const controller = new AbortController();

    await fetchHealth(controller.signal);
    await fetchQwenStatus(controller.signal);

    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/health", {
      signal: controller.signal,
    });
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/qwen/status", {
      signal: controller.signal,
    });
  });

  it("loads the fixed JPEG example as a named File through an abortable request", async () => {
    fetchMock.mockResolvedValue(
      new Response(new Blob(["example"], { type: "image/jpeg" }), {
        status: 200,
        headers: { "content-type": "image/jpeg" },
      }),
    );
    const controller = new AbortController();

    const example = await fetchExampleImage(controller.signal);

    expect(fetchMock).toHaveBeenCalledWith("/api/example", {
      signal: controller.signal,
    });
    expect(example).toBeInstanceOf(File);
    expect(example.name).toBe("field_corn_leaf.jpeg");
    expect(example.type).toBe("image/jpeg");
  });

  it("loads non-secret cloud provider status with an abort signal", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({
        providers: [
          {
            provider: "openai",
            display_name: "OpenAI",
            configured: true,
            model_id: "gpt-test",
            detail: "Ready",
          },
        ],
      }),
    );
    const controller = new AbortController();

    await fetchAdviceProviders(controller.signal);

    expect(fetchMock).toHaveBeenCalledWith("/api/advice/providers", {
      signal: controller.signal,
    });
  });

  it("sends only the manually selected provider and structured evidence", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({
        provider: "anthropic",
        model_id: "claude-test",
        message: "Conditional guidance.",
        action: "educational_guidance",
        refused: false,
        reasons: [],
        sources: [],
        scope: "educational_management_guidance",
        evidence_boundary: "Educational only.",
      }),
    );
    const visualEvidence: QwenAnswer = {
      raw_answer: "Circular tan spots with dark margins are visible.",
      observations: ["Circular tan spots with dark margins are visible."],
      message: "Circular tan spots with dark margins are visible.",
      action: "visual_evidence",
      refused: false,
      reasons: [],
      sources: ["qwen:local"],
      model_id: "qwen-local",
      scope: "visual_evidence_only",
      evidence_boundary: "Visual evidence only.",
    };

    await askForAdvice(
      "anthropic",
      "What management steps should I consider?",
      classification(),
      visualEvidence,
    );

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/advice/ask");
    expect(init?.method).toBe("POST");
    expect(init?.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(String(init?.body))).toEqual({
      provider: "anthropic",
      question: "What management steps should I consider?",
      selected_crop: "Corn",
      crop_probability: 0.96,
      selected_condition: "Northern Leaf Blight",
      condition_probability: 0.91,
      warnings: ["Educational demo only.", "Field generalization is unknown."],
      visual_observation: "Circular tan spots with dark margins are visible.",
    });
  });

  it("forwards abort signals to classifier and Qwen POST requests", async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(classification()))
      .mockResolvedValueOnce(jsonResponse({ refused: true }));
    const classifierController = new AbortController();
    const qwenController = new AbortController();

    await classifyImage(
      file,
      { topK: 5, includeGradcam: true },
      classifierController.signal,
    );
    await askQwen(file, "Safe question", undefined, qwenController.signal);

    expect(fetchMock.mock.calls[0][1]?.signal).toBe(classifierController.signal);
    expect(fetchMock.mock.calls[1][1]?.signal).toBe(qwenController.signal);
  });
});
