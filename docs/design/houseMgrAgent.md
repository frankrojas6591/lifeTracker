# HouseMgr Agent — Top-Level Design

**Version:** 0.2
**Date:** June 2026
**Status:** Design — pre-implementation

---

## 1. Design Goals

### 1.1 Lightweight Orchestrator

The HouseMgr is a **thin router and response synthesizer** — it holds no domain knowledge itself. Every piece of expertise lives in a discipline agent. The HouseMgr's job is:

1. Parse owner intent from natural language (via LLM)
2. Identify which agents are relevant
3. Query those agents with the current house context
4. Synthesize a unified response
5. Route any stored outcomes back to HouseRecords

**Anti-pattern to avoid:** A "fat" HouseMgr that accumulates logic for specific domains (e.g., knows HVAC rules, knows tax codes). That logic belongs in the agent. The HouseMgr only knows the *agent registry* — not what the agents know.

### 1.2 Design Principles (from Vision)

- **Owner never tracks details** — agents do. HouseMgr surfaces, not collects.
- **Proactive over reactive** — agents push action items to the monthly check-in queue; HouseMgr presents them.
- **Recommendation, not menu** — synthesized output is a clear "here's what to do," not a list of options.
- **DIY-first, frugal** — cost framing defaults to quality-for-budget, not premium-fastest.
- **Aging-in-place thread** — every agent response considers the owner's current life stage.

---

## 2. Position Within pyTrackers

```
pyTrackers/
├── llcRentalTracker/   ← LLC accounting & IRS (Flask, ledger engine, MCP)
├── medicalTracker/     ← Personalized health management (early stage)
├── houseTracker/       ← THIS PROJECT
│   ├── houseMgr/       ← Orchestrator (lightweight router)
│   ├── agents/         ← Discipline agents (one module per agent)
│   ├── records/        ← HouseRecords DB (JSON, local)
│   ├── ui/             ← Flask web interface (monthly check-in, chat)
│   └── wsCmd.py        ← CLI entry point (start, onboard, check-in)
└── financialTracker/   ← TBD — will integrate with Financing agent
```

**No shared infrastructure with sibling trackers.** Any future cross-tracker integration (e.g., houseTracker ↔ medicalTracker for Accessibility agent, houseTracker ↔ financialTracker for utility bills) will be explicitly designed as narrow API contracts, not shared code.

### 2.1 pyTrackers Conventions Followed

- Python 3, Flask for web UI
- `wsCmd.py` as the CLI entry point
- `setup_paths.py` anchors all paths — no hardcoded absolutes
- JSON files as the persistent data store (no external DB)
- No docstrings; one-line inline comments only when WHY is non-obvious
- Tests under `tests/` using `python -m tests.test_<module>`

---

### 2.2 Configuration Profile (`config.json`)

All filesystem paths, house records, and secrets live in **one file outside the git repo**:

```
~/.houseTracker/config.json
```

`config.json` is never committed. The git repo contains only code. All house data — records, documents, agent state — lives under `top_folder` for each house, also outside git.

**config.json schema:**

```json
{
  "default":            "ranch_house",
  "APP_SECRET_KEY":     "<flask signing key — one per houseTracker instance>",
  "APP_GPG_PASSPHRASE": "<gpg passphrase — encrypts the user db>",
  "houses": [
    {
      "house_id":   "ranch_house",
      "house_name": "Westwood Ranch",
      "top_folder": "~/houseTracker/ranch_house",
      "address":    "123 Ranch Rd, Austin TX 78701",
      "owner_id":   "frank"
    }
  ],
  "owners": [
    {
      "owner_id":  "frank",
      "full_name": "Frank Rojas",
      "email":     "frankr6591@gmail.com"
    }
  ]
}
```

`setup_paths.py` reads `~/.houseTracker/config.json` and exposes module-level path constants — `TOP`, `RECORDS_DIR`, `DOCUMENTS_DIR` — for the active house session. No hardcoded absolute paths anywhere else in the codebase.

---

### 2.3 H × O Service Model

The app supports **H homes × O owners**:

