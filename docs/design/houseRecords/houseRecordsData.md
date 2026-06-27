# HouseRecords Agent — Data Design

**Version:** 0.1
**Date:** June 2026
**Parent:** [Design Index](../houseMgrAgent.md)

---

## 1. Agent Responsibilities

The HouseRecords agent is the **institutional memory of the property**. It has three jobs:

1. **Store and track all existing records** — every document, invoice, photo, and event, indexed so any other agent can retrieve context about the house without scanning the filesystem.
2. **Track where official records live** — deed, title, surveys, permits, homestead exemption, and insurance policies each have an authoritative external location; the agent knows both the local file path and the official custodian.
3. **Apply property management best practices** — the agent is the on-call expert in five disciplines: construction, real estate, legal, finance, and database services. It knows what records a well-run property should have, flags gaps, and advises on retention.

Every other agent (HVAC, Plumbing, Financing, etc.) reads and writes through HouseRecords. No agent accesses the filesystem directly.

---

## 2. Multi-Discipline Expert Perspective

The schema is designed from the combined perspective of five disciplines a professional property manager must master:

| Discipline | What it demands of records |
|---|---|
| **Construction** | Every system documented with make/model/serial/install date; inspection reports preserved; before-and-after photos for each repair; pipe diagrams and floor plans as first-class records |
| **Real Estate** | Cost basis maintained from day one (purchase price + every capital improvement); deed, title insurance, and survey all current and filed; market comparables tracked over time |
| **Legal** | Permits pulled for every permitted work item; easements and encroachments documented; neighbor disputes logged with dates and communications; homestead exemption status current |
| **Finance** | Insurance policy history with claim log; property tax assessments vs. actual payments; capital improvements separated from maintenance for IRS purposes; warranty expiration calendar |
| **Database** | Normalized entities (property, systems, events, contractors, documents) with stable IDs; no duplication; every document in the index with path + external custodian; consistent `YYYYMMDD-` filename prefix |

---

## 3. JSON Schema

All records live under `houseTracker-data/<house_id>/records/`. The HouseRecords agent owns this entire subtree. Other agents read from it; only HouseRecords writes the top-level files.

### 3.1 `house_profile.json` — Property Identity

```json
{
  "house_id":       "kingsway_dr",
  "house_name":     "177 Kingsway Dr",
  "address":        "177 Kingsway Dr, Wimberley, TX 78676",
  "county":         "Hays",
  "parcel_id":      "R33204",
  "year_built":     1982,
  "style":          "Ranch — single family",
  "sqft_living":    1232,
  "lot_acres":      0.5,
  "foundation":     "pier-and-beam",
  "sewer":          "septic",
  "water_source":   "Wimberley Water Supply Corp",
  "acquisition": {
    "date":         "2022-12-31",
    "price":        335000,
    "method":       "cash",
    "hud_file":     "documents/legal/20230117-HUD_Settlement_Statement.pdf"
  },
  "prior_sale": {
    "date":         "2014-01-01",
    "price":        114000
  }
}
```

### 3.2 `utilities.json` — Service Accounts

```json
{
  "utilities": [
    {
      "utility_id":   "electricity",
      "provider":     "PEC (Pedernales Electric Cooperative)",
      "account":      "3000789437",
      "phone":        "888-554-4732",
      "pay_method":   "online",
      "notes":        ""
    },
    {
      "utility_id":   "water",
      "provider":     "Wimberley Water Supply Corp",
      "account":      "",
      "phone":        "512-847-2323",
      "address":      "P.O. Box 10, 110 LaPais, Wimberley TX 78676",
      "pay_url":      "https://payclix.com/wimberleywater",
      "notes":        "Pressure regulator installed — line pressure exceeds 100 PSI. Check valve prevents upstream reverse flow."
    },
    {
      "utility_id":   "cable",
      "provider":     "Spectrum",
      "account":      "",
      "phone":        ""
    },
    {
      "utility_id":   "waste",
      "provider":     "Texas Waste",
      "account":      "",
      "notes":        "Trash/recycling pickup"
    }
  ]
}
```

