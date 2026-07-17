import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import {
  askForAdvice,
  askQwen,
  classifyImage,
  clearAdviceProvider,
  configureAdviceProvider,
  fetchAdviceProviders,
  fetchExampleImage,
  fetchQwenStatus,
} from "../api/client";
import type {
  AdviceProviderId,
  AdviceProviderStatus,
  AdviceProvidersResponse,
  ClassificationResult,
  ClassifyOptions,
  FeatureState,
  ManagementAdvice,
  QwenAnswer,
  QwenStatus,
} from "../api/types";

type FeatureAction<T> =
  | { type: "start" }
  | { type: "success"; data: T }
  | { type: "error"; error: string }
  | { type: "reset" };

function initialFeatureState<T>(): FeatureState<T> {
  return { status: "idle", data: null, error: null };
}

function assertNever(value: never): never {
  throw new Error(`Unhandled feature action: ${JSON.stringify(value)}`);
}

function featureReducer<T>(
  _state: FeatureState<T>,
  action: FeatureAction<T>,
): FeatureState<T> {
  switch (action.type) {
    case "start":
      return { status: "loading", data: null, error: null };
    case "success":
      return { status: "success", data: action.data, error: null };
    case "error":
      return { status: "error", data: null, error: action.error };
    case "reset":
      return initialFeatureState<T>();
    default:
      return assertNever(action);
  }
}

function isAbortError(error: unknown): boolean {
  return (
    typeof error === "object" &&
    error !== null &&
    "name" in error &&
    error.name === "AbortError"
  );
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected request failure";
}

export interface DemoState {
  classification: FeatureState<ClassificationResult>;
  qwen: FeatureState<QwenAnswer>;
  qwenRuntime: FeatureState<QwenStatus>;
  adviceProviders: FeatureState<AdviceProvidersResponse>;
  advice: FeatureState<ManagementAdvice>;
  selectedFile: File | null;
  previewUrl: string | null;
  selectFile(file: File): void;
  classify(options: ClassifyOptions): Promise<void>;
  ask(question: string): Promise<void>;
  askAdvice(provider: AdviceProviderId, question: string): Promise<void>;
  configureProvider(
    provider: AdviceProviderId,
    apiKey: string,
    modelId?: string,
  ): Promise<void>;
  clearProvider(provider: AdviceProviderId): Promise<void>;
  refreshQwenRuntime(): Promise<void>;
  reset(): void;
}