- **H (homes):** A single houseTracker instance manages any number of houses. Each house has its own `top_folder`, its own agent records, and its own document vault.
- **O (owners):** Multiple owners can be registered (e.g., spouses, family members). Each owner authenticates separately and has access to the house(s) they are associated with.

The active session context is `(house_id, owner_id)`. The Flask session stores both after login. Multi-house owners select the active house at login or via a house-switcher in the nav bar.

---

## 3. Architecture

### 3.1 Component Map

```
Owner (voice / chat / monthly check-in)
        │
        ▼
┌──────────────────────────────────────────┐
│       ConfigLoader + AuthLayer            │
│  ~/.houseTracker/config.json             │
│  session: (house_id, owner_id, role)     │
└──────────┬───────────────────────────────┘
           │  house context injected on every request
           ▼
┌─────────────────────────────────────────┐
│            HouseMgr (Orchestrator)       │
│                                          │
│  IntentParser  ──►  AgentRouter          │
│       │                  │               │
│  (Claude API)     AgentRegistry          │
│                          │               │
│               ResponseSynthesizer        │
│                   (Claude API)           │
└──────────┬──────────────────────────────┘
           │  queries / receives action items
           ▼
┌──────────────────────────────────────────┐
│           Discipline Agents              │
│  Architecture │ HVAC │ Plumbing │ ...    │
│  (each agent: query / audit / record)    │
└──────────┬───────────────────────────────┘
           │  all reads/writes → top_folder/records/
           ▼
┌──────────────────────────────────────────┐
│           HouseRecords (DB)              │
│  ~/houseTracker/<house_id>/records/      │
│  house_profile.json                      │
│  agents/<agent_name>/records.json        │
│  agents/<agent_name>/action_items.json   │
│  documents/ (photos, PDFs, invoices)     │
└──────────────────────────────────────────┘
```

### 3.2 HouseMgr Core Loop

Two operating modes:

**Interactive mode** — owner sends a message, HouseMgr responds immediately:

```
owner_input → IntentParser → [relevant agents] → ResponseSynthesizer → reply
```

**Monthly check-in mode** — scheduled review of all agents:

```
for each agent:
    agent.audit() → list of action items
HouseMgr collects, ranks, presents as check-in report
Owner dismisses / defers / acts on items
```

### 3.3 Agent Interface Contract

Every discipline agent implements the same four methods. The HouseMgr only calls these — it never accesses agent internals.

```python
class DisciplineAgent:
    def brief(self) -> str:
        """Return a 2-3 sentence summary of current domain status."""

    def query(self, question: str, context: dict) -> AgentResponse:
        """Answer a domain-specific question given house context."""

    def audit(self) -> list[ActionItem]:
        """Proactive scan — return items needing owner attention."""

    def record(self, event: dict) -> None:
        """Log a domain event (repair done, system installed, etc.)."""
```

`AgentResponse` and `ActionItem` are shared dataclasses in `houseMgr/models.py` — the only shared contract between HouseMgr and agents.

### 3.4 LLM Usage Pattern

The HouseMgr uses Claude in two places only:

| Step | Input | Output | Model |
|---|---|---|---|
| **IntentParser** | Raw owner text | Intent JSON: `{agents: [...], question: str, mode: query/record/plan}` | Haiku (fast, cheap) |
| **ResponseSynthesizer** | Collected agent responses | Single coherent reply to owner | Sonnet |

Individual agents also call the LLM internally for domain reasoning — each agent manages its own LLM calls using its domain knowledge base (system prompt) + house-specific context from HouseRecords.

### 3.5 HouseRecords DB Structure

The records directory lives at `top_folder` for the active house — outside the git repo.

```
~/houseTracker/<house_id>/             ← top_folder from config.json
├── records/
│   ├── house_profile.json             ← House Profile agent output
│   ├── systems_registry.json          ← All systems/appliances
│   └── agents/
│       ├── architecture/
│       │   ├── knowledge.json         ← Floor plan, structural notes
│       │   └── action_items.json      ← Pending items from last audit
│       ├── hvac/
│       ├── plumbing/
│       └── ...                        ← One directory per agent
└── documents/                         ← PDFs, photos, invoices
    ├── permits/
    ├── invoices/
    └── photos/
```

