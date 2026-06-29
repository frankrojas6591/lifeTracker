# lifeTracker iOS App — Design Document

**Version:** 1.0
**Author:** Frank Rojas
**Date:** June 2026
**Status:** Design phase — no code yet

---

## 1. What This Document Covers

The lifeTracker iOS app is the native iPhone interface for the Personal Assistant ecosystem. It is **not** part of the `lifeTracker` Python repo — it lives in a separate repo (`pyTrackers/lifeTrackerIOS`). This document defines the architecture, tech stack, API contract, and build plan for that app.

**What the app does:** Gives the owner a voice-first, always-in-pocket interface to the Personal Assistant — identical in capability to calling the Twilio number but with lower friction, richer context, and no per-minute call cost.

---

## 2. Separate Repo: Why

| Factor | Decision |
|---|---|
| Language | Swift / Xcode ≠ Python monorepo |
| Build tooling | `xcodebuild`, Swift Package Manager — no overlap with `pip` / `pytest` |
| Deployment | TestFlight / App Store, not a server process |
| Intelligence | Stays in `lifeTracker` Flask backend — app is a thin UI shell |
| Coupling | App talks to backend via HTTP; API contract is the only integration point |

**Repo name:** `pyTrackers/lifeTrackerIOS`
**GitHub account:** `frankrojas6591` (personal, same as `lifeTracker`)
**SSH alias:** `github.com-fxr`

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────┐
│  iPhone (lifeTrackerIOS app)                        │
│                                                     │
│  ┌────────────────┐     ┌────────────────────────┐  │
│  │ SFSpeechRecog- │     │ AVSpeechSynthesizer     │  │
│  │ nizer (on-dev) │     │ (on-device TTS)         │  │
│  └───────┬────────┘     └────────────▲────────────┘  │
│          │ text                      │ text          │
│  ┌───────▼─────────────────────────┐ │               │
│  │  APIClient (URLSession)         │─┘               │
│  │  POST /api/query {text, owner}  │                 │
│  │  ← {response_text, action_items}│                 │
│  └────────────────┬────────────────┘                 │
└───────────────────┼─────────────────────────────────┘
                    │ HTTPS
                    ▼
┌─────────────────────────────────────────────────────┐
│  lifeTracker Flask backend  (unchanged)             │
│  Communication Agent → IntentParser → PA → Agents   │
└─────────────────────────────────────────────────────┘
```

**Design principle: Hybrid client.** The iPhone handles STT and TTS locally (on-device, fast, offline-tolerant). Text travels to/from the Flask backend. No audio bytes cross the network. All intelligence stays server-side.

This is better than a thin audio-stream approach because:
- Lower latency (no audio upload)
- Works on cellular and weak signals
- No audio streaming cost
- Backend API stays simple: text in, text out

---

## 4. Tech Stack

### 4.1 iOS Stack

| Component | Library | Notes |
|---|---|---|
| UI framework | **SwiftUI** | iOS 17+, single codebase |
| Speech-to-text | **SFSpeechRecognizer** | On-device, Apple Neural Engine; no cost, no data upload |
| Audio session | **AVAudioSession** | Manage mic input, speaker output, interrupt handling |
| Text-to-speech | **AVSpeechSynthesizer** | On-device; swap in ElevenLabs voice later via optional upgrade |
| HTTP client | **URLSession** | No third-party networking library needed |
| Keychain | **Security.framework** | Store auth token; never in UserDefaults |
| Push notifications | **APNs / UserNotifications** | PA alert delivery when app is backgrounded |
| Minimum iOS | **iOS 17** | Required for latest SFSpeechRecognizer quality and SwiftUI features |

### 4.2 Backend Stack (no changes)

The Flask backend in `lifeTracker` gains two new endpoints (§6). No existing code changes.

---

## 5. Screens

### 5.1 Voice Orb (Main Screen)

The only screen most sessions need.

```
┌──────────────────────────────┐
│                              │
│       [PA NAME / LOGO]       │
│                              │
│          ◉  ← orb            │
│     (idle / listening /      │
│      responding)             │
│                              │
│  [last response text area]   │
│                              │
│  [conversation history btn]  │
└──────────────────────────────┘
```

**States:**
- **Idle** — orb dim; tap to begin listening
- **Listening** — orb pulsing; SFSpeechRecognizer transcribing live
- **Processing** — orb spinner; API call in flight
- **Responding** — orb active; AVSpeechSynthesizer speaking; text displayed
- **Error** — orb red; message shown; retry option

**Interaction modes:**
- **Push-to-talk** (default) — hold orb to speak, release to send
- **Tap-to-talk** — tap to start, tap to stop
- **Wake word** (future) — "Hey Frank" — not in v1

### 5.2 Conversation History

Scrollable log of recent exchanges. Each item shows timestamp, transcript of owner input, and PA response text. Tap to expand full text. Voice replay of response via `AVSpeechSynthesizer`.

### 5.3 Notifications / Action Items

List of open action items surfaced by the PA. Tap to open in voice context ("Tell me more about this item"). Cleared when owner acknowledges via voice or tap.

### 5.4 Settings (minimal)

- Server URL (for dev/prod toggle)
- Voice speed and pitch
- Sign out

---

## 6. Backend API Contract

Two new Flask endpoints added to `lifeTracker`'s Communication Agent. No changes to existing routes.

### 6.1 POST `/api/query`

**Purpose:** Submit a voice query as text; receive PA response as text.

```
Request:
  POST /api/query
  Authorization: Bearer <token>
  Content-Type: application/json

  {
    "text": "How are my finances and can I afford a new roof?",
    "channel": "ios_voice",
    "owner_id": "frankr6591"
  }

