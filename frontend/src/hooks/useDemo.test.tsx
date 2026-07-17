import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  askQwen,
  classifyImage,
  fetchExampleImage,
  fetchQwenStatus,
} from "../api/client";
import type {
  ClassificationResult,
  ClassifyOptions,
  QwenAnswer,
  QwenStatus,
} from "../api/types";
import { useDemo } from "./useDemo";

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return {
    ...actual,
    askQwen: vi.fn(),
    classifyImage: vi.fn(),
    fetchExampleImage: vi.fn(),
    fetchQwenStatus: vi.fn(),
  };
});

interface Deferred<T> {
  promise: Promise<T>;
  resolve(value: T): void;
  reject(reason: unknown): void;
}

function deferred<T>(): Deferred<T> {
  let resolvePromise: ((value: T) => void) | undefined;
  let rejectPromise: ((reason: unknown) => void) | undefined;
  const promise = new Promise<T>((resolve, reject) => {
    resolvePromise = resolve;
    rejectPromise = reject;
  });
  return {
    promise,
    resolve(value: T) {
      resolvePromise?.(value);
    },
    reject(reason: unknown) {
      rejectPromise?.(reason);
    },
  };
}

function classification(className = "Corn___Northern_Leaf_Blight"): ClassificationResult {
  return {
    predictions: [{ class_index: 2, class_name: className, probability: 0.91 }],
    hierarchy: {
      method: "single_model_taxonomy_aggregation_v1",
      selected_crop: "Corn",
      selected_class_name: className,
      crops: [{ plant: "Corn", probability: 0.96 }],
      conditions: [
        {
          class_index: 2,
          class_name: className,
          plant: "Corn",
          condition: "Northern Leaf Blight",
          joint_probability: 0.91,
          conditional_probability: 0.9479166667,
        },
      ],
    },
    knowledge: {
      class_name: className,
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
    warnings: ["Field generalization is unknown."],
    gradcam: null,
  };
}

function qwenAnswer(message: string): QwenAnswer {
  return {
    raw_answer: "diseased",
    message,
    action: "educational_summary",
    refused: false,
    reasons: [],
    sources: [],
    model_id: "mlx-community/Qwen3-VL-4B-Instruct-4bit",
    scope: "exploratory_smoke",
    evidence_boundary: "Fixed smoke evidence only.",
  };
}

function qwenStatus(ready = true): QwenStatus {
  return {
    supported_platform: true,
    dependency_available: true,
    weights_cached: ready,
    ready,
    model_id: "mlx-community/Qwen3-VL-4B-Instruct-4bit",
    detail: ready ? "ready" : "Model weights are not in the local cache.",
  };
}

const classifyOptions: ClassifyOptions = {
  topK: 5,
  includeGradcam: true,
  device: "mps",
};

describe("useDemo", () => {
  let objectUrlCount = 0;

  beforeEach(() => {
    vi.clearAllMocks();
    objectUrlCount = 0;
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(() => `blob:preview-${++objectUrlCount}`),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(),
    });
    vi.mocked(fetchExampleImage).mockImplementation(
      () => new Promise<File>(() => undefined),
    );
    vi.mocked(fetchQwenStatus).mockResolvedValue(qwenStatus());
  });

  afterEach(() => {
    cleanup();
  });

  it("probes the real Qwen runtime on mount", async () => {
    vi.mocked(fetchQwenStatus).mockResolvedValue(qwenStatus(false));

    const { result } = renderHook(() => useDemo());

    await waitFor(() => expect(result.current.qwenRuntime.status).toBe("success"));
    expect(result.current.qwenRuntime.data?.ready).toBe(false);
    expect(fetchQwenStatus).toHaveBeenCalledOnce();
    expect(vi.mocked(fetchQwenStatus).mock.calls[0][0]).toBeInstanceOf(
      AbortSignal,
    );
  });

  it("retries the Qwen runtime probe after local setup changes", async () => {
    vi.mocked(fetchQwenStatus)
      .mockResolvedValueOnce(qwenStatus(false))
      .mockResolvedValueOnce(qwenStatus(true));
    const { result } = renderHook(() => useDemo());
    await waitFor(() => expect(result.current.qwenRuntime.data?.ready).toBe(false));

    await act(async () => result.current.refreshQwenRuntime());

    expect(result.current.qwenRuntime.data?.ready).toBe(true);
    expect(fetchQwenStatus).toHaveBeenCalledTimes(2);
  });

  it("aborts an older Qwen runtime probe and ignores its late result", async () => {
    const firstProbe = deferred<QwenStatus>();
    const secondProbe = deferred<QwenStatus>();
    const signals: AbortSignal[] = [];
    vi.mocked(fetchQwenStatus)
      .mockImplementationOnce((signal) => {
        if (!signal) throw new Error("Qwen status probe requires an abort signal");
        signals.push(signal);
        return firstProbe.promise;
      })
      .mockImplementationOnce((signal) => {
        if (!signal) throw new Error("Qwen status probe requires an abort signal");
        signals.push(signal);
        return secondProbe.promise;
      });
    const { result } = renderHook(() => useDemo());
    await waitFor(() => expect(signals).toHaveLength(1));

    let retryPromise: Promise<void> | undefined;
    act(() => {
      retryPromise = result.current.refreshQwenRuntime();
    });
    expect(signals).toHaveLength(2);
    expect(signals[0].aborted).toBe(true);

    await act(async () => {
      secondProbe.resolve(qwenStatus(true));
      await retryPromise;
    });
    expect(result.current.qwenRuntime.data?.ready).toBe(true);

    await act(async () => {
      firstProbe.resolve(qwenStatus(false));
      await firstProbe.promise;
    });
    expect(result.current.qwenRuntime.data?.ready).toBe(true);
  });

  it("aborts the active Qwen runtime probe when unmounted", async () => {
    const pendingProbe = deferred<QwenStatus>();
    let activeSignal: AbortSignal | undefined;
    vi.mocked(fetchQwenStatus).mockImplementation((signal) => {
      activeSignal = signal;
      return pendingProbe.promise;
    });
    const { unmount } = renderHook(() => useDemo());
    await waitFor(() => expect(activeSignal).toBeInstanceOf(AbortSignal));

    unmount();

    expect(activeSignal?.aborted).toBe(true);
  });

  it("loads the default example on mount and creates its preview URL", async () => {
    const example = new File(["example"], "field_corn_leaf.jpeg", {
      type: "image/jpeg",
    });
    vi.mocked(fetchExampleImage).mockResolvedValue(example);

    const { result } = renderHook(() => useDemo());

    await waitFor(() => expect(result.current.selectedFile).toBe(example));
    expect(result.current.previewUrl).toBe("blob:preview-1");
    expect(fetchExampleImage).toHaveBeenCalledOnce();
    expect(vi.mocked(fetchExampleImage).mock.calls[0][0]).toBeInstanceOf(
      AbortSignal,
    );
  });

  it("lets user selection preempt a late default-example response", async () => {
    const exampleRequest = deferred<File>();
    let exampleSignal: AbortSignal | undefined;
    vi.mocked(fetchExampleImage).mockImplementation((signal) => {
      exampleSignal = signal;
      return exampleRequest.promise;
    });
    const userFile = new File(["user"], "user.jpeg", { type: "image/jpeg" });
    const defaultFile = new File(["default"], "field_corn_leaf.jpeg", {
      type: "image/jpeg",
    });
    const { result } = renderHook(() => useDemo());

    act(() => result.current.selectFile(userFile));
    expect(exampleSignal?.aborted).toBe(true);
    await act(async () => {
      exampleRequest.resolve(defaultFile);
      await exampleRequest.promise;
    });

    expect(result.current.selectedFile).toBe(userFile);
    expect(result.current.previewUrl).toBe("blob:preview-1");
    expect(URL.createObjectURL).toHaveBeenCalledOnce();
  });

  it("revokes the previous object URL whenever the selected file changes", () => {
    const first = new File(["one"], "one.jpeg", { type: "image/jpeg" });
    const second = new File(["two"], "two.jpeg", { type: "image/jpeg" });
    const { result } = renderHook(() => useDemo());

    act(() => result.current.selectFile(first));
    act(() => result.current.selectFile(second));

    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:preview-1");
    expect(result.current.previewUrl).toBe("blob:preview-2");
  });

  it("keeps a successful classification when Qwen fails", async () => {
    const successfulClassification = classification();
    vi.mocked(classifyImage).mockResolvedValue(successfulClassification);
    vi.mocked(askQwen).mockRejectedValue(
      new ApiError(503, "Qwen unavailable"),
    );
    const file = new File(["leaf"], "leaf.jpeg", { type: "image/jpeg" });
    const { result } = renderHook(() => useDemo());

    act(() => result.current.selectFile(file));
    await act(async () => result.current.classify(classifyOptions));
    await act(async () => result.current.ask("What visual symptoms are visible?"));

    expect(result.current.classification).toEqual({
      status: "success",
      data: successfulClassification,
      error: null,
    });
    expect(result.current.qwen).toEqual({
      status: "error",
      data: null,
      error: "Qwen unavailable",
    });
  });

  it("aborts an older classifier request and ignores its late response", async () => {
    const first = deferred<ClassificationResult>();
    const second = deferred<ClassificationResult>();
    const signals: AbortSignal[] = [];
    vi.mocked(classifyImage)
      .mockImplementationOnce((_file, _options, signal) => {
        if (signal) signals.push(signal);
        return first.promise;
      })
      .mockImplementationOnce((_file, _options, signal) => {
        if (signal) signals.push(signal);
        return second.promise;
      });
    const { result } = renderHook(() => useDemo());
    act(() =>
      result.current.selectFile(
        new File(["leaf"], "leaf.jpeg", { type: "image/jpeg" }),
      ),
    );

    let firstRun: Promise<void> | undefined;
    let secondRun: Promise<void> | undefined;
    act(() => {
      firstRun = result.current.classify(classifyOptions);
    });
    act(() => {
      secondRun = result.current.classify(classifyOptions);
    });

    expect(signals[0]?.aborted).toBe(true);
    expect(signals[1]?.aborted).toBe(false);
    const secondResult = classification("Corn___Rust");
    await act(async () => {
      second.resolve(secondResult);
      await secondRun;
    });
    await act(async () => {
      first.resolve(classification("stale"));
      await firstRun;
    });
    expect(result.current.classification.data).toBe(secondResult);
  });

  it("aborts an older Qwen request and ignores its late response", async () => {
    const first = deferred<QwenAnswer>();
    const second = deferred<QwenAnswer>();
    const signals: AbortSignal[] = [];
    vi.mocked(askQwen)
      .mockImplementationOnce((_file, _question, _context, signal) => {
        if (signal) signals.push(signal);
        return first.promise;
      })
      .mockImplementationOnce((_file, _question, _context, signal) => {
        if (signal) signals.push(signal);
        return second.promise;
      });
    const { result } = renderHook(() => useDemo());
    act(() =>
      result.current.selectFile(
        new File(["leaf"], "leaf.jpeg", { type: "image/jpeg" }),
      ),
    );

    let firstRun: Promise<void> | undefined;
    let secondRun: Promise<void> | undefined;
    act(() => {
      firstRun = result.current.ask("first question");
    });
    act(() => {
      secondRun = result.current.ask("second question");
    });

    expect(signals[0]?.aborted).toBe(true);
    const secondAnswer = qwenAnswer("second answer");
    await act(async () => {
      second.resolve(secondAnswer);
      await secondRun;
    });
    await act(async () => {
      first.resolve(qwenAnswer("stale answer"));
      await firstRun;
    });
    expect(result.current.qwen.data).toBe(secondAnswer);
  });

  it.each(["resolve", "reject"] as const)(
    "keeps the blank-question error when the superseded Qwen request later %ss",
    async (settlement) => {
      const pendingAnswer = deferred<QwenAnswer>();
      let qwenSignal: AbortSignal | undefined;
      vi.mocked(askQwen).mockImplementation(
        (_file, _question, _context, signal) => {
          qwenSignal = signal;
          return pendingAnswer.promise;
        },
      );
      const { result } = renderHook(() => useDemo());
      act(() =>
        result.current.selectFile(
          new File(["leaf"], "leaf.jpeg", { type: "image/jpeg" }),
        ),
      );
      let firstRun: Promise<void> | undefined;
      act(() => {
        firstRun = result.current.ask("What symptoms are visible?");
      });

      await act(async () => result.current.ask("   "));

      expect(qwenSignal?.aborted).toBe(true);
      expect(result.current.qwen).toEqual({
        status: "error",
        data: null,
        error: "Enter a question first.",
      });
      await act(async () => {
        if (settlement === "resolve") {
          pendingAnswer.resolve(qwenAnswer("stale answer"));
        } else {
          pendingAnswer.reject(new ApiError(503, "stale Qwen error"));
        }
        await firstRun;
      });
      expect(result.current.qwen).toEqual({
        status: "error",
        data: null,
        error: "Enter a question first.",
      });
    },
  );

  it("aborts and resets Qwen when classification is rerun", async () => {
    const pendingAnswer = deferred<QwenAnswer>();
    let qwenSignal: AbortSignal | undefined;
    vi.mocked(askQwen).mockImplementation(
      (_file, _question, _context, signal) => {
        qwenSignal = signal;
        return pendingAnswer.promise;
      },
    );
    vi.mocked(classifyImage).mockResolvedValue(classification("Corn___Rust"));
    const { result } = renderHook(() => useDemo());
    act(() =>
      result.current.selectFile(
        new File(["leaf"], "leaf.jpeg", { type: "image/jpeg" }),
      ),
    );
    let askRun: Promise<void> | undefined;
    act(() => {
      askRun = result.current.ask("What symptoms are visible?");
    });

    await act(async () => result.current.classify(classifyOptions));

    expect(qwenSignal?.aborted).toBe(true);
    expect(result.current.qwen.status).toBe("idle");
    await act(async () => {
      pendingAnswer.resolve(qwenAnswer("stale answer"));
      await askRun;
    });
    expect(result.current.qwen.status).toBe("idle");
  });

  it("ignores a late Qwen error after classification is rerun", async () => {
    const pendingAnswer = deferred<QwenAnswer>();
    vi.mocked(askQwen).mockReturnValue(pendingAnswer.promise);
    vi.mocked(classifyImage).mockResolvedValue(classification("Corn___Rust"));
    const { result } = renderHook(() => useDemo());
    act(() =>
      result.current.selectFile(
        new File(["leaf"], "leaf.jpeg", { type: "image/jpeg" }),
      ),
    );
    let askRun: Promise<void> | undefined;
    act(() => {
      askRun = result.current.ask("What symptoms are visible?");
    });
    await act(async () => result.current.classify(classifyOptions));

    await act(async () => {
      pendingAnswer.reject(new ApiError(503, "stale Qwen error"));
      await askRun;
    });

    expect(result.current.qwen.status).toBe("idle");
  });

  it("reset aborts both features, revokes the preview, and restores idle state", () => {
    const classifierSignals: AbortSignal[] = [];
    const qwenSignals: AbortSignal[] = [];
    vi.mocked(classifyImage).mockImplementation((_file, _options, signal) => {
      if (signal) classifierSignals.push(signal);
      return new Promise<ClassificationResult>(() => undefined);
    });
    vi.mocked(askQwen).mockImplementation(
      (_file, _question, _context, signal) => {
        if (signal) qwenSignals.push(signal);
        return new Promise<QwenAnswer>(() => undefined);
      },
    );
    const { result } = renderHook(() => useDemo());
    act(() =>
      result.current.selectFile(
        new File(["leaf"], "leaf.jpeg", { type: "image/jpeg" }),
      ),
    );
    act(() => {
      void result.current.classify(classifyOptions);
      void result.current.ask("safe question");
    });

    act(() => result.current.reset());

    expect(classifierSignals[0]?.aborted).toBe(true);
    expect(qwenSignals[0]?.aborted).toBe(true);
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:preview-1");
    expect(result.current.selectedFile).toBeNull();
    expect(result.current.previewUrl).toBeNull();
    expect(result.current.classification.status).toBe("idle");
    expect(result.current.qwen.status).toBe("idle");
  });

  it("aborts in-flight work and revokes the preview on unmount", () => {
    let classifierSignal: AbortSignal | undefined;
    let qwenSignal: AbortSignal | undefined;
    vi.mocked(classifyImage).mockImplementation((_file, _options, signal) => {
      classifierSignal = signal;
      return new Promise<ClassificationResult>(() => undefined);
    });
    vi.mocked(askQwen).mockImplementation(
      (_file, _question, _context, signal) => {
        qwenSignal = signal;
        return new Promise<QwenAnswer>(() => undefined);
      },
    );
    const { result, unmount } = renderHook(() => useDemo());
    act(() =>
      result.current.selectFile(
        new File(["leaf"], "leaf.jpeg", { type: "image/jpeg" }),
      ),
    );
    act(() => {
      void result.current.classify(classifyOptions);
      void result.current.ask("safe question");
    });

    unmount();

    expect(classifierSignal?.aborted).toBe(true);
    expect(qwenSignal?.aborted).toBe(true);
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:preview-1");
  });
});
