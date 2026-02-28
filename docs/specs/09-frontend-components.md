# 09 - Frontend Components

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define the React component hierarchy, props, and rendering behavior for the
TTS web application UI.

**MRD traceability:** FR-001 through FR-011 (all UI features). NFR-007
(minimal clicks). Design spec: dark mode, two-panel layout, all component
placement.

## Component Hierarchy

```
App
  +-- AppProvider (Context)
      +-- AppShell
            +-- LeftPanel
            |     +-- ProviderSelector          (FR-001)
            |     +-- VoiceSelector             (FR-002)
            |     +-- SpeedControl              (FR-009)
            |     +-- GenerateButton            (FR-004)
            |     +-- SettingsButton
            |     +-- SettingsPanel (modal/drawer)  (FR-010)
            |
            +-- RightPanel
                  +-- TextInputArea             (FR-003)     [viewMode=input]
                  +-- HighlightedTextView       (FR-006/007) [viewMode=playback]
                  +-- ProgressIndicator         (FR-011)     [during generation]
                  +-- AudioPlayer               (FR-005/008) [after generation]
```

## Component Specifications

### AppShell

**File:** `components/AppShell.tsx`

**Purpose:** Root layout component implementing the two-panel dark-themed design.

**Props:** None (reads from context).

**Rendering:**
```
+--------------------------------------------------------------+
|  TTS Reader                                    [Settings]     |
+-------------------+------------------------------------------+
|                   |                                          |
|  Left Panel       |  Right Panel                             |
|  (controls)       |  (text / playback)                       |
|                   |                                          |
|  [Provider v]     |  +------------------------------------+  |
|                   |  |                                    |  |
|  [Voice    v]     |  |  Text input area                   |  |
|                   |  |  OR                                |  |
|  Speed: [===o==]  |  |  Highlighted text view             |  |
|                   |  |                                    |  |
|  [Generate]       |  |                                    |  |
|                   |  +------------------------------------+  |
|                   |                                          |
|                   |  [Progress: ====------  60%]             |
|                   |                                          |
|                   |  [|< Play  ====o======  3:24/5:30  DL]  |
+-------------------+------------------------------------------+
```

**CSS:**
- Use CSS Grid or Flexbox for the two-panel layout
- Left panel: fixed width (~280px)
- Right panel: flex-grow to fill remaining space
- Dark background: `#1a1a2e` or similar dark blue-gray
- Text color: `#e0e0e0`
- No responsive breakpoints needed (desktop only)

---

### ProviderSelector

**File:** `components/LeftPanel/ProviderSelector.tsx`

**Purpose:** Dropdown to select a TTS provider. (FR-001)

**Props:**
```typescript
interface ProviderSelectorProps {
  providers: ProviderInfo[];
  selectedProvider: ProviderName | null;
  onSelect: (provider: ProviderName) => void;
}
```

**Behavior:**
- Renders a `<select>` element with all providers
- Shows provider display_name
- Indicates unconfigured providers (e.g., grayed out text, "(not configured)")
- Unconfigured providers are still selectable but will show a message to
  configure API keys
- On change, dispatches `PROVIDER_SELECTED` and triggers voice loading

**Accessibility:**
- Label: "TTS Provider"
- `aria-label` on the select element

---

### VoiceSelector

**File:** `components/LeftPanel/VoiceSelector.tsx`

**Purpose:** Dropdown to select a voice from the current provider. (FR-002)

**Props:**
```typescript
interface VoiceSelectorProps {
  voices: Voice[];
  selectedVoice: Voice | null;
  onSelect: (voice: Voice) => void;
  loading: boolean;
  disabled: boolean;
}
```

**Behavior:**
- Renders a `<select>` element with available voices
- Shows voice name and language (e.g., "Neural2-A (English US)")
- Shows a loading spinner/state while voices are being fetched
- Disabled when no provider is selected or voices are loading
- On change, dispatches `VOICE_SELECTED`

---

### SpeedControl

**File:** `components/LeftPanel/SpeedControl.tsx`

**Purpose:** Slider to adjust speech speed. (FR-009)

**Props:**
```typescript
interface SpeedControlProps {
  speed: number;
  min: number;
  max: number;
  onChange: (speed: number) => void;
  disabled: boolean;
  visible: boolean;  // Hidden when provider doesn't support speed
}
```

**Behavior:**
- Renders `<input type="range">` with the provider's min/max range
- Displays current speed value (e.g., "1.0x")
- Hidden entirely (not just disabled) when `visible` is false
- Step: 0.05 or 0.1 for fine control
- On change, dispatches `SPEED_CHANGED`

---

### GenerateButton

**File:** `components/LeftPanel/GenerateButton.tsx`

**Purpose:** Trigger TTS generation. (FR-004)

**Props:**
```typescript
interface GenerateButtonProps {
  onClick: () => void;
  disabled: boolean;
  loading: boolean;    // True during generation
}
```

**Behavior:**
- Renders a prominent button ("Generate Audio")
- Disabled when: no provider selected, no voice selected, text is empty,
  or generation is in progress
- Shows a loading/spinner state during generation
- On click, calls the generation flow (POST /api/generate, start polling)

**Styling:**
- Primary action color (e.g., bright blue or accent color on dark background)
- Clear disabled state

---

### SettingsPanel

**File:** `components/LeftPanel/SettingsPanel.tsx`

**Purpose:** Configure API keys for each provider. (FR-010)

**Props:**
```typescript
interface SettingsPanelProps {
  providers: ProviderKeyStatus[];
  onSave: (provider: ProviderName, apiKey: string) => void;
  onClose: () => void;
  open: boolean;
}
```

