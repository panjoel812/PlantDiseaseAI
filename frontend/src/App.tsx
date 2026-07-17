import { AmbientGarden } from "./components/AmbientGarden";
import { AssistantPanel } from "./components/AssistantPanel";
import { ClassifierPanel } from "./components/ClassifierPanel";
import { Hero } from "./components/Hero";
import { ImageWorkspace } from "./components/ImageWorkspace";
import { SafetyNotice } from "./components/SafetyNotice";
import { useDemo } from "./hooks/useDemo";

export function App() {
  const demo = useDemo();

  return (
    <main className="page-shell">
      <AmbientGarden />
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
            <AssistantPanel
              classificationReady={demo.classification.status === "success"}
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
            />
          </div>
        </div>
        <SafetyNotice />
      </Hero>
    </main>
  );
}
