/**
 * Root layout component implementing the two-panel dark-themed design.
 * Left panel contains controls, right panel contains text and playback.
 * Wires together all child components, hooks, and state management.
 */

import React, { useCallback, useMemo } from "react";
import { useAppState } from "../state/AppContext";
import { useProviders } from "../hooks/useProviders";
import { useGenerationPolling } from "../hooks/useGenerationPolling";
import { apiClient } from "../api/client";
import type { ProviderName } from "../types/provider";
import type { Voice } from "../types/provider";
import type { AudioMetadata, TimingData } from "../types/audio";
import type { ProviderKeyStatus } from "../types/api";

import { ProviderSelector } from "./LeftPanel/ProviderSelector";
import { VoiceSelector } from "./LeftPanel/VoiceSelector";
import { SpeedControl } from "./LeftPanel/SpeedControl";
import { GenerateButton } from "./LeftPanel/GenerateButton";
import { SettingsPanel } from "./LeftPanel/SettingsPanel";
import { TextInputArea } from "./RightPanel/TextInputArea";
import { HighlightedTextView } from "./RightPanel/HighlightedTextView";
import { AudioPlayer } from "./RightPanel/AudioPlayer";
import { ProgressIndicator } from "./RightPanel/ProgressIndicator";

/**
 * Renders the two-panel layout with header, left panel (controls),
 * and right panel (text/playback). All styling comes from App.css.
 */
