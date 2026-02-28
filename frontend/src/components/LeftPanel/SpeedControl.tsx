/**
 * Slider component for adjusting speech speed.
 * Hidden entirely when the selected provider does not support speed control.
 */

import React from "react";

/** Props for the SpeedControl component. */
interface SpeedControlProps {
  /** Current speed multiplier */
  speed: number;
  /** Minimum allowed speed */
  min: number;
  /** Maximum allowed speed */
  max: number;
  /** Callback when speed value changes */
  onChange: (speed: number) => void;
  /** Whether the slider is disabled */
  disabled: boolean;
  /** Whether the slider should be rendered at all */
  visible: boolean;
}

/**
 * Renders a range slider with the current speed value displayed.
 * Returns null when visible is false (not just hidden, fully unmounted).
 */
export function SpeedControl({
  speed,
  min,
  max,
  onChange,
  disabled,
  visible,
}: SpeedControlProps): JSX.Element | null {
  if (!visible) {
    return null;
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    onChange(parseFloat(e.target.value));
  };

  /** Format a number so it always has at least one decimal place. */
  const formatNum = (n: number): string => {
    const s = n.toString();
    return s.includes(".") ? s : `${s}.0`;
  };

  return (
    <div className="speed-control">
      <label htmlFor="speed-slider">
        Speed: <span className="speed-value">{speed.toFixed(1)}x</span>
      </label>
      <input
        id="speed-slider"
        type="range"
        role="slider"
        min={formatNum(min)}
        max={formatNum(max)}
        step={0.1}
        value={speed}
        onChange={handleChange}
        disabled={disabled}
        aria-label="Speed"
      />
    </div>
  );
}
