# 10 - Playback and Highlighting

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define the audio playback management and synchronized text highlighting system.
This is the core user experience feature of the application.

**MRD traceability:** FR-005 (in-browser playback), FR-006 (word-by-word
highlighting), FR-007 (sentence-level fallback), NFR-003 (no perceptible lag
between audio and highlighting).

## Audio Playback Hook

```typescript
// hooks/useAudioPlayback.ts

interface UseAudioPlaybackReturn {
  audioRef: React.RefObject<HTMLAudioElement>;
  play: () => void;
  pause: () => void;
  seek: (timeMs: number) => void;
  currentTimeMs: number;
  duration: number;          // Total duration in ms
  isPlaying: boolean;
  isLoaded: boolean;
}

function useAudioPlayback(
  audioUrl: string | null,
  onTimeUpdate: (timeMs: number) => void,
  onEnded: () => void,
): UseAudioPlaybackReturn {
  // Implementation uses a ref to a hidden <audio> element
  // Binds event listeners for: timeupdate, ended, loadedmetadata, play, pause
  // The timeupdate event fires the onTimeUpdate callback with current time in ms
}
```

### Audio Element Setup

```typescript
// Inside the hook:
const audioRef = useRef<HTMLAudioElement>(null);

useEffect(() => {
  const audio = audioRef.current;
  if (!audio || !audioUrl) return;

  audio.src = audioUrl;
  audio.load();

  const handleTimeUpdate = () => {
    onTimeUpdate(Math.round(audio.currentTime * 1000));
  };

  const handleEnded = () => {
    onEnded();
  };

  audio.addEventListener("timeupdate", handleTimeUpdate);
  audio.addEventListener("ended", handleEnded);

  return () => {
    audio.removeEventListener("timeupdate", handleTimeUpdate);
    audio.removeEventListener("ended", handleEnded);
  };
}, [audioUrl]);
```

### Time Update Frequency

The HTML5 `timeupdate` event fires approximately 4 times per second (every
~250ms). For word-level highlighting, this may not be frequent enough for
short words.

**Solution:** Use `requestAnimationFrame` for smoother updates:

```typescript
useEffect(() => {
  if (!isPlaying) return;

  let animFrameId: number;
  const tick = () => {
    const audio = audioRef.current;
    if (audio && !audio.paused) {
      onTimeUpdate(Math.round(audio.currentTime * 1000));
      animFrameId = requestAnimationFrame(tick);
    }
  };
  animFrameId = requestAnimationFrame(tick);

  return () => cancelAnimationFrame(animFrameId);
}, [isPlaying]);
```

This gives ~60fps time updates, ensuring highlight transitions are smooth
(NFR-003).

## Highlighting Hook

```typescript
// hooks/useHighlighting.ts

interface HighlightInfo {
  /** Index of the currently active timing entry */
  activeIndex: number;
  /** Character range of the currently highlighted text */
  startChar: number;
  endChar: number;
}

function useHighlighting(
  timingData: TimingData | null,
  currentTimeMs: number,
): HighlightInfo | null {
  // Given the current playback time, determine which word or sentence
  // is currently active.
  //
  // Uses binary search for O(log n) performance on large timing arrays.
}
```

### Binary Search Algorithm

```typescript
function findActiveTimingIndex(
  timings: Array<{ start_ms: number; end_ms: number }>,
  currentTimeMs: number,
): number {
  // Binary search for the timing entry where:
  //   start_ms <= currentTimeMs < end_ms

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
```

## HighlightedTextView Rendering

### Word-Level Highlighting

When `timingData.timing_type === "word"`:

```typescript
function renderWordHighlighting(
  text: string,
  words: WordTiming[],
  activeIndex: number,
): React.ReactNode {
  // Strategy: split text into segments based on word timing character offsets
  // Each WordTiming has start_char and end_char
  //
  // Build an array of spans:
  // - For each timing entry, wrap the corresponding text range in a <span>
  // - Text between timing entries (whitespace, punctuation) is rendered as-is
  // - The span at activeIndex gets the "highlight-active" CSS class

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
      <span key={`word-${index}`} className={className} data-index={index}>
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
```

### Sentence-Level Highlighting

When `timingData.timing_type === "sentence"`:

Same approach but with `SentenceTiming` entries. Each sentence span is larger,
covering a full sentence.

### CSS Classes

```css
/* HighlightedTextView.css */

.highlighted-text-view {
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 16px;
  padding: 20px;
  overflow-y: auto;
  height: 100%;
}

.word-active,
.sentence-active {
  background-color: var(--highlight-bg);
  color: #ffffff;
  border-radius: 2px;
  padding: 1px 0;
}
```

## Auto-Scroll

The highlighted text view must auto-scroll to keep the active word/sentence
visible as playback progresses.

```typescript
function useAutoScroll(
  containerRef: React.RefObject<HTMLDivElement>,
  activeIndex: number,
) {
  useEffect(() => {
    if (activeIndex < 0) return;

    const container = containerRef.current;
    if (!container) return;

    const activeElement = container.querySelector(`[data-index="${activeIndex}"]`);
    if (!activeElement) return;

    // Scroll the active element into view, centered vertically
    activeElement.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }, [activeIndex]);
}
```

