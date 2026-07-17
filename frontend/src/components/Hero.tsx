import type { ReactNode } from "react";

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

function BrandLeafIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M20 4C11 4.4 6.2 8.2 6.4 15.4c4.4 2.2 9.7.3 11.8-4.1C19.5 8.7 20 6.1 20 4Z" />
      <path d="M4 20c3.1-5.2 7-8.8 12.5-11.5" />
    </svg>
  );
}

export function Hero({ onReset, children }: HeroProps) {
  return (
    <>
      <header className="site-header">
        <span className="brand">
          <BrandLeafIcon />
          PlantDiseaseAI
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
