# lifeTracker — Commons Design Index

**Version:** 1.0
**Date:** June 2026
**Status:** Design — pre-implementation

---

## 1. What This Directory Covers

`docs/design/` contains the design and implementation plans for **lifeTracker's shared common services** — the infrastructure that all discipline agents depend on. These are not agent-specific docs; they are the scaffolding every agent builds on top of.

| Doc | Service | What It Covers |
|---|---|---|
| `lifeTracker_auth.md` | **Auth** | Login, owner profile, GPG user DB, JWT sessions, `ltCmd.py --setup` |
| `lifeTracker_records.md` | **RecordAgent** | UANS path system, git-as-master store, read/write API |
| `lifeTracker_commWeb.md` | **Web UI** | Flask app, blueprint architecture, chat + checkin routes |
| `lifeTracker_commIOS.md` | **iOS API** | `/api/*` endpoints consumed by `mobileAudioIO` |

Discipline-agent-specific design docs live under each agent's `docs/design/` directory (e.g., `houseAgent/docs/design/`).

---

## 2. Code Repo Structure

```
lifeTracker/                    ← this repo
│
├── ltCmd.py                    ← CLI admin: --setup, --start, --check, --backup
├── wsgi.py                     ← Flask WSGI entry point for PythonAnywhere
├── requirements.txt
├── setup_paths.py              ← anchors all paths from repo root; reads config.json
├── config.json.example         ← schema template — no secrets committed
│
├── life/                       ← PersonalAssistant orchestrator
│   ├── pa.py                   ← PA: routes, synthesizes, monthly check-in
│   ├── router.py               ← IntentParser (Haiku) → agent routing
│   ├── synthesizer.py          ← ResponseSynthesizer (Sonnet); voice vs. web mode
│   ├── checkin.py              ← monthly check-in loop: collect briefings → unified view
│   └── models.py               ← AgentResponse, ActionItem, AgentBriefing dataclasses
│
├── core/                       ← shared infrastructure (auth + records)
│   ├── auth/
│   │   ├── gpg_users.py        ← GPG-encrypted owner DB: read/write/verify
│   │   ├── session.py          ← JWT issue/verify; Flask session helpers
│   │   └── decorators.py       ← @login_required, @owner_required
│   └── records/
│       ├── record_agent.py     ← RecordAgent: read/write/append/provision
│       ├── uans.py             ← UANS → filesystem path derivation
│       └── git_store.py        ← write_json / read_json / git commit+push
│
├── ui/                         ← Flask web UI (shared across all discipline agents)
│   ├── auth.py                 ← /login, /logout, /register routes
│   ├── chat.py                 ← /chat: browser text query interface
│   ├── checkin.py              ← /checkin: monthly PA dashboard
│   ├── api.py                  ← /api/*: iOS endpoints (query, auth, notifications)
│   └── templates/
│       ├── base.html
│       ├── login.html
│       ├── chat.html
│       └── checkin.html
│
├── houseAgent/                 ← House Manager discipline agent
│   ├── house_mgr.py            ← HouseMgr: registers with PA, implements PA interface
│   ├── agents/
│   │   ├── base.py             ← DisciplineAgent abstract base class
│   │   └── ...                 ← one file per discipline sub-agent
│   ├── ui/
│   │   └── house_views.py      ← house-specific Flask blueprints
│   └── docs/
│       ├── HouseManagerVision.md
│       └── design/             ← houseAgent implementation docs
│
├── [medicalAgent/ moneyAgent/ estateAgent/ emotionalAgent/ faithAgent/]
│   └── docs/                   ← agent vision + design docs (design phase)
│
├── recordAgent/
│   └── docs/                   ← RecordAgent vision + data schema docs
│
└── docs/
    ├── lifeTrackerVision.md    ← ecosystem-level vision (authoritative)
    ├── lifeTrackerDiagram.svg  ← architecture SVG
    └── design/                 ← this directory: commons design docs
```

**Outside git (never committed):**

```
~/.lifeTracker/
├── config.json                 ← secrets: Twilio keys, Flask secret, API keys, paths
└── owners.json.gpg             ← GPG-encrypted owner DB

~/dev/pyTrackers/lifeTracker-data/    ← private data repo (separate git repo)
└── records/
    └── agents/
        ├── house/              ← house.* UANS namespace
        ├── medical/            ← medical.* UANS namespace
        └── ...
```

