import type { ReactNode } from "react";

import { ProjectLogo } from "./ProjectLogo";

interface HeroProps {
  onReset(): void;
  children: ReactNode;
}

function ResetIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M19 8a7.5 7.5 0 1 0 1 6" />
      <path d="M19 3v5h-5" />
    </svg>
  );
}

export function Hero({ onReset, children }: HeroProps) {
  return (
    <>
      <header className="site-header">
        <span className="brand">
          <ProjectLogo className="brand-logo" />
          <span>PlantDiseaseAI</span>
        </span>
        <button className="reset-button" type="button" onClick={onReset}>
          <ResetIcon />
          Reset
        </button>
      </header>
      <div className="app-field">
        <section className="hero" aria-labelledby="research-demo-title">
          <h1 id="research-demo-title">Evidence before diagnosis.</h1>
          <p>Educational research demo — not a professional diagnosis.</p>
        </section>
        {children}
      </div>
    </>
  );
}
