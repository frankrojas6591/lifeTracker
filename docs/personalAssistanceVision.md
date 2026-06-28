# Personal Assistant Vision

**Version:** 0.2 (Design Draft)
**Author:** Frank Rojas
**Date:** June 2026

---

## 1. Why a Personal Assistant?

A **personalized Personal Assistant (PA) Agent** is your chief of staff — the single trusted point of contact that knows every active domain of your life and prevents any one of them from going dark.

Most people manage their health, finances, home, business, estate, and emotional life in silos. A doctor doesn't know your house is a financial drain. Your financial planner doesn't know your health is declining. Your home manager doesn't know your estate plan is outdated. The cost of these silos compounds with age — missed connections become missed decisions; missed decisions become crises.

The Personal Assistant Agent fixes this by sitting above every life domain, knowing the full picture, and surfacing what actually matters — without you having to ask.

> The goal is not to replace your advisors. It is to be the one person in the room who knows what every advisor is saying — and who synthesizes it into a clear picture of where you stand and what to do next.

### Life Discipline Trackers

| Tracker | Role |
|---|---|
| **lifeTracker** (this) | The Personal Assistant — chief of staff, cross-domain orchestrator |
| **houseTracker** | Home manager — systems, maintenance, financing, aging-in-place |
| **medicalTracker** | Health advisor — history, medications, tests, care advocacy |
| **moneyTracker** | Financial advisor — banking, savings, retirement, debt, investments |
| **estateTracker** | Estate manager — assets, trusts, succession, retirement wealth |
| **emotionalTracker** | Counselor — emotional health, life transitions, stress, grief |
| **faithTracker** | Spiritual advisor — faith practice, community, meaning |
| **businessTracker** | Business manager — LLC accounting, rental income, IRS tax prep |

### Why This Matters at 70

Life in your 70s creates a specific management challenge: the cognitive and logistical load of managing a full life does not decrease — it increases. Systems age. Health changes. Estate decisions become urgent. Emotional resilience is tested. Financial complexity grows.

The PA is built for this stage of life:

- You are never surprised by a life event that should have been anticipated.
- You are never managing two unrelated crises simultaneously when they are actually the same problem viewed from two disciplines.
- You are never wondering what matters most right now.
- You are never alone in navigating a domain you were not trained for.

---

\newpage

---

## 2. System Architecture

The Personal Assistant is the top-level orchestrator. All seven discipline trackers report up to it. All trackers share a single communication layer — one voice channel, one web interface, one local app.

```
╔══════════════════════════════════════════════════════════════════════════╗
║  COMMUNICATION CHANNELS (shared across all trackers)                    ║
║                                                                          ║
║  (A) iPhone Voice          (B) PA Web UI          (C) Local Mac UI      ║
║  ─────────────────          ────────────────        ──────────────────   ║
║  Call Twilio number         Browser → PA URL        Browser → :5000      ║
║  Speak / listen             Full web UI             Same web UI          ║
╚══════════════════════════════════════════════════════════════════════════╝
                    │ Twilio webhook  │ HTTPS  │ HTTP
                    ▼                 ▼        ▼
╔══════════════════════════════════════════════════════════════════════════╗
║  SHARED COMMUNICATION LAYER  (pytracker.core)                           ║
║                                                                          ║
║  Auth (GPG user DB + caller-ID)   │  IntentParser (Haiku)               ║
║  VoiceResponder (TwiML)           │  ResponseSynthesizer (Sonnet)        ║
║  SessionManager (tracker, owner)  │  ActionItemQueue (cross-tracker)     ║
╚══════════════════════════════════════════════════════════════════════════╝
                                   │
                    ┌──────────────▼──────────────┐
                    │  Personal Assistant Agent    │
                    │  lifeTracker Orchestrator    │
                    │  life.pa.*                   │
                    │                              │
                    │  – Route intent → tracker    │
                    │  – Monthly life review       │
                    │  – Cross-tracker synthesis   │
                    │  – Priority arbitration      │
                    └──┬──┬──┬──┬──┬──┬───────────┘
                       │  │  │  │  │  │
           ┌───────────┘  │  │  │  │  └──────────────┐
           │    ┌─────────┘  │  │  └──────────┐      │
           │    │    ┌───────┘  └──────┐       │      │
           ▼    ▼    ▼                 ▼       ▼      ▼
        ┌──────────────────────────────────────────────────┐
        │  house  │ medical │  money │ estate │emotional│faith│
        │Tracker  │Tracker  │Tracker │Tracker │Tracker  │Tracker│
        │house.*  │medical.*│money.* │estate.*│emotion.*│faith.*│
        └────┬────┴────┬────┴────┬───┴────┬───┴────┬────┴──┬────┘
             │         │         │         │        │       │
             └─────────┴─────────┴────┬────┴────────┘       │
                                      │                 llcRentalTracker
                                      ▼                 (separate — work)
                    ╔═════════════════════════════════╗
                    ║  Git Data Repos (private)        ║
                    ║  per-tracker data repos          ║
                    ║  <tracker>-data/<owner_id>/      ║
                    ║  records/**/*.json               ║
                    ╚═════════════════════════════════╝
```

