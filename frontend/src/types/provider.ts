// Stub: Provider types - to be implemented by developer

export type ProviderName = "google" | "amazon" | "elevenlabs" | "openai";

export interface ProviderCapabilities {
  supports_speed_control: boolean;
  supports_word_timing: boolean;
  min_speed: number;
  max_speed: number;
  default_speed: number;
  max_chunk_chars: number;
}

export interface ProviderInfo {
  name: ProviderName;
  display_name: string;
  capabilities: ProviderCapabilities;
  is_configured: boolean;
}

export interface Voice {
  voice_id: string;
  name: string;
  language_code: string;
  language_name: string;
  gender: string | null;
  provider: ProviderName;
}
