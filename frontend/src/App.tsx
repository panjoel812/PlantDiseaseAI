import { useEffect, useRef } from "react";

import { AmbientGarden } from "./components/AmbientGarden";
import { AssistantPanel } from "./components/AssistantPanel";
import { ClassifierPanel } from "./components/ClassifierPanel";
import { Hero } from "./components/Hero";
import { ImageWorkspace } from "./components/ImageWorkspace";
import { SafetyNotice } from "./components/SafetyNotice";
import { useDemo } from "./hooks/useDemo";

export function App() {
  const demo = useDemo();
  const resultsRef = useRef<HTMLElement>(null);
  const previousClassificationStatus = useRef(demo.classification.status);

  useEffect(() => {
    const previous = previousClassificationStatus.current;
    const current = demo.classification.status;
    previousClassificationStatus.current = current;
    if (previous !== "loading" || current !== "success") return;

    const results = resultsRef.current;
    if (!results) return;
    const reducedMotion =
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
    results.scrollIntoView({
      behavior: reducedMotion ? "auto" : "smooth",
      block: "start",
    });
    results.focus({ preventScroll: true });
  }, [demo.classification.status]);

  return (
    <main className="page-shell">
      <AmbientGarden />
      <Hero onReset={demo.reset}>
        <section className="upload-section" aria-label="Upload and analyze">
          <ImageWorkspace
            previewUrl={demo.previewUrl}
            selectedFileName={demo.selectedFile?.name ?? null}
            hasImage={demo.selectedFile !== null}
            classificationStatus={demo.classification.status}
            onSelectFile={demo.selectFile}
            onAnalyze={() =>
              void demo.classify({ topK: 5, includeGradcam: true })
            }
          />
        </section>
        <section
          ref={resultsRef}
          className="results-section"
          aria-labelledby="analysis-results-title"
          tabIndex={-1}
        >
          <div className="results-heading">
            <h2 id="analysis-results-title">Analysis results</h2>
            <p>Classifier evidence and optional management guidance.</p>
          </div>
          <div className="results-grid">
            <ClassifierPanel state={demo.classification} />
            <AssistantPanel
              guidanceEnabled={
                demo.classification.status === "success" &&
                demo.classification.data.hierarchy.crop_confident
              }
              qwenEnabled={
                demo.classification.status === "success" &&
                demo.qwenRuntime.status === "success" &&
                demo.qwenRuntime.data.ready
              }
              qwenRuntime={demo.qwenRuntime}
              qwenState={demo.qwen}
              providers={demo.adviceProviders}
              adviceState={demo.advice}
              onAskQwen={(question) => void demo.ask(question)}
              onRetryQwenRuntime={() => void demo.refreshQwenRuntime()}
              onAskAdvice={(provider, question) =>
                void demo.askAdvice(provider, question)
              }
              onConfigureProvider={demo.configureProvider}
              onClearProvider={demo.clearProvider}
            />
          </div>
        </section>
        <SafetyNotice />
      </Hero>
    </main>
  );
}