### 3.3 `systems_registry.json` — All Physical Systems

One entry per tracked system or appliance. This is the master calendar for maintenance and warranty.

```json
{
  "systems": [
    {
      "system_id":        "hvac_ac",
      "category":         "hvac",
      "name":             "AC Unit",
      "make":             "",
      "model":            "",
      "serial":           "",
      "install_date":     "",
      "warranty_expires": "",
      "expected_life_yrs": 15,
      "last_service":     "2016-05-16",
      "service_provider": "unknown",
      "notes":            "AC service and warranty contract 2016",
      "files":            ["documents/hvac/20160516-AC_Service_Warranty.pdf"]
    },
    {
      "system_id":        "roof",
      "category":         "roofing",
      "name":             "Metal Roof",
      "install_date":     "2016-12-12",
      "expected_life_yrs": 40,
      "notes":            "Metal decking work 2016",
      "files":            ["documents/roofing/20161212-Roof_Metal_Decking.pdf"]
    },
    {
      "system_id":        "hot_tub",
      "category":         "outdoor",
      "name":             "Marquis Spa",
      "make":             "Marquis",
      "model":            "VEGA SIL SL CHA",
      "serial":           "0101667",
      "install_date":     "2017-09-27",
      "filter_part":      "20342",
      "dealer":           "Southern Leisure Spas and Patio",
      "dealer_phone":     "512-240-7727",
      "service_contact":  "Joseph Polvado 512-508-9702 (A-Tex)",
      "notes":            "Surface roughness risk from excess shock+bromine. Texas Refinish (210) 903-6990.",
      "files":            []
    },
    {
      "system_id":        "septic",
      "category":         "plumbing",
      "name":             "Septic Tank",
      "capacity_gal":     1000,
      "last_pumped":      "2026-06-21",
      "recommended_interval_yrs": 3,
      "notes":            "Complex drain line layout documented in sewer_diagram.json. 2026-06-21: backed up at K.Sink and G.Tub; tank pumped; snaked multiple lines.",
      "files":            ["documents/plumbing/kingswaySewer2D.ipynb",
                          "documents/plumbing/photos/"]
    },
    {
      "system_id":        "water_softener",
      "category":         "plumbing",
      "name":             "Water Softener / Filtration",
      "notes":            "Installed for Wimberley hard water. See Water_Softener_Filtration.gdoc.",
      "files":            []
    },
    {
      "system_id":        "foundation",
      "category":         "structural",
      "name":             "Pier-and-Beam Foundation",
      "notes":            "Research conducted 2023 on pier-to-slab conversion — not executed. Living room beam rot discovered Feb 2025 during floor replacement.",
      "files":            ["documents/structural/20231113-ConvertToSlab.ipynb",
                          "documents/structural/20250215-LivingKitchenFloors/"]
    }
  ]
}
```

### 3.4 `maintenance_log.json` — All Repair & Service Events

