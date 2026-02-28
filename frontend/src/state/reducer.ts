/**
 * Application state reducer for the TTS Reader.
 * Handles all state transitions via pure function logic.
 */

import type { ProviderName, ProviderInfo, Voice } from "../types/provider";
import type { GenerationStatus, AudioMetadata } from "../types/audio";
import type { AppAction } from "./actions";

/** Shape of the entire application state. */
export interface AppState {
  /** Available TTS providers */
  providers: ProviderInfo[];
  /** Currently selected provider name */
  selectedProvider: ProviderName | null;
  /** Voices for the selected provider */
  voices: Voice[];
  /** Currently selected voice */
  selectedVoice: Voice | null;
  /** Whether voices are currently being fetched */
  voicesLoading: boolean;

  /** Playback speed multiplier */
  speed: number;

  /** User-entered text content */
  text: string;

  /** Current generation job status */
  generationStatus: GenerationStatus | null;
  /** Active job ID */
  jobId: string | null;
  /** Generation progress (0.0 to 1.0) */
  progress: number;
  /** Total number of text chunks being processed */
  totalChunks: number;
  /** Number of chunks completed so far */
  completedChunks: number;

  /** Object URL for the generated audio blob */
  audioUrl: string | null;
  /** Metadata including timing data for the generated audio */
  audioMetadata: AudioMetadata | null;
  /** Whether audio is currently playing */
  isPlaying: boolean;
  /** Current playback position in milliseconds */
  currentTimeMs: number;

  /** Whether the right panel shows input or playback view */
  viewMode: "input" | "playback";

  /** Current error state */
  error: { code: string; message: string } | null;

  /** Whether the settings panel is open */
  settingsPanelOpen: boolean;
}

/** Default initial state for the application. */
export const initialState: AppState = {
  providers: [],
  selectedProvider: null,
  voices: [],
  selectedVoice: null,
  voicesLoading: false,
  speed: 1.0,
  text: "",
  generationStatus: null,
  jobId: null,
  progress: 0,
  totalChunks: 0,
  completedChunks: 0,
  audioUrl: null,
  audioMetadata: null,
  isPlaying: false,
  currentTimeMs: 0,
  viewMode: "input",
  error: null,
  settingsPanelOpen: false,
};

/**
 * Look up the default speed for a provider from the providers list.
 * Falls back to 1.0 if the provider is not found.
 */
function getDefaultSpeed(
  providers: ProviderInfo[],
  providerName: ProviderName
): number {
  const provider = providers.find((p) => p.name === providerName);
  return provider?.capabilities.default_speed ?? 1.0;
}

/**
 * Revoke an existing Object URL and return null.
 * Prevents memory leaks from stale audio blob URLs.
 */
function revokeAndClear(audioUrl: string | null): null {
  if (audioUrl && typeof URL.revokeObjectURL === "function") {
    URL.revokeObjectURL(audioUrl);
  }
  return null;
}

/**
 * Pure reducer function that computes the next state from the current
 * state and an action. Every state transition in the app goes through here.
 */
export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "PROVIDERS_LOADED":
      return { ...state, providers: action.providers };

    case "PROVIDER_SELECTED":
      return {
        ...state,
        selectedProvider: action.provider,
        selectedVoice: null,
        voices: [],
        voicesLoading: true,
        speed: getDefaultSpeed(state.providers, action.provider),
      };

    case "VOICES_LOADING":
      return { ...state, voicesLoading: true };

    case "VOICES_LOADED":
      return { ...state, voices: action.voices, voicesLoading: false };

    case "VOICE_SELECTED":
      return { ...state, selectedVoice: action.voice };

    case "SPEED_CHANGED":
      return { ...state, speed: action.speed };

    case "TEXT_CHANGED":
      return { ...state, text: action.text };

    case "GENERATION_STARTED":
      return {
        ...state,
        generationStatus: "pending",
        jobId: action.jobId,
        progress: 0,
        totalChunks: 0,
        completedChunks: 0,
        error: null,
        audioUrl: revokeAndClear(state.audioUrl),
        audioMetadata: null,
      };

    case "GENERATION_PROGRESS":
      return {
        ...state,
        generationStatus: "in_progress",
        progress: action.progress,
        totalChunks: action.totalChunks,
        completedChunks: action.completedChunks,
      };

    case "GENERATION_COMPLETED":
      return {
        ...state,
        generationStatus: "completed",
        progress: 1.0,
        audioMetadata: action.audioMetadata,
      };

    case "GENERATION_FAILED":
      return {
        ...state,
        generationStatus: "failed",
        error: action.error,
      };

    case "AUDIO_LOADED":
      return {
        ...state,
        audioUrl: action.audioUrl,
      };

    case "PLAYBACK_STARTED":
      return { ...state, isPlaying: true, viewMode: "playback" };

    case "PLAYBACK_PAUSED":
      return { ...state, isPlaying: false, viewMode: "input" };

    case "PLAYBACK_TIME_UPDATE":
      return { ...state, currentTimeMs: action.currentTimeMs };

    case "PLAYBACK_ENDED":
      return { ...state, isPlaying: false, currentTimeMs: 0, viewMode: "input" };

    case "PLAYBACK_SEEK":
      return { ...state, currentTimeMs: action.timeMs };

    case "SWITCH_TO_INPUT":
      return { ...state, viewMode: "input", isPlaying: false };

    case "SWITCH_TO_PLAYBACK":
      return { ...state, viewMode: "playback" };

    case "SETTINGS_OPENED":
      return { ...state, settingsPanelOpen: true };

    case "SETTINGS_CLOSED":
      return { ...state, settingsPanelOpen: false };

    case "SETTINGS_UPDATED":
      return {
        ...state,
        providers: action.providers,
        settingsPanelOpen: false,
      };

    case "ERROR_CLEARED":
      return { ...state, error: null };

    case "ERROR_SET":
      return { ...state, error: action.error };

    default:
      return state;
  }
}
