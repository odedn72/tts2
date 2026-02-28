/**
 * Custom hook for polling TTS generation job status.
 * Periodically checks the backend for progress updates until the job
 * completes, fails, or the component unmounts.
 */

import { useEffect, useRef } from "react";
import { apiClient } from "../api/client";
import type { AudioMetadata } from "../types/audio";

/**
 * Polls the backend for generation job status at a configurable interval.
 * Automatically stops polling when the job completes or fails.
 * Cleans up on unmount to prevent memory leaks.
 *
 * @param jobId - The job ID to poll, or null to skip polling
 * @param onProgress - Callback for progress updates (progress, total, completed)
 * @param onCompleted - Callback when generation finishes successfully
 * @param onFailed - Callback when generation fails
 * @param pollIntervalMs - Milliseconds between poll attempts (default 1000)
 */
export function useGenerationPolling(
  jobId: string | null,
  onProgress: (progress: number, total: number, completed: number) => void,
  onCompleted: (metadata: AudioMetadata) => void,
  onFailed: (error: { code: string; message: string }) => void,
  pollIntervalMs: number = 1000
): void {
  // Store latest callbacks in refs to avoid restarting the interval
  const onProgressRef = useRef(onProgress);
  const onCompletedRef = useRef(onCompleted);
  const onFailedRef = useRef(onFailed);

  onProgressRef.current = onProgress;
  onCompletedRef.current = onCompleted;
  onFailedRef.current = onFailed;

  useEffect(() => {
    if (!jobId) {
      return;
    }

    let cancelled = false;
    let polling = false;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    /** Stop the polling interval immediately. */
    function stopPolling(): void {
      cancelled = true;
      if (intervalId !== null) {
        clearInterval(intervalId);
        intervalId = null;
      }
    }

    const poll = (): void => {
      if (cancelled || polling) return;
      polling = true;

      apiClient
        .getJobStatus(jobId)
        .then((status) => {
          if (cancelled) return;

          if (
            status.status === "in_progress" ||
            status.status === "pending"
          ) {
            polling = false;
            onProgressRef.current(
              status.progress,
              status.total_chunks,
              status.completed_chunks
            );
          } else if (status.status === "completed") {
            stopPolling();
            // Fetch audio metadata, then call onCompleted
            apiClient
              .getAudioMetadata(jobId)
              .then((metadata) => {
                onCompletedRef.current(metadata);
              })
              .catch(() => {
                // If metadata fetch fails, still signal completion
                // with a minimal metadata object
                onCompletedRef.current({
                  job_id: jobId,
                  duration_ms: 0,
                  format: "mp3",
                  size_bytes: 0,
                  timing: {
                    timing_type: "word",
                    words: [],
                    sentences: null,
                  },
                });
              });
          } else if (status.status === "failed") {
            stopPolling();
            onFailedRef.current({
              code: "GENERATION_FAILED",
              message: status.error_message || "Generation failed",
            });
          }
        })
        .catch(() => {
          if (cancelled) return;
          stopPolling();
          onFailedRef.current({
            code: "POLLING_ERROR",
            message: "Failed to check generation status",
          });
        });
    };

    intervalId = setInterval(poll, pollIntervalMs);

    return () => {
      stopPolling();
    };
  }, [jobId, pollIntervalMs]);
}