### Cross-Tracker Dependencies

```
PersonalAssistant ◄── ALL trackers (monthly briefings, action items, alerts)

estateTracker ◄── houseTracker (home value, equity, deferred maintenance cost)
              ◄── moneyTracker (account balances, retirement projections)
              ◄── llcRentalTracker (business income, depreciation, K-1)
              ◄── medicalTracker (longevity projection, care cost modeling)

moneyTracker  ◄── houseTracker (HELOC, home projects budget)
              ◄── llcRentalTracker (rental income, business distributions)
              ◄── medicalTracker (health insurance, HSA, out-of-pocket)

medicalTracker ◄── emotionalTracker (mental health ↔ physical health)
               ◄── houseTracker.accessibility (health needs → home mods)
               ◄── moneyTracker (HSA balance, insurance coverage)

emotionalTracker ◄── ALL trackers (stress events from any domain affect emotional state)
                 ◄── faithTracker (spiritual resilience ↔ emotional wellbeing)

houseTracker.finance ◄── moneyTracker (liquidity check before project approval)
houseTracker.accessibility ◄── medicalTracker (mobility needs → home adaptations)
```

---

## 3. Discipline Tracker Profiles

### 3.1 Personal Assistant — `life.pa`

**Role:** Chief of staff. Routes. Synthesizes. Prioritizes. Advocates for simplicity.

**What it knows:** The full priority stack across all trackers. What is overdue. What is in conflict between domains. What the owner most values right now.

**Key scenarios:**
- *Monthly life review:* Pull briefings from all active trackers → produce a unified view of where things stand, what needs attention, and what is on track
- *Cross-domain question:* "Can I afford to replace the HVAC this year?" → coordinate moneyTracker (liquidity), houseTracker (HVAC age and cost), estateTracker (impact on retirement runway)
- *Priority arbitration:* "I have four urgent items from four trackers — which one first?" → the PA knows context across domains and makes the call
- *Burden reduction:* Identify items on the action list that can be deferred, eliminated, or automated

---

### 3.2 houseTracker — `house.*`

**Role:** Home manager. Systems, maintenance, financing, aesthetics, aging-in-place.

**16 agents in 5 UANS categories:** `core.*`, `systems.*`, `designs.*`, `finance.*`, `life.*`

**Key cross-tracker signals:**
- Sends equity and deferred maintenance cost to estateTracker
- Requests liquidity check from moneyTracker before approving major projects
- Sends accessibility gaps to medicalTracker for aging-in-place coordination
- Reports capital improvements to llcRentalTracker if any part of house is business-use

Full design: `houseTracker/docs/HouseManagerVision.md`

---

### 3.3 medicalTracker — `medical.*`

**Role:** Health advocate. Clinical history, medication management, test tracking, care navigation, insurance.

**Domain expertise:** Endocrinology, geriatrics, cardiology (the disciplines most relevant to a 70-year-old owner).

**Key cross-tracker signals:**
- Sends longevity and care-cost projections to estateTracker
- Sends HSA contributions and medical spending to moneyTracker
- Sends mobility/cognition assessment to houseTracker.accessibility
- Receives emotional state from emotionalTracker (mind-body link)

