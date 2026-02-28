// TDD: Written from spec 09-frontend-components.md
// Tests for the ProgressIndicator component

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// This import will fail until implementation exists
import { ProgressIndicator } from "../../src/components/RightPanel/ProgressIndicator";

describe("ProgressIndicator", () => {
  const defaultProps = {
    progress: 0.6,
    totalChunks: 5,
    completedChunks: 3,
    visible: true,
  };

  it("should render when visible", () => {
    const { container } = render(<ProgressIndicator {...defaultProps} />);
    expect(container.firstChild).toBeTruthy();
  });

  it("should not render when not visible", () => {
    const { container } = render(
      <ProgressIndicator {...defaultProps} visible={false} />
    );
    expect(container.firstChild === null || container.innerHTML === "").toBeTruthy();
  });

  it("should display progress percentage", () => {
    render(<ProgressIndicator {...defaultProps} />);
    expect(screen.getByText(/60%/)).toBeTruthy();
  });

  it("should display chunk progress", () => {
    render(<ProgressIndicator {...defaultProps} />);
    // Should show "3 of 5" or similar
    expect(screen.getByText(/3/)).toBeTruthy();
    expect(screen.getByText(/5/)).toBeTruthy();
  });

  it("should have a progress bar element", () => {
    const { container } = render(<ProgressIndicator {...defaultProps} />);
    const progressBar =
      container.querySelector("[role='progressbar']") ||
      container.querySelector("progress") ||
      container.querySelector("[class*='progress']");
    expect(progressBar).toBeTruthy();
  });

  it("should show 100% when complete", () => {
    render(
      <ProgressIndicator
        progress={1.0}
        totalChunks={5}
        completedChunks={5}
        visible={true}
      />
    );
    expect(screen.getByText(/100%/)).toBeTruthy();
  });

  it("should show 0% at start", () => {
    render(
      <ProgressIndicator
        progress={0}
        totalChunks={5}
        completedChunks={0}
        visible={true}
      />
    );
    expect(screen.getByText(/0%/)).toBeTruthy();
  });
});
