// TDD: Written from spec 13-api-client.md
// Tests for the typed API client

import { describe, it, expect, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../mocks/server";

// This import will fail until implementation exists
import { apiClient } from "../../src/api/client";

describe("apiClient", () => {
  describe("getProviders", () => {
    it("should fetch providers list", async () => {
      const result = await apiClient.getProviders();
      expect(result.providers).toBeDefined();
      expect(result.providers.length).toBeGreaterThan(0);
    });

    it("should include provider capabilities", async () => {
      const result = await apiClient.getProviders();
      const google = result.providers.find((p) => p.name === "google");
      expect(google?.capabilities.supports_speed_control).toBe(true);
    });

    it("should handle server error", async () => {
      server.use(
        http.get("/api/providers", () => {
          return HttpResponse.json(
            { error_code: "INTERNAL_ERROR", message: "Server error", details: null },
            { status: 500 }
          );
        })
      );
      await expect(apiClient.getProviders()).rejects.toThrow();
    });
  });

  describe("getVoices", () => {
    it("should fetch voices for a provider", async () => {
      const result = await apiClient.getVoices("google");
      expect(result.voices).toBeDefined();
      expect(result.voices.length).toBeGreaterThan(0);
    });

    it("should send provider in request body", async () => {
      let capturedBody: any;
      server.use(
        http.post("/api/voices", async ({ request }) => {
          capturedBody = await request.json();
          return HttpResponse.json({ provider: "google", voices: [] });
        })
      );
      await apiClient.getVoices("google");
      expect(capturedBody.provider).toBe("google");
    });

    it("should throw ApiClientError on 400", async () => {
      server.use(
        http.post("/api/voices", () => {
          return HttpResponse.json(
            {
              error_code: "PROVIDER_NOT_CONFIGURED",
              message: "Provider not configured",
              details: null,
            },
            { status: 400 }
          );
        })
      );
      try {
        await apiClient.getVoices("google");
        expect.fail("Should have thrown");
      } catch (err: any) {
        expect(err.code).toBe("PROVIDER_NOT_CONFIGURED");
        expect(err.httpStatus).toBe(400);
      }
    });
  });

  describe("startGeneration", () => {
    it("should start a generation job", async () => {
      const result = await apiClient.startGeneration({
        provider: "google",
        voice_id: "en-US-Neural2-A",
        text: "Hello world",
        speed: 1.0,
      });
      expect(result.job_id).toBeDefined();
      expect(result.status).toBe("pending");
    });

    it("should handle validation error", async () => {
      server.use(
        http.post("/api/generate", () => {
          return HttpResponse.json(
            {
              error_code: "VALIDATION_ERROR",
              message: "Invalid input",
              details: null,
            },
            { status: 400 }
          );
        })
      );
      await expect(
        apiClient.startGeneration({
          provider: "google",
          voice_id: "test",
          text: "",
          speed: 1.0,
        })
      ).rejects.toThrow();
    });
  });

  describe("getJobStatus", () => {
    it("should return job status", async () => {
      const result = await apiClient.getJobStatus("test-job-123");
      expect(result.job_id).toBe("test-job-123");
      expect(result.status).toBeDefined();
    });

    it("should handle 404 for unknown job", async () => {
      server.use(
        http.get("/api/generate/:jobId/status", () => {
          return HttpResponse.json(
            {
              error_code: "JOB_NOT_FOUND",
              message: "Job not found",
              details: null,
            },
            { status: 404 }
          );
        })
      );
      await expect(apiClient.getJobStatus("bad-id")).rejects.toThrow();
    });
  });

  describe("getAudioMetadata", () => {
    it("should return audio metadata with timing", async () => {
      const result = await apiClient.getAudioMetadata("test-job-123");
      expect(result.job_id).toBe("test-job-123");
      expect(result.timing).toBeDefined();
      expect(result.timing.timing_type).toBe("word");
    });

    it("should handle 404", async () => {
      server.use(
        http.get("/api/audio/:jobId", () => {
          return HttpResponse.json(
            {
              error_code: "JOB_NOT_FOUND",
              message: "Not found",
              details: null,
            },
            { status: 404 }
          );
        })
      );
      await expect(apiClient.getAudioMetadata("bad-id")).rejects.toThrow();
    });

    it("should handle 409 not completed", async () => {
      server.use(
        http.get("/api/audio/:jobId", () => {
          return HttpResponse.json(
            {
              error_code: "JOB_NOT_COMPLETED",
              message: "Job not completed",
              details: null,
            },
            { status: 409 }
          );
        })
      );
      await expect(apiClient.getAudioMetadata("test-job-123")).rejects.toThrow();
    });
  });

  describe("getAudioFile", () => {
    it("should return a blob", async () => {
      const blob = await apiClient.getAudioFile("test-job-123");
      expect(blob).toBeInstanceOf(Blob);
      expect(blob.size).toBeGreaterThan(0);
    });

    it("should handle download error", async () => {
      server.use(
        http.get("/api/audio/:jobId/file", () => {
          return new HttpResponse(null, { status: 404 });
        })
      );
      await expect(apiClient.getAudioFile("bad-id")).rejects.toThrow();
    });
  });

  describe("getSettings", () => {
    it("should return provider configuration status", async () => {
      const result = await apiClient.getSettings();
      expect(result.providers).toBeDefined();
      expect(result.providers.length).toBe(4);
    });

    it("should not contain actual API keys", async () => {
      const result = await apiClient.getSettings();
      const text = JSON.stringify(result);
      expect(text).not.toContain("api_key");
    });
  });

  describe("updateSettings", () => {
    it("should update provider key", async () => {
      const result = await apiClient.updateSettings({
        provider: "openai",
        api_key: "sk-new-key",
      });
      expect(result.provider).toBe("openai");
      expect(result.is_configured).toBe(true);
    });

    it("should handle error response", async () => {
      server.use(
        http.put("/api/settings", () => {
          return HttpResponse.json(
            {
              error_code: "VALIDATION_ERROR",
              message: "Invalid",
              details: null,
            },
            { status: 400 }
          );
        })
      );
      await expect(
        apiClient.updateSettings({ provider: "openai", api_key: "" })
      ).rejects.toThrow();
    });
  });

  describe("error handling", () => {
    it("should throw ApiClientError with code on error response", async () => {
      server.use(
        http.get("/api/providers", () => {
          return HttpResponse.json(
            {
              error_code: "CUSTOM_ERROR",
              message: "Something bad",
              details: { foo: "bar" },
            },
            { status: 500 }
          );
        })
      );
      try {
        await apiClient.getProviders();
        expect.fail("Should have thrown");
      } catch (err: any) {
        expect(err.code).toBe("CUSTOM_ERROR");
        expect(err.message).toBe("Something bad");
        expect(err.httpStatus).toBe(500);
      }
    });

    it("should handle non-JSON error responses gracefully", async () => {
      server.use(
        http.get("/api/providers", () => {
          return new HttpResponse("Not Found", { status: 404 });
        })
      );
      try {
        await apiClient.getProviders();
        expect.fail("Should have thrown");
      } catch (err: any) {
        expect(err.httpStatus).toBe(404);
      }
    });
  });
});
