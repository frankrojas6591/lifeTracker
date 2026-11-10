# myMIA — Design

> It's November. The enrollment email lands. Frank asks one question: **"Enhanced or Essential?"**
> myMIA answers with his own claims, not a brochure.

## The Flow

```
 ~/GDrive/Family/Health/ (private, never in git)         lifeTracker repo (code only)
 ┌──────────────────────────────────────┐              ┌───────────────────────────┐
 │ medicalAgentProfile.json  (who/where)│─────┐        │ medicalAgent/profile.py   │
 │ MedicalIns/2027/                     │     ▼        │ medicalAgent/myMIA/       │
 │   annualProfile.json  ◄── YEAR INPUT │──► myMIA.ipynb│   claims → engine → rank  │
 │   2026_FYClaims_*.csv                │              └───────────────────────────┘
 │   Providers.json                     │
 └──────────────────────────────────────┘
```

## The Four Scenarios

| Story | Usage | Extras |
|---|---|---|
| healthy | 0.8x | no PT / endo / weight Rx |
| baseline | 1.0x | replay of last year's claims, annualized |
| inflated | 1.3x | prices creep up |
| illness | 1.8x | 2 ER + 1 inpatient stay |

- Weights live in the annual profile → **expected cost** and **worst case** per plan.
- Winner = lowest expected cost; worst case shown so the risk is visible.

## Cost Model (per plan, per scenario)

- **Premium** = (monthly − Part B credit) × 12
- **Medical** = visits replayed at plan copay; plan deductible paid first; capped at OOP max; events (ER, inpatient) added
- **Pharmacy** = tier copays; tier 3-4 deductible; capped at Part D catastrophic ($2,400)
- A visit = one provider on one day (multi-line claims count once)

## Guardrails

- Unknown provider / drug / copay class → **hard error**, no silent defaults
- Missing medicalAgent profile → created with a log warning
- Duplicate claim rows (overlapping UHC downloads) are dropped and logged
- Plan caps held flat in the 10-year view (conservative for Enhanced)

## The Story Going Forward

- Premiums +8%/yr, medical prices +6%/yr, my usage +3%/yr (all editable)
- 1 / 5 / 10-year cumulative cost, expected mix vs illness-every-year
- HRA runway: how many years the HRA covers expected OOP
