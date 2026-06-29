# houseAgent — Implementation Plan

**Version:** 1.0
**Date:** June 2026
**Parent:** [Design Index](./houseMgrAgent.md)

---

## 1. Prerequisites

houseAgent is **Phase 4**. Before writing any houseAgent code, the following lifeTracker common services must be stable:

| Phase | Common Service | Doc |
|---|---|---|
| Phase 0 | Auth (login, GPG owner DB, JWT, `ltCmd.py --setup`) | `docs/design/lifeTracker_auth.md` |
| Phase 1 | RecordAgent (UANS paths, git-as-master, provision) | `docs/design/lifeTracker_records.md` |
| Phase 2 | Web UI (Flask app, `/chat`, `/checkin`, Twilio `/voice`) | `docs/design/lifeTracker_commWeb.md` |
| Phase 3 | iOS API (`/api/query`, `/api/auth/token`, `/api/notifications`) | `docs/design/lifeTracker_commIOS.md` |

Milestone before Phase 4: `python ltCmd.py --start` → `/chat` → text query → PA responds (with stub agents). Auth, records, and iOS API all tested.

---

## 2. Guiding Rules

- Each phase produces a **runnable, testable milestone** — not just code.
- No sub-agent is started until its dependencies (see `houseMgrAgent_arch.md §6`) are stable.
- Every sub-agent implements the four-method `HouseSubAgent` interface from day one.
- Voice path and web path are both tested at each milestone.
- houseAgent code writes to RecordAgent only — never direct file I/O.

---

## 3. houseAgent File Structure

```
houseAgent/
├── house_mgr.py            ← HouseMgr: DisciplineAgent implementation
├── router.py               ← house-scoped IntentParser (Haiku)
├── registry.py             ← AgentRegistry: UANS name → sub-agent instance
├── models.py               ← House, MaintenanceEvent, System dataclasses
├── agents/
│   ├── base.py             ← HouseSubAgent abstract base class
│   ├── house_records.py    ← Tier 1
│   ├── house_profile.py    ← Tier 1
│   ├── communication.py    ← Tier 1
│   ├── architecture.py     ← Tier 2
│   ├── security.py         ← Tier 3
│   ├── accessibility.py    ← Tier 3
│   ├── hvac.py             ← Tier 3
│   ├── electrical.py       ← Tier 4
│   ├── plumbing.py         ← Tier 4
│   ├── roofing.py          ← Tier 4
│   ├── budget.py           ← Tier 5
│   ├── tax.py              ← Tier 5
│   ├── investment.py       ← Tier 5
│   ├── appliances.py       ← Tier 6
│   ├── landscaping.py      ← Tier 6
│   └── interior.py         ← Tier 6
└── ui/
    └── house_views.py      ← Flask blueprint: /house/* routes
```

---

## 4. Phase 4a — HouseMgr Scaffold + PA Registration

**Milestone:** `/chat` query routed to houseAgent returns a stub response. Monthly `/checkin` shows a house briefing card.

| Task | File | Notes |
|---|---|---|
| `HouseSubAgent` base class | `agents/base.py` | Abstract; `brief()`, `query()`, `audit()`, `record()` |
| `HouseMgr` scaffold | `house_mgr.py` | Implements `DisciplineAgent`; `brief()` returns stub; `query()` routes to registry |
| `AgentRegistry` | `registry.py` | Dict of `{uans_name: HouseSubAgent}`; `get(name)` |
| `house-scoped router` | `router.py` | Haiku IntentParser prompt for house sub-domains; returns sub-agent list |
| PA registration | `wsgi.py` | `pa.register("house", HouseMgr(config, record_agent))` |
| House blueprint stub | `ui/house_views.py` | `/house/profile` returns placeholder page |
| **Milestone test** | — | `/chat`: "How is my house?" → PA routes to HouseMgr → stub response in browser and spoken |

---

## 5. Phase 4b — Tier 1: Core Infrastructure

**Milestone:** House onboarding complete. Kingsway Dr profile is in RecordAgent. Monthly check-in reads from records.

| Priority | Task | File | Notes |
|---|---|---|---|
| 1 | HouseRecords sub-agent | `agents/house_records.py` | JSON CRUD via RecordAgent; `action_items` read/append; `documents_index` |
| 2 | HouseProfile sub-agent | `agents/house_profile.py` | Onboarding Q&A intake; writes `house.core.profile.house_profile`; `brief()` returns house summary |
| 3 | Onboard 177 Kingsway Dr | — | Run onboarding voice or web Q&A → profile written to RecordAgent |
| 4 | Communication sub-agent | `agents/communication.py` | Action item queue; aggregates audit results from all sub-agents; monthly summary |
| 5 | `/house/profile` web view | `ui/house_views.py` | Render `house.core.profile.house_profile` as HTML |
| **Milestone test** | — | `/house/profile` → shows Kingsway Dr data. `/checkin` → house card shows real profile summary |

