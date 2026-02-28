// TDD: Written from spec 10-playback-and-highlighting.md
// Tests for the useAudioPlayback hook

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

// This import will fail until implementation exists
import { useAudioPlayback } from "../../src/hooks/useAudioPlayback";

// Mock HTMLAudioElement
class MockAudioElement {
  src = "";
  currentTime = 0;
  duration = 10;
  paused = true;
  private listeners: Record<string, Function[]> = {};

  load() {}

  play() {
    this.paused = false;
    this.dispatchEvent("play");
  }

  pause() {
    this.paused = true;
    this.dispatchEvent("pause");
  }

  addEventListener(event: string, handler: Function) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(handler);
  }

  removeEventListener(event: string, handler: Function) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter((h) => h !== handler);
    }
  }

  dispatchEvent(event: string) {
    (this.listeners[event] || []).forEach((h) => h());
  }
}

describe("useAudioPlayback", () => {
  it("should return audioRef", () => {
    const onTimeUpdate = vi.fn();
    const onEnded = vi.fn();
    const { result } = renderHook(() =>
      useAudioPlayback(null, onTimeUpdate, onEnded)
    );
    expect(result.current.audioRef).toBeDefined();
  });

  it("should not be playing initially", () => {
    const onTimeUpdate = vi.fn();
    const onEnded = vi.fn();
    const { result } = renderHook(() =>
      useAudioPlayback(null, onTimeUpdate, onEnded)
    );
    expect(result.current.isPlaying).toBe(false);
  });

  it("should not be loaded with null url", () => {
    const onTimeUpdate = vi.fn();
    const onEnded = vi.fn();
    const { result } = renderHook(() =>
      useAudioPlayback(null, onTimeUpdate, onEnded)
    );
    expect(result.current.isLoaded).toBe(false);
  });

  it("should expose play and pause functions", () => {
    const onTimeUpdate = vi.fn();
    const onEnded = vi.fn();
    const { result } = renderHook(() =>
      useAudioPlayback("blob:test", onTimeUpdate, onEnded)
    );
    expect(typeof result.current.play).toBe("function");
    expect(typeof result.current.pause).toBe("function");
  });

  it("should expose seek function", () => {
    const onTimeUpdate = vi.fn();
    const onEnded = vi.fn();
    const { result } = renderHook(() =>
      useAudioPlayback("blob:test", onTimeUpdate, onEnded)
    );
    expect(typeof result.current.seek).toBe("function");
  });

  it("should expose currentTimeMs and duration", () => {
    const onTimeUpdate = vi.fn();
    const onEnded = vi.fn();
    const { result } = renderHook(() =>
      useAudioPlayback(null, onTimeUpdate, onEnded)
    );
    expect(typeof result.current.currentTimeMs).toBe("number");
    expect(typeof result.current.duration).toBe("number");
  });
});
