# Market Requirements Document: TTS Web Application
**Version:** 1.0
**Date:** 2026-02-28
**Author:** Product Agent
**Status:** Approved by User

## 1. Executive Summary
A personal text-to-speech web application that runs locally, enabling the user to paste text (up to chapter-length), select a TTS provider and voice, generate spoken audio, and play it back in the browser with real-time word-by-word text highlighting. The app supports four major TTS providers (Google Cloud TTS, Amazon Polly, ElevenLabs, OpenAI TTS), offers MP3 download, and provides speed control where the provider supports it. Built with a React frontend and Python backend, the application is designed as a single-user personal tool with no cloud deployment.

## 2. Problem Statement
- **What problem exists today:** Converting large blocks of text (e.g., book chapters) to speech requires navigating individual provider interfaces, each with different UIs and capabilities. There is no unified tool that lets a user easily compare providers and voices, generate audio, and follow along with highlighted text.
- **Who is affected:** The user -- a single individual who needs to convert chapter-length text to speech for personal use.
- **Impact of the problem remaining unsolved:** The user must manually switch between provider dashboards, loses the ability to compare voices side by side, and has no synchronized text-highlighting playback experience.

## 3. Target Users
| Persona | Description | Primary Needs |
|---------|-------------|---------------|
| Primary User | Single technical user running the app locally for personal text-to-speech conversion | Unified interface across multiple TTS providers, word-level text highlighting during playback, MP3 download, speed control |

## 4. Product Goals & Success Metrics
| Goal | Metric | Target |
|------|--------|--------|
| Unified TTS experience | Number of providers accessible from a single UI | 4 (Google Cloud TTS, Amazon Polly, ElevenLabs, OpenAI TTS) |
| Seamless playback with text tracking | Text highlighting accuracy during playback | Word-level where provider supports it, sentence-level fallback otherwise |
| Support long-form content | Maximum text length supported | Full book chapter (approximately 5,000-10,000 words) |
| Reliable audio generation | Successful generation rate for chapter-length text | > 95% without manual intervention |
| Local-first operation | External dependencies beyond TTS APIs | None -- runs entirely on local machine |

## 5. Functional Requirements

### 5.1 Must-Have (P0)
| ID | Requirement | Description | Acceptance Criteria |
|----|-------------|-------------|---------------------|
| FR-001 | Provider Selection | User can select from a list of supported TTS providers (Google Cloud TTS, Amazon Polly, ElevenLabs, OpenAI TTS) | Dropdown or similar UI element lists all four providers; selecting one loads its available voices |
| FR-002 | Voice Selection | User can browse and select from available voices for the chosen provider | Voice list is dynamically fetched from the provider API; voices display name and language/locale |
| FR-003 | Text Input | User can paste or type chapter-length text into a text input area | Text area accepts at least 10,000 words; no artificial character limit below chapter length |
| FR-004 | Audio Generation | System converts the input text to speech using the selected provider and voice | Audio is generated successfully and returned to the frontend; errors are clearly reported to the user |
| FR-005 | In-Browser Playback | User can play, pause, and seek through the generated audio in the browser | Standard audio player controls (play, pause, seek bar, time display) are functional |
| FR-006 | Word-by-Word Text Highlighting | Text is highlighted word by word in sync with audio playback | When the provider returns word-level timing data, each word highlights as it is spoken |
| FR-007 | Sentence-Level Highlighting Fallback | When word-level timing is unavailable, text highlights sentence by sentence | If word timing data is not available from the provider, sentences highlight in sync with audio |
| FR-008 | MP3 Download | User can download the generated audio as an MP3 file | A download button saves the MP3 to the user's local filesystem |
| FR-009 | Speed Control | User can adjust the speech speed where the provider supports it | Speed slider or input is available; disabled or hidden for providers that do not support speed control |
| FR-010 | API Key Configuration | User can configure API keys for each provider | Keys can be set via environment variables or a settings page in the app; keys are stored securely on the local machine |
| FR-011 | Chapter-Length Text Handling | System handles long text by chunking and providing progress indication | Long text is split into appropriate chunks per provider limits; a progress bar or indicator shows generation status |

### 5.2 Should-Have (P1)
| ID | Requirement | Description | Acceptance Criteria |
|----|-------------|-------------|---------------------|
| FR-012 | Cost Estimation | Display an estimated cost before generating audio | Before generation, the UI shows an approximate cost based on text length and selected provider/voice pricing |
| FR-013 | Provider Capability Indicators | UI indicates which features (speed control, word-level timing) each provider supports | Visual indicators show supported features per provider so the user can make informed choices |

### 5.3 Nice-to-Have (P2)
| ID | Requirement | Description | Acceptance Criteria |
|----|-------------|-------------|---------------------|
| FR-014 | Output Format Selection | User can choose audio output format (MP3, WAV, OGG) | Dropdown allows selecting format; generated audio matches selected format |
| FR-015 | Language/Locale Filtering | User can filter voices by language or locale | Voice list can be filtered by language (e.g., en-US, en-GB, es-ES) |
| FR-016 | Audio Generation History | User can see a list of recently generated audio files | A simple history list shows recent generations with the ability to re-download or replay |

