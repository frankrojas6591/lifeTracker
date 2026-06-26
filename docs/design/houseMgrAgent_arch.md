# HouseMgr — Architecture & Deployment

**Version:** 0.4
**Date:** June 2026
**Parent:** [Design Index](./houseMgrAgent.md)

---

## 1. Design Goals

### 1.1 Lightweight Orchestrator

The HouseMgr is a **thin router and response synthesizer** — it holds no domain knowledge. Every piece of expertise lives in a discipline agent. The HouseMgr's only jobs are:

1. Parse owner intent from speech or text (via LLM)
2. Identify which agents are relevant
3. Query those agents with current house context
4. Synthesize a unified spoken or written response
5. Route stored outcomes back to HouseRecords → Git

**Anti-pattern to avoid:** A "fat" HouseMgr that accumulates logic for specific domains (e.g., knows HVAC rules, knows tax codes). That logic belongs in the agent. The HouseMgr knows only the *agent registry* — never what the agents know.

### 1.2 Design Principles

- **Owner never tracks details** — agents do. HouseMgr surfaces; agents collect.
- **Proactive over reactive** — agents push action items to the monthly check-in queue; HouseMgr presents them.
- **Recommendation, not menu** — synthesized output is "here's what to do," not a list of options.
- **Voice-first** — spoken responses are ≤ 3 sentences; detail lives on the web UI.
- **DIY-first, frugal** — cost framing defaults to quality-for-budget, not premium-fastest.
- **Aging-in-place thread** — every agent response considers the owner's current life stage.

---

## 2. Communication Channels

HouseMgr has **three communication channels**. The same Flask codebase serves all three; channel detection sets the response format.

### Channel A — iPhone Voice

Owner calls a Twilio-owned phone number. No app install required. Twilio handles speech-to-text (STT) and text-to-speech (TTS); the PA Flask app receives and returns TwiML.

```
iPhone ──(call)──► Twilio number
                        │ STT transcript (HTTPS POST)
                        ▼
                   PA /voice route
                        │ TwiML <Say> reply
                        ▼
                   Twilio ──(TTS audio)──► iPhone speaker
```

Voice responses are **≤ 3 spoken sentences**. Full detail is always written to HouseRecords and available on the web UI. Voice is the primary *interaction* channel — the owner speaks to query, record, or request action. The phone never displays data.

**Voice only reaches PA.** Twilio requires a publicly reachable HTTPS endpoint. The local Mac instance does not handle voice.

### Channel B — PA Web UI

Browser connects to the PA-hosted Flask app over HTTPS. Full web experience: records browsing, monthly check-in dashboard, configurator, document upload.

```
Browser (any device) ──(HTTPS)──► PA Flask app
                                       │
                               HouseMgr web routes
                               /chat /checkin /records /config
```

Available anywhere — phone browser, tablet, desktop. Same Flask app as local, just served from PA.

### Channel C — Local Mac Web UI

The same Flask codebase runs on the owner's Mac at `localhost:5000` via `wsCmd.py --start`. Identical routes and templates as PA. Used for at-home admin, bulk record editing, and development.

```
Browser (Mac) ──(HTTP)──► localhost:5000 (wsCmd.py --start)
                                │
                        Same Flask app, same routes
                        /chat /checkin /records /config
                        (no /voice — Twilio can't reach localhost)
```

Before starting the local app: `wsCmd.py --pull` (git pull from data repo). After edits: `wsCmd.py --push` (git commit + push). The local app can also auto-push after each agent write (configurable in `config.json`).

---

## 3. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  CHANNEL A: iPhone Voice                                            │
│                                                                     │
│  iPhone ──► Twilio ──► PA /voice ──► HouseMgr ──► Twilio ──► iPhone│
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  CHANNEL B: PA Web UI                                               │
│                                                                     │
│  Browser ──HTTPS──► PythonAnywhere Flask App                        │
│                     /chat /checkin /records /config /login          │
│                            │                                        │
│                     ┌──────▼──────────────────────────────────┐    │
│                     │  HouseMgr Orchestrator                   │    │
│                     │  IntentParser (Haiku) → AgentRouter      │    │
│                     │  ResponseSynthesizer (Sonnet)            │    │
│                     └──────┬──────────────────────────────────┘    │
│                            │                                        │
│                     Discipline Agents                               │
│                            │                                        │
│                     HouseRecords checkout                           │
│                     /home/<pa_user>/houseTracker-data/              │
│                            │ git push (on each write)               │
│                            ▼                                        │
│                     Git Data Repo (master)                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  CHANNEL C: Local Mac Web UI                                        │
│                                                                     │
│  Browser ──HTTP──► localhost:5000 (wsCmd.py --start)                │
│                     /chat /checkin /records /config /login          │
│                            │                                        │
│                     Same HouseMgr stack (identical codebase)       │
│                            │                                        │
│                     HouseRecords checkout                           │
│                     ~/GDrive/dev/pyTrackers/houseTracker-data/      │
│                            │ git pull (on startup)                  │
│                            │ git push (on each write)               │
│                            ▼                                        │
│                     Git Data Repo (master)                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.1 Why PythonAnywhere

