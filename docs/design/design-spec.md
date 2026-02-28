# Design Spec: TTS Web Application

**Date:** 2026-02-28
**Status:** Approved by User

## Theme
- **Dark mode** — dark background with light text, optimized for long reading sessions

## Layout: Two-Panel
- **Left panel:** Controls
  - Provider selector (dropdown)
  - Voice selector (dynamic based on provider)
  - Speed control slider (shown/hidden based on provider support)
  - Generate button
  - Settings (API key configuration)
- **Right panel:** Text & Playback
  - Large text input area for pasting chapter-length content
  - Same area transforms to highlighted playback view during audio playback
  - Audio player controls at the bottom of the right panel (play/pause, progress bar, download button)

## Text Highlighting
- **Style:** Background highlight on the current word/sentence
- Word-by-word highlighting preferred (sentence-level fallback)
- Already-read text returns to normal styling
- Highlight color should contrast well against the dark theme (e.g., a muted blue or amber)

## General Notes
- Personal tool — keep the UI functional and clean, no need for marketing polish
- Progress indication for long chapter-length generation
- Responsive is not required (desktop use only)