---

## 3. Phase Plan — Common Services → houseAgent

### Phase 0 — Flask Scaffold + Auth

**Milestone:** Flask app running on PythonAnywhere. `/login` works. `ltCmd.py --setup` wizard runs. No agents yet.

| Task | Module | Notes |
|---|---|---|
| `setup_paths.py` | `setup_paths.py` | Reads `~/.lifeTracker/config.json`; exposes all path constants |
| `ltCmd.py --setup` | `ltCmd.py` | Interactive wizard: writes config.json, inits GPG owner DB, creates data repo checkout |
| Flask app factory | `wsgi.py` | `create_app()` registers all blueprints; channel detection middleware |
| Auth routes | `ui/auth.py` | `/login`, `/logout`, `/register` |
| `@login_required` decorator | `core/auth/decorators.py` | Redirects to `/login` if no valid session |
| GPG owner DB | `core/auth/gpg_users.py` | Add/verify/list owners; encrypted at rest |
| JWT session | `core/auth/session.py` | Issue JWT on login; verify on every request |
| Milestone test | — | Browser: go to PA URL → redirects to `/login` → enter passphrase → logged in |

Full design: `lifeTracker_auth.md`

---

### Phase 1 — RecordAgent + Data Repo

**Milestone:** RecordAgent provisions the full `records/agents/` directory tree. `write_json` and `read_json` work and auto-commit to `lifeTracker-data` git repo.

| Task | Module | Notes |
|---|---|---|
| `lifeTracker-data` repo | private GitHub | Create private repo; clone into `~/.lifeTracker/data/` or `~/dev/pyTrackers/lifeTracker-data/` |
| UANS path derivation | `core/records/uans.py` | `uans_to_path("house.systems.hvac")` → `records/agents/house/systems/hvac/` |
| Git store | `core/records/git_store.py` | `write_json(uans, filename, data)` → write → `git commit` → `git push` |
| RecordAgent provisioning | `core/records/record_agent.py` | `provision()` creates full directory tree for all agent namespaces |
| `ltCmd.py --setup` extension | `ltCmd.py` | Calls `RecordAgent.provision()` after config wizard |
| Milestone test | — | `python ltCmd.py --setup` → inspect `lifeTracker-data/records/agents/` → all directories exist |

Full design: `lifeTracker_records.md`

---

### Phase 2 — Web UI Communication Layer

**Milestone:** Log in at the PA URL → type a question in `/chat` → see PA respond (stub agents OK). Monthly check-in dashboard at `/checkin` shows placeholder briefings.

| Task | Module | Notes |
|---|---|---|
| PA orchestrator | `life/pa.py` | Registers all discipline agents; routes query to correct agent(s) |
| IntentParser | `life/router.py` | Haiku: parse `{agents: [...], question: str, mode: query/record}` |
| ResponseSynthesizer | `life/synthesizer.py` | Sonnet: `voice_mode=True` caps at 3 sentences; `web_mode` returns full structured text |
| Models | `life/models.py` | `AgentResponse`, `ActionItem`, `AgentBriefing` dataclasses |
| Chat route | `ui/chat.py` | `POST /chat`: text in → PA → response back → render |
| Check-in route | `ui/checkin.py` | `GET /checkin`: PA calls `brief()` on all registered agents → unified dashboard |
| Base templates | `ui/templates/` | `base.html`, `chat.html`, `checkin.html` |
| Milestone test | — | `/chat`: type "What's the status of my house?" → PA returns stub response |

Full design: `lifeTracker_commWeb.md`

---

### Phase 3 — iOS API Layer

**Milestone:** `POST /api/query` with Bearer token returns PA response. `mobileAudioIO` app can complete end-to-end voice query.