**Performance note:** `scrollIntoView` with `behavior: "smooth"` provides a
natural scrolling experience. The `block: "center"` ensures the active text
stays in the middle of the visible area.

## Generation Polling Hook

```typescript
// hooks/useGenerationPolling.ts

function useGenerationPolling(
  jobId: string | null,
  onProgress: (progress: number, total: number, completed: number) => void,
  onCompleted: (metadata: AudioMetadata) => void,
  onFailed: (error: { code: string; message: string }) => void,
  pollIntervalMs: number = 1000,
) {
  useEffect(() => {
    if (!jobId) return;

    const intervalId = setInterval(async () => {
      try {
        const status = await apiClient.getJobStatus(jobId);

        if (status.status === "in_progress" || status.status === "pending") {
          onProgress(status.progress, status.total_chunks, status.completed_chunks);
        } else if (status.status === "completed") {
          clearInterval(intervalId);
          // Fetch audio metadata
          const metadata = await apiClient.getAudioMetadata(jobId);
          onCompleted(metadata);
        } else if (status.status === "failed") {
          clearInterval(intervalId);
          onFailed({
            code: "GENERATION_FAILED",
            message: status.error_message || "Generation failed",
          });
        }
      } catch (error) {
        clearInterval(intervalId);
        onFailed({
          code: "POLLING_ERROR",
          message: "Failed to check generation status",
        });
      }
    }, pollIntervalMs);

    return () => clearInterval(intervalId);
  }, [jobId]);
}
```

## Audio Loading Flow

After generation completes:

```typescript
async function loadAudio(jobId: string, dispatch: React.Dispatch<AppAction>) {
  // 1. Fetch audio metadata (includes timing data)
  const metadata = await apiClient.getAudioMetadata(jobId);
  dispatch({ type: "GENERATION_COMPLETED", audioMetadata: metadata });

  // 2. Fetch audio file as blob
  const audioBlob = await apiClient.getAudioFile(jobId);
  const audioUrl = URL.createObjectURL(audioBlob);
  dispatch({ type: "AUDIO_LOADED", audioUrl });
}
```

## Providers Hook

```typescript
// hooks/useProviders.ts

function useProviders(dispatch: React.Dispatch<AppAction>) {
  // On mount: fetch providers list
  useEffect(() => {
    async function loadProviders() {
      try {
        const response = await apiClient.getProviders();
        dispatch({ type: "PROVIDERS_LOADED", providers: response.providers });
      } catch {
        dispatch({
          type: "ERROR_SET",
          error: { code: "LOAD_ERROR", message: "Failed to load providers" },
        });
      }
    }
    loadProviders();
  }, []);

  // When provider is selected: fetch voices
  const loadVoices = useCallback(async (provider: ProviderName) => {
    dispatch({ type: "VOICES_LOADING" });
    try {
      const response = await apiClient.getVoices(provider);
      dispatch({ type: "VOICES_LOADED", voices: response.voices });
    } catch {
      dispatch({
        type: "ERROR_SET",
        error: { code: "VOICES_ERROR", message: "Failed to load voices" },
      });
    }
  }, []);

  return { loadVoices };
}
```

## Dependencies

- React 18 (useRef, useEffect, useCallback, useMemo)
- AppState and AppAction types (spec 08)
- API client (spec 09 mentions it, defined in `api/client.ts`)
- TimingData, WordTiming, SentenceTiming types (spec 02)

## Error Handling

| Scenario | Handling |
|----------|----------|
| Audio fails to load | Dispatch ERROR_SET with user-friendly message |
| Polling fails | Stop polling, dispatch GENERATION_FAILED |
| Audio element error event | Dispatch ERROR_SET, show message |
| Timing data missing | Fall back to no highlighting (just display text) |
| Timing data has gaps | Binary search returns -1, no word highlighted (acceptable) |

## Notes for Developer

1. The `requestAnimationFrame` loop for time updates is critical for smooth
   highlighting. Without it, the `timeupdate` event (~4Hz) creates visible
   "jumping" between words.
2. The highlighting rendering function creates many `<span>` elements. For
   texts with 10,000 words, this is 10,000+ DOM elements. Measure performance
   and consider virtualization (e.g., only rendering visible text) if needed.
   However, for most chapter-length texts (5,000-10,000 words), modern
   browsers handle this fine.
3. Memoize the span array with `useMemo` -- only re-render when timing data
   changes (not on every time update). The active class should be applied via
   direct DOM manipulation or by only updating the className of the
   affected spans rather than re-rendering all spans.
4. For efficient highlighting updates, consider maintaining a ref to the
   previously active element and swapping classes directly:
   ```typescript
   // Instead of re-rendering all spans on every frame:
   prevActiveRef.current?.classList.remove("word-active");
   nextActive?.classList.add("word-active");
   prevActiveRef.current = nextActive;
   ```
   This avoids React re-renders entirely for time updates.
5. Test the binary search with edge cases: time before first word, time after
   last word, time exactly at a word boundary, time in a gap between words.
6. Test auto-scroll behavior: verify `scrollIntoView` is called when the
   active index changes.
7. The polling interval of 1000ms is appropriate for generation progress.
   No need for faster polling -- generation steps take seconds each.
