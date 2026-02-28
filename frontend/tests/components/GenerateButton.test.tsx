// TDD: Written from spec 09-frontend-components.md
// Tests for the GenerateButton component

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

// This import will fail until implementation exists
import { GenerateButton } from "../../src/components/LeftPanel/GenerateButton";

describe("GenerateButton", () => {
  const defaultProps = {
    onClick: vi.fn(),
    disabled: false,
    loading: false,
  };

  it("should render a button", () => {
    render(<GenerateButton {...defaultProps} />);
    const button = screen.getByRole("button");
    expect(button).toBeTruthy();
  });

  it("should display Generate Audio text", () => {
    render(<GenerateButton {...defaultProps} />);
    expect(screen.getByText(/generate/i)).toBeTruthy();
  });

  it("should call onClick when clicked", () => {
    const onClick = vi.fn();
    render(<GenerateButton {...defaultProps} onClick={onClick} />);
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("should be disabled when disabled prop is true", () => {
    render(<GenerateButton {...defaultProps} disabled={true} />);
    const button = screen.getByRole("button") as HTMLButtonElement;
    expect(button.disabled).toBe(true);
  });

  it("should show loading state during generation", () => {
    render(<GenerateButton {...defaultProps} loading={true} />);
    // Should show loading indicator or different text
    const button = screen.getByRole("button");
    expect(
      button.textContent?.includes("Generating") ||
      button.textContent?.includes("...") ||
      button.querySelector("[class*='spinner']") !== null ||
      (button as HTMLButtonElement).disabled
    ).toBeTruthy();
  });

  it("should not call onClick when disabled", () => {
    const onClick = vi.fn();
    render(<GenerateButton {...defaultProps} onClick={onClick} disabled={true} />);
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).not.toHaveBeenCalled();
  });
});
