/**
 * Progress bar component for showing TTS generation progress.
 * Displays percentage, chunk count, and a visual progress bar.
 */

import React from "react";

/** Props for the ProgressIndicator component. */
interface ProgressIndicatorProps {
  /** Progress value from 0.0 to 1.0 */
  progress: number;
  /** Total number of text chunks */
  totalChunks: number;
  /** Number of chunks completed */
  completedChunks: number;
  /** Whether the progress indicator should be visible */
  visible: boolean;
}

/**
 * Renders a progress bar with percentage and chunk count.
 * Returns null when not visible.
 */
export function ProgressIndicator({
  progress,
  totalChunks,
  completedChunks,
  visible,
}: ProgressIndicatorProps): JSX.Element | null {
  if (!visible) {
    return null;
  }

  const percentage = Math.round(progress * 100);

  return (
    <div className="progress-indicator">
      <div className="progress-text">
        Generating: chunk {completedChunks} of {totalChunks} ({percentage}%)
      </div>
      <div className="progress-bar-container" role="progressbar" aria-valuenow={percentage} aria-valuemin={0} aria-valuemax={100}>
        <div
          className="progress-bar-fill"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
