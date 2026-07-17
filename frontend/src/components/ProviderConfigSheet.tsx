import { useState, type FormEvent } from "react";

import type { AdviceProviderId, AdviceProviderStatus } from "../api/types";

interface ProviderConfigSheetProps {
  providers: AdviceProviderStatus[];
  onConfigure(
    provider: AdviceProviderId,
    apiKey: string,
    modelId?: string,
  ): Promise<void>;
  onClear(provider: AdviceProviderId): Promise<void>;
  onClose(): void;
}

export function ProviderConfigSheet({
  providers,
  onConfigure,
  onClear,
  onClose,
}: ProviderConfigSheetProps) {
  const [keys, setKeys] = useState<Partial<Record<AdviceProviderId, string>>>({});
  const [models, setModels] = useState<Partial<Record<AdviceProviderId, string>>>({});
  const [busy, setBusy] = useState<AdviceProviderId | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function save(event: FormEvent, provider: AdviceProviderStatus) {
    event.preventDefault();
    const key = keys[provider.provider]?.trim() ?? "";
    if (!key) {
      setError(`Enter a ${provider.display_name} API key.`);
      return;
    }
    setBusy(provider.provider);
    setError(null);
    try {
      await onConfigure(
        provider.provider,
        key,
        models[provider.provider]?.trim() || provider.model_id,
      );
      setKeys((current) => ({ ...current, [provider.provider]: "" }));
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Configuration failed.");
    } finally {
      setBusy(null);
    }
  }

  async function clear(provider: AdviceProviderStatus) {
    setBusy(provider.provider);
    setError(null);
    try {
      await onClear(provider.provider);
      setKeys((current) => ({ ...current, [provider.provider]: "" }));
    } catch (caught: unknown) {
      setError(caught instanceof Error ? caught.message : "Clear failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="provider-config-sheet" aria-label="Temporary provider configuration">
      <header>
        <div>
          <strong>Configure providers</strong>
          <p>Temporary · cleared when the API restarts</p>
        </div>
        <button type="button" aria-label="Close provider configuration" onClick={onClose}>×</button>
      </header>
      <div className="provider-config-list">
        {providers.map((provider) => (
          <form key={provider.provider} onSubmit={(event) => void save(event, provider)}>
            <div className="provider-config-name">
              <strong>{provider.display_name}</strong>
              <span>{provider.configured ? "Configured" : "Not configured"}</span>
            </div>
            <label htmlFor={`${provider.provider}-key`}>{provider.display_name} API key</label>
            <input
              id={`${provider.provider}-key`}
              type="password"
              autoComplete="off"
              placeholder="Paste temporary key"
              value={keys[provider.provider] ?? ""}
              onChange={(event) => {
                const value = event.currentTarget.value;
                setKeys((current) => ({
                  ...current,
                  [provider.provider]: value,
                }));
              }}
            />
            <label htmlFor={`${provider.provider}-model`}>{provider.display_name} model</label>
            <input
              id={`${provider.provider}-model`}
              value={models[provider.provider] ?? provider.model_id}
              onChange={(event) => {
                const value = event.currentTarget.value;
                setModels((current) => ({
                  ...current,
                  [provider.provider]: value,
                }));
              }}
            />
            <div className="provider-config-actions">
              <button type="submit" disabled={busy === provider.provider}>Save {provider.display_name}</button>
              <button type="button" disabled={busy === provider.provider} onClick={() => void clear(provider)}>Clear</button>
            </div>
          </form>
        ))}
      </div>
      {error ? <p className="provider-config-error" role="alert">{error}</p> : null}
      <p className="provider-config-note">Keys stay only in FastAPI process memory. Use localhost or HTTPS.</p>
    </section>
  );
}
