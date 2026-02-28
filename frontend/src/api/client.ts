/**
 * Typed API client for all backend communication.
 * All API calls go through this module for consistent error handling and typing.
 */

import type { ProviderName, ProviderInfo } from "../types/provider";
import type {
  GenerateRequest,
  GenerateResponse,
  JobStatusResponse,
  VoiceListResponse,
  SettingsResponse,
  UpdateSettingsRequest,
  ProviderKeyStatus,
} from "../types/api";
import type { AudioMetadata } from "../types/audio";

/**
 * Custom error class for API client errors.
 * Provides structured error information including HTTP status and error code.
 */
export class ApiClientError extends Error {
  constructor(
    public code: string,
    message: string,
    public details: Record<string, unknown> | null,
    public httpStatus: number
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

/** Base URL prefix for all API endpoints (proxied by Vite in dev). */
const BASE_URL = "/api";

/**
 * Generic JSON request helper. Sends a request and parses the JSON response.
 * Throws ApiClientError on non-OK responses with structured error details.
 */
async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`;

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorBody: {
      error_code?: string;
      message?: string;
      details?: Record<string, unknown>;
    } | null = null;
    try {
      errorBody = await response.json();
    } catch {
      // Response body is not JSON -- that is acceptable
    }

    throw new ApiClientError(
      errorBody?.error_code || "UNKNOWN_ERROR",
      errorBody?.message || `HTTP ${response.status}: ${response.statusText}`,
      errorBody?.details || null,
      response.status
    );
  }

  return response.json();
}

/**
 * Request helper for binary/blob responses (e.g., audio file download).
 * Throws ApiClientError on non-OK responses.
 */
async function requestBlob(path: string): Promise<Blob> {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new ApiClientError(
      "DOWNLOAD_ERROR",
      `Failed to download audio: HTTP ${response.status}`,
      null,
      response.status
    );
  }

  const arrayBuffer = await response.arrayBuffer();
  return new Blob([arrayBuffer], {
    type: response.headers.get("Content-Type") || "application/octet-stream",
  });
}

/**
 * The API client object with methods for every backend endpoint.
 * Components and hooks should use this exclusively -- never call fetch directly.
 */
export const apiClient = {
  /**
   * Fetch all available providers with capabilities and configuration status.
   */
  async getProviders(): Promise<{ providers: ProviderInfo[] }> {
    return request("/providers");
  },

  /**
   * Fetch available voices for a specific provider.
   */
  async getVoices(provider: ProviderName): Promise<VoiceListResponse> {
    return request("/voices", {
      method: "POST",
      body: JSON.stringify({ provider }),
    });
  },

  /**
   * Start a TTS generation job.
   */
  async startGeneration(req: GenerateRequest): Promise<GenerateResponse> {
    return request("/generate", {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  /**
   * Poll the status of a generation job.
   */
  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    return request(`/generate/${jobId}/status`);
  },

  /**
   * Get audio metadata and timing data for a completed job.
   */
  async getAudioMetadata(jobId: string): Promise<AudioMetadata> {
    return request(`/audio/${jobId}`);
  },

  /**
   * Download the audio file as a blob.
   */
  async getAudioFile(jobId: string): Promise<Blob> {
    return requestBlob(`/audio/${jobId}/file`);
  },

  /**
   * Get current settings (provider configuration status).
   */
  async getSettings(): Promise<SettingsResponse> {
    return request("/settings");
  },

  /**
   * Update a provider's API key.
   */
  async updateSettings(
    req: UpdateSettingsRequest
  ): Promise<ProviderKeyStatus> {
    return request("/settings", {
      method: "PUT",
      body: JSON.stringify(req),
    });
  },
};
