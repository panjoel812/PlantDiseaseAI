import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import {
  askQwen,
  classifyImage,
  fetchExampleImage,
  fetchQwenStatus,
} from "../api/client";
import type {
  ClassificationResult,
  ClassifyOptions,
  FeatureState,
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
  selectedFile: File | null;
  previewUrl: string | null;
  selectFile(file: File): void;
  classify(options: ClassifyOptions): Promise<void>;
  ask(question: string): Promise<void>;
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
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const selectedFileRef = useRef<File | null>(null);
  const previewUrlRef = useRef<string | null>(null);
  const classificationResultRef = useRef<ClassificationResult | undefined>(
    undefined,
  );
  const exampleControllerRef = useRef<AbortController | null>(null);
  const qwenStatusControllerRef = useRef<AbortController | null>(null);
  const classificationControllerRef = useRef<AbortController | null>(null);
  const qwenControllerRef = useRef<AbortController | null>(null);

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
      classificationControllerRef.current?.abort();
      qwenControllerRef.current?.abort();
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
      classificationResultRef.current = undefined;
      dispatchClassification({ type: "reset" });
      dispatchQwen({ type: "reset" });
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
    dispatchQwen({ type: "reset" });
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

  const reset = useCallback(() => {
    exampleControllerRef.current?.abort();
    exampleControllerRef.current = null;
    classificationControllerRef.current?.abort();
    classificationControllerRef.current = null;
    qwenControllerRef.current?.abort();
    qwenControllerRef.current = null;
    classificationResultRef.current = undefined;
    selectedFileRef.current = null;
    setSelectedFile(null);
    replacePreview(null);
    dispatchClassification({ type: "reset" });
    dispatchQwen({ type: "reset" });
  }, [replacePreview]);

  return {
    classification,
    qwen,
    qwenRuntime,
    selectedFile,
    previewUrl,
    selectFile,
    classify,
    ask,
    refreshQwenRuntime,
    reset,
  };
}
