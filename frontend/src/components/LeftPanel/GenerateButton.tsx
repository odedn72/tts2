/**
 * Primary action button to trigger TTS audio generation.
 * Shows loading state during active generation.
 */

import React from "react";

/** Props for the GenerateButton component. */
interface GenerateButtonProps {
  /** Callback when the button is clicked */
  onClick: () => void;
  /** Whether the button is disabled (no provider/voice/text) */
  disabled: boolean;
  /** Whether generation is currently in progress */
  loading: boolean;
}

/**
 * Renders a prominent button for starting audio generation.
 * Disabled and shows "Generating..." text when loading.
 */
export function GenerateButton({
  onClick,
  disabled,
  loading,
}: GenerateButtonProps): JSX.Element {
  return (
    <button
      className="generate-button"
      onClick={onClick}
      disabled={disabled || loading}
      type="button"
    >
      {loading ? "Generating..." : "Generate Audio"}
    </button>
  );
}
