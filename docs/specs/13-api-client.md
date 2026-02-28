# 13 - Frontend API Client

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define the typed frontend API client that handles all communication with the
backend.

**MRD traceability:** All FR requirements that involve backend communication.

## API Client

```typescript
// api/client.ts

import type {
  ProviderName,
  ProviderInfo,
  Voice,
} from "../types/provider";
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


class ApiClientError extends Error {
  constructor(
    public code: string,
    message: string,
    public details: Record<string, unknown> | null,
    public httpStatus: number,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}


const BASE_URL = "/api";


async function request<T>(
  path: string,
  options: RequestInit = {},
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
    let errorBody: { error_code?: string; message?: string; details?: Record<string, unknown> } | null = null;
    try {
      errorBody = await response.json();
    } catch {
      // Response body is not JSON
    }

    throw new ApiClientError(
      errorBody?.error_code || "UNKNOWN_ERROR",
      errorBody?.message || `HTTP ${response.status}: ${response.statusText}`,
      errorBody?.details || null,
      response.status,
    );
  }

  return response.json();
}


async function requestBlob(path: string): Promise<Blob> {
  const url = `${BASE_URL}${path}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new ApiClientError(
      "DOWNLOAD_ERROR",
      `Failed to download audio: HTTP ${response.status}`,
      null,
      response.status,
    );
  }

  return response.blob();
}


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
  async updateSettings(req: UpdateSettingsRequest): Promise<ProviderKeyStatus> {
    return request("/settings", {
      method: "PUT",
      body: JSON.stringify(req),
    });
  },
};
```

## Usage Pattern

Components and hooks use the `apiClient` object:

```typescript
// In a hook or component:
import { apiClient } from "../api/client";

// Fetch providers
const response = await apiClient.getProviders();
dispatch({ type: "PROVIDERS_LOADED", providers: response.providers });

// Start generation
const { job_id } = await apiClient.startGeneration({
  provider: "google",
  voice_id: "en-US-Neural2-A",
  text: "Hello world",
  speed: 1.0,
});
```

## Error Handling in Callers

```typescript
try {
  const response = await apiClient.getVoices(provider);
  dispatch({ type: "VOICES_LOADED", voices: response.voices });
} catch (error) {
  if (error instanceof ApiClientError) {
    dispatch({
      type: "ERROR_SET",
      error: { code: error.code, message: error.message },
    });
  } else {
    dispatch({
      type: "ERROR_SET",
      error: { code: "NETWORK_ERROR", message: "Failed to connect to the server" },
    });
  }
}
```

## Testing

Use MSW (Mock Service Worker) to intercept API calls in tests:

```typescript
// tests/setup.ts
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";

export const server = setupServer(
  http.get("/api/providers", () => {
    return HttpResponse.json({
      providers: [
        {
          name: "google",
          display_name: "Google Cloud TTS",
          capabilities: { /* ... */ },
          is_configured: true,
        },
      ],
    });
  }),

  http.post("/api/voices", async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      provider: body.provider,
      voices: [
        {
          voice_id: "en-US-Neural2-A",
          name: "Neural2-A",
          language_code: "en-US",
          language_name: "English (US)",
          gender: "FEMALE",
          provider: body.provider,
        },
      ],
    });
  }),

  // ... handlers for other endpoints
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## Notes for Developer

1. The `BASE_URL` is `/api` (relative). In development, Vite's proxy forwards
   these to the backend. In production, the backend serves the frontend and
   handles `/api` routes directly.
2. Always use `apiClient` methods -- never call `fetch` directly in components
   or hooks. This ensures consistent error handling and typing.
3. The `requestBlob` function is separate because it does not parse JSON. It
   returns a raw `Blob` that can be used with `URL.createObjectURL`.
4. Test error scenarios with MSW by adding error handlers:
   ```typescript
   server.use(
     http.post("/api/voices", () => {
       return HttpResponse.json(
         { error_code: "PROVIDER_NOT_CONFIGURED", message: "..." },
         { status: 400 },
       );
     }),
   );
   ```
5. Write tests for:
   - Successful requests (verify correct URL, method, body)
   - Error responses (verify ApiClientError is thrown with correct code)
   - Network failures (verify error handling when fetch throws)
   - Blob download success and failure
