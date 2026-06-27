# HouseRecords Agent — Data Design

**Version:** 0.2
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

## 3. Official Records Custodian Map

Best-practice property management requires knowing not just where the local file is, but who holds the authoritative original.

| Record | Local File | External Custodian |
|---|---|---|
| Deed | `documents/legal/Deed.pdf` | Hays County Clerk (recorded) |
| Title Insurance | `documents/legal/20230201-TitleInsurance.pdf` | Title company; insured policy is permanent |
| Survey (current) | `documents/legal/Survey-2014.pdf` | Original surveyor + county records |
| Homestead Exemption | `documents/legal/20230501-HomesteadExemption.pdf` | Hays CAD parcel R33204 — verify annually at `esearch.hayscad.com` |
| Property Tax | `documents/legal/20240329-PropTaxPayment.pdf` | Hays CAD — `esearch.hayscad.com/Property/View/R33204` |
| HUD Settlement | `documents/legal/20230117-HUD_Settlement_Statement.pdf` | Lender archive; IRS requires 7 years |
| Home Inspection | `documents/inspection/Inspection_Report_177_Kingsway.pdf` | Owner — no external registry |
| Insurance Policy | `documents/insurance/20230110-HomeIns.pdf` | Carrier |
| Sellers Disclosure | `documents/legal/20221106-SellersDisclosureNotice.pdf` | Owner — retain permanently |

---

## 4. Recommended Document Folder Structure

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

---

## 5. Best Practices Flagged for KingswayDr

From the current GDrive analysis, the HouseRecords agent should raise these action items on first audit:

| Gap | Discipline | Action |
|---|---|---|
| No permits on file for electrical work (2024) or floor repair (2025) | Legal/Construction | Confirm whether permits were pulled; obtain copies from Hays County if so |
| Capital improvements log missing | Finance/Legal | Create `capital_improvements.json`; back-fill floor repair (2025) and any other qualifying work |
| Roof metal decking (2016) — pre-purchase, no install details | Construction | Extract make/model/warranty from invoice; add to systems_registry |
| Sewer layout is "spaghetti" (owner description) | Construction | Populate `sewer_diagram.json` from the matplotlib notebook; add cleanout locations |
| Homestead exemption — verify it remains active each year | Finance/Legal | Check Hays CAD R33204 annually; add to check-in calendar |
| No current survey (2014 survey is 12 years old) | Real Estate/Legal | Consider updated survey, especially given neighbor dispute history |
| Prior water loss claim (2021-07-28, $13K) on insurance history | Finance | 5-year lookback period expires 2026-07-28; affects insurance premiums |
| Hot tub surface damage (chemical roughness noted) | Construction | Document current state; schedule refinishing assessment |
| Pier-to-slab conversion — researched 2023, not decided | Construction | Record as open project in Architecture agent; link research notebooks |

---

## 6. Implementation Plan