All JSON. All local. No cloud dependency. `setup_paths.py` sets `RECORDS_DIR` and `DOCUMENTS_DIR` to these paths at startup.

---

### 3.6 Authentication & Login Layer

Follows the `llcRentalTracker` pattern (`llcLogin_auth.py`).

**User DB:** A single GPG-encrypted file at `~/.houseTracker/users.json.gpg` (outside git). Decrypted in-memory only; never written to disk as plaintext. Passphrase loaded from `config.json` → `APP_GPG_PASSPHRASE`.

**Roles:**

| Role | Access |
|---|---|
| `houseMgr` | Full admin — all houses, user management, configurator |
| `owner` | Full access to their associated house(s) |
| `viewer` | Read-only access to a house (e.g., family member) |

**Routes registered by `make_auth_routes(app)` in `ui/houseLogin_auth.py`:**

| Route | Method | Description |
|---|---|---|
| `/login` | GET/POST | Credential check against GPG user DB; sets session context |
| `/logout` | GET | Clears session, redirects to `/login` |
| `/register` | GET/POST | `houseMgr` only — creates new user account |
| `/select_house` | GET/POST | Multi-house owners pick the active house after login |

**House context stored in Flask session:**

```python
session["logged_in"] = True
session["username"]  = "frank"
session["role"]      = "owner"
session["house_id"]  = "ranch_house"   # active house
session["owner_id"]  = "frank"
```

`login_required` decorator (from `ui/houseLogin_auth.py`) protects all routes except `/login`, `/logout`, and `/register`. Flask secret key is loaded from `config.json` → `APP_SECRET_KEY` at startup.

---

## 4. Agent Build Priority & Interdependencies

### 4.1 Dependency Map

```
HouseRecords ◄─── ALL agents (every agent reads/writes here)
House Profile ◄─── ALL agents (every agent reads for house context)
Communication ◄─── ALL agents (all push action items here for check-in)

Architecture ◄─── Plumbing, Electrical, HVAC, Roofing, Landscaping, Decoration
                  (all need floor plan / structural knowledge)

Financing ◄─── Architecture, HVAC, Electrical, Plumbing, Roofing
               (all project agents need budget framing)

Tax ◄─── Financing (capital improvement categorization)
Investment ◄─── Tax (basis), Financing (equity)

Accessibility ◄─── Architecture (structural mods), Security (lighting/safety)
Landscaping ◄─── Architecture (site map), Plumbing (irrigation zones)
Decoration ◄─── Architecture (floor plan, room dimensions)
HVAC ◄─── Electrical (panel capacity for heat pump conversion)
```

### 4.2 Build Tiers

Agents within a tier can be built in parallel. Each tier depends on the tier above it being stable.

---

**Tier 1 — Infrastructure** *(build first; nothing else works without these)*

| Priority | Component | Why First |
|---|---|---|
| 1 | **Setup WebServer** | `wsCmd.py --setup` flow: creates `~/.houseTracker/config.json`, bootstraps the records directory tree, and registers the first user. Nothing else starts without this. |
| 2 | **Configurator (Owner, House)** | Web UI for registering and editing houses and owners in `config.json`. Must exist before agents can be configured for a specific house. |
| 3 | **HouseRecords** | All agents store and retrieve through here; must exist before any agent is built |
| 4 | **House Profile** | Briefs every agent with house context; onboarding starts here |
| 5 | **Communication** | Owner interaction layer; monthly check-in and alert routing |

---

**Tier 2 — House Knowledge** *(understand the physical asset before advising on it)*

| Priority | Agent | Why This Tier |
|---|---|---|
| 4 | **Architecture** | Floor plan and structural knowledge is a prerequisite for Plumbing, Electrical, HVAC, Landscaping, Decoration, and Roofing agents |

---

**Tier 3 — Safety & Life Stage** *(immediate value; senior owner priority)*

