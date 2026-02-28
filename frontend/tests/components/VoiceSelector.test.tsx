// TDD: Written from spec 09-frontend-components.md
// Tests for the VoiceSelector component

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

// This import will fail until implementation exists
import { VoiceSelector } from "../../src/components/LeftPanel/VoiceSelector";
import { mockVoices } from "../mocks/handlers";

describe("VoiceSelector", () => {
  const defaultProps = {
    voices: mockVoices,
    selectedVoice: null,
    onSelect: vi.fn(),
    loading: false,
    disabled: false,
  };

  it("should render a select element", () => {
    render(<VoiceSelector {...defaultProps} />);
    const select = screen.getByRole("combobox") || screen.getByLabelText(/voice/i);
    expect(select).toBeTruthy();
  });

  it("should display voice names with language", () => {
    render(<VoiceSelector {...defaultProps} />);
    expect(screen.getByText(/Neural2-A/)).toBeTruthy();
  });

  it("should be disabled when disabled prop is true", () => {
    render(<VoiceSelector {...defaultProps} disabled={true} />);
    const select = screen.getByRole("combobox") || screen.getByLabelText(/voice/i);
    expect((select as HTMLSelectElement).disabled).toBe(true);
  });

  it("should show loading state", () => {
    render(<VoiceSelector {...defaultProps} loading={true} />);
    // Should show a loading indicator
    const loadingElements = screen.queryAllByText(/loading/i);
    expect(
      loadingElements.length > 0 ||
      screen.getByRole("combobox")?.getAttribute("disabled")
    ).toBeTruthy();
  });

  it("should call onSelect when voice is chosen", () => {
    const onSelect = vi.fn();
    render(<VoiceSelector {...defaultProps} onSelect={onSelect} />);
    const select = screen.getByRole("combobox") || screen.getByLabelText(/voice/i);
    fireEvent.change(select, { target: { value: "en-US-Neural2-A" } });
    expect(onSelect).toHaveBeenCalled();
  });

  it("should handle empty voices list", () => {
    render(<VoiceSelector {...defaultProps} voices={[]} />);
    // Should show some placeholder or empty state
    const select = screen.getByRole("combobox") || screen.getByLabelText(/voice/i);
    expect(select).toBeTruthy();
  });
});
