# HouseMgr Agent — Design Index

**Version:** 0.4
**Date:** June 2026
**Status:** Design — pre-implementation

---

## System Overview

HouseMgr is a voice-first home management assistant with **three communication channels** and a **Git-as-master records model**. The private Git data repo is the single source of truth for all house records; both the PA-hosted instance and the local Mac instance sync against it.

```
┌──────────────────────────────────────────────────────────────────┐
│  COMMUNICATION CHANNELS                                          │
│                                                                  │
│  (A) iPhone (voice)    (B) PA Web UI          (C) Local Mac UI  │
│  ─────────────────     ────────────────        ───────────────── │
│  Call Twilio number    Browser → PA URL        Browser → :5000  │
│  Speak / listen        Full web UI             Same web UI      │
│  No record display     Records, check-in       Records, check-in│
└───────┬────────────────────────┬────────────────────────┬───────┘
        │ Twilio webhook         │ HTTPS                  │ HTTP
        ▼                        ▼                        ▼
┌───────────────────────┐   ┌────────────────────────────────────┐
│ PythonAnywhere (PA)   │   │ Local Mac (Flask, same codebase)   │
│ Flask WSGI — public   │   │ wsCmd.py --start — localhost:5000  │
│ /voice + all web UIs  │   │ web UIs only (no Twilio /voice)    │
└───────────┬───────────┘   └──────────────┬─────────────────────┘
            │ git pull / push               │ git pull / push
            └──────────────┬───────────────┘
                           ▼
            ┌──────────────────────────────┐
            │  Git Data Repo (private)     │
            │  github.com/<user>/          │
            │  houseTracker-data           │
            │  ← master records store →   │
            │  <house_id>/records/**/*.json│
            └──────────────────────────────┘
```

**Records master:** Git data repo. PA and Local Mac both maintain a local checkout; both pull before a session and push immediately after any write. Voice calls only reach PA (Twilio requires a public HTTPS endpoint).

---

## Design Documents

| Document | Scope |
|---|---|
| [Architecture & Deployment](./houseMgrAgent_arch.md) | 3-channel model, PA + local deployment, Twilio voice, component map, H×O model |
| [Agent Catalog](./houseMgrAgent_agents.md) | Agent interface contract, LLM usage, build tiers, dependency graph |
| [Data & Auth](./houseMgrAgent_data.md) | Git as master records store, sync model, config schema, GPG auth |
| [Implementation Plan](./houseMgrAgent_impl.md) | Phase-by-phase build from scaffold through full agent suite |

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Records master** | Private Git data repo | Version history, off-host redundancy, sync between PA and local without a separate DB or cloud service |
| **Channel A — voice** | iPhone → Twilio → PA `/voice` | Twilio requires public HTTPS; PA is always-on; no app install on phone |
| **Channel B — remote web** | Browser → PA hosted web UI | Full record viewing and check-in from any device, anywhere |
| **Channel C — local web** | Browser → localhost Mac Flask | Same codebase run locally; fast for at-home admin and record editing |
| **Sync model** | git pull on startup; git push on each write | No separate sync daemon; Git is the sync bus; conflicts surface as merge errors |
| **Orchestrator** | Thin router — zero domain logic in HouseMgr | Domain bugs stay in agents; HouseMgr stays stable as agents are added |
| **LLM** | Haiku for intent parsing; Sonnet for synthesis | Cost-efficient routing; quality response generation |
| **Auth** | GPG-encrypted user DB; Flask session `(house_id, owner_id)` | Sensitive data never on disk as plaintext; follows llcRentalTracker pattern |
| **Multi-house** | H × O — any number of homes × owners per instance | Config-driven; no code change to add a new house or owner |
| **Agent naming** | Universal Agent Naming Schema (UANS): `house.<category>.<agent>.<record>` | Every agent name maps directly to a records path; no separate lookup table; `systems.*`, `designs.*`, `finance.*`, `core.*`, `life.*` are the five categories |
