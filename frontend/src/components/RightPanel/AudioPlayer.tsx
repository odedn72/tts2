/**
 * Custom audio player controls with play/pause, seek bar, time display, and download.
 * Uses a hidden <audio> element for actual playback.
 * Uses requestAnimationFrame for ~60fps time updates (smooth highlighting).
 */

import React, { useRef, useState, useEffect, useCallback } from "react";

/** Props for the AudioPlayer component. */
interface AudioPlayerProps {
  /** Object URL for the audio blob, or null if no audio */
  audioUrl: string | null;
  /** Callback when play is triggered */
  onPlay: () => void;
  /** Callback when pause is triggered */
  onPause: () => void;
  /** Callback for time updates during playback */
  onTimeUpdate: (timeMs: number) => void;
  /** Callback when playback reaches the end */
  onEnded: () => void;
  /** Callback when user seeks to a position */
  onSeek: (timeMs: number) => void;
  /** Whether audio is currently playing */
  isPlaying: boolean;
  /** Playback speed multiplier */
  speed?: number;
}

/** Format milliseconds as "M:SS" */
function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

/**
 * Renders custom audio controls: play/pause button, seek bar, time display, and download link.
 * Hidden entirely when no audio URL is provided.
 */
export function AudioPlayer({
  audioUrl,
  onPlay,
  onPause,
  onTimeUpdate,
  onEnded,
  onSeek,
  isPlaying,
  speed = 1.0,
}: AudioPlayerProps): JSX.Element | null {
  const audioRef = useRef<HTMLAudioElement>(null);
  const rafRef = useRef<number>(0);
  const [currentTimeMs, setCurrentTimeMs] = useState(0);
  const [durationMs, setDurationMs] = useState(0);

  // Sync playback rate with speed prop
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = speed;
    }
  }, [speed]);

  // rAF loop for smooth ~60fps time updates during playback
  const tick = useCallback(() => {
    const audio = audioRef.current;
    if (audio && !audio.paused) {
      const timeMs = Math.round(audio.currentTime * 1000);
      setCurrentTimeMs(timeMs);
      onTimeUpdate(timeMs);
      rafRef.current = requestAnimationFrame(tick);
    }
  }, [onTimeUpdate]);

  useEffect(() => {
    if (isPlaying) {
      rafRef.current = requestAnimationFrame(tick);
    }
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [isPlaying, tick]);

  if (!audioUrl) {
    return null;
  }

  const handlePlayPause = (): void => {
    if (isPlaying) {
      onPause();
      audioRef.current?.pause();
    } else {
      onPlay();
      const result = audioRef.current?.play();
      if (result && typeof result.catch === "function") {
        result.catch(() => {
          // Autoplay blocked by browser -- ignore silently
        });
      }
    }
  };

  const handleSeek = (
    e: React.ChangeEvent<HTMLInputElement>
  ): void => {
    const timeMs = parseFloat(e.target.value);
    setCurrentTimeMs(timeMs);
    onSeek(timeMs);
    if (audioRef.current) {
      audioRef.current.currentTime = timeMs / 1000;
    }
  };

  const handleLoadedMetadata = (): void => {
    if (audioRef.current && isFinite(audioRef.current.duration)) {
      setDurationMs(Math.round(audioRef.current.duration * 1000));
    }
  };

  const handleDownload = (): void => {
    if (audioUrl) {
      const link = document.createElement("a");
      link.href = audioUrl;
      link.download = "tts-audio.mp3";
      link.click();
    }
  };

  return (
    <div className="audio-player">
      <audio
        ref={audioRef}
        src={audioUrl}
        onEnded={onEnded}
        onLoadedMetadata={handleLoadedMetadata}
        preload="metadata"
      />

      <button
        className="play-pause-button"
        onClick={handlePlayPause}
        type="button"
        aria-label={isPlaying ? "Pause" : "Play"}
      >
        {isPlaying ? "Pause" : "Play"}
      </button>

      <span className="time-display" aria-label="Time">
        {formatTime(currentTimeMs)} / {formatTime(durationMs)}
      </span>

      <input
        type="range"
        className="seek-bar"
        min={0}
        max={durationMs || 1}
        step={100}
        value={currentTimeMs}
        onChange={handleSeek}
        aria-label="Seek"
      />

      <button
        className="download-button"
        onClick={handleDownload}
        type="button"
        aria-label="Download"
      >
        Download
      </button>
    </div>
  );
}
