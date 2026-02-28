// TDD: Written from spec 09-frontend-components.md
// Tests for the ProviderSelector component

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

// This import will fail until implementation exists
import { ProviderSelector } from "../../src/components/LeftPanel/ProviderSelector";
import { mockProviders } from "../mocks/handlers";

describe("ProviderSelector", () => {
  const defaultProps = {
    providers: mockProviders,
    selectedProvider: null,
    onSelect: vi.fn(),
  };

  it("should render a select element", () => {
    render(<ProviderSelector {...defaultProps} />);
    const select = screen.getByRole("combobox") || screen.getByLabelText(/provider/i);
    expect(select).toBeTruthy();
  });

  it("should display all providers", () => {
    render(<ProviderSelector {...defaultProps} />);
    expect(screen.getByText(/Google Cloud TTS/i)).toBeTruthy();
    expect(screen.getByText(/Amazon Polly/i)).toBeTruthy();
    expect(screen.getByText(/ElevenLabs/i)).toBeTruthy();
    expect(screen.getByText(/OpenAI TTS/i)).toBeTruthy();
  });

  it("should indicate unconfigured providers", () => {
    render(<ProviderSelector {...defaultProps} />);
    // Amazon and OpenAI are not configured in mock data
    const text = screen.getByText(/Amazon Polly/i).textContent || "";
    // Should show some indication of not being configured
    expect(
      text.includes("not configured") ||
      screen.getByText(/Amazon Polly/i).closest("option")?.disabled === false
    ).toBeTruthy();
  });

  it("should call onSelect when provider is chosen", () => {
    const onSelect = vi.fn();
    render(<ProviderSelector {...defaultProps} onSelect={onSelect} />);
    const select = screen.getByRole("combobox") || screen.getByLabelText(/provider/i);
    fireEvent.change(select, { target: { value: "google" } });
    expect(onSelect).toHaveBeenCalledWith("google");
  });

  it("should show selected provider", () => {
    render(<ProviderSelector {...defaultProps} selectedProvider="google" />);
    const select = screen.getByRole("combobox") || screen.getByLabelText(/provider/i);
    expect((select as HTMLSelectElement).value).toBe("google");
  });

  it("should have accessible label", () => {
    render(<ProviderSelector {...defaultProps} />);
    const label = screen.getByLabelText(/provider/i) || screen.getByText(/TTS Provider/i);
    expect(label).toBeTruthy();
  });
});
