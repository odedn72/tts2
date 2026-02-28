// TDD: Written from spec 09-frontend-components.md
// Tests for the AudioPlayer component

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

// This import will fail until implementation exists
import { AudioPlayer } from "../../src/components/RightPanel/AudioPlayer";

describe("AudioPlayer", () => {
  const defaultProps = {
    audioUrl: "blob:test-audio-url",
    onPlay: vi.fn(),
    onPause: vi.fn(),
    onTimeUpdate: vi.fn(),
    onEnded: vi.fn(),
    onSeek: vi.fn(),
    isPlaying: false,
  };

  it("should render when audioUrl is provided", () => {
    const { container } = render(<AudioPlayer {...defaultProps} />);
    expect(container.firstChild).toBeTruthy();
  });

  it("should not render when audioUrl is null", () => {
    const { container } = render(<AudioPlayer {...defaultProps} audioUrl={null} />);
    // Component should be hidden or not render content
    const buttons = screen.queryAllByRole("button");
    // Should have no play/pause button when no audio
    expect(buttons.length === 0 || container.firstChild === null || container.innerHTML === "").toBeTruthy();
  });

  it("should show play button when not playing", () => {
    render(<AudioPlayer {...defaultProps} isPlaying={false} />);
    const playButton = screen.getByRole("button", { name: /play/i });
    expect(playButton).toBeTruthy();
  });

  it("should show pause button when playing", () => {
    render(<AudioPlayer {...defaultProps} isPlaying={true} />);
    const pauseButton = screen.getByRole("button", { name: /pause/i });
    expect(pauseButton).toBeTruthy();
  });

  it("should call onPlay when play is clicked", () => {
    const onPlay = vi.fn();
    render(<AudioPlayer {...defaultProps} onPlay={onPlay} isPlaying={false} />);
    fireEvent.click(screen.getByRole("button", { name: /play/i }));
    expect(onPlay).toHaveBeenCalledOnce();
  });

  it("should call onPause when pause is clicked", () => {
    const onPause = vi.fn();
    render(<AudioPlayer {...defaultProps} onPause={onPause} isPlaying={true} />);
    fireEvent.click(screen.getByRole("button", { name: /pause/i }));
    expect(onPause).toHaveBeenCalledOnce();
  });

  it("should include a download button", () => {
    render(<AudioPlayer {...defaultProps} />);
    const downloadBtn = screen.getByRole("button", { name: /download/i }) ||
                        screen.getByRole("link", { name: /download/i });
    expect(downloadBtn).toBeTruthy();
  });

  it("should include a seek bar", () => {
    const { container } = render(<AudioPlayer {...defaultProps} />);
    const seekBar = container.querySelector("input[type='range']") ||
                    container.querySelector("[role='slider']");
    expect(seekBar).toBeTruthy();
  });

  it("should contain a hidden audio element", () => {
    const { container } = render(<AudioPlayer {...defaultProps} />);
    const audio = container.querySelector("audio");
    expect(audio).toBeTruthy();
  });
});
