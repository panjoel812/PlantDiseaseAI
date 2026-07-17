import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  askQwen,
  classifyImage,
  fetchExampleImage,
  fetchHealth,
  fetchQwenStatus,
} from "./client";
import type { ClassificationResult } from "./types";

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
      method: "single_model_taxonomy_aggregation_v1",
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
    },
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

  it("sends the selected image and exact Grad-CAM controls", async () => {
    fetchMock.mockResolvedValue(jsonResponse(classification()));

    await classifyImage(file, {
      topK: 5,
      includeGradcam: true,
      device: "mps",
      targetLayer: "layer4.2",
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
  });

  it("omits optional classifier controls instead of sending undefined text", async () => {
    fetchMock.mockResolvedValue(jsonResponse(classification()));

    await classifyImage(file, { topK: 3, includeGradcam: false });

    const body = fetchMock.mock.calls[0][1]?.body as FormData;
    expect(body.get("include_gradcam")).toBe("false");
    expect(body.has("device")).toBe(false);
    expect(body.has("target_layer")).toBe(false);
  });

  it("sends Qwen classifier context with repeated warning fields", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({
        raw_answer: "diseased",
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