| Issue | Title | Depends On |
|---|---|---|
| [#1](https://github.com/frankrojas6591/houseTracker/issues/1) | houseRecords: Phase 0 — Bootstrap Records | — |
| [#2](https://github.com/frankrojas6591/houseTracker/issues/2) | houseRecords: Phase 1 — Migrate KingswayDr Files | #1 |
| [#3](https://github.com/frankrojas6591/houseTracker/issues/3) | houseRecords: Phase 2 — Agent Query Interface | #1, #2 |

---

## Appendix A — JSON Schema

All records live under `houseTracker-data/<house_id>/records/`. The HouseRecords agent owns this entire subtree. Other agents read from it; only HouseRecords writes the top-level files.

### A.1 `house_profile.json` — Property Identity

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

### A.2 `utilities.json` — Service Accounts

```json
{
  "utilities": [
    {
      "utility_id":   "electricity",
      "provider":     "PEC (Pedernales Electric Cooperative)",
      "account":      "3000789437",
      "phone":        "888-554-4732",
      "pay_method":   "online"
    },
    {
      "utility_id":   "water",
      "provider":     "Wimberley Water Supply Corp",
      "phone":        "512-847-2323",
      "address":      "P.O. Box 10, 110 LaPais, Wimberley TX 78676",
      "pay_url":      "https://payclix.com/wimberleywater",
      "notes":        "Pressure regulator installed — line pressure exceeds 100 PSI. Check valve prevents upstream reverse flow."
    },
    { "utility_id": "cable",  "provider": "Spectrum" },
    { "utility_id": "waste",  "provider": "Texas Waste", "notes": "Trash/recycling pickup" }
  ]
}
```

### A.3 `systems_registry.json` — All Physical Systems

One entry per tracked system or appliance. Drives the maintenance and warranty calendar.

```json
{
  "systems": [
    {
      "system_id":        "hvac_ac",
      "category":         "hvac",
      "name":             "AC Unit",
      "install_date":     "",
      "expected_life_yrs": 15,
      "last_service":     "2016-05-16",
      "files":            ["documents/hvac/20160516-AC_Service_Warranty.pdf"]
    },
    {
      "system_id":        "roof",
      "category":         "roofing",
      "name":             "Metal Roof",
      "install_date":     "2016-12-12",
      "expected_life_yrs": 40,
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
      "notes":            "Surface roughness risk from excess shock+bromine. Texas Refinish (210) 903-6990."
    },
    {
      "system_id":        "septic",
      "category":         "plumbing",
      "name":             "Septic Tank",
      "capacity_gal":     1000,
      "last_pumped":      "2026-06-21",
      "recommended_interval_yrs": 3,
      "notes":            "Complex drain layout — see sewer_diagram.json. 2026-06-21: backed up at K.Sink and G.Tub.",
      "files":            ["documents/plumbing/photos/"]
    },
    {
      "system_id":        "water_softener",
      "category":         "plumbing",
      "name":             "Water Softener / Filtration"
    },
    {
      "system_id":        "foundation",
      "category":         "structural",
      "name":             "Pier-and-Beam Foundation",
      "notes":            "Pier-to-slab conversion researched 2023 — not executed. Beam rot in living room discovered Feb 2025.",
      "files":            ["documents/structural/20250215-LivingKitchenFloors/"]
    }
  ]
}
```

### A.4 `maintenance_log.json` — All Repair & Service Events

```json
{
  "events": [
    {
      "event_id":     "maint-001",
      "date":         "2022-12-06",
      "system_id":    "plumbing_general",
      "type":         "repair",
      "description":  "Post-inspection plumbing repairs — major pipe opening found during inspection",
      "contractor_id":"wimberley_plumbing",
      "invoice_file": "documents/plumbing/20221210-PlumbingInvoice_7284.pdf"
    },
    {
      "event_id":     "maint-002",
      "date":         "2024-10-21",
      "system_id":    "septic",
      "type":         "maintenance",
      "description":  "Septic maintenance",
      "files":        ["documents/plumbing/20241021-SepticMaintenance.gdoc"]
    },
    {
      "event_id":     "maint-003",
      "date":         "2024-11-30",
      "system_id":    "electrical",
      "type":         "repair",
      "description":  "Electrical work",
      "files":        ["documents/electrical/20241130-ElectricalWork.gdoc"]
    },
    {
      "event_id":     "maint-004",
      "date":         "2025-02-15",
      "system_id":    "foundation",
      "type":         "repair",
      "description":  "Living room and kitchen floor replacement. Beam rot discovered and repaired.",
      "files":        ["documents/structural/20250215-LivingKitchenFloors/"]
    },
    {
      "event_id":     "maint-005",
      "date":         "2026-06-21",
      "system_id":    "septic",
      "type":         "repair",
      "description":  "K.Sink and G.Tub backup. Tank pumped. Lines snaked: G.Tub cleared, M.Tub cleared (hair). See sewer_diagram.json for root cause.",
      "files":        ["documents/plumbing/20260522-PlumbingService_Kingsway.gdoc",
                       "documents/plumbing/photos/20260523-KSinkCleanout.png"]
    }
  ]
}
```

### A.5 `capital_improvements.json` — IRS Basis Tracking

```json
{
  "purchase_basis": 335000,
  "improvements": [
    {
      "date":           "2025-02-15",
      "description":    "Living room and kitchen floor replacement (structural beam rot)",
      "cost":           null,
      "is_capital":     true,
      "permit_required": false,
      "notes":          "Beam rot — qualifies as capital improvement, not maintenance repair"
    }
  ],
  "notes": "Total basis = purchase_basis + sum(improvements.cost). Required at sale for capital gains calculation."
}
```

### A.6 `legal_records.json` — Title, Surveys, Legal Status

```json
{
  "deed": {
    "file":          "documents/legal/Deed.pdf",
    "recorded_with": "Hays County Clerk",
    "record_date":   "2023-01-19",
    "grantee":       "Frank Rojas"
  },
  "title_insurance": {
    "file":           "documents/legal/20230201-TitleInsurance.pdf",
    "commitment_file":"documents/legal/20230105-CommitmentForTitleInsurance_T-7.pdf"
  },
  "surveys": [
    { "date": "1979-01-01", "type": "Plat",   "file": "documents/legal/Survey-1979Plat.tiff" },
    { "date": "1985-01-01", "type": "Survey", "file": "documents/legal/Survey-1985.pdf" },
    { "date": "2014-01-01", "type": "Survey", "file": "documents/legal/Survey-2014.pdf",
      "notes": "Most recent — use for boundary disputes" }
  ],
  "homestead_exemption": {
    "status":     "active",
    "county":     "Hays",
    "parcel_id":  "R33204",
    "filed_date": "2023-05-01",
    "file":       "documents/legal/20230501-HomesteadExemptionForm.pdf"
  },
  "permits": [],
  "easements": [],
  "neighbor_disputes": [
    {
      "neighbor": "D",
      "log_file": "documents/neighbor/HistoryOfEventsWithNeighborD.gdoc",
      "status":   "documented"
    }
  ],
  "sellers_disclosure": {
    "file":  "documents/legal/20221106-SellersDisclosureNotice.pdf",
    "notes": "Retain permanently — discloses known defects at time of purchase"
  }
}
```

### A.7 `insurance.json` — Policy History and Claims

```json
{
  "current": {
    "file":  "documents/insurance/20230110-HomeIns.pdf",
    "notes": "April 2025 quotes compared in HomeInsurance notebook"
  },
  "claims": [
    {
      "date":  "2021-07-28",
      "type":  "water loss",
      "paid":  13000,
      "notes": "Prior owner claim. 5-year lookback expires 2026-07-28."
    }
  ],
  "history": [
    {
      "carrier":   "Choice Home Warranty",
      "type":      "home warranty",
      "start":     "2022-01-10",
      "end":       "2025-04-02",
      "cancelled": true,
      "file":      "documents/insurance/20250402-Cancel-ChoiceHomeWarranty.pdf"
    }
  ]
}
```

### A.8 `contractors.json` — Vetted Service Providers

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
      "last_used":     "2022-11-13"
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
      "specialty":     "hot tub / spa service"
    },
    {
      "contractor_id": "new_braunfels_pool",
      "name":          "New Braunfels Pool & Spa",
      "contact":       "Emalie or Kat",
      "phone":         "830-660-6270",
      "specialty":     "spa chemicals / water chemistry"
    }
  ]
}
```

### A.9 `sewer_diagram.json` — Plumbing Layout

Derived from the 2D matplotlib notebook. Captures tribal knowledge as structured data so the Plumbing agent can reason about root causes.

```json
{
  "diagram_version": "2026-06",
  "source_file":     "documents/plumbing/kingswaySewer2D.ipynb",
  "description":     "Top-view drain line layout. Pier-and-beam — all pipes accessible from crawl space.",
  "nodes": [
    { "id": "o1", "label": "Kitchen Sink drain entry",    "connects_to": "y1" },
    { "id": "o2", "label": "Guest Bath Sink drain entry", "connects_to": "y1" },
    { "id": "t1", "label": "Master Bath Tub drain",       "connects_to": "main" },
    { "id": "t2", "label": "Guest Bath Tub drain",        "connects_to": "y2" },
    { "id": "T1", "label": "Master Bath Toilet drain",    "connects_to": "main" },
    { "id": "T2", "label": "Guest Bath Toilet drain",     "connects_to": "y2" },
    { "id": "y1", "label": "T-connector (kitchen+sink)",  "connects_to": "main" },
    { "id": "y2", "label": "T-connector (guest bath)",    "connects_to": "main" },
    { "id": "main", "label": "Main drain → Septic Tank",  "connects_to": "septic" }
  ],
  "known_issues": "Layout is non-standard. K.Sink and G.Tub share drain path through y1. Clog at y1 backs up both. Snake from cleanout, not from fixture."
}
```

---

## Appendix B — Documents Index Strategy

Every file under `documents/` is registered in `documents_index.json` with its local path, type, date, external custodian, and owning agent.

```json
{
  "documents": [
    {
      "doc_id":      "deed-001",
      "file":        "documents/legal/Deed.pdf",
      "type":        "deed",
      "date":        "2023-01-19",
      "custodian":   "Hays County Clerk (authoritative — local is a copy)",
      "owner_agent": "house_records"
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

## Appendix C — Migration Map from GDrive

Current location: `~/GDrive/Family/Assets/KingswayDr`
Target: `houseTracker-data/kingsway_dr/documents/`

| Current GDrive Path | Target Path |
|---|---|
| `Home Docs/Deed.pdf` | `documents/legal/` |
| `Home Docs/20221106-SellersDisclosureNotice.pdf` | `documents/legal/` |
| `Home Docs/Survey-*.pdf / .tiff` | `documents/legal/` |
| `Home Docs/20230117-HUD Settlement Statement-Final.pdf` | `documents/legal/` |
| `Home Docs/20230201-TitleInsurance.pdf` | `documents/legal/` |
| `Home Docs/20221231-Contract-Closing-335k_Cash/` | `documents/legal/` |
| `20230501-HomesteadExemptionForm.pdf` | `documents/legal/` |
| `20240329-PropTaxPayment.pdf` | `documents/legal/` |
| `20221113-Inspection/` | `documents/inspection/` |
| `Reciepts/20221112-HomeInspection.pdf` | `documents/inspection/` |
| `HomeInsurance/` | `documents/insurance/` |
| `Reciepts/20250402-Cancel-Choice Home Warranty.pdf` | `documents/insurance/` |
| `HouseMaintainanceReciepts/Plumbing/` | `documents/plumbing/` |
| `HouseMaintainanceReciepts/20241130-ElectricalWork.gdoc` | `documents/electrical/` |
| `HouseMaintainanceReciepts/20250215-LivingKitchenFloors/` | `documents/structural/` |
| `HomeImprovements/` | `documents/structural/` |
| `PierMorter2Slab/` | `documents/structural/` |
| `Home Docs/2016-2017 Celebrity Owners Manual.pdf` | `documents/outdoor/` |
| `Notebooks/HotTubInfo.ipynb` | `documents/outdoor/` |
| `HouseMaintainanceReciepts/Water Softner-Filtration.gdoc` | `documents/plumbing/` |
| `History of Events with Neighbor D.gdoc` | `documents/neighbor/` |
| `Morg-checklist/` | `documents/financial/` |
| `Home Docs/20230105-10KLoan-Amplify.pdf` | `documents/financial/` |
| `HouseMaintainanceReciepts/20160516-AC_Service_*.pdf` | `documents/hvac/` |
| `HouseMaintainanceReciepts/20161212-Roof_Metal-decking.pdf` | `documents/roofing/` |