---

## 6. Phase 4c — Tier 2: Architecture

**Milestone:** Floor plan data in RecordAgent. All system sub-agents can read structural context.

*Architecture is the gateway for all systems agents. No systems agent builds until Architecture is stable.*

| Task | File | Notes |
|---|---|---|
| Architecture sub-agent | `agents/architecture.py` | Floor plan Q&A intake; room registry; structural notes; pier-and-beam context |
| Floor plan data entry | — | Voice or web Q&A: room dimensions, locations, structural notes for Kingsway Dr |
| Web upload | `ui/house_views.py` | `/house/floor-plan` — optional photo/PDF upload; stores path in documents_index |
| **Milestone test** | — | "What is the layout of my house?" → Architecture agent describes rooms correctly |

---

## 7. Phase 4d — Tiers 3–6: Systems, Finance, Life

Build in priority order within each tier. Tiers within a row can be built in parallel after Architecture is stable.

### Tier 3 — Safety & Life Stage (build after Architecture)

| Priority | UANS | Sub-agent | Why This Tier |
|---|---|---|---|
| 7 | `house.systems.security` | Security & Safety | Smoke/CO, fall lighting, emergency plan — actionable today |
| 8 | `house.life.accessibility` | Accessibility | Critical for 68yo owner; cross-posts to medicalAgent via PA |
| 9 | `house.systems.hvac` | HVAC | Comfort + health; seasonal maintenance calendar has immediate ROI |

### Tier 4 — Critical Systems

| Priority | UANS | Sub-agent | Why |
|---|---|---|---|
| 10 | `house.systems.electrical` | Electrical | Safety-critical; panel age + GFCI coverage; needed by HVAC (heat pump) |
| 11 | `house.systems.plumbing` | Plumbing | High failure risk; water heater lifespan |
| 12 | `house.systems.roofing` | Roofing | Most expensive deferred maintenance failure |

### Tier 5 — Financial Intelligence

| Priority | UANS | Sub-agent | Why |
|---|---|---|---|
| 13 | `house.finance.budget` | Financing | Budget framing + ROI for every project recommendation |
| 14 | `house.finance.tax` | Tax | Capital improvements tracking; basis matters at sale |
| 15 | `house.finance.investment` | Investment | Home value model; cross-posts equity to estateAgent |

### Tier 6 — Quality of Life

| Priority | UANS | Sub-agent | Why |
|---|---|---|---|
| 16 | `house.systems.appliances` | Appliances | Lifecycle tracking; lower urgency |
| 17 | `house.designs.landscaping` | Landscaping | Outdoor living; low-maintenance conversion |
| 18 | `house.designs.interior` | Interior Design | Aesthetics; primarily for remodel projects |

---

## 8. Per-Sub-Agent Build Pattern

Every sub-agent follows this exact pattern, in this order:

1. **`agents/<name>.py`** — implement `HouseSubAgent`:
   - `brief()` — reads its UANS records via RecordAgent; returns 2-3 sentence status
   - `query()` — calls Haiku with domain system prompt + records context + question
   - `audit()` — scans records for overdue items; returns `ActionItem` list
   - `record()` — writes event to `<uans>.maintenance_log` or appropriate record

2. **Register in `registry.py`** — add to `AgentRegistry.__init__()`:
   ```python
   self._agents["house.systems.hvac"] = HvacAgent(record_agent)
   ```

3. **Add to IntentParser prompt** in `router.py` — so HouseMgr can route to it

4. **Data entry** — run voice or web Q&A to populate initial records for Kingsway Dr

5. **Milestone test** — ask a domain question; verify the sub-agent answers correctly with real data

---

## 9. Tests

```
tests/
└── houseAgent/
    ├── test_house_mgr.py           ← test brief(), query(), audit() with mock sub-agents
    ├── test_house_records.py       ← test JSON read/write via RecordAgent stub
    ├── test_house_profile.py       ← test onboarding Q&A; house_profile.json output
    ├── test_router.py              ← test IntentParser output for house queries
    └── test_agents/
        ├── test_hvac.py            ← filter-change audit, maintenance log append
        └── ...
```

Run:
```bash
python -m tests.houseAgent.test_house_records
python -m tests.houseAgent.test_hvac
```
