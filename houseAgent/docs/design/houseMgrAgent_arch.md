# houseAgent — Architecture

**Version:** 1.0
**Date:** June 2026
**Parent:** [Design Index](./houseMgrAgent.md)

---

## 1. Design Goals

### 1.1 Thin Orchestrator

HouseMgr is a **thin router and response synthesizer** for house domain queries — it holds no domain knowledge. Every piece of expertise lives in a discipline sub-agent. HouseMgr's jobs:

1. Receive a query from the PA via `query(text, context)`
2. Parse intent to identify which sub-agents are relevant (house-scoped Haiku call)
3. Query those sub-agents with current house context
4. Synthesize a unified response to return to the PA
5. Write outcomes back to RecordAgent (`house.*` UANS namespace)

**Anti-pattern to avoid:** HouseMgr accumulating domain logic (knowing HVAC rules, knowing tax codes). That belongs in the sub-agent. HouseMgr knows only the sub-agent registry.

### 1.2 Design Principles

- **Owner never tracks details** — sub-agents do. HouseMgr surfaces; agents collect.
- **Proactive over reactive** — sub-agents push action items to the check-in queue; HouseMgr presents them via `audit()`.
- **Recommendation, not menu** — synthesized output is "here's what to do," not a list of options.
- **Voice-first** — spoken responses ≤ 3 sentences; detail lives in the web record view.
- **DIY-first, frugal** — cost framing defaults to quality-for-budget, not premium-fastest.
- **Aging-in-place thread** — every sub-agent response considers the 68yo owner's life stage.

---

## 2. DisciplineAgent Interface

HouseMgr implements the four-method interface that the lifeTracker PersonalAssistant calls. These are defined in `life/models.py`.

```python
class HouseMgr:
    """
    lifeTracker discipline agent for the house domain.
    The PA only calls these four methods — never accesses sub-agent internals.
    """

    def brief(self) -> AgentBriefing:
        """
        2-3 sentence current house status.
        Called by PA for monthly check-in. Aggregates sub-agent briefs.
        """

    def query(self, question: str, context: dict) -> AgentResponse:
        """
        Answer a house-domain question.
        context: cross-agent data PA passes in (e.g., health state, liquidity).
        Internally routes to sub-agents and synthesizes.
        """

    def audit(self) -> list[ActionItem]:
        """
        Proactive scan across all sub-agents.
        Returns items needing owner attention for this month's check-in.
        """

    def record(self, event: dict) -> None:
        """
        Log a house event (repair completed, inspection, appliance installed, etc.).
        Routes to appropriate sub-agent based on event type.
        """
```

---

## 3. LLM Usage

HouseMgr uses Claude in two places:

| Step | Input | Output | Model |
|---|---|---|---|
| **House IntentParser** | House query text | `{sub_agents: [...], question: str, mode: query/record}` | Haiku (fast, cheap) |
| **House Synthesizer** | Collected sub-agent responses + mode | Spoken prose ≤3 sent. (voice) or structured text (web) | Sonnet |

This is a **house-scoped** intent parse — separate from the top-level PA IntentParser. The PA IntentParser identifies that this is a house domain question and calls `HouseMgr.query()`. The HouseMgr then does a second, house-specific parse to identify which of the 18 sub-agents should answer.

Each sub-agent also makes its own LLM calls internally using house-specific system prompts and UANS context from RecordAgent.

### House IntentParser system prompt (abbreviated)

```
You are the intent parser for the house management agent. Given a house question,
identify which of these sub-agents should answer:
  house.core.records | house.core.profile | house.systems.hvac |
  house.systems.electrical | house.systems.plumbing | house.systems.roofing |
  house.systems.security | house.systems.appliances |
  house.designs.architecture | house.designs.landscaping | house.designs.interior |
  house.finance.budget | house.finance.tax | house.finance.investment |
  house.life.accessibility

Return JSON: {"sub_agents": [...], "question": "...", "mode": "query|record|plan"}
```

---

## 4. Sub-Agent Interface