| Priority | Agent | Why This Tier |
|---|---|---|
| 5 | **Security & Safety** | Smoke/CO detectors, fall lighting, emergency plan — actionable today with no dependencies |
| 6 | **Accessibility & Aging-in-Place** | Critical for a 70-year-old owner; depends on Architecture for structural mods |
| 7 | **HVAC** | Comfort, indoor air quality, health impact; seasonal maintenance calendar has immediate ROI |

---

**Tier 4 — Critical Systems** *(high failure cost; proactive monitoring value)*

| Priority | Agent | Why This Tier |
|---|---|---|
| 8 | **Electrical** | Safety-critical; panel age and GFCI coverage audit is high-value; needed by HVAC (heat pump) |
| 9 | **Plumbing** | High failure risk (water damage); water heater lifespan tracking |
| 10 | **Roofing & Building Envelope** | Most expensive deferred maintenance failure; annual inspection calendar |

---

**Tier 5 — Financial Intelligence** *(needed before any major project is approved)*

| Priority | Agent | Why This Tier |
|---|---|---|
| 11 | **Financing** | Budget framing and ROI for every Tier 3–4 project recommendation |
| 12 | **Tax** | Capital improvements tracking should start at first project; basis matters at sale |
| 13 | **Investment & Value** | Home value model and project ROI; depends on Tax (basis) and Financing (equity) |

---

**Tier 6 — Quality of Life** *(valuable but not safety-critical)*

| Priority | Agent | Why This Tier |
|---|---|---|
| 14 | **Appliances** | Lifecycle tracking; lower urgency than systems |
| 15 | **Landscaping** | Outdoor living, curb appeal, low-maintenance conversion |
| 16 | **Decoration & Interior Design** | Aesthetics and finish selection; primarily needed for remodel projects |

---

### 4.3 Interdependency Summary Table

| Agent | Hard Dependencies | Soft Dependencies |
|---|---|---|
| HouseRecords | — | — |
| House Profile | HouseRecords | — |
| Communication | HouseRecords | All agents (receives action items) |
| Architecture | HouseRecords, House Profile | — |
| Security & Safety | HouseRecords | Communication |
| Accessibility | Architecture | Security, HVAC, medicalTracker (external) |
| HVAC | Architecture | Electrical, Financing |
| Electrical | Architecture | Financing |
| Plumbing | Architecture | Financing |
| Roofing | Architecture | Electrical (solar), Financing |
| Financing | HouseRecords | All project agents |
| Tax | Financing | Investment |
| Investment | Tax, Financing | — |
| Appliances | HouseRecords | Financing |
| Landscaping | Architecture, Plumbing | Financing |
| Decoration | Architecture | Financing |

---

## 5. Project File Structure

**Outside git (config & data):**

```
~/.houseTracker/
├── config.json                 ← Profile: houses, owners, secrets (never committed)
└── users.json.gpg              ← GPG-encrypted user DB (AES-256 symmetric)

~/houseTracker/<house_id>/      ← top_folder for each registered house
├── records/
│   ├── house_profile.json
│   ├── systems_registry.json
│   └── agents/
│       └── <agent_name>/
│           ├── knowledge.json
│           └── action_items.json
└── documents/
    ├── permits/
    ├── invoices/
    └── photos/
```

**Repo (code only):**

