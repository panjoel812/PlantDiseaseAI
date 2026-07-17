import type {
  ClassificationResult,
  ClassifyOptions,
  DemoHealth,
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

export async function fetchExampleImage(signal?: AbortSignal): Promise<File> {
  const response = await ensureOk(await fetch("/api/example", { signal }));
  const blob = await response.blob();
  return new File([blob], "field_corn_leaf.jpeg", {
    type: blob.type || "image/jpeg",
  });
}

export function askQwen(
  file: File,
  question: string,
  classification?: ClassificationResult,
  signal?: AbortSignal,
): Promise<QwenAnswer> {
  const body = new FormData();
  body.append("image", file);
  body.append("question", question);
  const selectedCondition = classification?.hierarchy.conditions[0];
  const fallbackPrediction = classification?.predictions[0];
  const className = selectedCondition?.class_name ?? fallbackPrediction?.class_name;
  const confidence =
    selectedCondition?.joint_probability ?? fallbackPrediction?.probability;
  if (className !== undefined && confidence !== undefined) {
    body.append("classifier_top_class_name", className);
    body.append("classifier_confidence", String(confidence));
    for (const warning of classification?.warnings ?? []) {
      body.append("classifier_warnings", warning);
    }
  }
  return requestJson<QwenAnswer>("/api/qwen/ask", {
    method: "POST",
    body,
    signal,
  });
}