Every house sub-agent implements the same four methods. HouseMgr calls only these.

```python
class HouseSubAgent:
    def brief(self) -> str:
        """2-3 sentence domain status for house monthly summary."""

    def query(self, question: str, house_context: dict) -> AgentResponse:
        """Answer a domain question. house_context comes from HouseProfile."""

    def audit(self) -> list[ActionItem]:
        """Proactive scan — return items needing attention this month."""

    def record(self, event: dict) -> None:
        """Log an event in this sub-agent's UANS record directory."""
```

`AgentResponse` and `ActionItem` come from `life/models.py` — the shared contract. No sub-agent imports from another sub-agent or from another discipline agent.

---

## 5. House Context

Every sub-agent query receives a `house_context` dict populated from `house.core.profile`:

```python
house_context = {
    "address": "177 Kingsway Dr, Wimberley TX 78676",
    "purchase_date": "2022-12-31",
    "purchase_price": 335000,
    "sqft": 1232,
    "construction": "pier-and-beam",
    "year_built": 2006,
    "county": "Hays",
    "parcel_id": "R33204",
    "owner_age": 68,
    "owner_mobility_notes": "...",    # from medicalAgent cross-agent signal
    "current_budget": "...",          # from house.finance.budget
}
```

`HouseProfile` (Tier 1) is the sole owner and writer of this context. All other sub-agents read it; none write to it.

---

## 6. Sub-Agent Dependency Map

```
house.core.records  ◄── ALL sub-agents (every sub-agent reads/writes here)
house.core.profile  ◄── ALL sub-agents (reads for house context)

house.designs.architecture ◄── systems.plumbing, systems.electrical,
                                systems.hvac, systems.roofing,
                                designs.landscaping, designs.interior

house.finance.budget  ◄── systems.hvac, systems.electrical, systems.plumbing,
                           systems.roofing, designs.architecture

house.finance.tax        ◄── finance.budget (capital improvement categorization)
house.finance.investment ◄── finance.tax (basis), finance.budget (equity)

house.life.accessibility ◄── designs.architecture (structural mods),
                              systems.security (safety lighting)
                              medicalAgent signal (mobility needs — via PA)

house.systems.hvac        ◄── systems.electrical (panel capacity for heat pump)
house.designs.landscaping ◄── designs.architecture (site map), systems.plumbing (irrigation)
house.designs.interior    ◄── designs.architecture (floor plan, room dimensions)
```

---

## 7. Flask Blueprint Registration

houseAgent registers its own web views as a Flask blueprint. The lifeTracker Flask app (`wsgi.py`) imports and registers it:

```python
# wsgi.py
from houseAgent.ui.house_views import house_bp
app.register_blueprint(house_bp, url_prefix="/house")
```

House-specific routes (under `/house/`):

| Route | Description |
|---|---|
| `GET /house/profile` | View house profile (address, purchase info, systems inventory) |
| `GET /house/records` | Browse all house UANS records |
| `GET /house/checkin` | House-specific monthly detail (supplements PA `/checkin`) |
| `POST /house/record` | Log a house event via web form |

All routes are protected by the shared `@login_required` decorator from `core/auth/decorators.py`.

---

## 8. Records Access Pattern

HouseMgr and all sub-agents access records **only through the shared RecordAgent** instance passed at construction. No direct file I/O.

```python
class HvacAgent(HouseSubAgent):
    def __init__(self, record_agent: RecordAgent):
        self._ra = record_agent

    def record(self, event: dict) -> None:
        log = self._ra.read("house.systems.hvac.maintenance_log") or {"events": []}
        log["events"].append(event)
        self._ra.write("house.systems.hvac.maintenance_log", log)
        # write() → commits to lifeTracker-data → pushes to GitHub

    def audit(self) -> list[ActionItem]:
        log = self._ra.read("house.systems.hvac.maintenance_log") or {"events": []}
        # inspect log → return overdue items
        ...
```

Write → commit → push is automatic. The git history in `lifeTracker-data` IS the audit trail.
