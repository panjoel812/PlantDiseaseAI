import type {
  AdviceProviderId,
  AdviceProviderStatus,
  AdviceProvidersResponse,
  ClassificationResult,
  ClassifyOptions,
  DemoHealth,
  ManagementAdvice,
  QwenAnswer,
  QwenStatus,
} from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function validationDetail(value: unknown): string | undefined {
  if (typeof value === "string") return value;
  if (!Array.isArray(value)) return undefined;
  const messages: string[] = [];
  for (const item of value) {
    if (!isRecord(item) || typeof item.msg !== "string") continue;
    const location = Array.isArray(item.loc)
      ? item.loc
          .filter(
            (segment): segment is string | number =>
              typeof segment === "string" || typeof segment === "number",
          )
          .join(".")
      : "";
    messages.push(location ? `${location}: ${item.msg}` : item.msg);
  }
  return messages.length > 0 ? messages.join("; ") : undefined;
}

async function errorDetail(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("json")) {
    try {
      const payload: unknown = await response.json();
      if (isRecord(payload)) {
        const detail = validationDetail(payload.detail);
        if (detail) return detail;
      }
    } catch {
      return response.statusText || `Request failed with status ${response.status}`;
    }
  } else {
    const body = (await response.text()).trim();
    if (body) return body;
  }
  return response.statusText || `Request failed with status ${response.status}`;
}

async function ensureOk(response: Response): Promise<Response> {
  if (!response.ok) {
    throw new ApiError(response.status, await errorDetail(response));
  }
  return response;
}

async function requestJson<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<T> {
  const response = await ensureOk(await fetch(input, init));
  const payload: unknown = await response.json();
  return payload as T;
}

export async function classifyImage(
  file: File,
  options: ClassifyOptions,
  signal?: AbortSignal,
): Promise<ClassificationResult> {
  const body = new FormData();
  body.append("image", file);
  body.append("top_k", String(options.topK));
  body.append("include_gradcam", String(options.includeGradcam));
  if (options.device) body.append("device", options.device);
  if (options.targetLayer) body.append("target_layer", options.targetLayer);
  return requestJson<ClassificationResult>("/api/classify", {
    method: "POST",
    body,
    signal,
  });
}

export function fetchHealth(signal?: AbortSignal): Promise<DemoHealth> {
  return requestJson<DemoHealth>("/api/health", { signal });
}

export function fetchQwenStatus(signal?: AbortSignal): Promise<QwenStatus> {
  return requestJson<QwenStatus>("/api/qwen/status", { signal });
}

export function fetchAdviceProviders(
  signal?: AbortSignal,
): Promise<AdviceProvidersResponse> {
  return requestJson<AdviceProvidersResponse>("/api/advice/providers", { signal });
}

export function configureAdviceProvider(
  provider: AdviceProviderId,
  apiKey: string,
  modelId?: string,
  signal?: AbortSignal,
): Promise<AdviceProviderStatus> {
  return requestJson<AdviceProviderStatus>(
    `/api/advice/providers/${provider}/configure`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        api_key: apiKey,
        ...(modelId?.trim() ? { model_id: modelId.trim() } : {}),
      }),
      signal,
    },
  );
}

export function clearAdviceProvider(
  provider: AdviceProviderId,
  signal?: AbortSignal,
): Promise<AdviceProviderStatus> {
  return requestJson<AdviceProviderStatus>(
    `/api/advice/providers/${provider}/configure`,
    { method: "DELETE", signal },
  );
}

export async function fetchExampleImage(signal?: AbortSignal): Promise<File> {
  const response = await ensureOk(await fetch("/api/example", { signal }));
  const blob = await response.blob();
  return new File([blob], "field_corn_leaf.jpeg", {
    type: blob.type || "image/jpeg",
  });
}

export async function askQwen(
  file: File,
  question: string,
  classification?: ClassificationResult,
  signal?: AbortSignal,
): Promise<QwenAnswer> {
  const body = new FormData();
  body.append("image", file);
  body.append("question", question);
  const selectedCondition = classification?.hierarchy.crop_confident
    ? classification.hierarchy.conditions[0]
    : undefined;
  const className = selectedCondition?.class_name;
  const confidence = selectedCondition?.joint_probability;
  if (className !== undefined && confidence !== undefined) {
    body.append("classifier_top_class_name", className);
    body.append("classifier_confidence", String(confidence));
    for (const warning of classification?.warnings ?? []) {
      body.append("classifier_warnings", warning);
    }
  }
  const answer = await requestJson<QwenAnswer>("/api/qwen/ask", {
    method: "POST",
    body,
    signal,
  });
  return {
    ...answer,
    observations: Array.isArray(answer.observations)
      ? answer.observations.filter(
          (observation): observation is string =>
            typeof observation === "string" && observation.trim().length > 0,
        )
      : [],
  };
}

export function askForAdvice(
  provider: AdviceProviderId,
  question: string,
  classification: ClassificationResult,
  visualEvidence?: QwenAnswer,
  signal?: AbortSignal,
): Promise<ManagementAdvice> {
  const crop = classification.hierarchy.crops.find(
    (item) => item.plant === classification.hierarchy.selected_crop,
  );
  const condition = classification.hierarchy.conditions[0];
  if (!classification.hierarchy.crop_confident || !crop || !condition) {
    return Promise.reject(
      new Error(
        "Crop identity is uncertain, so management guidance is disabled for this image.",
      ),
    );
  }
  const visualObservation =
    visualEvidence && !visualEvidence.refused
      ? (visualEvidence.observations.join(" ") || visualEvidence.message).trim()
      : "";
  const payload = {
    provider,
    question,
    selected_crop: classification.hierarchy.selected_crop,
    crop_probability: crop.probability,
    selected_condition: condition.condition,
    condition_probability: condition.joint_probability,
    warnings: classification.warnings,
    ...(visualObservation ? { visual_observation: visualObservation } : {}),
  };
  return requestJson<ManagementAdvice>("/api/advice/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
}