```json
{
  "events": [
    {
      "event_id":      "maint-001",
      "date":          "2022-12-06",
      "system_id":     "plumbing_general",
      "type":          "repair",
      "description":   "Post-inspection plumbing repairs — major pipe opening found during inspection",
      "contractor_id": "wimberley_plumbing",
      "cost":          null,
      "invoice_file":  "documents/plumbing/20221210-PlumbingInvoice_7284.pdf",
      "photos":        []
    },
    {
      "event_id":      "maint-002",
      "date":          "2024-10-21",
      "system_id":     "septic",
      "type":          "maintenance",
      "description":   "Septic maintenance",
      "files":         ["documents/plumbing/20241021-SepticMaintenance.gdoc"]
    },
    {
      "event_id":      "maint-003",
      "date":          "2024-11-30",
      "system_id":     "electrical",
      "type":          "repair",
      "description":   "Electrical work",
      "files":         ["documents/electrical/20241130-ElectricalWork.gdoc"]
    },
    {
      "event_id":      "maint-004",
      "date":          "2025-02-15",
      "system_id":     "foundation",
      "type":          "repair",
      "description":   "Living room and kitchen floor replacement. Beam rot discovered. Photos document extent of rot before repair.",
      "files":         ["documents/structural/20250215-LivingKitchenFloors/"]
    },
    {
      "event_id":      "maint-005",
      "date":          "2026-06-21",
      "system_id":     "septic",
      "type":          "repair",
      "description":   "Kitchen sink and guest tub backup. Septic pumped. Multiple lines snaked: G.Tub cleared, M.Tub (hair). Sewer layout is complex — see sewer_diagram.json.",
      "files":         ["documents/plumbing/20260522-PlumbingService_Kingsway.gdoc",
                        "documents/plumbing/photos/20260523-KSinkCleanout.png"]
    }
  ]
}
```

### 3.5 `capital_improvements.json` — IRS Basis Tracking

Separate from maintenance. Capital improvements increase the tax cost basis; ordinary repairs do not. This file is the IRS exhibit at sale.

```json
{
  "purchase_basis": 335000,
  "improvements": [
    {
      "date":           "2025-02-15",
      "description":    "Living room and kitchen floor replacement (structural beam rot)",
      "cost":           null,
      "contractor":     "",
      "invoice_file":   "",
      "is_capital":     true,
      "permit_required": false,
      "permit_number":   "",
      "notes":          "Beam rot — qualifies as capital improvement, not maintenance repair"
    }
  ],
  "notes": "Track every improvement from acquisition date. Total basis = purchase + improvements. Needed at sale for capital gains calculation."
}
```

### 3.6 `legal_records.json` — Title, Surveys, Legal Status

```json
{
  "deed": {
    "file":           "documents/legal/Deed.pdf",
    "recorded_with":  "Hays County Clerk",
    "record_date":    "2023-01-19",
    "grantor":        "",
    "grantee":        "Frank Rojas"
  },
  "title_insurance": {
    "file":           "documents/legal/20230201-TitleInsurance.pdf",
    "commitment_file":"documents/legal/20230105-CommitmentForTitleInsurance_T-7.pdf",
    "insurer":        "",
    "policy_number":  "",
    "coverage":       ""
  },
  "surveys": [
    { "date": "1979-01-01", "type": "Plat", "surveyor": "", "file": "documents/legal/Survey-1979Plat.tiff" },
    { "date": "1985-01-01", "type": "Survey", "surveyor": "", "file": "documents/legal/Survey-1985.pdf" },
    { "date": "2014-01-01", "type": "Survey", "surveyor": "", "file": "documents/legal/Survey-2014.pdf",
      "notes": "Most recent — use for boundary disputes" }
  ],
  "homestead_exemption": {
    "status":         "active",
    "county":         "Hays",
    "parcel_id":      "R33204",
    "filed_date":     "2023-05-01",
    "file":           "documents/legal/20230501-HomesteadExemptionForm.pdf"
  },
  "permits": [],
  "easements": [],
  "neighbor_disputes": [
    {
      "neighbor":     "D",
      "log_file":     "documents/legal/HistoryOfEventsWithNeighborD.gdoc",
      "status":       "documented",
      "notes":        "Maintain chronological event log with dates and any written communications"
    }
  ],
  "sellers_disclosure": {
    "file":           "documents/legal/20221106-SellersDisclosureNotice.pdf",
    "notes":          "Retain permanently — discloses known defects at time of purchase"
  }
}
```

### 3.7 `insurance.json` — Policy History and Claims