Full design: `medicalTracker/docs/medicalTrackerVision.md` *(planned)*

---

### 3.4 moneyTracker — `money.*`

**Role:** Financial advisor. All personal accounts — checking, savings, investment, retirement (401k, IRA), health (HSA), and debt management.

**Not a business tracker** — that is llcRentalTracker. moneyTracker is personal wealth management.

**Key cross-tracker signals:**
- Sends account balances and liquidity to estateTracker and houseTracker
- Receives rental distributions from llcRentalTracker
- Sends HSA balance to medicalTracker
- Reports retirement runway to PersonalAssistant for life-stage planning

Full design: `moneyTracker/docs/moneyTrackerVision.md` *(planned)*

---

### 3.5 estateTracker — `estate.*`

**Role:** Estate manager. Comprehensive view of all assets (house, accounts, business, personal property) and their disposition. Trust management, succession planning, retirement wealth trajectory.

**Key cross-tracker signals:**
- Aggregates home value from houseTracker, accounts from moneyTracker, business value from llcRentalTracker
- Receives longevity/care projections from medicalTracker
- Sends estate tax exposure and succession priorities to PersonalAssistant

Full design: `estateTracker/docs/estateTrackerVision.md` *(planned)*

---

### 3.6 emotionalTracker — `emotional.*`

**Role:** Counselor and emotional health advisor. Life stage transitions, stress, grief, relationship dynamics, cognitive resilience.

**Domain expertise:** CBT principles, grief stages, life transition models, positive psychology.

**Key cross-tracker signals:**
- Receives stress events from all trackers (financial stress, health events, house crises)
- Informs medicalTracker about mental health status (mind-body link)
- Informs PersonalAssistant about owner's current emotional load (to calibrate how much to surface at once)

Full design: `emotionalTracker/docs/emotionalTrackerVision.md` *(planned)*

---

### 3.7 faithTracker — `faith.*`

**Role:** Spiritual advisor. Faith practice tracking, prayer and reflection calendars, community connection, meaning-making during life transitions.

**Domain expertise:** Catholic spiritual direction, lectio divina, liturgical calendar, community service.

**Key cross-tracker signals:**
- Receives major life events from all trackers (illness, loss, financial change) to suggest spiritual response
- Informs emotionalTracker (spiritual resilience and emotional health are linked)
- Informs PersonalAssistant about community and service commitments

Full design: `faithTracker/docs/faithTrackerVision.md` *(planned)*

---

### 3.8 llcRentalTracker — `llc.*`

**Role:** Primary business manager. LLC accounting, rental income tracking, expense categorization, annual IRS tax prep (Form 1065, Schedule K-1), property agent.

**Note:** This tracker is on the **work account** (`wbgroupmgr/llcRentalTracker`) and is the most mature tracker in the ecosystem. It remains a separate repo and separate deployment.

**Key cross-tracker signals:**
- Sends annual K-1 distributions and business income to moneyTracker
- Sends property depreciation and capital improvements to estateTracker
- Sends business net income to PersonalAssistant for annual life financial review

Full design: `llcRentalTracker/docs/` (extensive — see existing design docs)

---

## 4. Shared Communication Layer

This is the most important shared infrastructure decision: **all trackers share one communication layer**.

The owner does not have a different voice number for medical questions vs. house questions. They call the same number, speak naturally, and the PersonalAssistant routes the intent to the right tracker behind the scenes.

### 4.1 What Is Shared

| Component | Shared? | Notes |
|---|---|---|
| Twilio voice number | Yes — one number | PersonalAssistant answers; routes to tracker |
| PA Flask deployment | Yes — one app | All trackers registered as Flask blueprints under one WSGI |
| Auth (GPG user DB) | Yes — one user DB | Session carries `(owner_id, active_tracker)` |
| IntentParser (Haiku) | Yes — one model call | Parses intent + identifies which tracker handles it |
| ResponseSynthesizer (Sonnet) | Yes — one model call | Synthesizes across one or more tracker responses |
| Monthly check-in loop | Yes — PersonalAssistant aggregates | Pulls briefings from all registered trackers |
| Local Mac web UI | Yes — one Flask app | Same app, all tracker UIs under one server |

