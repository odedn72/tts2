/**
 * Large text area for pasting chapter-length content.
 * Fills the right panel and supports very long text inputs.
 */

import React from "react";

/** Props for the TextInputArea component. */
interface TextInputAreaProps {
  /** Current text content */
  text: string;
  /** Callback when text content changes */
  onChange: (text: string) => void;
  /** Whether the text area is disabled (e.g., during generation) */
  disabled: boolean;
}

/**
 * Renders a full-height textarea with dark theme styling.
 * No artificial character limit -- supports 10,000+ words.
 */
export function TextInputArea({
  text,
  onChange,
  disabled,
}: TextInputAreaProps): JSX.Element {
  const handleChange = (
    e: React.ChangeEvent<HTMLTextAreaElement>
  ): void => {
    onChange(e.target.value);
  };

  return (
    <div className="text-input-area">
      <textarea
        className="text-input"
        value={text}
        onChange={handleChange}
        disabled={disabled}
        placeholder="Paste your text here..."
        aria-label="Text input"
      />
    </div>
  );
}
