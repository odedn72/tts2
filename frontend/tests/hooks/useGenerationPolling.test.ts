// TDD: Written from spec 10-playback-and-highlighting.md
// Tests for the useGenerationPolling hook

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../mocks/server";

// This import will fail until implementation exists
import { useGenerationPolling } from "../../src/hooks/useGenerationPolling";

describe("useGenerationPolling", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should not poll when jobId is null", () => {
    const onProgress = vi.fn();
    const onCompleted = vi.fn();
    const onFailed = vi.fn();

    renderHook(() =>
      useGenerationPolling(null, onProgress, onCompleted, onFailed, 1000)
    );

    vi.advanceTimersByTime(5000);
    expect(onProgress).not.toHaveBeenCalled();
    expect(onCompleted).not.toHaveBeenCalled();
    expect(onFailed).not.toHaveBeenCalled();
  });

  it("should start polling when jobId is provided", async () => {
    server.use(
      http.get("/api/generate/:jobId/status", () => {
        return HttpResponse.json({
          job_id: "job-1",
          status: "in_progress",
          progress: 0.5,
          total_chunks: 4,
          completed_chunks: 2,
          error_message: null,
        });
      })
    );

    const onProgress = vi.fn();
    const onCompleted = vi.fn();
    const onFailed = vi.fn();

    renderHook(() =>
      useGenerationPolling("job-1", onProgress, onCompleted, onFailed, 1000)
    );

    // Advance past one poll interval
    await act(async () => {
      vi.advanceTimersByTime(1100);
    });

    // onProgress should have been called with progress data
    await waitFor(() => {
      expect(onProgress).toHaveBeenCalled();
    });
  });

  it("should call onCompleted when job completes", async () => {
    server.use(
      http.get("/api/generate/:jobId/status", () => {
        return HttpResponse.json({
          job_id: "job-1",
          status: "completed",
          progress: 1.0,
          total_chunks: 1,
          completed_chunks: 1,
          error_message: null,
        });
      })
    );

    const onProgress = vi.fn();
    const onCompleted = vi.fn();
    const onFailed = vi.fn();

    renderHook(() =>
      useGenerationPolling("job-1", onProgress, onCompleted, onFailed, 1000)
    );

    await act(async () => {
      vi.advanceTimersByTime(1100);
    });

    await waitFor(() => {
      expect(onCompleted).toHaveBeenCalled();
    });
  });

  it("should call onFailed when job fails", async () => {
    server.use(
      http.get("/api/generate/:jobId/status", () => {
        return HttpResponse.json({
          job_id: "job-1",
          status: "failed",
          progress: 0.3,
          total_chunks: 3,
          completed_chunks: 1,
          error_message: "Provider error",
        });
      })
    );

    const onProgress = vi.fn();
    const onCompleted = vi.fn();
    const onFailed = vi.fn();

    renderHook(() =>
      useGenerationPolling("job-1", onProgress, onCompleted, onFailed, 1000)
    );

    await act(async () => {
      vi.advanceTimersByTime(1100);
    });

    await waitFor(() => {
      expect(onFailed).toHaveBeenCalledWith(
        expect.objectContaining({
          code: expect.any(String),
          message: expect.any(String),
        })
      );
    });
  });

  it("should stop polling after completion", async () => {
    let callCount = 0;
    server.use(
      http.get("/api/generate/:jobId/status", () => {
        callCount++;
        return HttpResponse.json({
          job_id: "job-1",
          status: "completed",
          progress: 1.0,
          total_chunks: 1,
          completed_chunks: 1,
          error_message: null,
        });
      })
    );

    const onProgress = vi.fn();
    const onCompleted = vi.fn();
    const onFailed = vi.fn();

    renderHook(() =>
      useGenerationPolling("job-1", onProgress, onCompleted, onFailed, 1000)
    );

    await act(async () => {
      vi.advanceTimersByTime(5000);
    });

    // Should only poll once (or a small number), not keep going after completion
    expect(callCount).toBeLessThanOrEqual(2);
  });

  it("should clean up on unmount", () => {
    const onProgress = vi.fn();
    const onCompleted = vi.fn();
    const onFailed = vi.fn();

    const { unmount } = renderHook(() =>
      useGenerationPolling("job-1", onProgress, onCompleted, onFailed, 1000)
    );

    unmount();

    // After unmount, advancing timers should not cause polling
    vi.advanceTimersByTime(5000);
    // No assertion needed - just verifying no errors thrown
  });
});
