# houseAgent — Design Index

**Version:** 1.0
**Date:** June 2026
**Status:** Design — pre-implementation

---

## Overview

houseAgent is the **House Manager discipline agent** within the lifeTracker Personal Assistant ecosystem. It is **Phase 4** in the build plan — built after the lifeTracker common services (auth, records, web UI, iOS API) are stable.

houseAgent is not a standalone app. It is one of six discipline agents registered with the lifeTracker PersonalAssistant. It uses lifeTracker's shared auth, RecordAgent records service, and Flask web UI infrastructure.

**Property:** 177 Kingsway Dr, Wimberley TX 78676 (Hays County R33204). Purchased 2022-12-31, $335K cash. Pier-and-beam, 1,232 sqft, 0.5 acres.

---

## This Directory

| Doc | What It Covers |
|---|---|
| `houseMgrAgent.md` | This file — design index, role in lifeTracker, module structure |
| `houseMgrAgent_arch.md` | HouseMgr architecture: agent interface, LLM usage, dependency map |
| `houseMgrAgent_agents.md` | Full agent catalog: 18 sub-agents, UANS, build tiers |
| `houseMgrAgent_data.md` | Data design: UANS paths, record schemas, config |
| `houseMgrAgent_impl.md` | Implementation plan: phases, file structure, milestones |

Vision doc: `houseAgent/docs/HouseManagerVision.md`
Ecosystem context: `docs/lifeTrackerVision.md`
Commons design: `docs/design/lifeTracker_design.md`

---

## houseAgent's Role in lifeTracker

houseAgent is one node in the PA's discipline agent graph. The PA calls it through the standard `DisciplineAgent` interface (defined in `life/models.py`). houseAgent never communicates directly with other discipline agents — all cross-agent signals route through the PA.

```
PersonalAssistant
       │
       ├─ query(text, context) ──→ HouseMgr
       │                               │
       │                    ┌──────────▼──────────────┐
       │                    │  houseAgent router      │  ← house-scoped intent parsing
       │                    │  AgentRegistry          │
       │                    └──────────┬──────────────┘
       │                               │
       │               ┌───────────────┼───────────────┐
       │               ▼               ▼               ▼
       │          HouseRecords   HouseProfile    [systems/designs/
       │          (Tier 1)       (Tier 1)         finance/life agents]
       │               │
       │           RecordAgent   ← shared lifeTracker RecordAgent (core/records/)
       │               │
       │       lifeTracker-data/records/agents/house/
       │
       └─ brief() ──→ HouseMgr.brief() → 2-3 sentence status for monthly PA check-in
```

**Cross-agent signals houseAgent sends (mediated by PA):**
- `house.finance.investment` → estateAgent (home value, equity)
- `house.life.accessibility` → medicalAgent (mobility gaps → home mods)
- Requests liquidity check from moneyAgent before approving major projects

---

## Module Structure

houseAgent code lives at `houseAgent/` in the lifeTracker repo root:

```
houseAgent/
├── house_mgr.py            ← HouseMgr: implements DisciplineAgent; registers with PA
├── router.py               ← house-scoped intent parser: maps question to sub-agents
├── registry.py             ← AgentRegistry: UANS name → sub-agent instance
├── models.py               ← house-specific models (e.g., House, System, MaintenanceLog)
├── agents/
│   ├── base.py             ← HouseAgent base class (extends life/models DisciplineAgent)
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
├── ui/
│   └── house_views.py      ← Flask blueprint: /house/records, /house/profile
└── docs/
    ├── HouseManagerVision.md
    └── design/             ← this directory
```

---

## Registration with PersonalAssistant

In `wsgi.py`, after the app factory creates the PA:

```python
from houseAgent.house_mgr import HouseMgr
from core.records.record_agent import RecordAgent

record_agent = RecordAgent(config)
pa = PersonalAssistant(config)
pa.register("house", HouseMgr(config, record_agent))
app.config["PA_INSTANCE"] = pa
```

`HouseMgr` receives the shared `RecordAgent` — it does not create its own. All sub-agents write through this shared instance using UANS `house.*` paths.
