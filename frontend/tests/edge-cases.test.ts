// TDD Mode 2: Additional edge case tests discovered during validation review
// These tests cover edge cases not covered by the original TDD test suite.

import { describe, it, expect, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "./mocks/server";
import { appReducer, initialState } from "../src/state/reducer";
import type { AppState } from "../src/state/reducer";
import { findActiveTimingIndex } from "../src/hooks/useHighlighting";
import { apiClient, ApiClientError } from "../src/api/client";

describe("Edge cases: appReducer state transitions", () => {
  it("GENERATION_STARTED should reset totalChunks and completedChunks to zero", () => {
    const stateWithProgress: AppState = {
      ...initialState,
      generationStatus: "completed",
      progress: 1.0,
      totalChunks: 5,
      completedChunks: 5,
    };
    const state = appReducer(stateWithProgress, {
      type: "GENERATION_STARTED",
      jobId: "new-job",
    });
    expect(state.totalChunks).toBe(0);
    expect(state.completedChunks).toBe(0);
    expect(state.progress).toBe(0);
  });

  it("GENERATION_FAILED should preserve other state fields", () => {
    const stateWithData: AppState = {
      ...initialState,
      text: "Some text",
      selectedProvider: "google",
      speed: 1.5,
    };
    const state = appReducer(stateWithData, {
      type: "GENERATION_FAILED",
      error: { code: "ERR", message: "Failed" },
    });
    expect(state.text).toBe("Some text");
    expect(state.selectedProvider).toBe("google");
    expect(state.speed).toBe(1.5);
  });

  it("PROVIDER_SELECTED should fallback to 1.0 speed if provider not in list", () => {
    const state = appReducer(initialState, {
      type: "PROVIDER_SELECTED",
      provider: "google",
    });
    // No providers loaded, so getDefaultSpeed should fallback to 1.0
    expect(state.speed).toBe(1.0);
  });

  it("multiple ERROR_SET calls should keep only the last error", () => {
    let state = appReducer(initialState, {
      type: "ERROR_SET",
      error: { code: "ERR1", message: "First" },
    });
    state = appReducer(state, {
      type: "ERROR_SET",
      error: { code: "ERR2", message: "Second" },
    });
    expect(state.error).toEqual({ code: "ERR2", message: "Second" });
  });

  it("SWITCH_TO_INPUT should stop playback but not clear audio URL", () => {
    const stateWithPlayback: AppState = {
      ...initialState,
      viewMode: "playback",
      isPlaying: true,
      audioUrl: "blob:test-url",
      currentTimeMs: 5000,
    };
    const state = appReducer(stateWithPlayback, { type: "SWITCH_TO_INPUT" });
    expect(state.isPlaying).toBe(false);
    expect(state.viewMode).toBe("input");
    // Audio URL should be preserved so user can switch back
    expect(state.audioUrl).toBe("blob:test-url");
  });

  it("PLAYBACK_ENDED should reset time to 0 but keep audioUrl", () => {
    const stateWithPlayback: AppState = {
      ...initialState,
      isPlaying: true,
      currentTimeMs: 5000,
      audioUrl: "blob:audio",
    };
    const state = appReducer(stateWithPlayback, { type: "PLAYBACK_ENDED" });
    expect(state.currentTimeMs).toBe(0);
    expect(state.isPlaying).toBe(false);
    expect(state.audioUrl).toBe("blob:audio");
  });
});

describe("Edge cases: findActiveTimingIndex binary search", () => {
  it("should handle large timing arrays efficiently", () => {
    // Generate 10000 timing entries
    const timings = Array.from({ length: 10000 }, (_, i) => ({
      start_ms: i * 100,
      end_ms: (i + 1) * 100,
    }));

    // Find the last entry
    expect(findActiveTimingIndex(timings, 999950)).toBe(9999);
    // Find the first entry
    expect(findActiveTimingIndex(timings, 0)).toBe(0);
    // Find a middle entry
    expect(findActiveTimingIndex(timings, 500050)).toBe(5000);
  });

  it("should return -1 when time is exactly at end_ms of last entry", () => {
    const timings = [
      { start_ms: 0, end_ms: 100 },
      { start_ms: 100, end_ms: 200 },
    ];
    // end_ms is exclusive, so time 200 is outside the last entry
    expect(findActiveTimingIndex(timings, 200)).toBe(-1);
  });

  it("should handle entries with gaps correctly", () => {
    const timings = [
      { start_ms: 0, end_ms: 100 },
      { start_ms: 500, end_ms: 600 },
      { start_ms: 1000, end_ms: 1100 },
    ];
    // In the gap between entries
    expect(findActiveTimingIndex(timings, 250)).toBe(-1);
    expect(findActiveTimingIndex(timings, 750)).toBe(-1);
    // On actual entries
    expect(findActiveTimingIndex(timings, 50)).toBe(0);
    expect(findActiveTimingIndex(timings, 550)).toBe(1);
    expect(findActiveTimingIndex(timings, 1050)).toBe(2);
  });

  it("should handle entries with zero duration", () => {
    const timings = [
      { start_ms: 0, end_ms: 0 },
      { start_ms: 100, end_ms: 200 },
    ];
    // A zero-duration entry: start_ms <= time < end_ms can never be true when start == end
    expect(findActiveTimingIndex(timings, 0)).toBe(-1);
    expect(findActiveTimingIndex(timings, 150)).toBe(1);
  });
});

describe("Edge cases: ApiClientError", () => {
  it("should be an instance of Error", () => {
    const err = new ApiClientError("TEST_CODE", "Test message", null, 400);
    expect(err).toBeInstanceOf(Error);
    expect(err.name).toBe("ApiClientError");
  });

  it("should preserve all properties", () => {
    const details = { field: "text" };
    const err = new ApiClientError("VALIDATION_ERROR", "Bad input", details, 422);
    expect(err.code).toBe("VALIDATION_ERROR");
    expect(err.message).toBe("Bad input");
    expect(err.details).toEqual(details);
    expect(err.httpStatus).toBe(422);
  });
});

describe("Edge cases: API client error path", () => {
  it("should use UNKNOWN_ERROR when error response has no error_code", async () => {
    server.use(
      http.get("/api/providers", () => {
        return HttpResponse.json(
          { message: "Something went wrong" },
          { status: 500 }
        );
      })
    );
    try {
      await apiClient.getProviders();
      expect.fail("Should have thrown");
    } catch (err: any) {
      expect(err.code).toBe("UNKNOWN_ERROR");
    }
  });

  it("should handle completely empty error response body", async () => {
    server.use(
      http.get("/api/providers", () => {
        return HttpResponse.json({}, { status: 503 });
      })
    );
    try {
      await apiClient.getProviders();
      expect.fail("Should have thrown");
    } catch (err: any) {
      expect(err.code).toBe("UNKNOWN_ERROR");
      expect(err.httpStatus).toBe(503);
    }
  });

  it("should include error details when present in response", async () => {
    server.use(
      http.get("/api/providers", () => {
        return HttpResponse.json(
          {
            error_code: "PROVIDER_ERROR",
            message: "Provider issue",
            details: { provider: "google", reason: "quota" },
          },
          { status: 502 }
        );
      })
    );
    try {
      await apiClient.getProviders();
      expect.fail("Should have thrown");
    } catch (err: any) {
      expect(err.details).toEqual({ provider: "google", reason: "quota" });
    }
  });
});
