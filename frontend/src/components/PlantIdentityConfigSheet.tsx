import { useState, type FormEvent } from "react";

import type { PlantIdentityStatus } from "../api/types";

interface PlantIdentityConfigSheetProps {
  status: PlantIdentityStatus;
  onConfigure(apiKey: string): Promise<void>;
  onClear(): Promise<void>;
  onClose(): void;
}

export function PlantIdentityConfigSheet({
  status,
  onConfigure,
  onClear,
  onClose,
}: PlantIdentityConfigSheetProps) {
  const [apiKey, setApiKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save(event: FormEvent) {
    event.preventDefault();
    const key = apiKey.trim();
    if (!key) {
      setError("Enter a Pl@ntNet API key.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await onConfigure(key);
      setApiKey("");
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Configuration failed.");
    } finally {
      setBusy(false);
    }
  }

  async function clear() {
    setBusy(true);
    setError(null);
    try {
      await onClear();
      setApiKey("");
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Clear failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="provider-config-sheet plant-identity-sheet" aria-label="Broad plant identity configuration">
      <header>
        <div>
          <strong>100+ species identity</strong>
          <p>Pl@ntNet leaf identity · temporary local configuration</p>
        </div>
        <button type="button" aria-label="Close plant identity configuration" onClick={onClose}>×</button>
      </header>
      <form className="plant-identity-form" onSubmit={(event) => void save(event)}>
        <div className="provider-config-name">
          <strong>{status.display_name}</strong>
          <span>{status.configured ? "Configured" : "Local fallback: 114 classes"}</span>
        </div>
        <label htmlFor="plantnet-api-key">Pl@ntNet API key</label>
        <input
          id="plantnet-api-key"
          type="password"
          autoComplete="off"
          placeholder="Paste temporary key"
          value={apiKey}
          onChange={(event) => setApiKey(event.currentTarget.value)}
        />
        <div className="provider-config-actions">
          <button type="submit" disabled={busy}>Enable 100+ species</button>
          <button type="button" disabled={busy} onClick={() => void clear()}>Use local 114</button>
        </div>
      </form>
      <p className="provider-config-note">{status.detail}</p>
      <p className="provider-config-note">
        The isolated leaf is sent to Pl@ntNet only after you configure a key. Keys stay in FastAPI process memory.
      </p>
      {error ? <p className="provider-config-error" role="alert">{error}</p> : null}
    </section>
  );
}