Response (200):
  {
    "response_text": "Your liquid savings are $42K. Roof replacement runs ...",
    "action_items": [],          // new items to surface in Notifications tab
    "agent_sources": ["money", "house"],   // for debug/display only
    "session_id": "abc123"
  }
```

`channel: "ios_voice"` signals the ResponseSynthesizer to produce ≤3 spoken sentences — same constraint as Twilio voice.

### 6.2 POST `/api/auth/token`

**Purpose:** Authenticate and receive a session token for Keychain storage.

```
Request:
  POST /api/auth/token
  Content-Type: application/json

  {
    "owner_id": "frankr6591",
    "passphrase": "..."           // GPG passphrase; never stored on device
  }

Response (200):
  {
    "token": "eyJ...",
    "expires_at": "2026-07-28T00:00:00Z"
  }
```

Token stored in iOS Keychain. Refreshed silently before expiry.

### 6.3 GET `/api/notifications`

**Purpose:** Fetch open action items for Notifications tab (polled on app launch and foreground).

```
Response (200):
  {
    "action_items": [
      {
        "id": "...",
        "agent": "house",
        "summary": "HVAC filter due for replacement",
        "priority": "medium",
        "created_at": "..."
      }
    ]
  }
```

---

## 7. Voice Interaction Flow

```
Owner taps orb (push-to-talk)
    │
    ▼
AVAudioSession activates microphone
SFSpeechRecognizer starts live transcription (streaming, on-device)
    │
    ▼
Owner releases orb (or silence detected after 1.5s)
    │
    ▼
Transcript finalized → POST /api/query
    │
    ▼
Backend: IntentParser (Haiku) → PA routes → Agents → ResponseSynthesizer (Sonnet)
    │
    ▼
response_text returned in <2s target latency
    │
    ▼
AVSpeechSynthesizer speaks response (on-device voice)
Response text shown in orb UI
    │
    ▼
