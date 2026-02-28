/**
 * Application-level React Context provider.
 * Wraps the entire app and provides global state + dispatch via useReducer.
 */

import { createContext, useContext, useReducer } from "react";
import type { ReactNode } from "react";
import { appReducer, initialState } from "./reducer";
import type { AppState } from "./reducer";
import type { AppAction } from "./actions";

/** Shape of the context value: state + dispatch. */
export interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

/** The React context instance. Null until an AppProvider is mounted. */
const AppContext = createContext<AppContextType | null>(null);

/** Props for the AppProvider wrapper component. */
interface AppProviderProps {
  children: ReactNode;
}

/**
 * Provider component that wraps the app tree and supplies
 * global state and dispatch to all descendants.
 */
export function AppProvider({ children }: AppProviderProps): JSX.Element {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

/**
 * Custom hook to access global app state and dispatch.
 * Must be called inside an AppProvider -- throws otherwise.
 */
export function useAppState(): AppContextType {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppState must be used within AppProvider");
  }
  return context;
}
