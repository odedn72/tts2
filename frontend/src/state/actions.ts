/**
 * Action types for the application state reducer.
 * Defines every possible state transition in the TTS Reader app.
 */

import type { ProviderName, ProviderInfo, Voice } from "../types/provider";
import type { AudioMetadata } from "../types/audio";

/** Union of all actions that can be dispatched to the app reducer. */
export type AppAction =
  // Provider actions
  | { type: "PROVIDERS_LOADED"; providers: ProviderInfo[] }
  | { type: "PROVIDER_SELECTED"; provider: ProviderName }
  | { type: "VOICES_LOADING" }
  | { type: "VOICES_LOADED"; voices: Voice[] }
  | { type: "VOICE_SELECTED"; voice: Voice }

  // Speed
  | { type: "SPEED_CHANGED"; speed: number }

  // Text
  | { type: "TEXT_CHANGED"; text: string }

  // Generation
  | { type: "GENERATION_STARTED"; jobId: string }
  | {
      type: "GENERATION_PROGRESS";
      progress: number;
      totalChunks: number;
      completedChunks: number;
    }
  | { type: "GENERATION_COMPLETED"; audioMetadata: AudioMetadata }
  | { type: "GENERATION_FAILED"; error: { code: string; message: string } }

  // Audio / Playback
  | { type: "AUDIO_LOADED"; audioUrl: string }
  | { type: "PLAYBACK_STARTED" }
  | { type: "PLAYBACK_PAUSED" }
  | { type: "PLAYBACK_TIME_UPDATE"; currentTimeMs: number }
  | { type: "PLAYBACK_ENDED" }
  | { type: "PLAYBACK_SEEK"; timeMs: number }

  // UI mode
  | { type: "SWITCH_TO_INPUT" }
  | { type: "SWITCH_TO_PLAYBACK" }

  // Settings
  | { type: "SETTINGS_OPENED" }
  | { type: "SETTINGS_CLOSED" }
  | { type: "SETTINGS_UPDATED"; providers: ProviderInfo[] }

  // Error
  | { type: "ERROR_CLEARED" }
  | { type: "ERROR_SET"; error: { code: string; message: string } };