| Task | Module | Notes |
|---|---|---|
| `/api/auth/token` | `ui/api.py` | POST passphrase → verify GPG owner DB → return JWT |
| `/api/query` | `ui/api.py` | POST `{text, channel, owner_id}` → PA → `{response_text, action_items}` |
| `/api/notifications` | `ui/api.py` | GET open action items for iOS Notifications tab |
| Channel detection | `life/synthesizer.py` | `channel: "ios_voice"` → same ≤3 sentence constraint as Twilio voice |
| Bearer auth middleware | `core/auth/decorators.py` | `Authorization: Bearer <jwt>` validates for `/api/*` routes |
| Milestone test | — | `curl POST /api/query` with valid token → JSON response |

Full design: `lifeTracker_commIOS.md`

---

### Phase 4 — houseAgent (Tier 1)

**Milestone:** Ask a house question via `/chat` or iOS app → houseAgent answers. Monthly check-in includes a house briefing.

Prerequisites: Phases 0–3 stable and tested.

See `houseAgent/docs/design/houseMgrAgent_impl.md` for the full houseAgent phase plan.

| Task | Module | Notes |
|---|---|---|
| HouseMgr registers with PA | `houseAgent/house_mgr.py` | Implements `brief()`, `query()`, `audit()`, `record()` |
| HouseRecords agent | `houseAgent/agents/house_records.py` | JSON CRUD through RecordAgent interface |
| House Profile agent | `houseAgent/agents/house_profile.py` | Onboarding Q&A; feeds house context to all sub-agents |
| Tier 1 voice path | `houseAgent/house_mgr.py` | PA routes house query → HouseMgr → spoken response |
| House blueprints | `houseAgent/ui/house_views.py` | Register `/house/*` routes with Flask app |
| Milestone test | — | "What systems need service?" → HouseMgr answers from house profile data |

---

### Phase 5+ — Remaining Discipline Agents

Each agent follows the same pattern: implement `DisciplineAgent`, register with PA, write through RecordAgent. Build order per `lifeTrackerVision.md §10`:

`medicalAgent` → `moneyAgent` → `estateAgent` → `emotionalAgent` → `faithAgent`

---

## 4. Shared Contracts

### 4.1 DisciplineAgent Interface

Every discipline agent implements these four methods. The PA calls only these — never accesses agent internals.

```python
class DisciplineAgent:
    def brief(self) -> AgentBriefing:
        """2-3 sentence current domain status. Called monthly."""

    def query(self, question: str, context: dict) -> AgentResponse:
        """Answer a domain question. PA passes cross-agent context dict."""

    def audit(self) -> list[ActionItem]:
        """Proactive scan — return items needing owner attention."""

    def record(self, event: dict) -> None:
        """Log a domain event. Called when owner reports something happened."""
```

`AgentResponse`, `ActionItem`, `AgentBriefing` defined in `life/models.py` — the only shared import contract. No agent imports from another agent.

### 4.2 Voice Response Constraint

When synthesizing for voice (Twilio or `channel: "ios_voice"`), the Synthesizer produces **≤ 3 sentences** of spoken prose — no markdown, no lists, no headers. Full structured response is always written to RecordAgent and available in the web UI.

### 4.3 UANS Naming

Every agent name, record file, and directory path derives from the 4-segment UANS:

```
<namespace>.<category>.<agent>.<record>
         ↓         ↓       ↓        ↓
records/agents/<namespace>/<category>/<agent>/<record>.json
```

---

## 5. Deployment

**Primary deployment:** PythonAnywhere (PA)
- Flask WSGI app at `<username>.pythonanywhere.com`
- Twilio voice webhook: `https://<username>.pythonanywhere.com/voice`
- PA URL: `https://<username>.pythonanywhere.com`

**Local Mac (development):**
- `python ltCmd.py --start` → Flask at `localhost:5000`
- No Twilio (voice webhook not reachable); web UI + API fully functional
- iOS app on device connects to Mac's LAN IP: `192.168.x.x:5000`

**Config (never committed):**
```json
{
  "owner_id": "frankr6591",
  "flask_secret": "...",
  "twilio_account_sid": "...",
  "twilio_auth_token": "...",
  "twilio_phone_number": "+1...",
  "anthropic_api_key": "...",
  "data_repo_path": "/home/frankr6591/lifeTracker-data",
  "gpg_owner_db": "/home/frankr6591/.lifeTracker/owners.json.gpg",
  "gpg_key_id": "..."
}
```