export function AppShell(): JSX.Element {
  const { state, dispatch } = useAppState();

  // Load providers on mount and provide voice-loading capability
  const { loadVoices } = useProviders(dispatch);

  // --- Callbacks ---

  const handleProviderSelect = useCallback(
    (provider: ProviderName) => {
      localStorage.setItem("tts-selected-provider", provider);
      dispatch({ type: "PROVIDER_SELECTED", provider });
      loadVoices(provider);
    },
    [dispatch, loadVoices]
  );

  const handleVoiceSelect = useCallback(
    (voice: Voice) => {
      localStorage.setItem("tts-selected-voice-id", voice.voice_id);
      dispatch({ type: "VOICE_SELECTED", voice });
    },
    [dispatch]
  );

  const handleSpeedChange = useCallback(
    (speed: number) => {
      dispatch({ type: "SPEED_CHANGED", speed });
    },
    [dispatch]
  );

  const handleTextChange = useCallback(
    (text: string) => {
      dispatch({ type: "TEXT_CHANGED", text });
    },
    [dispatch]
  );

  const handleGenerate = useCallback(async () => {
    if (!state.selectedProvider || !state.selectedVoice || !state.text.trim()) {
      return;
    }
    try {
      const response = await apiClient.startGeneration({
        provider: state.selectedProvider,
        voice_id: state.selectedVoice.voice_id,
        text: state.text,
        speed: 1.0,
      });
      dispatch({ type: "GENERATION_STARTED", jobId: response.job_id });
    } catch {
      dispatch({
        type: "ERROR_SET",
        error: { code: "GENERATION_ERROR", message: "Failed to start generation" },
      });
    }
  }, [state.selectedProvider, state.selectedVoice, state.text, dispatch]);

  // --- Generation polling ---

  const handleProgress = useCallback(
    (progress: number, totalChunks: number, completedChunks: number) => {
      dispatch({
        type: "GENERATION_PROGRESS",
        progress,
        totalChunks,
        completedChunks,
      });
    },
    [dispatch]
  );

  const handleCompleted = useCallback(
    async (metadata: AudioMetadata) => {
      dispatch({ type: "GENERATION_COMPLETED", audioMetadata: metadata });
      // Fetch the audio blob
      if (state.jobId) {
        try {
          const blob = await apiClient.getAudioFile(state.jobId);
          const url = URL.createObjectURL(blob);
          dispatch({ type: "AUDIO_LOADED", audioUrl: url });
        } catch {
          dispatch({
            type: "ERROR_SET",
            error: { code: "AUDIO_ERROR", message: "Failed to load audio" },
          });
        }
      }
    },
    [dispatch, state.jobId]
  );

  const handleFailed = useCallback(
    (error: { code: string; message: string }) => {
      dispatch({ type: "GENERATION_FAILED", error });
    },
    [dispatch]
  );

  useGenerationPolling(
    state.generationStatus === "pending" || state.generationStatus === "in_progress"
      ? state.jobId
      : null,
    handleProgress,
    handleCompleted,
    handleFailed
  );

  // --- Playback callbacks ---

  const handlePlay = useCallback(() => {
    dispatch({ type: "PLAYBACK_STARTED" });
  }, [dispatch]);

  const handlePause = useCallback(() => {
    dispatch({ type: "PLAYBACK_PAUSED" });
  }, [dispatch]);

  const handleTimeUpdate = useCallback(
    (timeMs: number) => {
      dispatch({ type: "PLAYBACK_TIME_UPDATE", currentTimeMs: timeMs });
    },
    [dispatch]
  );

  const handleEnded = useCallback(() => {
    dispatch({ type: "PLAYBACK_ENDED" });
  }, [dispatch]);

  const handleSeek = useCallback(
    (timeMs: number) => {
      dispatch({ type: "PLAYBACK_SEEK", timeMs });
    },
    [dispatch]
  );

  // --- Settings ---

  const handleSettingsOpen = useCallback(() => {
    dispatch({ type: "SETTINGS_OPENED" });
  }, [dispatch]);

  const handleSettingsClose = useCallback(() => {
    dispatch({ type: "SETTINGS_CLOSED" });
  }, [dispatch]);

  const handleSettingsSave = useCallback(
    async (provider: ProviderName, apiKey: string) => {
      try {
        const response = await apiClient.updateSettings({ provider, api_key: apiKey });
        dispatch({ type: "SETTINGS_UPDATED", providers: response.providers.map((p: ProviderKeyStatus) => ({
          name: p.provider,
          display_name: p.provider,
          capabilities: state.providers.find((sp) => sp.name === p.provider)?.capabilities ?? {
            supports_speed_control: false,
            supports_word_timing: false,
            min_speed: 1,
            max_speed: 1,
            default_speed: 1,
            max_chunk_chars: 4000,
          },
          is_configured: p.is_configured,
        })) });
        // Reload providers to get fresh data
        const providersResp = await apiClient.getProviders();
        dispatch({ type: "PROVIDERS_LOADED", providers: providersResp.providers });
      } catch {
        dispatch({
          type: "ERROR_SET",
          error: { code: "SETTINGS_ERROR", message: "Failed to save settings" },
        });
      }
    },
    [dispatch, state.providers]
  );

  // --- UI state ---

  const isGenerating =
    state.generationStatus === "pending" || state.generationStatus === "in_progress";

  const canGenerate =
    !!state.selectedProvider &&
    !!state.selectedVoice &&
    !!state.text.trim() &&
    !isGenerating;

  const selectedProviderInfo = state.providers.find(
    (p) => p.name === state.selectedProvider
  );

  const supportsSpeed = selectedProviderInfo?.capabilities.supports_speed_control ?? false;

  const settingsProviders: ProviderKeyStatus[] = state.providers.map((p) => ({
    provider: p.name,
    is_configured: p.is_configured,
  }));

  const emptyTiming: TimingData = useMemo(
    () => ({ timing_type: "word", words: [], sentences: null }),
    []
  );

  const handleSwitchToInput = useCallback(() => {
    dispatch({ type: "SWITCH_TO_INPUT" });
  }, [dispatch]);

  return (
    <div className="app-shell" data-testid="app-shell">
      <header className="app-header">
        <h1>TTS Reader</h1>
        <button
          className="settings-button"
          onClick={handleSettingsOpen}
          aria-label="Settings"
        >
          Settings
        </button>
      </header>

      {state.error && (
        <div className="error-banner" role="alert">
          <span>{state.error.message}</span>
          <button onClick={() => dispatch({ type: "ERROR_CLEARED" })}>Dismiss</button>
        </div>
      )}

      <div className="app-body">
        <div className="left-panel" data-testid="left-panel">
          <ProviderSelector
            providers={state.providers}
            selectedProvider={state.selectedProvider}
            onSelect={handleProviderSelect}
          />
          <VoiceSelector
            voices={state.voices}
            selectedVoice={state.selectedVoice}
            onSelect={handleVoiceSelect}
            loading={state.voicesLoading}
            disabled={!state.selectedProvider || isGenerating}
          />
          <SpeedControl
            speed={state.speed}
            min={selectedProviderInfo?.capabilities.min_speed ?? 0.25}
            max={selectedProviderInfo?.capabilities.max_speed ?? 4.0}
            onChange={handleSpeedChange}
            disabled={isGenerating}
            visible={supportsSpeed}
          />
          <GenerateButton
            onClick={handleGenerate}
            disabled={!canGenerate}
            loading={isGenerating}
          />
        </div>

        <div className="right-panel" data-testid="right-panel">
          {state.viewMode === "input" ? (
            <TextInputArea
              text={state.text}
              onChange={handleTextChange}
              disabled={isGenerating}
            />
          ) : (
            <>
              <button
                className="back-to-input-button"
                onClick={handleSwitchToInput}
              >
                Back to Edit
              </button>
              <HighlightedTextView
                text={state.text}
                timingData={state.audioMetadata?.timing ?? emptyTiming}
                currentTimeMs={state.currentTimeMs}
                isPlaying={state.isPlaying}
              />
            </>
          )}

          <ProgressIndicator
            progress={state.progress}
            totalChunks={state.totalChunks}
            completedChunks={state.completedChunks}
            visible={isGenerating}
          />

          <AudioPlayer
            audioUrl={state.audioUrl}
            onPlay={handlePlay}
            onPause={handlePause}
            onTimeUpdate={handleTimeUpdate}
            onEnded={handleEnded}
            onSeek={handleSeek}
            isPlaying={state.isPlaying}
            speed={state.speed}
          />
        </div>
      </div>

      <SettingsPanel
        providers={settingsProviders}
        onSave={handleSettingsSave}
        onClose={handleSettingsClose}
        open={state.settingsPanelOpen}
      />
    </div>
  );
}