```json
{
  "current": {
    "carrier":          "",
    "policy_number":    "",
    "effective":        "2025-01-01",
    "premium_annual":   null,
    "file":             "documents/insurance/20230110-HomeIns.pdf",
    "notes":            "April 2025 quotes compared in HomeInsurance notebook"
  },
  "claims": [
    {
      "date":           "2021-07-28",
      "type":           "water loss",
      "paid":           13000,
      "carrier":        "",
      "notes":          "5-year carry forward on loss history. Prior owner claim — disclosed at purchase."
    }
  ],
  "history": [
    {
      "carrier":        "Choice Home Warranty",
      "type":           "home warranty",
      "start":          "2022-01-10",
      "end":            "2025-04-02",
      "cancelled":      true,
      "file":           "documents/insurance/20250402-Cancel-ChoiceHomeWarranty.pdf"
    }
  ]
}
```

### 3.8 `contractors.json` — Vetted Service Providers

```json
{
  "contractors": [
    {
      "contractor_id": "casa_lago_inspection",
      "name":          "Casa Lago Home Inspections & Mold Consultants",
      "contact":       "Casey Herbert",
      "license":       "TREC #24484",
      "phone":         "830-200-9098",
      "email":         "crherber1@gmail.com",
      "specialty":     "home inspection, mold",
      "last_used":     "2022-11-13",
      "rating":        null
    },
    {
      "contractor_id": "wimberley_plumbing",
      "name":          "Wimberley Plumbing",
      "specialty":     "plumbing",
      "last_used":     "2022-12-06"
    },
    {
      "contractor_id": "atex_spa",
      "name":          "A-Tex (Spa Service)",
      "contact":       "Joseph Polvado",
      "phone":         "512-508-9702",
      "specialty":     "hot tub / spa service",
      "last_used":     null
    },
    {
      "contractor_id": "new_braunfels_pool",
      "name":          "New Braunfels Pool & Spa",
      "contact":       "Emalie or Kat",
      "phone":         "830-660-6270",
      "specialty":     "spa chemicals / water chemistry",
      "notes":         "Chemical level guidance for hot tub"
    }
  ]
}
```

### 3.9 `sewer_diagram.json` — Plumbing Layout (Structured)

Derived from the 2D matplotlib notebook. Captures tribal knowledge as structured data.

```json
{
  "diagram_version": "2026-06",
  "source_file":     "documents/plumbing/kingswaySewer2D.ipynb",
  "description":     "Top-view drain line layout. Pier-and-beam — all pipes accessible from crawl space.",
  "nodes": [
    { "id": "o1", "label": "Kitchen Sink drain entry",       "connects_to": "y1" },
    { "id": "o2", "label": "Guest Bath Sink drain entry",    "connects_to": "y1" },
    { "id": "t1", "label": "Master Bath Tub drain entry",    "connects_to": "main" },
    { "id": "t2", "label": "Guest Bath Tub drain entry",     "connects_to": "y2" },
    { "id": "T1", "label": "Master Bath Toilet drain",       "connects_to": "main" },
    { "id": "T2", "label": "Guest Bath Toilet drain",        "connects_to": "y2" },
    { "id": "y1", "label": "T-connector (kitchen/sink)",     "connects_to": "main" },
    { "id": "y2", "label": "T-connector (guest bath)",       "connects_to": "main" },
    { "id": "main", "label": "Main drain → Septic Tank",     "connects_to": "septic" }
  ],
  "known_issues":    "Layout is non-standard ('spaghetti'). K.Sink and G.Tub share drain path through y1. Clog at y1 backs up both. Snaking must be attempted from cleanout, not from fixture."
}
```

---

## 4. Documents Index Strategy

Every file under `documents/` is registered in `documents_index.json` with:
- Local file path (relative to `records/`)
- Document type and date
- External custodian (for official records)
- Which agent owns/uses it