| Factor | Rationale |
|---|---|
| **Public HTTPS** | Required for Twilio voice webhook; PA provides SSL automatically |
| **Always-on** | Voice calls work 24/7 without the owner's Mac being on |
| **Managed WSGI** | No server ops; PA handles gunicorn, SSL, process restart |
| **SSH console** | Admin tasks (`wsCmd.py --setup`, GPG key management) |
| **Cost** | $5–12/mo for a personal always-on app |

### 3.2 Why Twilio for Voice

| Factor | Rationale |
|---|---|
| **Phone number ownership** | Owner calls a real number — no app install required |
| **STT/TTS managed** | Twilio Gather (STT) + Say (TTS) — no audio processing on PA |
| **Webhook model** | Each call is a POST to `/voice`; stateless on PA side |
| **Caller ID** | Known numbers auto-login; unknown numbers hear a PIN challenge |

### 3.3 Why Same Codebase for PA and Local

- No divergence risk between environments
- Local Mac is also a test environment for new agents before PA deploy
- `setup_paths.py` detects environment from `config.json → env` key (`"pa"` vs `"local"`) to set paths; no other code branches on environment
- The only functional difference: `env=pa` registers the `/voice` route; `env=local` skips it

---

## 4. Component Map

```
Voice (Twilio)    Web Browser (PA)    Web Browser (local)
      │                  │                     │
      ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────┐
│  ConfigLoader + AuthLayer                           │
│  ~/.houseTracker/config.json                        │
│  session: (house_id, owner_id, role, channel)       │
└──────────┬──────────────────────────────────────────┘
           │ house context on every request
           ▼
┌─────────────────────────────────────────────────────┐
│  HouseMgr Orchestrator (Flask WSGI)                 │
│                                                     │
│  IntentParser ──► AgentRouter                       │
│       │                │                            │
│  (Haiku API)     AgentRegistry                      │
│                        │                            │
│               ResponseSynthesizer (Sonnet)          │
│                        │                            │
│         ┌──────────────┴──────────┐                 │
│         │ VoiceResponder          │                 │
│         │ (TwiML TTS → Twilio)    │                 │
│         │ WebResponder            │                 │
│         │ (HTML → browser)        │                 │
│         └─────────────────────────┘                 │
└──────────┬──────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────┐
│  Discipline Agents (16 agents)                      │
│  Architecture │ HVAC │ Plumbing │ ...               │
└──────────┬──────────────────────────────────────────┘
           │ read / write
           ▼
┌─────────────────────────────────────────────────────┐
│  HouseRecords (local Git checkout)                  │
│  agents commit + push to Git data repo after write  │
└──────────┬──────────────────────────────────────────┘
           │ git push / pull
           ▼
┌─────────────────────────────────────────────────────┐
│  Git Data Repo — MASTER                             │
│  github.com/<user>/houseTracker-data (private)      │
│  <house_id>/records/**/*.json                       │
└─────────────────────────────────────────────────────┘
```

---

## 5. H × O Service Model

The app supports **H homes × O owners** per instance (PA or local):

- **H (homes):** One instance manages any number of houses. Each house has its own subdirectory in the data repo.
- **O (owners):** Multiple owners authenticate separately and access only their associated houses.

Active session context is `(house_id, owner_id)`. Multi-house owners pick the active house at login or via the house-switcher nav. Voice caller ID maps to `owner_id` for auto-login.

---

## 6. Position Within pyTrackers

```
pyTrackers/
├── llcRentalTracker/   ← LLC accounting & IRS (Flask, ledger engine, MCP)
├── medicalTracker/     ← Personalized health (early stage)
├── houseTracker/       ← THIS PROJECT (PA-hosted + local Mac)
│   ├── houseMgr/       ← Orchestrator (thin router)
│   ├── agents/         ← Discipline agents (one module per agent)
│   ├── ui/             ← Flask views (voice + web routes)
│   └── wsCmd.py        ← CLI: --setup, --start, --pull, --push
└── financialTracker/   ← TBD
```

No shared infrastructure with sibling trackers. Cross-tracker integration will be explicit narrow API contracts, not shared code.

---

## 7. Implementation Plan (Architecture Scope)

### Phase 0 — Scaffold (both environments)

- [ ] PA: create account; deploy Flask skeleton via `wsgi.py`; set `env=pa` in config.json
- [ ] Local Mac: clone code repo; `wsCmd.py --setup`; set `env=local` in config.json
- [ ] Data repo: create private `houseTracker-data` repo; clone to PA and to local Mac
- [ ] `setup_paths.py`: detects env; sets `TOP`, `RECORDS_DIR`, `DATA_REPO_PATH`; registers `/voice` only when `env=pa`
- [ ] Twilio: purchase number; webhook → `https://<app>.pa.com/voice`
- [ ] Smoke test A: call Twilio → hear TTS "HouseMgr ready"
- [ ] Smoke test B: `localhost:5000/login` → authenticated web session
- [ ] Smoke test C: PA URL `/login` → authenticated web session

### Phase 1 — Voice Loop + Web Shell

- [ ] `VoiceResponder`: TwiML `<Say>` + `<Gather>` for multi-turn voice conversation
- [ ] Caller ID auto-login; PIN challenge for unknown numbers
- [ ] `WebResponder`: same HouseMgr response as HTML for web channels

### Phase 2+ — Full Stack

See [Implementation Plan](./houseMgrAgent_impl.md) for phase-by-phase agent build.