Orb returns to Idle
```

**Latency target:** Under 2 seconds from release-orb to first spoken word.
**Latency budget:** ~100ms STT finalization + ~1500ms backend roundtrip + ~200ms TTS onset = 1.8s typical.

---

## 8. Error Handling

| Error | User Experience | Recovery |
|---|---|---|
| No microphone permission | Settings prompt on first launch | Link to iOS Settings |
| No network | "No connection — try again" in orb | Retry button |
| Backend timeout (>5s) | "Taking longer than expected..." | Auto-cancel at 8s; retry available |
| Auth expired | Silent token refresh; if fail → sign-in screen | Restore after sign-in |
| STT no speech detected | Orb returns to Idle; no API call | Owner taps again |
| Backend error (5xx) | "Something went wrong — try again" | Retry |

---

## 9. Privacy & Security

- **No audio stored on device.** SFSpeechRecognizer is on-device only; no audio is sent anywhere. Apple's STT is on-device for supported languages.
- **No audio crosses the network.** Only text (transcript and response) is transmitted.
- **Token in Keychain.** Never in UserDefaults, never in iCloud backup scope.
- **HTTPS only.** Backend enforces TLS; no HTTP fallback.
- **No analytics SDK.** No Crashlytics, Firebase, or third-party telemetry. Crash logs via Xcode Organizer only.
- **No App Store.** Distributed via TestFlight to a single device (Frank's iPhone). No App Store review process needed.

---

## 10. Distribution

**v1:** TestFlight, single device.

No App Store submission needed for personal use. TestFlight allows one-person beta indefinitely. The bundle ID `com.frankrojas.lifeTracker` registered under personal Apple ID.

---

## 11. Repo Structure

```
lifeTrackerIOS/
├── lifeTrackerIOS.xcodeproj/
├── lifeTrackerIOS/
│   ├── App/
│   │   ├── lifeTrackerIOSApp.swift     ← app entry, auth gate
│   │   └── AppState.swift              ← ObservableObject; global state
│   ├── Voice/
│   │   ├── SpeechRecognizer.swift      ← SFSpeechRecognizer wrapper
│   │   ├── AudioSessionManager.swift   ← AVAudioSession lifecycle
│   │   └── TTSPlayer.swift             ← AVSpeechSynthesizer wrapper
│   ├── API/
│   │   ├── APIClient.swift             ← URLSession; /api/query, /api/notifications
│   │   ├── AuthManager.swift           ← token fetch, refresh, Keychain storage
│   │   └── Models.swift                ← QueryRequest, QueryResponse, ActionItem
│   ├── Views/
│   │   ├── VoiceOrbView.swift          ← main orb screen
│   │   ├── HistoryView.swift           ← conversation log
│   │   ├── NotificationsView.swift     ← action items list
│   │   └── SettingsView.swift
│   └── Resources/
│       └── Assets.xcassets
├── README.md
└── CLAUDE.md
```

---

## 12. Build Plan

### Phase 0 — Backend Prerequisite

Before any iOS code: add `/api/query`, `/api/auth/token`, `/api/notifications` to the `lifeTracker` Flask backend (Communication Agent). iOS app has nothing to connect to until these exist.

| Task | Repo | Notes |
|---|---|---|
| Add `POST /api/query` | `lifeTracker` | Returns text response; honors `channel: ios_voice` for length constraint |
| Add `POST /api/auth/token` | `lifeTracker` | Issues JWT from GPG user DB |
| Add `GET /api/notifications` | `lifeTracker` | Returns open action items |

### Phase 1 — iOS Scaffold

| Task | Notes |
|---|---|
| Create Xcode project | SwiftUI, iOS 17, bundle `com.frankrojas.lifeTracker` |
| CLAUDE.md for iOS repo | Set conventions; no docstrings, no multi-line comments |
| `APIClient.swift` stub | URLSession wrappers; returns mock response |
| `AuthManager.swift` | Token flow + Keychain write/read; test against backend |
| Sign-in screen | Passphrase entry → token → stored → AppState.isAuthenticated |

### Phase 2 — Voice Core

| Task | Notes |
|---|---|
| `SpeechRecognizer.swift` | SFSpeechRecognizer; request permission; stream partial results |
| `AudioSessionManager.swift` | Activate/deactivate mic; handle phone call interrupts |
| `TTSPlayer.swift` | AVSpeechSynthesizer; speak text; fire completion callback |
| Push-to-talk gesture | LongPressGesture on orb → start STT; release → finalize → send |
| End-to-end voice test | Speak → transcript → POST /api/query → response text → TTS spoken |

### Phase 3 — UI Polish

| Task | Notes |
|---|---|
| `VoiceOrbView.swift` | Orb states (idle / listening / processing / responding / error) with animation |
| `HistoryView.swift` | Conversation log; persist to UserDefaults |
| `NotificationsView.swift` | Fetch on foreground; badge count on tab |
| Error states | Network, auth, STT, timeout — all shown cleanly in orb |

### Phase 4 — Distribution

| Task | Notes |
|---|---|
| TestFlight setup | Apple Developer account; upload build; install on iPhone |
| Push notifications | APNs entitlement; backend sends push for high-priority PA alerts |
| Background fetch | Refresh action items silently when app backgrounds |

---

## 13. Future Enhancements (not v1)

- **ElevenLabs TTS voice** — custom voice for PA; replaces AVSpeechSynthesizer for richer output
- **Wake word** ("Hey Frank") — ambient activation without touching the phone
- **iPad support** — same codebase; wider layout for HistoryView
- **Siri Shortcuts** — "Hey Siri, ask my PA..." as an on-ramp
- **Watch app** — single-sentence quick queries from Apple Watch

---

*This document covers the iOS app design only. Backend design: `lifeTracker/docs/lifeTrackerVision.md §7`. Communication Agent implementation: `lifeTracker/pytracker-core/comm/`.*
