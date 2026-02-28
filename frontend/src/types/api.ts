// Stub: API types - to be implemented by developer

import type { ProviderName, ProviderInfo, Voice } from "./provider";
import type { GenerationStatus, AudioMetadata } from "./audio";

export interface GenerateRequest {
  provider: ProviderName;
  voice_id: string;
  text: string;
  speed: number;
}

export interface GenerateResponse {
  job_id: string;
  status: GenerationStatus;
}

export interface JobStatusResponse {
  job_id: string;
  status: GenerationStatus;
  progress: number;
  total_chunks: number;
  completed_chunks: number;
  error_message: string | null;
}

export interface VoiceListResponse {
  provider: ProviderName;
  voices: Voice[];
}

export interface ProviderKeyStatus {
  provider: ProviderName;
  is_configured: boolean;
}

export interface SettingsResponse {
  providers: ProviderKeyStatus[];
}

export interface UpdateSettingsRequest {
  provider: ProviderName;
  api_key: string;
}

export interface ApiError {
  error_code: string;
  message: string;
  details: Record<string, unknown> | null;
}
