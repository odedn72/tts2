// TDD: Written from spec 09-frontend-components.md
// Tests for the TextInputArea component

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

// This import will fail until implementation exists
import { TextInputArea } from "../../src/components/RightPanel/TextInputArea";

describe("TextInputArea", () => {
  const defaultProps = {
    text: "",
    onChange: vi.fn(),
    disabled: false,
  };

  it("should render a textarea", () => {
    render(<TextInputArea {...defaultProps} />);
    const textarea = screen.getByRole("textbox");
    expect(textarea).toBeTruthy();
  });

  it("should display placeholder text", () => {
    render(<TextInputArea {...defaultProps} />);
    const textarea = screen.getByPlaceholderText(/paste your text/i);
    expect(textarea).toBeTruthy();
  });

  it("should display the text value", () => {
    render(<TextInputArea {...defaultProps} text="Hello world" />);
    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
    expect(textarea.value).toBe("Hello world");
  });

  it("should call onChange when text is typed", () => {
    const onChange = vi.fn();
    render(<TextInputArea {...defaultProps} onChange={onChange} />);
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "New text" } });
    expect(onChange).toHaveBeenCalledWith("New text");
  });

  it("should be disabled when disabled prop is true", () => {
    render(<TextInputArea {...defaultProps} disabled={true} />);
    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
    expect(textarea.disabled).toBe(true);
  });

  it("should accept long text", () => {
    const longText = "word ".repeat(10000);
    render(<TextInputArea {...defaultProps} text={longText} />);
    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
    expect(textarea.value.length).toBeGreaterThan(40000);
  });
});