```
houseTracker/
├── wsCmd.py                    ← CLI: --setup, --start, --onboard, --checkin
├── wsgi.py                     ← Flask WSGI entry
├── requirements.txt
├── setup_paths.py              ← Reads ~/.houseTracker/config.json; sets TOP, RECORDS_DIR, etc.
│
├── houseMgr/                   ← Orchestrator package
│   ├── __init__.py
│   ├── router.py               ← IntentParser + AgentRouter
│   ├── synthesizer.py          ← ResponseSynthesizer
│   ├── registry.py             ← AgentRegistry (maps name → agent instance)
│   ├── checkin.py              ← Monthly check-in workflow
│   └── models.py               ← AgentResponse, ActionItem dataclasses
│
├── agents/                     ← One module per discipline agent
│   ├── base.py                 ← DisciplineAgent base class (interface contract)
│   ├── house_records.py        ← HouseRecords agent (A.14)
│   ├── house_profile.py        ← House Profile agent (A.15)
│   ├── communication.py        ← Communication agent (A.16)
│   ├── architecture.py         ← Architecture agent (A.1)
│   └── ...                     ← One file per remaining agent
│
├── ui/                         ← Flask views
│   ├── __init__.py
│   ├── houseLogin_auth.py      ← Auth routes + login_required decorator (GPG user DB)
│   ├── configurator.py         ← Configurator routes: manage houses + owners in config.json
│   ├── chat.py                 ← Chat / voice interface route
│   ├── checkin.py              ← Monthly check-in UI route
│   └── templates/
│       ├── login.html
│       ├── register.html
│       ├── select_house.html
│       ├── configurator.html
│       └── ...
│
├── tests/
│   ├── test_router.py
│   ├── test_checkin.py
│   ├── test_setup_paths.py
│   └── test_agents/
│       └── test_house_records.py
│
└── docs/
    ├── HouseManagerVision.md   ← Vision (also README.md)
    └── design/
        └── houseMgrAgent.md    ← THIS FILE
```

---

## 6. Implementation Approach

### Phase 0 — Scaffold (no agents yet)

- `wsCmd.py --setup` flow: create `~/.houseTracker/config.json`, bootstrap the records directory tree, register the first user (GPG-encrypted user DB)
- `setup_paths.py`: reads `~/.houseTracker/config.json`, sets `TOP`, `RECORDS_DIR`, `DOCUMENTS_DIR` module globals
- `ui/houseLogin_auth.py`: GPG user DB, `make_auth_routes()`, `login_required` decorator
- `ui/configurator.py`: Configurator routes for adding/editing houses and owners in `config.json`
- `houseMgr/models.py`: `AgentResponse`, `ActionItem` dataclasses
- `agents/base.py`: `DisciplineAgent` interface
- Flask app skeleton: `/login`, `/logout`, `/register`, `/select_house`, `/chat`, `/checkin`, `/configurator`

### Phase 1 — Tier 1 Agents (infrastructure)

Build and test HouseRecords → House Profile → Communication in sequence. At the end of Phase 1, the monthly check-in loop runs end-to-end with stub data.

### Phase 2 — Tier 2 Agent (Architecture)

The Architecture agent is the gateway for all subsequent system agents. Onboarding (floor plan intake, room tagging, site map) is the Phase 2 deliverable.

### Phase 3+ — Remaining Tiers

Each tier follows the priority order in §4.2. Every new agent follows the `DisciplineAgent` interface from day one — no exceptions — to keep the HouseMgr router unchanged as agents are added.

---

## 7. Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Orchestrator pattern** | Thin router (no domain logic in HouseMgr) | Keeps HouseMgr stable as agents are added; domain bugs stay in agents |
| **LLM for intent parsing** | Haiku (fast/cheap) for routing, Sonnet for synthesis | Intent parsing is a simple classification; synthesis needs quality |
| **Agent LLM calls** | Each agent manages its own | Agents have domain-specific system prompts; centralized LLM would require HouseMgr to know all domains |
| **Storage** | Local JSON via HouseRecords agent | Consistent with pyTrackers; no cloud dependency; sensitive data stays local |
| **Config profile location** | `~/.houseTracker/config.json` (outside git) | House data and secrets are personal; same pattern as llcRentalTracker; nothing sensitive ever enters the repo |
| **Multi-house model (H × O)** | Houses and owners defined in config.json; session holds `(house_id, owner_id)` | Supports multiple properties and co-owners without coupling agents to a single house at the code level |
| **Authentication** | GPG-encrypted user DB (`users.json.gpg`); `llcRentalTracker` pattern | AES-256 symmetric encryption; passphrase never touches disk; proven pattern from sibling tracker |
| **Agent interface** | 4-method contract (brief/query/audit/record) | Minimal surface area; new agents drop in without changing router |
| **Monthly check-in as primary UX** | Scheduled pull, not push | Matches owner preference; avoids notification fatigue; agents queue items between check-ins |
| **No shared infrastructure with sibling trackers** | Explicit integration contracts only | Each tracker evolves independently; avoids coupling |
