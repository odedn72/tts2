/**
 * Dropdown component for selecting a voice from the current provider.
 * Shows loading state while voices are being fetched.
 */

import React from "react";
import type { Voice } from "../../types/provider";

/** Props for the VoiceSelector component. */
interface VoiceSelectorProps {
  /** Available voices for the selected provider */
  voices: Voice[];
  /** Currently selected voice, or null */
  selectedVoice: Voice | null;
  /** Callback when user selects a voice */
  onSelect: (voice: Voice) => void;
  /** Whether voices are currently being fetched */
  loading: boolean;
  /** Whether the selector should be disabled */
  disabled: boolean;
}

/**
 * Renders a labeled select dropdown with voices.
 * Displays voice name and language. Shows loading text when fetching.
 */
export function VoiceSelector({
  voices,
  selectedVoice,
  onSelect,
  loading,
  disabled,
}: VoiceSelectorProps): JSX.Element {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>): void => {
    const voiceId = e.target.value;
    const voice = voices.find((v) => v.voice_id === voiceId);
    if (voice) {
      onSelect(voice);
    }
  };

  return (
    <div className="voice-selector">
      <label htmlFor="voice-select">Voice</label>
      {loading && <span className="loading-indicator">Loading voices...</span>}
      <select
        id="voice-select"
        aria-label="Voice"
        value={selectedVoice?.voice_id ?? ""}
        onChange={handleChange}
        disabled={disabled || loading}
      >
        <option value="" disabled>
          {loading ? "Loading voices..." : "Select a voice..."}
        </option>
        {voices.map((voice) => {
          const gender = voice.gender === "MALE" ? "M" : voice.gender === "FEMALE" ? "F" : null;
          return (
            <option key={voice.voice_id} value={voice.voice_id}>
              {voice.name} ({voice.language_name}{gender ? `, ${gender}` : ""})
            </option>
          );
        })}
      </select>
    </div>
  );
}
