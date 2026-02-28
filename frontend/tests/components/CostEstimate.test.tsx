import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

import { CostEstimate } from "../../src/components/LeftPanel/CostEstimate";
import type { ProviderName, Voice } from "../../src/types/provider";

function makeVoice(overrides: Partial<Voice> & { voice_id: string; provider: ProviderName }): Voice {
  return {
    name: "Test Voice",
    language_code: "en-US",
    language_name: "English (US)",
    gender: "FEMALE",
    ...overrides,
  };
}

describe("CostEstimate", () => {
  // --- Renders nothing when inputs are incomplete ---

  it("should render nothing when provider is null", () => {
    const voice = makeVoice({ voice_id: "en-US-Standard-A", provider: "google" });
    const { container } = render(
      <CostEstimate text="hello" provider={null} voice={voice} />
    );
    expect(container.innerHTML).toBe("");
  });

  it("should render nothing when voice is null", () => {
    const { container } = render(
      <CostEstimate text="hello" provider="google" voice={null} />
    );
    expect(container.innerHTML).toBe("");
  });

  it("should render nothing when text is empty", () => {
    const voice = makeVoice({ voice_id: "en-US-Standard-A", provider: "google" });
    const { container } = render(
      <CostEstimate text="" provider="google" voice={voice} />
    );
    expect(container.innerHTML).toBe("");
  });

  // --- Google voice types ---

  it("should compute cost for Google Standard voice", () => {
    const voice = makeVoice({ voice_id: "en-US-Standard-A", provider: "google" });
    // 1000 chars at $4/1M = $0.004 → "< $0.01"
    render(<CostEstimate text={"a".repeat(1000)} provider="google" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("< $0.01");
  });

  it("should compute cost for Google Standard voice at scale", () => {
    const voice = makeVoice({ voice_id: "en-US-Standard-A", provider: "google" });
    // 100_000 chars at $4/1M = $0.40
    render(<CostEstimate text={"a".repeat(100_000)} provider="google" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("$0.40");
  });

  it("should compute cost for Google Neural2 voice", () => {
    const voice = makeVoice({ voice_id: "en-US-Neural2-A", provider: "google" });
    // 100_000 chars at $16/1M = $1.60
    render(<CostEstimate text={"a".repeat(100_000)} provider="google" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("$1.60");
  });

  it("should compute cost for Google WaveNet voice", () => {
    const voice = makeVoice({ voice_id: "en-US-Wavenet-D", provider: "google" });
    // 100_000 chars at $16/1M = $1.60
    render(<CostEstimate text={"a".repeat(100_000)} provider="google" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("$1.60");
  });

  it("should compute cost for Google Chirp3-HD voice", () => {
    const voice = makeVoice({ voice_id: "en-US-Chirp3-HD-A", provider: "google" });
    // 100_000 chars at $30/1M = $3.00
    render(<CostEstimate text={"a".repeat(100_000)} provider="google" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("$3.00");
  });

  it("should compute cost for Google Chirp-HD voice", () => {
    const voice = makeVoice({ voice_id: "en-US-Chirp-HD-B", provider: "google" });
    render(<CostEstimate text={"a".repeat(100_000)} provider="google" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("$3.00");
  });

  it("should compute cost for Google Studio voice", () => {
    const voice = makeVoice({ voice_id: "en-US-Studio-O", provider: "google" });
    // 100_000 chars at $160/1M = $16.00
    render(<CostEstimate text={"a".repeat(100_000)} provider="google" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("$16.00");
  });

  it("should fall back to default rate for unknown Google voice type", () => {
    const voice = makeVoice({ voice_id: "en-US-UnknownType-A", provider: "google" });
    // Default google = $16/1M → 100_000 chars = $1.60
    render(<CostEstimate text={"a".repeat(100_000)} provider="google" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("$1.60");
  });

  // --- Amazon Polly ---

  it("should compute cost for Amazon Standard voice", () => {
    const voice = makeVoice({
      voice_id: "Joanna",
      name: "Joanna (Standard)",
      provider: "amazon",
    });
    // 100_000 chars at $4/1M = $0.40
    render(<CostEstimate text={"a".repeat(100_000)} provider="amazon" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("$0.40");
  });

  it("should compute cost for Amazon Neural voice", () => {
    const voice = makeVoice({
      voice_id: "Joanna",
      name: "Joanna (Neural)",
      provider: "amazon",
    });
    // 100_000 chars at $16/1M = $1.60
    render(<CostEstimate text={"a".repeat(100_000)} provider="amazon" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("$1.60");
  });

  it("should fall back to default rate for Amazon voice with no type hint", () => {
    const voice = makeVoice({
      voice_id: "Joanna",
      name: "Joanna",
      provider: "amazon",
    });
    // Default amazon = $4/1M → 100_000 chars = $0.40
    render(<CostEstimate text={"a".repeat(100_000)} provider="amazon" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("$0.40");
  });

  // --- OpenAI ---

  it("should compute cost for OpenAI standard voice", () => {
    const voice = makeVoice({ voice_id: "alloy", provider: "openai" });
    // 100_000 chars at $15/1M = $1.50
    render(<CostEstimate text={"a".repeat(100_000)} provider="openai" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("$1.50");
  });

  it("should compute cost for OpenAI HD voice", () => {
    const voice = makeVoice({ voice_id: "alloy-hd", provider: "openai" });
    // 100_000 chars at $30/1M = $3.00
    render(<CostEstimate text={"a".repeat(100_000)} provider="openai" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("$3.00");
  });

  // --- ElevenLabs ---

  it("should compute cost for ElevenLabs voice", () => {
    const voice = makeVoice({ voice_id: "some-elevenlabs-id", provider: "elevenlabs" });
    // 100_000 chars at $300/1M = $30.00
    render(<CostEstimate text={"a".repeat(100_000)} provider="elevenlabs" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("$30.00");
  });

  // --- Formatting ---

  it("should show '< $0.01' for very small costs", () => {
    const voice = makeVoice({ voice_id: "en-US-Standard-A", provider: "google" });
    // 10 chars at $4/1M = $0.00004
    render(<CostEstimate text={"a".repeat(10)} provider="google" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("< $0.01");
  });

  it("should show dollar amount with two decimals for costs >= $0.01", () => {
    const voice = makeVoice({ voice_id: "en-US-Studio-O", provider: "google" });
    // 50_000 chars at $160/1M = $8.00
    render(<CostEstimate text={"a".repeat(50_000)} provider="google" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("$8.00");
  });

  it("should include 'Estimated cost:' label", () => {
    const voice = makeVoice({ voice_id: "alloy", provider: "openai" });
    render(<CostEstimate text={"a".repeat(100_000)} provider="openai" voice={voice} />);
    expect(screen.getByTestId("cost-estimate").textContent).toContain("Estimated cost:");
  });
});
