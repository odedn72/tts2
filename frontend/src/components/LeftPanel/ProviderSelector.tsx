/**
 * Dropdown component for selecting a TTS provider.
 * Displays all available providers with configuration status.
 */

import React from "react";
import type { ProviderName, ProviderInfo } from "../../types/provider";

/** Props for the ProviderSelector component. */
interface ProviderSelectorProps {
  /** List of available TTS providers */
  providers: ProviderInfo[];
  /** Currently selected provider name, or null if none */
  selectedProvider: ProviderName | null;
  /** Callback when user selects a provider */
  onSelect: (provider: ProviderName) => void;
}

/**
 * Renders a labeled select dropdown with all TTS providers.
 * Unconfigured providers are marked with "(not configured)".
 */
export function ProviderSelector({
  providers,
  selectedProvider,
  onSelect,
}: ProviderSelectorProps): JSX.Element {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>): void => {
    const value = e.target.value as ProviderName;
    if (value) {
      onSelect(value);
    }
  };

  return (
    <div className="provider-selector">
      <label htmlFor="provider-select">TTS Provider</label>
      <select
        id="provider-select"
        aria-label="TTS Provider"
        value={selectedProvider ?? ""}
        onChange={handleChange}
      >
        <option value="" disabled>
          Select a provider...
        </option>
        {providers.map((provider) => (
          <option key={provider.name} value={provider.name}>
            {provider.display_name}
            {!provider.is_configured ? " (not configured)" : ""}
          </option>
        ))}
      </select>
    </div>
  );
}
