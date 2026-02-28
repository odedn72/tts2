// TDD: Written from spec 09-frontend-components.md
// Tests for the SpeedControl component

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

// This import will fail until implementation exists
import { SpeedControl } from "../../src/components/LeftPanel/SpeedControl";

describe("SpeedControl", () => {
  const defaultProps = {
    speed: 1.0,
    min: 0.25,
    max: 4.0,
    onChange: vi.fn(),
    disabled: false,
    visible: true,
  };

  it("should render a range input when visible", () => {
    render(<SpeedControl {...defaultProps} />);
    const slider = screen.getByRole("slider");
    expect(slider).toBeTruthy();
  });

  it("should not render when visible is false", () => {
    const { container } = render(<SpeedControl {...defaultProps} visible={false} />);
    // Component should be hidden or not rendered
    const slider = container.querySelector("input[type='range']");
    expect(slider).toBeNull();
  });

  it("should display current speed value", () => {
    render(<SpeedControl {...defaultProps} speed={1.5} />);
    expect(screen.getByText(/1\.5/)).toBeTruthy();
  });

  it("should call onChange when slider moves", () => {
    const onChange = vi.fn();
    render(<SpeedControl {...defaultProps} onChange={onChange} />);
    const slider = screen.getByRole("slider");
    fireEvent.change(slider, { target: { value: "2.0" } });
    expect(onChange).toHaveBeenCalled();
  });

  it("should have correct min and max attributes", () => {
    render(<SpeedControl {...defaultProps} min={0.5} max={2.0} />);
    const slider = screen.getByRole("slider") as HTMLInputElement;
    expect(slider.min).toBe("0.5");
    expect(slider.max).toBe("2.0");
  });

  it("should be disabled when disabled prop is true", () => {
    render(<SpeedControl {...defaultProps} disabled={true} />);
    const slider = screen.getByRole("slider") as HTMLInputElement;
    expect(slider.disabled).toBe(true);
  });

  it("should display speed with x suffix", () => {
    render(<SpeedControl {...defaultProps} speed={1.0} />);
    expect(screen.getByText(/1\.0x|1x/)).toBeTruthy();
  });
});
