// TDD: Written from spec 08-frontend-state.md
// Tests for the appReducer and all action types

import { describe, it, expect } from "vitest";

// These imports will fail until implementation exists -- that is expected in TDD.
import { appReducer, initialState } from "../../src/state/reducer";
import type { AppState } from "../../src/state/reducer";
import type { AppAction } from "../../src/state/actions";

describe("appReducer", () => {
  describe("initial state", () => {
    it("should have null selectedProvider", () => {
      expect(initialState.selectedProvider).toBeNull();
    });

    it("should have empty providers list", () => {
      expect(initialState.providers).toEqual([]);
    });

    it("should have empty voices list", () => {
      expect(initialState.voices).toEqual([]);
    });

    it("should have default speed 1.0", () => {
      expect(initialState.speed).toBe(1.0);
    });

    it("should have empty text", () => {
      expect(initialState.text).toBe("");
    });

    it("should have null generationStatus", () => {
      expect(initialState.generationStatus).toBeNull();
    });

    it("should have viewMode input", () => {
      expect(initialState.viewMode).toBe("input");
    });

    it("should have no error", () => {
      expect(initialState.error).toBeNull();
    });

    it("should have settings panel closed", () => {
      expect(initialState.settingsPanelOpen).toBe(false);
    });
  });

  describe("PROVIDERS_LOADED", () => {
    it("should set providers list", () => {
      const providers = [
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
      ];
      const state = appReducer(initialState, {
        type: "PROVIDERS_LOADED",
        providers,
      });
      expect(state.providers).toEqual(providers);
    });
  });

  describe("PROVIDER_SELECTED", () => {
    it("should set selectedProvider", () => {
      const state = appReducer(initialState, {
        type: "PROVIDER_SELECTED",
        provider: "google",
      });
      expect(state.selectedProvider).toBe("google");
    });

    it("should reset selectedVoice to null", () => {
      const stateWithVoice = {
        ...initialState,
        selectedVoice: {
          voice_id: "old",
          name: "Old",
          language_code: "en",
          language_name: "English",
          gender: null,
          provider: "google" as const,
        },
      };
      const state = appReducer(stateWithVoice, {
        type: "PROVIDER_SELECTED",
        provider: "openai",
      });
      expect(state.selectedVoice).toBeNull();
    });

    it("should clear voices list", () => {
      const state = appReducer(initialState, {
        type: "PROVIDER_SELECTED",
        provider: "google",
      });
      expect(state.voices).toEqual([]);
    });

    it("should set voicesLoading to true", () => {
      const state = appReducer(initialState, {
        type: "PROVIDER_SELECTED",
        provider: "google",
      });
      expect(state.voicesLoading).toBe(true);
    });

    it("should set default speed from provider capabilities", () => {
      const stateWithProviders = {
        ...initialState,
        providers: [
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
            is_configured: true,
          },
        ],
      };
      const state = appReducer(stateWithProviders, {
        type: "PROVIDER_SELECTED",
        provider: "amazon",
      });
      expect(state.speed).toBe(1.0);
    });
  });

  describe("VOICES_LOADING", () => {
    it("should set voicesLoading to true", () => {
      const state = appReducer(initialState, { type: "VOICES_LOADING" });
      expect(state.voicesLoading).toBe(true);
    });
  });

  describe("VOICES_LOADED", () => {
    it("should set voices and stop loading", () => {
      const voices = [
        {
          voice_id: "en-US-Neural2-A",
          name: "Neural2-A",
          language_code: "en-US",
          language_name: "English (US)",
          gender: "FEMALE",
          provider: "google" as const,
        },
      ];
      const state = appReducer(
        { ...initialState, voicesLoading: true },
        { type: "VOICES_LOADED", voices }
      );
      expect(state.voices).toEqual(voices);
      expect(state.voicesLoading).toBe(false);
    });
  });

  describe("VOICE_SELECTED", () => {
    it("should set selectedVoice", () => {
      const voice = {
        voice_id: "alloy",
        name: "Alloy",
        language_code: "en-US",
        language_name: "English (US)",
        gender: null,
        provider: "openai" as const,
      };
      const state = appReducer(initialState, {
        type: "VOICE_SELECTED",
        voice,
      });
      expect(state.selectedVoice).toEqual(voice);
    });
  });

  describe("SPEED_CHANGED", () => {
    it("should update speed", () => {
      const state = appReducer(initialState, {
        type: "SPEED_CHANGED",
        speed: 1.5,
      });
      expect(state.speed).toBe(1.5);
    });
  });

  describe("TEXT_CHANGED", () => {
    it("should update text", () => {
      const state = appReducer(initialState, {
        type: "TEXT_CHANGED",
        text: "Hello world",
      });
      expect(state.text).toBe("Hello world");
    });
  });

  describe("GENERATION_STARTED", () => {
    it("should set pending status and jobId", () => {
      const state = appReducer(initialState, {
        type: "GENERATION_STARTED",
        jobId: "job-123",
      });
      expect(state.generationStatus).toBe("pending");
      expect(state.jobId).toBe("job-123");
      expect(state.progress).toBe(0);
      expect(state.error).toBeNull();
    });

    it("should clear old audio", () => {
      const stateWithAudio = {
        ...initialState,
        audioUrl: "blob:old-url",
        audioMetadata: {} as any,
      };
      const state = appReducer(stateWithAudio, {
        type: "GENERATION_STARTED",
        jobId: "job-456",
      });
      expect(state.audioUrl).toBeNull();
      expect(state.audioMetadata).toBeNull();
    });
  });

  describe("GENERATION_PROGRESS", () => {
    it("should update progress fields", () => {
      const state = appReducer(initialState, {
        type: "GENERATION_PROGRESS",
        progress: 0.6,
        totalChunks: 5,
        completedChunks: 3,
      });
      expect(state.generationStatus).toBe("in_progress");
      expect(state.progress).toBe(0.6);
      expect(state.totalChunks).toBe(5);
      expect(state.completedChunks).toBe(3);
    });
  });

  describe("GENERATION_COMPLETED", () => {
    it("should set completed status and metadata", () => {
      const metadata = {
        job_id: "job-123",
        duration_ms: 5000,
        format: "mp3",
        size_bytes: 50000,
        timing: {
          timing_type: "word" as const,
          words: [],
          sentences: null,
        },
      };
      const state = appReducer(initialState, {
        type: "GENERATION_COMPLETED",
        audioMetadata: metadata,
      });
      expect(state.generationStatus).toBe("completed");
      expect(state.progress).toBe(1.0);
      expect(state.audioMetadata).toEqual(metadata);
    });
  });

  describe("GENERATION_FAILED", () => {
    it("should set failed status and error", () => {
      const error = { code: "PROVIDER_API_ERROR", message: "API failed" };
      const state = appReducer(initialState, {
        type: "GENERATION_FAILED",
        error,
      });
      expect(state.generationStatus).toBe("failed");
      expect(state.error).toEqual(error);
    });
  });

  describe("AUDIO_LOADED", () => {
    it("should set audioUrl and stay in input mode", () => {
      const state = appReducer(initialState, {
        type: "AUDIO_LOADED",
        audioUrl: "blob:test-url",
      });
      expect(state.audioUrl).toBe("blob:test-url");
      expect(state.viewMode).toBe("input");
    });
  });

  describe("PLAYBACK_STARTED", () => {
    it("should set isPlaying to true", () => {
      const state = appReducer(initialState, { type: "PLAYBACK_STARTED" });
      expect(state.isPlaying).toBe(true);
    });
  });

  describe("PLAYBACK_PAUSED", () => {
    it("should set isPlaying to false", () => {
      const state = appReducer(
        { ...initialState, isPlaying: true },
        { type: "PLAYBACK_PAUSED" }
      );
      expect(state.isPlaying).toBe(false);
    });
  });

  describe("PLAYBACK_TIME_UPDATE", () => {
    it("should update currentTimeMs", () => {
      const state = appReducer(initialState, {
        type: "PLAYBACK_TIME_UPDATE",
        currentTimeMs: 1500,
      });
      expect(state.currentTimeMs).toBe(1500);
    });
  });

  describe("PLAYBACK_ENDED", () => {
    it("should stop playing and reset time", () => {
      const state = appReducer(
        { ...initialState, isPlaying: true, currentTimeMs: 5000 },
        { type: "PLAYBACK_ENDED" }
      );
      expect(state.isPlaying).toBe(false);
      expect(state.currentTimeMs).toBe(0);
    });
  });

  describe("PLAYBACK_SEEK", () => {
    it("should set currentTimeMs", () => {
      const state = appReducer(initialState, {
        type: "PLAYBACK_SEEK",
        timeMs: 3000,
      });
      expect(state.currentTimeMs).toBe(3000);
    });
  });

  describe("SWITCH_TO_INPUT", () => {
    it("should set viewMode to input and stop playback", () => {
      const state = appReducer(
        { ...initialState, viewMode: "playback", isPlaying: true },
        { type: "SWITCH_TO_INPUT" }
      );
      expect(state.viewMode).toBe("input");
      expect(state.isPlaying).toBe(false);
    });
  });

  describe("SWITCH_TO_PLAYBACK", () => {
    it("should set viewMode to playback", () => {
      const state = appReducer(initialState, { type: "SWITCH_TO_PLAYBACK" });
      expect(state.viewMode).toBe("playback");
    });
  });

  describe("SETTINGS_OPENED", () => {
    it("should open settings panel", () => {
      const state = appReducer(initialState, { type: "SETTINGS_OPENED" });
      expect(state.settingsPanelOpen).toBe(true);
    });
  });

  describe("SETTINGS_CLOSED", () => {
    it("should close settings panel", () => {
      const state = appReducer(
        { ...initialState, settingsPanelOpen: true },
        { type: "SETTINGS_CLOSED" }
      );
      expect(state.settingsPanelOpen).toBe(false);
    });
  });

  describe("SETTINGS_UPDATED", () => {
    it("should update providers and close settings", () => {
      const providers = [
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
      ];
      const state = appReducer(
        { ...initialState, settingsPanelOpen: true },
        { type: "SETTINGS_UPDATED", providers }
      );
      expect(state.providers).toEqual(providers);
      expect(state.settingsPanelOpen).toBe(false);
    });
  });

  describe("ERROR_CLEARED", () => {
    it("should clear error", () => {
      const state = appReducer(
        { ...initialState, error: { code: "ERR", message: "Oops" } },
        { type: "ERROR_CLEARED" }
      );
      expect(state.error).toBeNull();
    });
  });

  describe("ERROR_SET", () => {
    it("should set error", () => {
      const error = { code: "TEST_ERR", message: "Test error" };
      const state = appReducer(initialState, {
        type: "ERROR_SET",
        error,
      });
      expect(state.error).toEqual(error);
    });
  });

  describe("unknown action", () => {
    it("should return current state for unknown action", () => {
      const state = appReducer(initialState, {
        type: "UNKNOWN_ACTION" as any,
      });
      expect(state).toEqual(initialState);
    });
  });
});
