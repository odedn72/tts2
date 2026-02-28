// TDD: MSW request handlers for frontend tests
// Written from specs 05, 13

import { http, HttpResponse } from "msw";

/** Sample provider data matching spec 02 and spec 05 */
export const mockProviders = [
  {
    name: "google" as const,
    display_name: "Google Cloud TTS",
    capabilities: {
      supports_speed_control: true,
      supports_word_timing: true,
      min_speed: 0.25,
      max_speed: 4.0,
      default_speed: 1.0,
      max_chunk_chars: 4500,
    },
    is_configured: true,
  },
  {
    name: "amazon" as const,
    display_name: "Amazon Polly",
    capabilities: {
      supports_speed_control: true,
      supports_word_timing: true,
      min_speed: 0.5,
      max_speed: 2.0,
      default_speed: 1.0,
      max_chunk_chars: 2800,
    },
    is_configured: false,
  },
  {
    name: "elevenlabs" as const,
    display_name: "ElevenLabs",
    capabilities: {
      supports_speed_control: true,
      supports_word_timing: true,
      min_speed: 0.7,
      max_speed: 1.2,
      default_speed: 1.0,
      max_chunk_chars: 4500,
    },
    is_configured: true,
  },
  {
    name: "openai" as const,
    display_name: "OpenAI TTS",
    capabilities: {
      supports_speed_control: true,
      supports_word_timing: false,
      min_speed: 0.25,
      max_speed: 4.0,
      default_speed: 1.0,
      max_chunk_chars: 4000,
    },
    is_configured: false,
  },
];

export const mockVoices = [
  {
    voice_id: "en-US-Neural2-A",
    name: "Neural2-A",
    language_code: "en-US",
    language_name: "English (US)",
    gender: "FEMALE",
    provider: "google",
  },
  {
    voice_id: "en-US-Neural2-B",
    name: "Neural2-B",
    language_code: "en-US",
    language_name: "English (US)",
    gender: "MALE",
    provider: "google",
  },
];

export const mockTimingData = {
  timing_type: "word" as const,
  words: [
    { word: "Hello", start_ms: 0, end_ms: 300, start_char: 0, end_char: 5 },
    { word: "world.", start_ms: 300, end_ms: 600, start_char: 6, end_char: 12 },
  ],
  sentences: null,
};

export const mockAudioMetadata = {
  job_id: "test-job-123",
  duration_ms: 600,
  format: "mp3",
  size_bytes: 1024,
  timing: mockTimingData,
};

export const handlers = [
  // GET /api/providers
  http.get("/api/providers", () => {
    return HttpResponse.json({ providers: mockProviders });
  }),

  // POST /api/voices
  http.post("/api/voices", async ({ request }) => {
    const body = (await request.json()) as { provider: string };
    return HttpResponse.json({
      provider: body.provider,
      voices: mockVoices,
    });
  }),

  // POST /api/generate
  http.post("/api/generate", () => {
    return HttpResponse.json(
      { job_id: "test-job-123", status: "pending" },
      { status: 202 }
    );
  }),

  // GET /api/generate/:jobId/status
  http.get("/api/generate/:jobId/status", () => {
    return HttpResponse.json({
      job_id: "test-job-123",
      status: "completed",
      progress: 1.0,
      total_chunks: 1,
      completed_chunks: 1,
      error_message: null,
    });
  }),

  // GET /api/audio/:jobId
  http.get("/api/audio/:jobId", ({ params }) => {
    if (params.jobId === "test-job-123") {
      return HttpResponse.json(mockAudioMetadata);
    }
    return HttpResponse.json(
      { error_code: "JOB_NOT_FOUND", message: "Job not found", details: null },
      { status: 404 }
    );
  }),

  // GET /api/audio/:jobId/file
  http.get("/api/audio/:jobId/file", () => {
    return new HttpResponse(new Blob([new Uint8Array(1024)]), {
      headers: {
        "Content-Type": "audio/mpeg",
        "Content-Disposition": 'attachment; filename="tts-test.mp3"',
      },
    });
  }),

  // GET /api/settings
  http.get("/api/settings", () => {
    return HttpResponse.json({
      providers: [
        { provider: "google", is_configured: true },
        { provider: "amazon", is_configured: false },
        { provider: "elevenlabs", is_configured: true },
        { provider: "openai", is_configured: false },
      ],
    });
  }),

  // PUT /api/settings
  http.put("/api/settings", async ({ request }) => {
    const body = (await request.json()) as { provider: string; api_key: string };
    return HttpResponse.json({
      provider: body.provider,
      is_configured: true,
    });
  }),
];