**Behavior:**
- Renders as a modal overlay or slide-out drawer
- Lists all providers with their configuration status
- For each provider, shows:
  - Provider name
  - Status indicator (configured / not configured)
  - Password input field for API key
  - Save button per provider
- On save, calls PUT /api/settings, then refreshes provider list
- Close button or click-outside to dismiss

**Security:**
- API key input uses `type="password"`
- Never displays existing API key values (NFR-004)
- Shows only configured/not-configured status

---

### TextInputArea

**File:** `components/RightPanel/TextInputArea.tsx`

**Purpose:** Large text area for pasting chapter-length text. (FR-003)

**Props:**
```typescript
interface TextInputAreaProps {
  text: string;
  onChange: (text: string) => void;
  disabled: boolean;
}
```

**Behavior:**
- Renders a `<textarea>` that fills the right panel
- Placeholder text: "Paste your text here..."
- No artificial character limit (supports 10,000+ words per FR-003)
- Disabled during generation/playback
- Monospace or readable font on dark background

**Styling:**
- Background: slightly lighter than panel background
- Border: subtle
- Font size: comfortable for reading (14-16px)
- Full height of the content area

---

### HighlightedTextView

**File:** `components/RightPanel/HighlightedTextView.tsx`

**Purpose:** Display text with word-by-word or sentence-level highlighting
synchronized to audio playback. (FR-006, FR-007)

**Props:**
```typescript
interface HighlightedTextViewProps {
  text: string;
  timingData: TimingData;
  currentTimeMs: number;
  isPlaying: boolean;
}
```

**Behavior:**
- Renders the full text with `<span>` elements wrapping each word or sentence
- The currently-spoken word/sentence gets a highlight CSS class
- Already-spoken text returns to normal styling (design spec)
- Auto-scrolls to keep the highlighted text visible
- Read-only (not editable)
- Includes a "Back to Edit" button to switch viewMode to "input"

**Highlighting logic:** See spec 10 for detailed algorithm.

**Styling (design spec):**
- Highlight color: muted amber (`#c8a960`) or muted blue (`#4a90d9`) background
  on the current word/sentence
- Already-read text: normal text color (no special styling)
- Unread text: normal text color
- Current word/sentence: highlight background + slightly brighter text

**Performance:**
- For large texts (5,000+ words), rendering thousands of `<span>` elements
  must be efficient. Use `React.memo` to prevent re-renders of unchanged spans.
- The `currentTimeMs` prop changes frequently. The highlighting logic should
  use binary search on the timing array, not linear scan.

---

### AudioPlayer

**File:** `components/RightPanel/AudioPlayer.tsx`

**Purpose:** Audio playback controls. (FR-005, FR-008)

**Props:**
```typescript
interface AudioPlayerProps {
  audioUrl: string | null;
  onPlay: () => void;
  onPause: () => void;
  onTimeUpdate: (timeMs: number) => void;
  onEnded: () => void;
  onSeek: (timeMs: number) => void;
  isPlaying: boolean;
}
```

**Behavior:**
- Renders custom audio controls (not the browser's native `<audio>` controls)
- Play/Pause toggle button
- Seek bar (range input or custom slider)
- Current time / total duration display (e.g., "2:34 / 5:10")
- Download button (links to `/api/audio/{job_id}/file`)
- Hidden when no audio is available
- Uses a hidden `<audio>` element managed by the `useAudioPlayback` hook

---

### ProgressIndicator

**File:** `components/RightPanel/ProgressIndicator.tsx`

**Purpose:** Show generation progress. (FR-011, NFR-002)

**Props:**
```typescript
interface ProgressIndicatorProps {
  progress: number;          // 0.0 to 1.0
  totalChunks: number;
  completedChunks: number;
  visible: boolean;
}
```

**Behavior:**
- Renders a progress bar with percentage
- Shows "Generating: chunk 3 of 5 (60%)"
- Visible only during generation (status is pending or in_progress)
- Smooth animation on progress updates

## Dark Theme CSS Variables

```css
/* App.css */
:root {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --bg-surface: #0f3460;
  --bg-input: #1e2a4a;
  --text-primary: #e0e0e0;
  --text-secondary: #a0a0b0;
  --text-muted: #606080;
  --accent-primary: #4a90d9;
  --accent-hover: #5aa0e9;
  --highlight-word: #c8a960;       /* Amber highlight for current word */
  --highlight-bg: rgba(200, 169, 96, 0.3);
  --error: #e74c3c;
  --success: #2ecc71;
  --border: #2a2a4e;
  --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-mono: "SF Mono", "Fira Code", monospace;
}

body {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-body);
  margin: 0;
  padding: 0;
}
```

## Notes for Developer

1. Use standard HTML elements (`select`, `input`, `button`, `textarea`) styled
   with CSS. No component library needed for this simple UI.
2. The `HighlightedTextView` is the most complex component. See spec 10 for
   detailed rendering and highlighting logic.
3. The `AudioPlayer` uses a hidden `<audio>` element. The visible UI is custom.
   Wire up the `<audio>` element's events to the state via the
   `useAudioPlayback` hook.
4. For the `SettingsPanel`, a simple modal overlay with a semi-transparent
   backdrop is sufficient. No need for a full modal library.
5. Test each component in isolation with React Testing Library. Mock the
   context provider and verify rendering behavior and event handling.
6. For the two-panel layout, use CSS Grid:
   ```css
   .app-shell {
     display: grid;
     grid-template-columns: 280px 1fr;
     height: 100vh;
   }
   ```
7. All components receive data and callbacks via props. The `AppShell`
   component is the one that connects context state to child component props.
