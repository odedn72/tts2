/**
 * Displays an estimated API cost below the Generate button,
 * based on provider, voice type, and text length.
 */

import type { ProviderName, Voice } from "../../types/provider";

interface CostEstimateProps {
  text: string;
  provider: ProviderName | null;
  voice: Voice | null;
}

/** Cost per 1 million characters, keyed by provider then voice-type keyword. */
const PRICING: Record<string, Record<string, number>> = {
  google: {
    standard: 4,
    wavenet: 16,
    neural2: 16,
    news: 16,
    polyglot: 16,
    "chirp-hd": 30,
    "chirp3-hd": 30,
    casual: 30,
    studio: 160,
  },
  amazon: {
    standard: 4,
    neural: 16,
    long_form: 16,
    generative: 16,
  },
  openai: {
    "tts-1": 15,
    "tts-1-hd": 30,
  },
  elevenlabs: {
    _default: 300,
  },
};

/** Default rate per provider when voice type can't be matched. */
const PROVIDER_DEFAULTS: Record<string, number> = {
  google: 16,
  amazon: 4,
  openai: 15,
  elevenlabs: 300,
};

/**
 * Extract the voice type keyword from a Google voice_id.
 * e.g. "en-US-Neural2-A" → "neural2", "en-US-Chirp3-HD-A" → "chirp3-hd"
 */
function extractGoogleVoiceType(voiceId: string): string {
  const parts = voiceId.split("-");
  // Typical format: lang-REGION-Type[-Subtype]-Variant
  // Slice off first two (lang, region) and last (variant letter)
  return parts.slice(2, -1).join("-").toLowerCase();
}

function getRate(provider: ProviderName, voice: Voice): number {
  const providerPricing = PRICING[provider];
  if (!providerPricing) return 0;

  if (provider === "elevenlabs") {
    return providerPricing._default;
  }

  if (provider === "google") {
    const voiceType = extractGoogleVoiceType(voice.voice_id);
    if (providerPricing[voiceType] !== undefined) {
      return providerPricing[voiceType];
    }
    return PROVIDER_DEFAULTS[provider];
  }

  if (provider === "amazon") {
    // Amazon voice names often include engine info; check voice_id or name
    const id = voice.voice_id.toLowerCase();
    const name = voice.name.toLowerCase();
    for (const key of Object.keys(providerPricing)) {
      if (id.includes(key) || name.includes(key)) {
        return providerPricing[key];
      }
    }
    return PROVIDER_DEFAULTS[provider];
  }

  if (provider === "openai") {
    // OpenAI voice_id may encode the model (tts-1, tts-1-hd)
    const id = voice.voice_id.toLowerCase();
    if (id.includes("hd")) {
      return providerPricing["tts-1-hd"];
    }
    return providerPricing["tts-1"];
  }

  return PROVIDER_DEFAULTS[provider] ?? 0;
}

function formatCost(cost: number): string {
  if (cost >= 0.01) {
    return `$${cost.toFixed(2)}`;
  }
  return "< $0.01";
}

export function CostEstimate({ text, provider, voice }: CostEstimateProps): JSX.Element | null {
  if (!provider || !voice || !text.length) {
    return null;
  }

  const rate = getRate(provider, voice);
  if (rate === 0) return null;

  const cost = (text.length / 1_000_000) * rate;
  const label = cost > 0 ? formatCost(cost) : null;
  if (!label) return null;

  return (
    <div className="cost-estimate" data-testid="cost-estimate">
      Estimated cost: {label}
    </div>
  );
}
