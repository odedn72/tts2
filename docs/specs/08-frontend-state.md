# 08 - Frontend State Management

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define the React state management architecture using Context + useReducer.
This covers global application state, actions, and the reducer logic.

**MRD traceability:** FR-001 through FR-011 all require coordinated UI state.
NFR-007 (minimal clicks) requires smooth state transitions. Design spec:
two-panel layout with dynamic content switching.

## State Shape

```typescript
// state/AppContext.tsx

interface AppState {
  // Provider & Voice selection (FR-001, FR-002)
  providers: ProviderInfo[];
  selectedProvider: ProviderName | null;
  voices: Voice[];
  selectedVoice: Voice | null;
  voicesLoading: boolean;

  // Speed control (FR-009)
  speed: number;

  // Text input (FR-003)
  text: string;

  // Generation (FR-004, FR-011)
  generationStatus: GenerationStatus | null;
  jobId: string | null;
  progress: number;            // 0.0 to 1.0
  totalChunks: number;
  completedChunks: number;

  // Audio & Playback (FR-005, FR-006, FR-007, FR-008)
  audioUrl: string | null;     // Object URL for the audio blob
  audioMetadata: AudioMetadata | null;
  isPlaying: boolean;
  currentTimeMs: number;       // Current playback position in ms

  // UI mode
  viewMode: "input" | "playback";  // Design spec: text area transforms

  // Errors
  error: { code: string; message: string } | null;

  // Settings (FR-010)
  settingsPanelOpen: boolean;
}
```

## Initial State

```typescript
const initialState: AppState = {
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
```

## Actions

```typescript
// state/actions.ts

type AppAction =
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
  | { type: "GENERATION_PROGRESS"; progress: number; totalChunks: number; completedChunks: number }
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
```

## Reducer

```typescript
// state/reducer.ts

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "PROVIDERS_LOADED":
      return { ...state, providers: action.providers };

    case "PROVIDER_SELECTED":
      return {
        ...state,
        selectedProvider: action.provider,
        selectedVoice: null,    // Reset voice when provider changes
        voices: [],             // Clear old voices
        voicesLoading: true,    // Loading new voices
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
        audioUrl: revokeAndClear(state.audioUrl),  // Clean up old audio
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
        viewMode: "playback",
      };

    case "PLAYBACK_STARTED":
      return { ...state, isPlaying: true };

    case "PLAYBACK_PAUSED":
      return { ...state, isPlaying: false };

    case "PLAYBACK_TIME_UPDATE":
      return { ...state, currentTimeMs: action.currentTimeMs };

    case "PLAYBACK_ENDED":
      return { ...state, isPlaying: false, currentTimeMs: 0 };

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
      return { ...state, providers: action.providers, settingsPanelOpen: false };

    case "ERROR_CLEARED":
      return { ...state, error: null };

    case "ERROR_SET":
      return { ...state, error: action.error };

    default:
      return state;
  }
}
```

## Context Provider

```typescript
// state/AppContext.tsx

import { createContext, useContext, useReducer, ReactNode } from "react";

interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

const AppContext = createContext<AppContextType | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppState(): AppContextType {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppState must be used within AppProvider");
  }
  return context;
}
```

## Helper Functions

```typescript
function getDefaultSpeed(
  providers: ProviderInfo[],
  providerName: ProviderName
): number {
  const provider = providers.find((p) => p.name === providerName);
  return provider?.capabilities.default_speed ?? 1.0;
}

function revokeAndClear(audioUrl: string | null): null {
  if (audioUrl) {
    URL.revokeObjectURL(audioUrl);
  }
  return null;
}
```

## State Transition Diagram

```
App Load
  |
  +---> PROVIDERS_LOADED (fetch /api/providers on mount)
  |
  v
User selects provider
  |
  +---> PROVIDER_SELECTED
  +---> VOICES_LOADING
  +---> (fetch /api/voices)
  +---> VOICES_LOADED
  |
  v
User selects voice, enters text, adjusts speed
  |
  +---> VOICE_SELECTED / TEXT_CHANGED / SPEED_CHANGED
  |
  v
User clicks Generate
  |
  +---> GENERATION_STARTED (POST /api/generate)
  +---> Start polling /api/generate/{id}/status
  +---> GENERATION_PROGRESS (repeated)
  +---> GENERATION_COMPLETED or GENERATION_FAILED
  |
  v (if completed)
  +---> Fetch /api/audio/{id} (metadata + timing)
  +---> Fetch /api/audio/{id}/file (MP3 blob)
  +---> AUDIO_LOADED (Object URL created)
  +---> SWITCH_TO_PLAYBACK
  |
  v
User plays audio
  |
  +---> PLAYBACK_STARTED / PLAYBACK_PAUSED / PLAYBACK_TIME_UPDATE
  +---> (HighlightedTextView uses currentTimeMs + timing data)
  +---> PLAYBACK_ENDED
  |
  v
User clicks "Edit Text" or "New"
  |
  +---> SWITCH_TO_INPUT
```

## Notes for Developer

1. Use `URL.createObjectURL()` to create a local URL for the audio blob.
   Always revoke old URLs when new audio is loaded (prevent memory leaks).
2. The `PLAYBACK_TIME_UPDATE` action fires frequently (from the audio element's
   `timeupdate` event). The reducer must be fast -- no expensive computations.
3. Consider debouncing `TEXT_CHANGED` if performance is a concern with very
   large text, but for this app it should be fine without.
4. Test the reducer with unit tests for every action type. Test state
   transitions in sequence (e.g., PROVIDER_SELECTED resets voice and loads
   voices).
5. The `viewMode` toggle ("input" vs "playback") controls whether the right
   panel shows the editable text area or the highlighted text view. This
   matches the design spec: "Same area transforms to highlighted playback
   view during audio playback."
6. When generation fails, the `error` field is populated and the UI should
   display an error message. The `ERROR_CLEARED` action dismisses it.
