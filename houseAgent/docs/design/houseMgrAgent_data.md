# houseAgent — Data Design

**Version:** 1.0
**Date:** June 2026
**Parent:** [Design Index](./houseMgrAgent.md)

---

## 1. Storage Model

houseAgent uses the **lifeTracker RecordAgent** for all data storage. No houseAgent-specific database, no direct file I/O. All house records live in `lifeTracker-data/records/agents/house/` under the `house.*` UANS namespace.

Storage model: `docs/design/lifeTracker_records.md`

houseAgent has no config of its own. It reads from `~/.lifeTracker/config.json` via `setup_paths.py`, the same config file used by all lifeTracker services.

---

## 2. UANS Directory Tree — `house.*`

```
lifeTracker-data/
└── records/
    └── agents/
        └── house/
            ├── core/
            │   ├── records/          ← house.core.records.*
            │   ├── profile/          ← house.core.profile.*
            │   └── comm/             ← house.core.comm.*
            ├── systems/
            │   ├── hvac/             ← house.systems.hvac.*
            │   ├── electrical/       ← house.systems.electrical.*
            │   ├── plumbing/         ← house.systems.plumbing.*
            │   ├── roofing/          ← house.systems.roofing.*
            │   ├── security/         ← house.systems.security.*
            │   └── appliances/       ← house.systems.appliances.*
            ├── designs/
            │   ├── architecture/     ← house.designs.architecture.*
            │   ├── landscaping/      ← house.designs.landscaping.*
            │   └── interior/         ← house.designs.interior.*
            ├── finance/
            │   ├── budget/           ← house.finance.budget.*
            │   ├── tax/              ← house.finance.tax.*
            │   └── investment/       ← house.finance.investment.*
            └── life/
                └── accessibility/    ← house.life.accessibility.*
```

All directories are provisioned by `RecordAgent.provision()` in Phase 1 before any houseAgent code runs.

---

## 3. Record Ownership

Each JSON file is owned by exactly one sub-agent — the sole writer. All agents may read any file through RecordAgent, but only the owner writes.

| UANS | Owner Agent | JSON Files |
|---|---|---|
| `house.core.records` | HouseRecords | `legal_records.json` · `insurance.json` · `utilities.json` · `contractors.json` · `documents_index.json` · `action_items.json` |
| `house.core.profile` | HouseProfile | `house_profile.json` · `action_items.json` |
| `house.core.comm` | Communication | `checkin_log.json` · `action_items.json` |
| `house.systems.hvac` | HVAC | `systems.json` · `maintenance_log.json` · `action_items.json` |
| `house.systems.electrical` | Electrical | `panel.json` · `circuits.json` · `maintenance_log.json` · `action_items.json` |
| `house.systems.plumbing` | Plumbing | `systems.json` · `sewer_diagram.json` · `maintenance_log.json` · `action_items.json` |
| `house.systems.roofing` | Roofing | `systems.json` · `maintenance_log.json` · `action_items.json` |
| `house.systems.security` | Security | `systems.json` · `action_items.json` |
| `house.systems.appliances` | Appliances | `registry.json` · `maintenance_log.json` · `action_items.json` |
| `house.designs.architecture` | Architecture | `floor_plan.json` · `structural_notes.json` · `action_items.json` |
| `house.designs.landscaping` | Landscaping | `site_map.json` · `maintenance_log.json` · `action_items.json` |
| `house.designs.interior` | Interior Design | `rooms.json` · `action_items.json` |
| `house.finance.budget` | Financing | `capital_improvements.json` · `budget.json` · `action_items.json` |
| `house.finance.tax` | Tax | `basis_log.json` · `action_items.json` |
| `house.finance.investment` | Investment | `valuation.json` · `action_items.json` |
| `house.life.accessibility` | Accessibility | `assessment.json` · `action_items.json` |

---

## 4. Key Record Schemas

### `house.core.profile.house_profile`

```json
{
  "address": "177 Kingsway Dr, Wimberley TX 78676",
  "county": "Hays",
  "parcel_id": "R33204",
  "purchase_date": "2022-12-31",
  "purchase_price": 335000,
  "sqft": 1232,
  "lot_acres": 0.5,
  "construction_type": "pier-and-beam",
  "year_built": 2006,
  "bedrooms": 3,
  "bathrooms": 2,
  "stories": 1,
  "owner_id": "frankr6591",
  "last_updated": "2026-06-28T00:00:00Z"
}
```

### `house.systems.hvac.systems`

```json
{
  "units": [
    {
      "id": "hvac_1",
      "type": "heat_pump",
      "brand": "...",
      "model": "...",
      "install_date": "...",
      "location": "...",
      "warranty_expires": "...",
      "filter_size": "...",
      "filter_change_interval_days": 90
    }
  ]
}
```

### `house.systems.hvac.maintenance_log`

```json
{
  "events": [
    {
      "date": "2026-03-15",
      "type": "filter_change",
      "description": "Changed 16x25x1 filter",
      "performed_by": "owner",
      "cost": 12.00,
      "next_due": "2026-06-15"
    }
  ]
}
```

### `house.core.records.action_items`

```json
{
  "action_items": [
    {
      "id": "act_20260628_001",
      "agent": "house.systems.hvac",
      "summary": "HVAC filter overdue — last changed 2026-03-15",
      "priority": "medium",
      "created_at": "2026-06-28T00:00:00Z",
      "resolved": false
    }
  ]
}
```

---

## 5. Cross-Agent Data Signals

These are records houseAgent writes that other agents (via PA) consume. houseAgent writes them; PA reads them and passes relevant context to the consuming agent.

| houseAgent writes | Consuming agent | Signal |
|---|---|---|
| `house.finance.investment.valuation` | estateAgent | Current home value, equity |
| `house.life.accessibility.assessment` | medicalAgent | Mobility gap flags, recommended mods |
| `house.finance.budget.capital_improvements` | moneyAgent | Project cost, liquidity request |

---

## 6. Documents (not in Git)

PDFs, photos, and scanned documents are large binary files — they are **not** stored in `lifeTracker-data`. They live in a local directory on each machine, not in git.

```
~/GDrive/dev/pyTrackers/lifeTracker-docs/house/
├── deeds/
│   └── warranty_deed_2022.pdf
├── permits/
├── inspection_reports/
├── photos/
└── insurance/
    └── policy_2026.pdf
```

The `house.core.records.documents_index` JSON file contains a pointer to each document:

```json
{
  "documents": [
    {
      "id": "doc_deed_2022",
      "type": "deed",
      "filename": "warranty_deed_2022.pdf",
      "local_path": "~/GDrive/dev/pyTrackers/lifeTracker-docs/house/deeds/warranty_deed_2022.pdf",
      "date": "2022-12-31",
      "description": "Warranty deed — 177 Kingsway Dr",
      "custodian": "Hays County Clerk"
    }
  ]
}
```

The index is in git (via RecordAgent); the PDFs are not.
