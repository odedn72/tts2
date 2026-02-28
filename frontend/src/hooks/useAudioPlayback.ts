/**
 * Custom hook for managing HTML5 audio playback.
 * Wraps a hidden <audio> element and exposes play/pause/seek controls
 * along with current time and duration state.
 */

import { useRef, useState, useEffect, useCallback } from "react";

/** Return type of the useAudioPlayback hook. */
export interface UseAudioPlaybackReturn {
  /** Ref to attach to a hidden <audio> element in the DOM */
  audioRef: React.RefObject<HTMLAudioElement | null>;
  /** Start playback */
  play: () => void;
  /** Pause playback */
  pause: () => void;
  /** Seek to a position in milliseconds */
  seek: (timeMs: number) => void;
  /** Current playback position in milliseconds */
  currentTimeMs: number;
  /** Total audio duration in milliseconds */
  duration: number;
  /** Whether audio is currently playing */
  isPlaying: boolean;
  /** Whether audio metadata has been loaded and is ready */
  isLoaded: boolean;
}

/**
 * Hook that manages an HTML5 audio element for TTS playback.
 *
 * @param audioUrl - Object URL for the audio blob, or null if no audio
 * @param onTimeUpdate - Callback fired with current time in ms during playback
 * @param onEnded - Callback fired when playback reaches the end
 * @returns Controls and state for audio playback
 */
export function useAudioPlayback(
  audioUrl: string | null,
  onTimeUpdate: (timeMs: number) => void,
  onEnded: () => void
): UseAudioPlaybackReturn {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isLoaded, setIsLoaded] = useState<boolean>(false);
  const [currentTimeMs, setCurrentTimeMs] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);

  // Set up audio source and event listeners when audioUrl changes
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !audioUrl) {
      setIsLoaded(false);
      setIsPlaying(false);
      setCurrentTimeMs(0);
      setDuration(0);
      return;
    }

    audio.src = audioUrl;
    audio.load();

    const handleLoadedMetadata = (): void => {
      setDuration(Math.round(audio.duration * 1000));
      setIsLoaded(true);
    };

    const handleTimeUpdate = (): void => {
      const timeMs = Math.round(audio.currentTime * 1000);
      setCurrentTimeMs(timeMs);
      onTimeUpdate(timeMs);
    };

    const handleEnded = (): void => {
      setIsPlaying(false);
      setCurrentTimeMs(0);
      onEnded();
    };

    const handlePlay = (): void => {
      setIsPlaying(true);
    };

    const handlePause = (): void => {
      setIsPlaying(false);
    };

    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);

    return () => {
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);
    };
  }, [audioUrl, onTimeUpdate, onEnded]);

  /** Start audio playback. */
  const play = useCallback((): void => {
    const audio = audioRef.current;
    if (audio) {
      audio.play().catch(() => {
        // Autoplay may be blocked by browser -- ignore silently
      });
    }
  }, []);

  /** Pause audio playback. */
  const pause = useCallback((): void => {
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
    }
  }, []);

  /** Seek to a specific time in milliseconds. */
  const seek = useCallback((timeMs: number): void => {
    const audio = audioRef.current;
    if (audio) {
      audio.currentTime = timeMs / 1000;
      setCurrentTimeMs(timeMs);
    }
  }, []);

  return {
    audioRef,
    play,
    pause,
    seek,
    currentTimeMs,
    duration,
    isPlaying,
    isLoaded,
  };
}
