/**
 * Root application component.
 * Wraps the entire UI in the AppProvider and renders the AppShell layout
 * with all child components connected to global state.
 */

import React from "react";
import { AppProvider } from "./state/AppContext";
import { AppShell } from "./components/AppShell";
import "./App.css";

/**
 * Top-level component that provides state context and renders the app.
 */
function App(): JSX.Element {
  return (
    <AppProvider>
      <AppShell />
    </AppProvider>
  );
}

export default App;