```json
{
  "documents": [
    {
      "doc_id":      "deed-001",
      "file":        "documents/legal/Deed.pdf",
      "type":        "deed",
      "date":        "2023-01-19",
      "custodian":   "Hays County Clerk (authoritative — local is a copy)",
      "owner_agent": "house_records",
      "description": "Warranty deed — purchase closing"
    },
    {
      "doc_id":      "survey-2014",
      "file":        "documents/legal/Survey-2014.pdf",
      "type":        "survey",
      "date":        "2014-01-01",
      "custodian":   "Hays County records + original surveyor",
      "owner_agent": "house_records"
    }
  ]
}
```

**Filename convention (enforced by agent on ingest):** `YYYYMMDD-<ShortDescription>.<ext>`

---

## 5. Official Records Custodian Map

Best-practice property management requires knowing not just where the local file is, but who holds the authoritative original.

| Record | Local File | External Custodian |
|---|---|---|
| Deed | `documents/legal/Deed.pdf` | Hays County Clerk (recorded) |
| Title Insurance | `documents/legal/20230201-TitleInsurance.pdf` | Title company; insured policy is permanent |
| Survey (current) | `documents/legal/Survey-2014.pdf` | Original surveyor + county records |
| Homestead Exemption | `documents/legal/20230501-HomesteadExemption.pdf` | Hays CAD (parcel R33204) — verify annually |
| Property Tax | `documents/legal/20240329-PropTaxPayment.pdf` | Hays CAD — `esearch.hayscad.com/Property/View/R33204` |
| HUD Settlement | `documents/legal/20230117-HUD_Settlement_Statement.pdf` | Lender archive; IRS requires 7 years |
| Home Inspection | `documents/inspection/Inspection_Report_177_Kingsway.pdf` | Owner — no external registry |
| Insurance Policy | `documents/insurance/20230110-HomeIns.pdf` | Carrier |
| Sellers Disclosure | `documents/legal/20221106-SellersDisclosureNotice.pdf` | Owner — retain permanently |

---

## 6. Recommended Document Folder Structure

```
houseTracker-data/kingsway_dr/
├── records/
│   ├── house_profile.json
│   ├── utilities.json
│   ├── systems_registry.json
│   ├── maintenance_log.json
│   ├── capital_improvements.json
│   ├── legal_records.json
│   ├── insurance.json
│   ├── contractors.json
│   ├── sewer_diagram.json
│   ├── documents_index.json
│   └── agents/
│       └── house_records/
│           └── action_items.json
└── documents/                      ← not committed to Git; filesystem only
    ├── legal/                      ← deed, title, surveys, homestead, HUD, permits
    ├── inspection/                 ← inspection reports
    ├── insurance/                  ← policies, claims, warranties
    ├── plumbing/                   ← invoices, sewer diagram, photos
    │   └── photos/
    ├── electrical/
    ├── hvac/
    ├── roofing/
    ├── structural/                 ← foundation docs, floor rot photos
    │   └── 20250215-LivingKitchenFloors/
    ├── outdoor/                    ← hot tub, deck, landscaping
    ├── financial/                  ← tax returns used at closing, mortgage docs
    └── neighbor/                   ← dispute logs and correspondence
```

**Migration from `~/GDrive/Family/Assets/KingswayDr`:** existing files map 1:1 to this structure. See §7.

---

## 7. Migration Map from Current GDrive Structure