### 4.2 What Is Tracker-Specific

| Component | Per Tracker | Notes |
|---|---|---|
| Discipline agents | Per tracker | Each tracker has its own agent suite |
| Records data repo | Per tracker | `<tracker>-data/` private Git repo |
| Domain system prompts | Per tracker | Each agent has its own LLM context |
| Web UI templates | Per tracker | Blueprint owns its own templates |
| UANS namespace | Per tracker | `house.*`, `medical.*`, `money.*`, etc. |

### 4.3 Communication Flow

```
Owner speaks: "How are my finances and can I afford a new roof?"

Step 1 — IntentParser (Haiku):
  → trackers: ["money", "house"]
  → question: "current financial position and cost of roof replacement"
  → mode: query

Step 2 — PersonalAssistant routes:
  → moneyTracker.query("current liquidity and available funds")
  → houseTracker.systems.roofing.query("replacement cost and urgency")

Step 3 — ResponseSynthesizer (Sonnet):
  → mode: voice → ≤ 3 sentences
  "Your current liquid savings are $42K. Roof replacement is estimated at $18–22K
   and the inspector flagged it as needed within 2 years. You have the funds, and
   the timing is good — do you want me to get contractor bids?"
```

### 4.4 pytracker.core Package

The shared layer is extracted into `pytracker.core` — a Python package installed as a dependency by every tracker:

```
pytracker-core/
├── comm/
│   ├── voice.py          ← Twilio TwiML builder, Gather loop
│   ├── web.py            ← shared Flask route helpers
│   └── local.py          ← localhost config helpers
├── auth/
│   ├── gpg_users.py      ← GPG-encrypted user DB
│   └── session.py        ← session management (owner_id, tracker, channel)
├── records/
│   ├── uans.py           ← UANS path derivation (namespace + category + agent + record)
│   └── git_store.py      ← read_json / write_json / git commit+push
├── llm/
│   ├── intent_parser.py  ← Haiku IntentParser; identifies trackers + question
│   └── synthesizer.py    ← Sonnet ResponseSynthesizer; voice vs. web mode
└── models/
    └── models.py         ← AgentResponse, ActionItem, TrackerBriefing dataclasses
```

---

## 5. Universal Agent Naming Schema — Ecosystem Extension

Within each tracker, the UANS defined in `houseTracker` extends naturally:

```
<tracker_namespace>.<category>.<agent>.<record>
```

| Tracker | Namespace | Example UANS | File Path |
|---|---|---|---|
| lifeTracker | `life` | `life.pa.briefings.monthly` | `records/pa/briefings/monthly.json` |
| houseTracker | `house` | `house.systems.hvac.log` | `records/agents/systems/hvac/log.json` |
| medicalTracker | `medical` | `medical.health.medications.current` | `records/agents/health/medications/current.json` |
| moneyTracker | `money` | `money.accounts.retirement.ira` | `records/agents/accounts/retirement/ira.json` |
| estateTracker | `estate` | `estate.assets.real_estate.home` | `records/agents/assets/real_estate/home.json` |
| emotionalTracker | `emotional` | `emotional.journal.events.log` | `records/agents/journal/events/log.json` |
| faithTracker | `faith` | `faith.practice.prayer.calendar` | `records/agents/practice/prayer/calendar.json` |
| llcRentalTracker | `llc` | `llc.books.gl.ledger` | (existing, separate repo) |

The PersonalAssistant's intent parser identifies both the tracker namespace and the category/agent from the owner's spoken or typed query.

---

## 6. Cross-Tracker Scenarios

### 6.1 The Annual Life Review (January)

**Trackers:** ALL

PersonalAssistant runs the annual review — one unified conversation touching every domain:
- Medical: key health events, upcoming screenings, medication changes
- Money: account performance, retirement runway update, debt status
- Estate: net worth snapshot, trust review flag, beneficiary currency
- House: deferred maintenance list, systems approaching end-of-life, accessibility gaps
- LLC: business net income, distributions received, tax prep status
- Emotional: major life events and how they were processed; stress level trending
- Faith: practice consistency, community engagement, spiritual goals