export function useDemo(): DemoState {
  const [classification, dispatchClassification] = useReducer(
    featureReducer<ClassificationResult>,
    initialFeatureState<ClassificationResult>(),
  );
  const [qwen, dispatchQwen] = useReducer(
    featureReducer<QwenAnswer>,
    initialFeatureState<QwenAnswer>(),
  );
  const [qwenRuntime, dispatchQwenRuntime] = useReducer(
    featureReducer<QwenStatus>,
    initialFeatureState<QwenStatus>(),
  );
  const [adviceProviders, dispatchAdviceProviders] = useReducer(
    featureReducer<AdviceProvidersResponse>,
    initialFeatureState<AdviceProvidersResponse>(),
  );
  const [advice, dispatchAdvice] = useReducer(
    featureReducer<ManagementAdvice>,
    initialFeatureState<ManagementAdvice>(),
  );
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const selectedFileRef = useRef<File | null>(null);
  const previewUrlRef = useRef<string | null>(null);
  const classificationResultRef = useRef<ClassificationResult | undefined>(
    undefined,
  );
  const qwenResultRef = useRef<QwenAnswer | undefined>(undefined);
  const exampleControllerRef = useRef<AbortController | null>(null);
  const qwenStatusControllerRef = useRef<AbortController | null>(null);
  const adviceStatusControllerRef = useRef<AbortController | null>(null);
  const classificationControllerRef = useRef<AbortController | null>(null);
  const qwenControllerRef = useRef<AbortController | null>(null);
  const adviceControllerRef = useRef<AbortController | null>(null);
  const providerConfigControllerRef = useRef<AbortController | null>(null);
  const adviceProvidersRef = useRef<AdviceProvidersResponse | null>(null);

  const replacePreview = useCallback((url: string | null) => {
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    previewUrlRef.current = url;
    setPreviewUrl(url);
  }, []);

  const refreshQwenRuntime = useCallback(async () => {
    qwenStatusControllerRef.current?.abort();
    const controller = new AbortController();
    qwenStatusControllerRef.current = controller;
    dispatchQwenRuntime({ type: "start" });
    try {
      const status = await fetchQwenStatus(controller.signal);
      if (
        controller.signal.aborted ||
        qwenStatusControllerRef.current !== controller
      ) {
        return;
      }
      dispatchQwenRuntime({ type: "success", data: status });
    } catch (error: unknown) {
      if (!controller.signal.aborted && qwenStatusControllerRef.current === controller) {
        dispatchQwenRuntime({ type: "error", error: errorMessage(error) });
      }
    } finally {
      if (qwenStatusControllerRef.current === controller) {
        qwenStatusControllerRef.current = null;
      }
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    exampleControllerRef.current = controller;
    void refreshQwenRuntime();

    const adviceStatusController = new AbortController();
    adviceStatusControllerRef.current = adviceStatusController;
    dispatchAdviceProviders({ type: "start" });
    void fetchAdviceProviders(adviceStatusController.signal)
      .then((providers) => {
        if (
          adviceStatusController.signal.aborted ||
          adviceStatusControllerRef.current !== adviceStatusController
        ) {
          return;
        }
        dispatchAdviceProviders({ type: "success", data: providers });
        adviceProvidersRef.current = providers;
      })
      .catch((error: unknown) => {
        if (
          !adviceStatusController.signal.aborted &&
          adviceStatusControllerRef.current === adviceStatusController
        ) {
          dispatchAdviceProviders({ type: "error", error: errorMessage(error) });
        }
      })
      .finally(() => {
        if (adviceStatusControllerRef.current === adviceStatusController) {
          adviceStatusControllerRef.current = null;
        }
      });

    void fetchExampleImage(controller.signal)
      .then((file) => {
        if (
          controller.signal.aborted ||
          exampleControllerRef.current !== controller
        ) {
          return;
        }
        selectedFileRef.current = file;
        setSelectedFile(file);
        replacePreview(URL.createObjectURL(file));
        exampleControllerRef.current = null;
      })
      .catch((error: unknown) => {
        if (!isAbortError(error) && exampleControllerRef.current === controller) {
          exampleControllerRef.current = null;
        }
      });

    return () => {
      controller.abort();
      qwenStatusControllerRef.current?.abort();
      qwenStatusControllerRef.current = null;
      adviceStatusControllerRef.current?.abort();
      adviceStatusControllerRef.current = null;
      classificationControllerRef.current?.abort();
      qwenControllerRef.current?.abort();
      adviceControllerRef.current?.abort();
      providerConfigControllerRef.current?.abort();
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current);
        previewUrlRef.current = null;
      }
    };
  }, [refreshQwenRuntime, replacePreview]);

  const selectFile = useCallback(
    (file: File) => {
      exampleControllerRef.current?.abort();
      exampleControllerRef.current = null;
      classificationControllerRef.current?.abort();
      classificationControllerRef.current = null;
      qwenControllerRef.current?.abort();
      qwenControllerRef.current = null;
      adviceControllerRef.current?.abort();
      adviceControllerRef.current = null;
      classificationResultRef.current = undefined;
      qwenResultRef.current = undefined;
      dispatchClassification({ type: "reset" });
      dispatchQwen({ type: "reset" });
      dispatchAdvice({ type: "reset" });
      selectedFileRef.current = file;
      setSelectedFile(file);
      replacePreview(URL.createObjectURL(file));
    },
    [replacePreview],
  );

  const classify = useCallback(async (options: ClassifyOptions) => {
    const file = selectedFileRef.current;
    if (!file) {
      dispatchClassification({ type: "error", error: "Select an image first." });
      return;
    }
    qwenControllerRef.current?.abort();
    qwenControllerRef.current = null;
    adviceControllerRef.current?.abort();
    adviceControllerRef.current = null;
    dispatchQwen({ type: "reset" });
    dispatchAdvice({ type: "reset" });
    qwenResultRef.current = undefined;
    classificationControllerRef.current?.abort();
    const controller = new AbortController();
    classificationControllerRef.current = controller;
    classificationResultRef.current = undefined;
    dispatchClassification({ type: "start" });
    try {
      const result = await classifyImage(file, options, controller.signal);
      if (
        controller.signal.aborted ||
        classificationControllerRef.current !== controller
      ) {
        return;
      }
      classificationResultRef.current = result;
      dispatchClassification({ type: "success", data: result });
    } catch (error: unknown) {
      if (
        !controller.signal.aborted &&
        classificationControllerRef.current === controller
      ) {
        dispatchClassification({ type: "error", error: errorMessage(error) });
      }
    } finally {
      if (classificationControllerRef.current === controller) {
        classificationControllerRef.current = null;
      }
    }
  }, []);

  const ask = useCallback(async (question: string) => {
    qwenControllerRef.current?.abort();
    qwenControllerRef.current = null;
    const file = selectedFileRef.current;
    if (!file) {
      dispatchQwen({ type: "error", error: "Select an image first." });
      return;
    }
    const normalizedQuestion = question.trim();
    if (!normalizedQuestion) {
      dispatchQwen({ type: "error", error: "Enter a question first." });
      return;
    }
    const controller = new AbortController();
    qwenControllerRef.current = controller;
    dispatchQwen({ type: "start" });
    try {
      const answer = await askQwen(
        file,
        normalizedQuestion,
        classificationResultRef.current,
        controller.signal,
      );
      if (controller.signal.aborted || qwenControllerRef.current !== controller) {
        return;
      }
      dispatchQwen({ type: "success", data: answer });
      qwenResultRef.current = answer;
    } catch (error: unknown) {
      if (!controller.signal.aborted && qwenControllerRef.current === controller) {
        dispatchQwen({ type: "error", error: errorMessage(error) });
      }
    } finally {
      if (qwenControllerRef.current === controller) {
        qwenControllerRef.current = null;
      }
    }
  }, []);

  const askAdvice = useCallback(
    async (provider: AdviceProviderId, question: string) => {
      adviceControllerRef.current?.abort();
      adviceControllerRef.current = null;
      const currentClassification = classificationResultRef.current;
      if (!currentClassification) {
        dispatchAdvice({ type: "error", error: "Analyze an image first." });
        return;
      }
      const normalizedQuestion = question.trim();
      if (!normalizedQuestion) {
        dispatchAdvice({ type: "error", error: "Enter a question first." });
        return;
      }
      const controller = new AbortController();
      adviceControllerRef.current = controller;
      dispatchAdvice({ type: "start" });
      try {
        const answer = await askForAdvice(
          provider,
          normalizedQuestion,
          currentClassification,
          qwenResultRef.current,
          controller.signal,
        );
        if (
          controller.signal.aborted ||
          adviceControllerRef.current !== controller
        ) {
          return;
        }
        dispatchAdvice({ type: "success", data: answer });
      } catch (error: unknown) {
        if (
          !controller.signal.aborted &&
          adviceControllerRef.current === controller
        ) {
          dispatchAdvice({ type: "error", error: errorMessage(error) });
        }
      } finally {
        if (adviceControllerRef.current === controller) {
          adviceControllerRef.current = null;
        }
      }
    },
    [],
  );

  const updateProviderStatus = useCallback((status: AdviceProviderStatus) => {
    const current = adviceProvidersRef.current ?? { providers: [] };
    const exists = current.providers.some(
      (item) => item.provider === status.provider,
    );
    const next = {
      providers: exists
        ? current.providers.map((item) =>
            item.provider === status.provider ? status : item,
          )
        : [...current.providers, status],
    };
    adviceProvidersRef.current = next;
    dispatchAdviceProviders({ type: "success", data: next });
  }, []);

  const configureProvider = useCallback(
    async (
      provider: AdviceProviderId,
      apiKey: string,
      modelId?: string,
    ) => {
      providerConfigControllerRef.current?.abort();
      const controller = new AbortController();
      providerConfigControllerRef.current = controller;
      try {
        const status = await configureAdviceProvider(
          provider,
          apiKey,
          modelId,
          controller.signal,
        );
        if (
          !controller.signal.aborted &&
          providerConfigControllerRef.current === controller
        ) {
          updateProviderStatus(status);
        }
      } finally {
        if (providerConfigControllerRef.current === controller) {
          providerConfigControllerRef.current = null;
        }
      }
    },
    [updateProviderStatus],
  );

  const clearProvider = useCallback(
    async (provider: AdviceProviderId) => {
      providerConfigControllerRef.current?.abort();
      const controller = new AbortController();
      providerConfigControllerRef.current = controller;
      try {
        const status = await clearAdviceProvider(provider, controller.signal);
        if (
          !controller.signal.aborted &&
          providerConfigControllerRef.current === controller
        ) {
          updateProviderStatus(status);
        }
      } finally {
        if (providerConfigControllerRef.current === controller) {
          providerConfigControllerRef.current = null;
        }
      }
    },
    [updateProviderStatus],
  );

  const reset = useCallback(() => {
    exampleControllerRef.current?.abort();
    exampleControllerRef.current = null;
    classificationControllerRef.current?.abort();
    classificationControllerRef.current = null;
    qwenControllerRef.current?.abort();
    qwenControllerRef.current = null;
    adviceControllerRef.current?.abort();
    adviceControllerRef.current = null;
    providerConfigControllerRef.current?.abort();
    providerConfigControllerRef.current = null;
    classificationResultRef.current = undefined;
    qwenResultRef.current = undefined;
    selectedFileRef.current = null;
    setSelectedFile(null);
    replacePreview(null);
    dispatchClassification({ type: "reset" });
    dispatchQwen({ type: "reset" });
    dispatchAdvice({ type: "reset" });
  }, [replacePreview]);

  return {
    classification,
    qwen,
    qwenRuntime,
    adviceProviders,
    advice,
    selectedFile,
    previewUrl,
    selectFile,
    classify,
    ask,
    askAdvice,
    configureProvider,
    clearProvider,
    refreshQwenRuntime,
    reset,
  };
}
