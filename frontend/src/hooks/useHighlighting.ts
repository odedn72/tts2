/**
 * Custom hook for determining which word or sentence is currently active
 * based on playback time and timing data.
 * Uses binary search for O(log n) performance on large timing arrays.
 */

import { useMemo } from "react";
import type { TimingData } from "../types/audio";

/** Information about the currently highlighted text segment. */
export interface HighlightInfo {
  /** Index of the currently active timing entry (-1 if none) */
  activeIndex: number;
  /** Character offset where the highlighted segment starts */
  startChar: number;
  /** Character offset where the highlighted segment ends */
  endChar: number;
}

/**
 * Binary search to find which timing entry contains the given time.
 * Returns the index where start_ms <= currentTimeMs < end_ms,
 * or -1 if the time falls outside or between entries.
 *
 * @param timings - Sorted array of timing entries with start_ms and end_ms
 * @param currentTimeMs - Current playback time in milliseconds
 * @returns Index of the matching entry, or -1
 */
export function findActiveTimingIndex(
  timings: Array<{ start_ms: number; end_ms: number }>,
  currentTimeMs: number
): number {
  if (timings.length === 0) {
    return -1;
  }

  let low = 0;
  let high = timings.length - 1;

  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    const entry = timings[mid];

    if (currentTimeMs < entry.start_ms) {
      high = mid - 1;
    } else if (currentTimeMs >= entry.end_ms) {
      low = mid + 1;
    } else {
      return mid; // Found: start_ms <= currentTimeMs < end_ms
    }
  }

  return -1; // Between entries or outside range
}

/**
 * Hook that computes highlighting information from timing data and playback time.
 *
 * @param timingData - Timing data with word or sentence entries, or null
 * @param currentTimeMs - Current playback position in milliseconds
 * @returns HighlightInfo with active index and char range, or null if no timing data
 */
export function useHighlighting(
  timingData: TimingData | null,
  currentTimeMs: number
): HighlightInfo | null {
  return useMemo(() => {
    if (!timingData) {
      return null;
    }

    const entries =
      timingData.timing_type === "word"
        ? timingData.words
        : timingData.sentences;

    if (!entries || entries.length === 0) {
      return null;
    }

    const activeIndex = findActiveTimingIndex(entries, currentTimeMs);

    if (activeIndex === -1) {
      return { activeIndex: -1, startChar: 0, endChar: 0 };
    }

    const active = entries[activeIndex];
    return {
      activeIndex,
      startChar: active.start_char,
      endChar: active.end_char,
    };
  }, [timingData, currentTimeMs]);
}
