# HouseMgr — Agent Catalog & Build Priority

**Version:** 0.4
**Date:** June 2026
**Parent:** [Design Index](./houseMgrAgent.md)

---

## 1. Agent Interface Contract

Every discipline agent implements the same four methods. The HouseMgr only calls these — it never accesses agent internals.

```python
class DisciplineAgent:
    def brief(self) -> str:
        """2-3 sentence summary of current domain status."""

    def query(self, question: str, context: dict) -> AgentResponse:
        """Answer a domain question given house context."""

    def audit(self) -> list[ActionItem]:
        """Proactive scan — return items needing owner attention."""

    def record(self, event: dict) -> None:
        """Log a domain event (repair, install, inspection, etc.)."""
```

`AgentResponse` and `ActionItem` are shared dataclasses in `houseMgr/models.py` — the only shared contract between HouseMgr and agents. No agent imports from another agent.

### Voice Response Constraint

When the HouseMgr synthesizes a response destined for the phone (TTS), it instructs the Synthesizer to produce **≤ 3 sentences** of spoken prose — no markdown, no lists, no headers. The full structured response is always written to HouseRecords and available via the web view.

---

## 2. Universal Agent Naming Schema (UANS)

Every agent name follows the 4-segment dot-notation defined in [HouseManagerVision §3.5](../HouseManagerVision.md#35-universal-agent-naming-schema-uans):

```
house.<category>.<agent>.<record>
```

The five categories and their agents:

| Category | UANS | Agent | Records Dir |
|---|---|---|---|
| **core** | `house.core.records` | HouseRecords | `agents/core/records/` |
| **core** | `house.core.profile` | House Profile | `agents/core/profile/` |
| **core** | `house.core.comm` | Communication | `agents/core/comm/` |
| **systems** | `house.systems.hvac` | HVAC | `agents/systems/hvac/` |
| **systems** | `house.systems.electrical` | Electrical | `agents/systems/electrical/` |
| **systems** | `house.systems.plumbing` | Plumbing | `agents/systems/plumbing/` |
| **systems** | `house.systems.roofing` | Roofing | `agents/systems/roofing/` |
| **systems** | `house.systems.security` | Security & Safety | `agents/systems/security/` |
| **systems** | `house.systems.appliances` | Appliances | `agents/systems/appliances/` |
| **designs** | `house.designs.architecture` | Architecture | `agents/designs/architecture/` |
| **designs** | `house.designs.landscaping` | Landscaping | `agents/designs/landscaping/` |
| **designs** | `house.designs.interior` | Interior Design | `agents/designs/interior/` |
| **finance** | `house.finance.budget` | Financing | `agents/finance/budget/` |
| **finance** | `house.finance.tax` | Tax | `agents/finance/tax/` |
| **finance** | `house.finance.investment` | Investment | `agents/finance/investment/` |
| **life** | `house.life.accessibility` | Accessibility | `agents/life/accessibility/` |

The `AgentRegistry` in `houseMgr/registry.py` keys agents by their UANS string. `HouseRecords` derives the filesystem path from UANS: `agents/<category>/<agent>/`.

---

## 3. LLM Usage Pattern

The HouseMgr uses Claude in two places only:

| Step | Input | Output | Model |
|---|---|---|---|
| **IntentParser** | Owner speech transcript | `{agents: [...], question: str, mode: query/record/plan}` | Haiku (fast, cheap) |
| **ResponseSynthesizer** | Collected agent responses + mode (voice/web) | Spoken prose (voice) or structured HTML (web) | Sonnet |

Individual agents call the LLM internally for domain reasoning using domain-specific system prompts + house context from HouseRecords. Each agent manages its own LLM calls.

---

## 4. Dependency Map

```
house.core.records ◄─── ALL agents (every agent reads/writes here)
house.core.profile ◄─── ALL agents (every agent reads for house context)
house.core.comm    ◄─── ALL agents (all push action items for check-in)

house.designs.architecture ◄─── systems.plumbing, systems.electrical,
                                 systems.hvac, systems.roofing,
                                 designs.landscaping, designs.interior
                                 (all need floor plan / structural knowledge)

house.finance.budget ◄─── designs.architecture, systems.hvac,
                           systems.electrical, systems.plumbing, systems.roofing
                           (all project agents need budget framing)

house.finance.tax        ◄─── finance.budget (capital improvement categorization)
house.finance.investment ◄─── finance.tax (basis), finance.budget (equity)

house.life.accessibility ◄─── designs.architecture (structural mods),
                               systems.security (safety lighting)
house.designs.landscaping ◄─── designs.architecture (site map),
                                systems.plumbing (irrigation zones)
house.designs.interior    ◄─── designs.architecture (floor plan, room dimensions)
house.systems.hvac        ◄─── systems.electrical (panel capacity for heat pump)
```

---

## 5. Build Tiers

Agents within a tier can be built in parallel. Each tier depends on the tier above it being stable.

### Tier 1 — Core Infrastructure (`house.core.*`)

*Build first — nothing else runs without these.*

| Priority | UANS | Component | Why First |
|---|---|---|---|
| 1 | — | **Setup WebServer** | `wsCmd.py --setup` on PA console: creates config, bootstraps records tree, registers first user. Nothing else starts without this. |
| 2 | — | **Configurator (Owner, House)** | Web UI to register and edit houses/owners in config.json. Must exist before agents are configured for a specific house. |
| 3 | `house.core.records` | **HouseRecords** | All agents store and retrieve through here; must exist before any agent is built. |
| 4 | `house.core.profile` | **House Profile** | Briefs every agent with house context; onboarding starts here. |
| 5 | `house.core.comm` | **Communication** | Owner interaction layer; monthly check-in and alert routing. |

### Tier 2 — Designs Foundation (`house.designs.architecture`)

*Understand the physical asset before advising on it.*

| Priority | UANS | Agent | Why This Tier |
|---|---|---|---|
| 6 | `house.designs.architecture` | **Architecture** | Floor plan and structural knowledge is a prerequisite for all systems agents, landscaping, and interior design. |

### Tier 3 — Safety & Life Stage

*Immediate value; senior owner priority.*

| Priority | UANS | Agent | Why This Tier |
|---|---|---|---|
| 7 | `house.systems.security` | **Security & Safety** | Smoke/CO detectors, fall lighting, emergency plan — actionable today with no dependencies. |
| 8 | `house.life.accessibility` | **Accessibility & Aging-in-Place** | Critical for a 70-year-old owner; depends on Architecture for structural mods. |
| 9 | `house.systems.hvac` | **HVAC** | Comfort, indoor air quality, health impact; seasonal maintenance calendar has immediate ROI. |

### Tier 4 — Critical Systems (`house.systems.*`)

*High failure cost; proactive monitoring value.*

| Priority | UANS | Agent | Why This Tier |
|---|---|---|---|
| 10 | `house.systems.electrical` | **Electrical** | Safety-critical; panel age and GFCI coverage audit; needed by HVAC (heat pump). |
| 11 | `house.systems.plumbing` | **Plumbing** | High failure risk (water damage); water heater lifespan tracking. |
| 12 | `house.systems.roofing` | **Roofing** | Most expensive deferred maintenance failure; annual inspection calendar. |

### Tier 5 — Financial Intelligence (`house.finance.*`)

*Required before any major project is approved.*

| Priority | UANS | Agent | Why This Tier |
|---|---|---|---|
| 13 | `house.finance.budget` | **Financing** | Budget framing and ROI for every Tier 3–4 project recommendation. |
| 14 | `house.finance.tax` | **Tax** | Capital improvements tracking should start at first project; basis matters at sale. |
| 15 | `house.finance.investment` | **Investment & Value** | Home value model and project ROI; depends on Tax (basis) and Financing (equity). |

### Tier 6 — Quality of Life

*Valuable but not safety-critical.*

| Priority | UANS | Agent | Why This Tier |
|---|---|---|---|
| 16 | `house.systems.appliances` | **Appliances** | Lifecycle tracking; lower urgency than systems. |
| 17 | `house.designs.landscaping` | **Landscaping** | Outdoor living, curb appeal, low-maintenance conversion. |
| 18 | `house.designs.interior` | **Interior Design** | Aesthetics and finish selection; primarily needed for remodel projects. |

---

## 6. Interdependency Summary Table

| UANS | Agent | Hard Dependencies | Soft Dependencies |
|---|---|---|---|
| `house.core.records` | HouseRecords | — | — |
| `house.core.profile` | House Profile | core.records | — |
| `house.core.comm` | Communication | core.records | All agents (receives action items) |
| `house.designs.architecture` | Architecture | core.records, core.profile | — |
| `house.systems.security` | Security & Safety | core.records | core.comm |
| `house.life.accessibility` | Accessibility | designs.architecture | systems.security, systems.hvac, medicalTracker (external) |
| `house.systems.hvac` | HVAC | designs.architecture | systems.electrical, finance.budget |
| `house.systems.electrical` | Electrical | designs.architecture | finance.budget |
| `house.systems.plumbing` | Plumbing | designs.architecture | finance.budget |
| `house.systems.roofing` | Roofing | designs.architecture | systems.electrical (solar), finance.budget |
| `house.finance.budget` | Financing | core.records | All project agents |
| `house.finance.tax` | Tax | finance.budget | finance.investment |
| `house.finance.investment` | Investment | finance.tax, finance.budget | — |
| `house.systems.appliances` | Appliances | core.records | finance.budget |
| `house.designs.landscaping` | Landscaping | designs.architecture, systems.plumbing | finance.budget |
| `house.designs.interior` | Interior Design | designs.architecture | finance.budget |

### 6.1 Agent Records Ownership

Every JSON file in `records/agents/` belongs to exactly one agent — the sole writer. HouseRecords provides the read/write interface; agents never touch the filesystem directly. The directory path derives from UANS: `agents/<category>/<agent>/`. See [houseRecordsData.md §4](./houseRecords/houseRecordsData.md#4-records-directory-structure) for the full directory tree.

| UANS | Agent | Records Dir | Owned JSON Files |
|---|---|---|---|
| `house.core.records` | HouseRecords | `agents/core/records/` | `legal_records` · `insurance` · `utilities` · `contractors` · `documents_index` · `action_items` |
| `house.core.profile` | House Profile | `agents/core/profile/` | `house_profile` · `action_items` |
| `house.core.comm` | Communication | `agents/core/comm/` | `check_in_log` · `action_items` |
| `house.systems.hvac` | HVAC | `agents/systems/hvac/` | `systems` · `maintenance_log` · `action_items` |
| `house.systems.electrical` | Electrical | `agents/systems/electrical/` | `panel` · `circuits` · `maintenance_log` · `action_items` |
| `house.systems.plumbing` | Plumbing | `agents/systems/plumbing/` | `systems` · `sewer_diagram` · `maintenance_log` · `action_items` |
| `house.systems.roofing` | Roofing | `agents/systems/roofing/` | `systems` · `maintenance_log` · `action_items` |
| `house.systems.security` | Security & Safety | `agents/systems/security/` | `systems` · `action_items` |
| `house.systems.appliances` | Appliances | `agents/systems/appliances/` | `registry` · `maintenance_log` · `action_items` |
| `house.designs.architecture` | Architecture | `agents/designs/architecture/` | `floor_plan` · `structural_notes` · `action_items` |
| `house.designs.landscaping` | Landscaping | `agents/designs/landscaping/` | `site_map` · `maintenance_log` · `action_items` |
| `house.designs.interior` | Interior Design | `agents/designs/interior/` | `rooms` · `action_items` |
| `house.finance.budget` | Financing | `agents/finance/budget/` | `capital_improvements` · `budget` · `action_items` |
| `house.finance.tax` | Tax | `agents/finance/tax/` | `basis_log` · `action_items` |
| `house.finance.investment` | Investment | `agents/finance/investment/` | `valuation` · `action_items` |
| `house.life.accessibility` | Accessibility | `agents/life/accessibility/` | `assessment` · `action_items` |

---

## 7. Implementation Plan (Agents Scope)

### Phase 1 — Tier 1 Agents (after PA scaffold)

Build and test in sequence: HouseRecords → House Profile → Communication. Milestone: monthly check-in loop runs end-to-end with stub data, spoken via Twilio voice.

- [ ] `agents/house_records.py` — JSON read/write; path helpers
- [ ] `agents/house_profile.py` — onboarding intake; briefing output
- [ ] `agents/communication.py` — action item queue; check-in report generator
- [ ] Voice check-in: call Twilio number → hear monthly summary spoken back

### Phase 2 — Tier 2 (Architecture)

Architecture is the gateway for all system agents. Floor plan intake, room tagging, site map — full onboarding via voice Q&A and optional photo upload via web.

- [ ] `agents/architecture.py` — floor plan intake; structural note recording
- [ ] Web UI: photo/document upload for floor plan scans

### Phase 3 — Tiers 3–6

Follow priority order in §4. Each agent follows the `DisciplineAgent` interface from day one — no exceptions — so the HouseMgr router never changes as agents are added.
