// TDD: Written from spec 09-frontend-components.md
// Tests for the AppShell two-panel layout component

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

import { AppShell } from "../../src/components/AppShell";
import { AppProvider } from "../../src/state/AppContext";

// Wrapper with context provider
function renderWithProvider(ui: React.ReactElement) {
  return render(<AppProvider>{ui}</AppProvider>);
}

describe("AppShell", () => {
  it("should render without crashing", () => {
    renderWithProvider(<AppShell />);
  });

  it("should contain a left panel", () => {
    const { container } = renderWithProvider(<AppShell />);
    const leftPanel = container.querySelector(".left-panel, [data-testid='left-panel']");
    expect(leftPanel).toBeTruthy();
  });

  it("should contain a right panel", () => {
    const { container } = renderWithProvider(<AppShell />);
    const rightPanel = container.querySelector(".right-panel, [data-testid='right-panel']");
    expect(rightPanel).toBeTruthy();
  });

  it("should have dark theme background", () => {
    const { container } = renderWithProvider(<AppShell />);
    const shell = container.firstChild as HTMLElement;
    // The element should have the app-shell class for dark theme styling
    expect(
      shell?.classList.contains("app-shell") ||
      shell?.getAttribute("data-testid") === "app-shell"
    ).toBeTruthy();
  });

  it("should display the app title", () => {
    renderWithProvider(<AppShell />);
    expect(screen.getByText(/TTS Reader/i)).toBeTruthy();
  });
});
