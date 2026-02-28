/**
 * Displays text with synchronized word-by-word or sentence-level highlighting
 * during audio playback. Read-only view that replaces the text input area
 * when in playback mode.
 */

import React, { useMemo, useRef, useEffect } from "react";
import type { TimingData, WordTiming, SentenceTiming } from "../../types/audio";
import { findActiveTimingIndex } from "../../hooks/useHighlighting";

/** Props for the HighlightedTextView component. */
interface HighlightedTextViewProps {
  /** The full text content to display */
  text: string;
  /** Timing data for word or sentence highlighting */
  timingData: TimingData;
  /** Current playback position in milliseconds */
  currentTimeMs: number;
  /** Whether audio is currently playing */
  isPlaying: boolean;
}

/**
 * Renders word-level highlighting by wrapping each timed word in a span.
 * The active word gets the "word-active" CSS class.
 */
function renderWordHighlighting(
  text: string,
  words: WordTiming[],
  activeIndex: number
): React.ReactNode[] {
  const elements: React.ReactNode[] = [];
  let lastEnd = 0;

  words.forEach((wt, index) => {
    // Text before this word (whitespace, punctuation between words)
    if (wt.start_char > lastEnd) {
      elements.push(
        <span key={`gap-${index}`}>
          {text.slice(lastEnd, wt.start_char)}
        </span>
      );
    }

    // The word itself
    const className = index === activeIndex ? "word-active" : "";
    elements.push(
      <span
        key={`word-${index}`}
        className={className || undefined}
        data-index={index}
      >
        {text.slice(wt.start_char, wt.end_char)}
      </span>
    );

    lastEnd = wt.end_char;
  });

  // Any remaining text after the last word
  if (lastEnd < text.length) {
    elements.push(
      <span key="tail">{text.slice(lastEnd)}</span>
    );
  }

  return elements;
}

/**
 * Renders sentence-level highlighting by wrapping each timed sentence in a span.
 * The active sentence gets the "sentence-active" CSS class.
 */
function renderSentenceHighlighting(
  text: string,
  sentences: SentenceTiming[],
  activeIndex: number
): React.ReactNode[] {
  const elements: React.ReactNode[] = [];
  let lastEnd = 0;

  sentences.forEach((st, index) => {
    // Text before this sentence
    if (st.start_char > lastEnd) {
      elements.push(
        <span key={`gap-${index}`}>
          {text.slice(lastEnd, st.start_char)}
        </span>
      );
    }

    // The sentence itself
    const className = index === activeIndex ? "sentence-active" : "";
    elements.push(
      <span
        key={`sentence-${index}`}
        className={className || undefined}
        data-index={index}
      >
        {text.slice(st.start_char, st.end_char)}
      </span>
    );

    lastEnd = st.end_char;
  });

  // Any remaining text after the last sentence
  if (lastEnd < text.length) {
    elements.push(
      <span key="tail">{text.slice(lastEnd)}</span>
    );
  }

  return elements;
}

/**
 * Read-only view that displays text with highlighted words or sentences
 * synchronized to audio playback time.
 */
export function HighlightedTextView({
  text,
  timingData,
  currentTimeMs,
  isPlaying,
}: HighlightedTextViewProps): JSX.Element {
  const containerRef = useRef<HTMLDivElement>(null);

  // Determine which entry is currently active
  const activeIndex = useMemo(() => {
    if (!isPlaying && currentTimeMs === 0) return -1;

    const entries =
      timingData.timing_type === "word"
        ? timingData.words
        : timingData.sentences;

    if (!entries || entries.length === 0) return -1;

    return findActiveTimingIndex(entries, currentTimeMs);
  }, [timingData, currentTimeMs, isPlaying]);

  // Build the highlighted spans
  const content = useMemo(() => {
    if (timingData.timing_type === "word" && timingData.words) {
      return renderWordHighlighting(text, timingData.words, activeIndex);
    }
    if (timingData.timing_type === "sentence" && timingData.sentences) {
      return renderSentenceHighlighting(
        text,
        timingData.sentences,
        activeIndex
      );
    }
    return text;
  }, [text, timingData, activeIndex]);

  // Auto-scroll to keep active word/sentence visible
  useEffect(() => {
    if (activeIndex < 0) return;
    const container = containerRef.current;
    if (!container) return;
    const activeElement = container.querySelector(`[data-index="${activeIndex}"]`);
    if (!activeElement) return;
    if (typeof activeElement.scrollIntoView === "function") {
      activeElement.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [activeIndex]);

  return (
    <div
      ref={containerRef}
      className="highlighted-text-view"
      data-testid="highlighted-text"
    >
      {content}
    </div>
  );
}
