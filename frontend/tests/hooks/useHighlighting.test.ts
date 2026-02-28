// TDD: Written from spec 10-playback-and-highlighting.md
// Tests for the useHighlighting hook and binary search algorithm

import { describe, it, expect } from "vitest";
import { renderHook } from "@testing-library/react";

// These imports will fail until implementation exists
import { useHighlighting, findActiveTimingIndex } from "../../src/hooks/useHighlighting";
import type { TimingData } from "../../src/types/audio";

const wordTimingData: TimingData = {
  timing_type: "word",
  words: [
    { word: "Hello", start_ms: 0, end_ms: 300, start_char: 0, end_char: 5 },
    { word: "world.", start_ms: 300, end_ms: 600, start_char: 6, end_char: 12 },
    { word: "How", start_ms: 700, end_ms: 900, start_char: 13, end_char: 16 },
    { word: "are", start_ms: 900, end_ms: 1100, start_char: 17, end_char: 20 },
    { word: "you?", start_ms: 1100, end_ms: 1400, start_char: 21, end_char: 25 },
  ],
  sentences: null,
};

const sentenceTimingData: TimingData = {
  timing_type: "sentence",
  words: null,
  sentences: [
    {
      sentence: "Hello world.",
      start_ms: 0,
      end_ms: 600,
      start_char: 0,
      end_char: 12,
    },
    {
      sentence: "How are you?",
      start_ms: 700,
      end_ms: 1400,
      start_char: 13,
      end_char: 25,
    },
  ],
};

describe("findActiveTimingIndex", () => {
  const timings = [
    { start_ms: 0, end_ms: 300 },
    { start_ms: 300, end_ms: 600 },
    { start_ms: 700, end_ms: 900 },
    { start_ms: 900, end_ms: 1100 },
    { start_ms: 1100, end_ms: 1400 },
  ];

  it("should find first word at time 0", () => {
    expect(findActiveTimingIndex(timings, 0)).toBe(0);
  });

  it("should find first word at time 150", () => {
    expect(findActiveTimingIndex(timings, 150)).toBe(0);
  });

  it("should find second word at time 300", () => {
    expect(findActiveTimingIndex(timings, 300)).toBe(1);
  });

  it("should find last word at time 1200", () => {
    expect(findActiveTimingIndex(timings, 1200)).toBe(4);
  });

  it("should return -1 for time in gap between entries", () => {
    // Time 650 is between word 2 (end 600) and word 3 (start 700)
    expect(findActiveTimingIndex(timings, 650)).toBe(-1);
  });

  it("should return -1 for time after all entries", () => {
    expect(findActiveTimingIndex(timings, 2000)).toBe(-1);
  });

  it("should return -1 for negative time", () => {
    expect(findActiveTimingIndex(timings, -100)).toBe(-1);
  });

  it("should handle single entry", () => {
    expect(findActiveTimingIndex([{ start_ms: 0, end_ms: 500 }], 250)).toBe(0);
  });

  it("should handle empty array", () => {
    expect(findActiveTimingIndex([], 100)).toBe(-1);
  });

  it("should find at exact boundary (start_ms)", () => {
    expect(findActiveTimingIndex(timings, 700)).toBe(2);
  });

  it("should not match at exact end boundary (end_ms)", () => {
    // end_ms is exclusive: start_ms <= time < end_ms
    expect(findActiveTimingIndex(timings, 300)).toBe(1); // start of next
  });
});

describe("useHighlighting", () => {
  it("should return null when timing data is null", () => {
    const { result } = renderHook(() => useHighlighting(null, 0));
    expect(result.current).toBeNull();
  });

  it("should find active word for word timing", () => {
    const { result } = renderHook(() =>
      useHighlighting(wordTimingData, 150)
    );
    expect(result.current).not.toBeNull();
    expect(result.current!.activeIndex).toBe(0);
    expect(result.current!.startChar).toBe(0);
    expect(result.current!.endChar).toBe(5);
  });

  it("should find second word at time 400", () => {
    const { result } = renderHook(() =>
      useHighlighting(wordTimingData, 400)
    );
    expect(result.current!.activeIndex).toBe(1);
  });

  it("should find active sentence for sentence timing", () => {
    const { result } = renderHook(() =>
      useHighlighting(sentenceTimingData, 100)
    );
    expect(result.current).not.toBeNull();
    expect(result.current!.activeIndex).toBe(0);
    expect(result.current!.startChar).toBe(0);
    expect(result.current!.endChar).toBe(12);
  });

  it("should return null highlight when time is in gap", () => {
    const { result } = renderHook(() =>
      useHighlighting(wordTimingData, 650)
    );
    // When no word is active, either null or activeIndex -1
    if (result.current !== null) {
      expect(result.current.activeIndex).toBe(-1);
    }
  });

  it("should update when currentTimeMs changes", () => {
    const { result, rerender } = renderHook(
      ({ time }) => useHighlighting(wordTimingData, time),
      { initialProps: { time: 0 } }
    );
    expect(result.current!.activeIndex).toBe(0);

    rerender({ time: 1200 });
    expect(result.current!.activeIndex).toBe(4);
  });
});