## 6. Non-Functional Requirements
| ID | Category | Requirement | Target |
|----|----------|-------------|--------|
| NFR-001 | Performance | Audio generation for a single page of text (~300 words) should complete in a reasonable time | Under 30 seconds |
| NFR-002 | Performance | Chapter-length audio generation should provide progress feedback | Progress indicator updates at least once per chunk |
| NFR-003 | Performance | In-browser playback and text highlighting should be smooth | No perceptible lag between audio and highlighting |
| NFR-004 | Security | API keys must not be exposed to the browser or logged in plaintext | Keys stored server-side only; never sent to the frontend |
| NFR-005 | Security | The application only listens on localhost | No external network access to the app |
| NFR-006 | Reliability | Graceful error handling for API failures, rate limits, and network issues | Clear error messages displayed to the user; partial results preserved where possible |
| NFR-007 | Usability | The UI should be clean and simple -- minimal clicks to generate audio | Text-to-audio in 3 clicks or fewer (select provider, select voice, click generate) |
| NFR-008 | Compatibility | Runs on macOS (primary development and usage environment) | Application starts and functions correctly on macOS |

## 7. Technical Constraints & Preferences
- **Frontend:** React
- **Backend:** Python (likely FastAPI or Flask for the API layer)
- **Deployment:** Local only -- runs on the user's machine (no cloud hosting)
- **API keys:** Configured via environment variables or an in-app settings page; stored securely on the local machine
- **TTS Providers:** Google Cloud TTS, Amazon Polly, ElevenLabs, OpenAI TTS -- each behind an abstract interface to allow easy addition of future providers
- **Audio format:** MP3 as the primary output format
- **Budget:** No hosting costs; TTS API costs are the user's responsibility per their own provider accounts
- **Chunking:** Long text must be split into provider-appropriate chunks and reassembled into a single audio file

## 8. Out of Scope
- User accounts, authentication, or multi-user support
- Cloud deployment or hosting
- Sharing audio with other users
- Voice cloning or custom voice training
- Audio editing (trimming, splicing, effects)
- SSML editing or advanced markup input
- Pitch, volume, or emotion/style controls (may be considered in future versions)
- Mobile-specific UI (desktop browser is the target)
- Batch processing of multiple texts simultaneously

## 9. Open Questions & Risks
| Risk/Question | Impact | Mitigation |
|---------------|--------|------------|
| Word-level timing data availability varies by provider | Some providers may only support sentence-level highlighting, degrading the ideal experience | Implement sentence-level fallback; document which providers support word-level timing |
| Chapter-length text may hit API rate limits or payload size limits | Audio generation could fail or be throttled for long content | Implement chunking with appropriate delays between requests; show progress to user |
| Cost per chapter varies significantly across providers | User may incur unexpected costs | Implement cost estimation (P1) to give the user visibility before generating |
| Audio chunk stitching quality | Concatenating multiple audio chunks may produce audible seams or inconsistent pacing | Investigate provider-specific best practices for chunking; add slight overlap or silence between chunks if needed |
| Timing data format differs across providers | Each provider returns timing/sync data in a different format, increasing implementation complexity | Normalize timing data into a common internal format behind the provider abstraction layer |
| ElevenLabs and OpenAI TTS may have limited or no word-level timestamp support | Word-by-word highlighting may not be possible for all providers | Gracefully degrade to sentence-level; research each provider's capabilities during implementation |

## 10. Appendix

### User Interview Notes
- **User profile:** Single technical user building this as a personal tool
- **Primary use case:** Converting book chapters to speech with synchronized text highlighting
- **Provider preference:** Google Cloud TTS, Amazon Polly, ElevenLabs, OpenAI TTS
- **Tech stack preference:** React frontend, Python backend
- **Deployment:** Local only (macOS)
- **Key concern:** API costs -- user wants visibility but cost estimation is not critical for v1
- **Highlighting preference:** Word-by-word is ideal, sentence-level is an acceptable fallback
- **Audio output:** Both in-browser playback and MP3 download required
- **Speed control:** Desired where provider supports it
- **API key management:** User is comfortable configuring keys via environment variables or settings page

### Provider Capability Summary (Preliminary)
| Capability | Google Cloud TTS | Amazon Polly | ElevenLabs | OpenAI TTS |
|------------|-----------------|--------------|------------|------------|
| Speed control | Yes (via SSML/speaking rate) | Yes (via SSML) | Yes (via API parameter) | Yes (via speed parameter) |
| Word-level timing | Yes (timepoints) | Yes (speech marks) | Yes (word-level timestamps) | Limited (no native word timestamps) |
| MP3 output | Yes | Yes | Yes | Yes |
| Free tier | Yes (limited) | Yes (limited) | No (paid plans) | No (pay per use) |
