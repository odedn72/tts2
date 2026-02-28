/**
 * Custom hook for loading TTS providers and their voices.
 * Fetches the provider list on mount and provides a function to load
 * voices when a provider is selected.
 */

import { useEffect, useCallback } from "react";
import { apiClient } from "../api/client";
import type { AppAction } from "../state/actions";
import type { ProviderName } from "../types/provider";

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
  // Fetch providers list on mount
  useEffect(() => {
    async function loadProviders(): Promise<void> {
      try {
        const response = await apiClient.getProviders();
        dispatch({
          type: "PROVIDERS_LOADED",
          providers: response.providers,
        });
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
