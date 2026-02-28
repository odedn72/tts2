/**
 * Custom hook for loading TTS providers and their voices.
 * Fetches the provider list on mount and provides a function to load
 * voices when a provider is selected.
 */

import { useEffect, useCallback } from "react";
import { apiClient } from "../api/client";
import type { AppAction } from "../state/actions";
import type { ProviderName, ProviderInfo } from "../types/provider";

/**
 * Return type of the useProviders hook.
 */
interface UseProvidersReturn {
  /** Function to fetch and load voices for a given provider */
  loadVoices: (provider: ProviderName) => Promise<void>;
}

/**
 * Hook that loads providers on mount and provides voice-loading capability.
 *
 * @param dispatch - The app state dispatch function
 * @returns Object with loadVoices function
 */
export function useProviders(
  dispatch: React.Dispatch<AppAction>
): UseProvidersReturn {
  // Fetch providers list on mount, then restore saved selection
  useEffect(() => {
    async function loadProviders(): Promise<void> {
      try {
        const response = await apiClient.getProviders();
        dispatch({
          type: "PROVIDERS_LOADED",
          providers: response.providers,
        });

        // Restore saved provider selection
        const savedProvider = localStorage.getItem("tts-selected-provider") as ProviderName | null;
        if (savedProvider) {
          const providerInfo = response.providers.find(
            (p: ProviderInfo) => p.name === savedProvider && p.is_configured
          );
          if (providerInfo) {
            dispatch({ type: "PROVIDER_SELECTED", provider: savedProvider });

            // Load voices and restore saved voice selection
            dispatch({ type: "VOICES_LOADING" });
            try {
              const voicesResponse = await apiClient.getVoices(savedProvider);
              dispatch({ type: "VOICES_LOADED", voices: voicesResponse.voices });

              const savedVoiceId = localStorage.getItem("tts-selected-voice-id");
              if (savedVoiceId) {
                const voice = voicesResponse.voices.find(
                  (v: { voice_id: string }) => v.voice_id === savedVoiceId
                );
                if (voice) {
                  dispatch({ type: "VOICE_SELECTED", voice });
                }
              }
            } catch {
              dispatch({
                type: "ERROR_SET",
                error: { code: "VOICES_ERROR", message: "Failed to load voices" },
              });
            }
          }
        }
      } catch {
        dispatch({
          type: "ERROR_SET",
          error: {
            code: "LOAD_ERROR",
            message: "Failed to load providers",
          },
        });
      }
    }
    loadProviders();
  }, [dispatch]);

  // Load voices for a selected provider
  const loadVoices = useCallback(
    async (provider: ProviderName): Promise<void> => {
      dispatch({ type: "VOICES_LOADING" });
      try {
        const response = await apiClient.getVoices(provider);
        dispatch({ type: "VOICES_LOADED", voices: response.voices });
      } catch {
        dispatch({
          type: "ERROR_SET",
          error: {
            code: "VOICES_ERROR",
            message: "Failed to load voices",
          },
        });
      }
    },
    [dispatch]
  );

  return { loadVoices };
}
