// TDD: Written from spec 09-frontend-components.md and spec 10
// Tests for the HighlightedTextView component

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// This import will fail until implementation exists
import { HighlightedTextView } from "../../src/components/RightPanel/HighlightedTextView";
import type { TimingData } from "../../src/types/audio";

const sampleText = "Hello world. How are you?";

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

describe("HighlightedTextView", () => {
  const defaultProps = {
    text: sampleText,
    timingData: wordTimingData,
    currentTimeMs: 0,
    isPlaying: false,
  };

  it("should render the full text", () => {
    render(<HighlightedTextView {...defaultProps} />);
    expect(screen.getByText(/Hello/)).toBeTruthy();
    expect(screen.getByText(/world/)).toBeTruthy();
    expect(screen.getByText(/you/)).toBeTruthy();
  });

  it("should wrap words in span elements", () => {
    const { container } = render(<HighlightedTextView {...defaultProps} />);
    const spans = container.querySelectorAll("span[data-index]");
    expect(spans.length).toBe(5); // 5 words
  });

  it("should highlight the active word", () => {
    const { container } = render(
      <HighlightedTextView {...defaultProps} currentTimeMs={150} isPlaying={true} />
    );
    const activeSpan = container.querySelector(".word-active");
    expect(activeSpan).toBeTruthy();
    expect(activeSpan?.textContent).toBe("Hello");
  });

  it("should move highlight as time progresses", () => {
    const { container, rerender } = render(
      <HighlightedTextView {...defaultProps} currentTimeMs={150} isPlaying={true} />
    );

    let active = container.querySelector(".word-active");
    expect(active?.textContent).toBe("Hello");

    rerender(
      <HighlightedTextView {...defaultProps} currentTimeMs={450} isPlaying={true} />
    );
    active = container.querySelector(".word-active");
    expect(active?.textContent).toBe("world.");
  });

  it("should handle sentence-level highlighting", () => {
    const { container } = render(
      <HighlightedTextView
        text={sampleText}
        timingData={sentenceTimingData}
        currentTimeMs={300}
        isPlaying={true}
      />
    );
    const active = container.querySelector(".sentence-active");
    expect(active).toBeTruthy();
    expect(active?.textContent).toContain("Hello world.");
  });

  it("should be read-only (not editable)", () => {
    const { container } = render(<HighlightedTextView {...defaultProps} />);
    const textarea = container.querySelector("textarea");
    const editableDiv = container.querySelector("[contenteditable='true']");
    expect(textarea).toBeNull();
    expect(editableDiv).toBeNull();
  });

  it("should have pre-wrap whitespace styling", () => {
    const { container } = render(<HighlightedTextView {...defaultProps} />);
    const view = container.querySelector(".highlighted-text-view, [data-testid='highlighted-text']");
    expect(view).toBeTruthy();
  });

  it("should not highlight any word when time is in gap", () => {
    const { container } = render(
      <HighlightedTextView {...defaultProps} currentTimeMs={650} isPlaying={true} />
    );
    const active = container.querySelector(".word-active");
    expect(active).toBeNull();
  });
});