Output: a 2-page annual life summary — what happened, what it means, what to do next.

---

### 6.2 Health Crisis Response

**Trackers:** medical · emotional · money · house · estate

When a significant health event occurs:
1. medicalTracker logs the event and assesses care plan impact
2. emotionalTracker records the stress event and offers coping framework
3. moneyTracker checks insurance coverage and out-of-pocket exposure
4. houseTracker.accessibility flags modifications that support recovery
5. estateTracker flags whether any advance directive or care proxy documents need updating
6. PersonalAssistant presents a unified "here's what this means and what to do" response

---

### 6.3 Major Financial Decision

**Trackers:** money · estate · house · llc

"Should I sell the house and move to a smaller place?"
1. houseTracker: current home value, deferred maintenance estimate, selling costs
2. moneyTracker: current liquid position, impact on income if equity is freed
3. estateTracker: tax basis, §121 exclusion, impact on estate plan
4. llcRentalTracker: any business-use allocations to reconcile
5. medicalTracker: accessibility of potential new home given current and projected health
6. PersonalAssistant: synthesizes a recommendation — financially, medically, emotionally sound?

---

### 6.4 Estate Planning Trigger

**Trackers:** estate · money · house · llc · medical · faith

Triggered annually or when a major life event occurs (health change, death of spouse, large asset change):
- Full asset inventory (house + accounts + business)
- Updated longevity and care-cost model (from medicalTracker)
- Trust and beneficiary review
- Advance directive currency check
- Faith-informed values clarification for end-of-life decisions

---

## 7. Design Principles

1. **One voice, many domains.** The owner has one relationship — with the PersonalAssistant. All trackers surface through it, never directly. The owner should never need to remember which app or which phone call handles which domain.

2. **The PA advocates for less cognitive load, not more.** The system's job is to reduce what the owner needs to think about — not to create a dashboard they have to monitor. The default is silence; the exception is action.

3. **Cross-domain synthesis is the highest-value function.** Any single tracker can answer domain questions. Only the PersonalAssistant can answer questions that span domains. Prioritize building the cross-tracker routing layer before extending individual trackers.

4. **Shared comm layer, isolated domain logic.** The communication layer (voice, web, auth, LLM) is shared infrastructure. Each tracker's domain expertise is fully isolated. No tracker knows about another tracker's internals — they only communicate through the PersonalAssistant.

5. **Life-stage calibration.** Every response is calibrated to the Senior Owner stage: proactive, low-friction, clear recommendation (not a menu of options), with energy and capacity constraints respected.

6. **Trust through consistency.** The system only earns trust if it shows up reliably on the monthly check-in, remembers what was discussed, and follows through on action items. A system that forgets is worse than no system.

7. **No domain gets permanently dark.** Even if the owner hasn't interacted with a tracker in months, the monthly check-in surfaces it. No domain is allowed to go unreviewed for more than 90 days.

---

## 8. Build Order / Provisioning Sequence

Build in dependency order. The communication layer must exist before any tracker can register. The PersonalAssistant routes before trackers can answer.

| Phase | Component | Milestone |
|---|---|---|
| 0 | `pytracker.core` — shared comm layer | One voice number routes to one PA; auth works |
| 1 | PersonalAssistant (lifeTracker) — orchestrator | Monthly check-in loop runs end-to-end with stub responses |
| 2 | houseTracker — Tier 1 agents | First discipline tracker integrated; house queries answered by voice |
| 3 | medicalTracker — Tier 1 agents | Health queries answered; health events cross-posted to PA monthly review |
| 4 | moneyTracker — Tier 1 agents | Financial position queryable; monthly review shows account snapshot |
| 5 | estateTracker | Full asset view; estate plan currency tracked |
| 6 | emotionalTracker | Stress events tracked; emotional load informs PA's communication style |
| 7 | faithTracker | Practice calendar; liturgical-calendar-aware check-ins |
| 8+ | Cross-tracker scenarios | Active routing of multi-domain queries; annual life review automated |

---

*This document is v0.2 — working draft. Next: establish pytracker.core shared package design and update each discipline tracker vision doc.*
