function WarningIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path d="M10.3 4.1 2.8 17a2 2 0 0 0 1.7 3h15a2 2 0 0 0 1.7-3L13.7 4.1a2 2 0 0 0-3.4 0Z" />
      <path d="M12 9v4M12 17h.01" />
    </svg>
  );
}

export function SafetyNotice() {
  return (
    <aside className="safety-notice" aria-labelledby="safety-title">
      <div className="safety-title">
        <WarningIcon />
        <h2 id="safety-title">Research boundary</h2>
      </div>
      <p>PlantVillage performance does not establish field accuracy.</p>
      <p>Qwen fixed smoke: choice/few-shot 11/15; fine-grained condition 1/5.</p>
    </aside>
  );
}
