import { ClassifierPanel } from "./components/ClassifierPanel";
import { Hero } from "./components/Hero";
import { ImageWorkspace } from "./components/ImageWorkspace";
import { QwenPanel } from "./components/QwenPanel";
import { SafetyNotice } from "./components/SafetyNotice";
import { useDemo } from "./hooks/useDemo";

export function App() {
  const demo = useDemo();

  return (
    <main className="page-shell">
      <Hero onReset={demo.reset}>
        <div className="workspace-grid">
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
          <div className="result-rail">
            <ClassifierPanel state={demo.classification} />
            <QwenPanel
              enabled={
                demo.classification.status === "success" &&
                demo.qwenRuntime.status === "success" &&
                demo.qwenRuntime.data.ready
              }
              runtime={demo.qwenRuntime}
              state={demo.qwen}
              onAsk={(question) => void demo.ask(question)}
              onRetryRuntime={() => void demo.refreshQwenRuntime()}
            />
          </div>
        </div>
        <SafetyNotice />
      </Hero>
    </main>
  );
}