| Current GDrive Path | → Records Path |
|---|---|
| `Home Docs/Deed.pdf` | `documents/legal/Deed.pdf` |
| `Home Docs/20221106-SellersDisclosureNotice.pdf` | `documents/legal/` |
| `Home Docs/Survey-*.pdf` | `documents/legal/` |
| `Home Docs/20230117-HUD Settlement Statement-Final.pdf` | `documents/legal/` |
| `Home Docs/20230201-TitleInsurance.pdf` | `documents/legal/` |
| `Home Docs/20221231-Contract-Closing-335k_Cash/` | `documents/legal/` |
| `20230501-HomesteadExemptionForm.pdf` | `documents/legal/` |
| `20240329-PropTaxPayment.pdf` | `documents/legal/` |
| `20221113-Inspection/` | `documents/inspection/` |
| `HomeInsurance/` | `documents/insurance/` |
| `Reciepts/` | `documents/insurance/` |
| `HouseMaintainanceReciepts/Plumbing/` | `documents/plumbing/` |
| `HouseMaintainanceReciepts/20241130-ElectricalWork.gdoc` | `documents/electrical/` |
| `HouseMaintainanceReciepts/20250215-LivingKitchenFloors/` | `documents/structural/` |
| `HomeImprovements/` | `documents/structural/` |
| `PierMorter2Slab/` | `documents/structural/` |
| `Home Docs/2016-2017 Celebrity Owners Manual.pdf` | `documents/outdoor/` (spa) |
| `Notebooks/HotTubInfo.ipynb` | `documents/outdoor/` |
| `History of Events with Neighbor D.gdoc` | `documents/neighbor/` |
| `Morg-checklist/` | `documents/financial/` |

---

## 8. Best Practices Flagged for KingswayDr

From the current GDrive analysis, the HouseRecords agent should raise these action items on first audit:

| Gap | Discipline | Action |
|---|---|---|
| No permits on file for electrical work (2024) or floor repair (2025) | Legal/Construction | Confirm whether permits were pulled; obtain copies from Hays County if so |
| Capital improvements log missing | Finance/Legal | Create `capital_improvements.json`; back-fill floor repair (2025) and any other qualifying work |
| Roof metal decking (2016) — pre-purchase, no install details | Construction | Extract make/model/warranty from invoice; add to systems_registry |
| Sewer layout is "spaghetti" (owner's words) | Construction | Populate `sewer_diagram.json` from the matplotlib notebook; add cleanout locations |
| Homestead exemption — verify it remains active each year | Finance/Legal | Check Hays CAD R33204 annually; add to check-in calendar |
| No current survey (2014 survey is 12 years old) | Real Estate/Legal | Consider updated survey, especially given neighbor dispute history |
| Prior water loss claim (2021, $13K) on insurance history | Finance | Confirm 5-year lookback period expires 2026-07-28; affects insurance premiums |
| Hot tub surface damage (chemical roughness) | Construction | Document current state; schedule refinishing assessment |
| Pier-to-slab conversion — researched, not decided | Construction | Record as open project in Architecture agent; link research notebooks |

---

## 9. Implementation Plan (HouseRecords Scope)

### Phase 0 — Bootstrap Records

- [ ] Create all JSON files with empty or stub data for KingswayDr
- [ ] `agents/house_records.py`: `read_json`, `write_json`, `append_event`, `get_events`, `search_docs` — all path-safe, all git-push on write
- [ ] `wsCmd.py --ingest <path>`: CLI tool to register an existing document into `documents_index.json` (prompts for type, date, description)

### Phase 1 — Migrate KingswayDr Files

- [ ] Copy existing GDrive files to `houseTracker-data/kingsway_dr/documents/` per migration map in §7
- [ ] Populate `house_profile.json`, `utilities.json`, `contractors.json` from known data
- [ ] Populate `systems_registry.json` for all known systems (see §3.3 stubs above)
- [ ] Back-fill `maintenance_log.json` from existing receipts and invoices
- [ ] Populate `legal_records.json` with all filed documents
- [ ] Raise action items from §8 into `agents/house_records/action_items.json`

### Phase 2 — Agent Query Interface

- [ ] `brief()`: returns property snapshot (address, sqft, acquisition date, active insurance, open action items count)
- [ ] `query(question, context)`: answers questions about documents, systems, or history using RAG over the JSON records
- [ ] `audit()`: scans for gaps per §8 best practices; returns action items
- [ ] `record(event)`: appends to `maintenance_log.json` or `capital_improvements.json` based on event type; git-pushes
