/**
 * Modal panel for configuring TTS provider API keys.
 * Displays each provider with its configuration status and a
 * password input for entering/updating API keys.
 */

import React, { useState } from "react";
import type { ProviderName } from "../../types/provider";
import type { ProviderKeyStatus } from "../../types/api";

/** Props for the SettingsPanel component. */
interface SettingsPanelProps {
  /** Configuration status for each provider */
  providers: ProviderKeyStatus[];
  /** Callback to save a provider's API key */
  onSave: (provider: ProviderName, apiKey: string) => void;
  /** Callback to close the settings panel */
  onClose: () => void;
  /** Whether the panel is currently visible */
  open: boolean;
}

/**
 * Renders a modal overlay with API key configuration for each provider.
 * Uses password inputs for security. Never displays existing key values.
 */
export function SettingsPanel({
  providers,
  onSave,
  onClose,
  open,
}: SettingsPanelProps): JSX.Element | null {
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});

  if (!open) {
    return null;
  }

  const handleKeyChange = (
    provider: ProviderName,
    value: string
  ): void => {
    setApiKeys((prev) => ({ ...prev, [provider]: value }));
  };

  const handleSave = (provider: ProviderName): void => {
    const key = apiKeys[provider];
    if (key && key.trim()) {
      onSave(provider, key.trim());
      setApiKeys((prev) => ({ ...prev, [provider]: "" }));
    }
  };

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div
        className="settings-panel"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Settings"
      >
        <div className="settings-header">
          <h2>Settings</h2>
          <button
            className="settings-close"
            onClick={onClose}
            type="button"
            aria-label="Close settings"
          >
            X
          </button>
        </div>

        <div className="settings-body">
          {providers.map((p) => (
            <div key={p.provider} className="settings-provider">
              <div className="settings-provider-info">
                <span className="settings-provider-name">{p.provider}</span>
                <span
                  className={`settings-status ${
                    p.is_configured ? "configured" : "not-configured"
                  }`}
                >
                  {p.is_configured ? "Configured" : "Not configured"}
                </span>
              </div>
              <div className="settings-provider-input">
                <input
                  type="password"
                  placeholder="Enter API key..."
                  value={apiKeys[p.provider] ?? ""}
                  onChange={(e) =>
                    handleKeyChange(
                      p.provider as ProviderName,
                      e.target.value
                    )
                  }
                  aria-label={`API key for ${p.provider}`}
                />
                <button
                  type="button"
                  onClick={() => handleSave(p.provider as ProviderName)}
                  disabled={!apiKeys[p.provider]?.trim()}
                >
                  Save
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
