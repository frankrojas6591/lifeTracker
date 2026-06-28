# pyTrackers Git Repository Strategy

**Version:** 0.1
**Date:** June 2026
**Status:** Decision required

---

## The Design Constraint That Drives This Decision

All discipline trackers share one communication layer (voice, web, auth, LLM). That shared layer is code — it must live somewhere. The git strategy is primarily the answer to: **where does the shared code live, and how does each tracker access it?**

---

## Current State

| Tracker | Repo | Account | Status |
|---|---|---|---|
| llcRentalTracker | `wbgroupmgr/llcRentalTracker` | Work | Most mature; active development |
| houseTracker | `frankrojas6591/houseTracker` | Personal | Docs only; no source code yet |
| medicalTracker | *(no repo)* | Personal | Early design doc only |
| moneyTracker | *(no repo)* | Personal | Empty directory |
| estateTracker | *(no repo)* | Personal | Empty directory |
| emotionalTracker | *(no repo)* | Personal | Empty directory |
| faithTracker | *(no repo)* | Personal | Empty directory |
| lifeTracker | *(no repo)* | Personal | Vision doc only |

**Key constraint:** `llcRentalTracker` is on the work account and must stay separate — it is a business tool, separate deployment, separate concern.

---

## Options

### Option A: One Repo Per Tracker (Status Quo Extended)

Continue creating separate repos: `houseTracker`, `medicalTracker`, `moneyTracker`, `estateTracker`, `emotionalTracker`, `faithTracker`, `lifeTracker`.

Shared comm layer → `pytracker-core` published as a private pip package.

```
github.com/frankrojas6591/pytracker-core     ← shared pip package
github.com/frankrojas6591/houseTracker
github.com/frankrojas6591/medicalTracker
github.com/frankrojas6591/moneyTracker
github.com/frankrojas6591/estateTracker
github.com/frankrojas6591/emotionalTracker
github.com/frankrojas6591/faithTracker
github.com/frankrojas6591/lifeTracker
github.com/wbgroupmgr/llcRentalTracker        ← separate, stays separate
```

**Pro:**
- Clean separation; each tracker deploys independently
- Mirrors the existing llcRentalTracker pattern
- Each tracker can be on a different deployment cadence

**Con:**
- 7 repos to maintain + 1 shared package to version
- Cross-tracker changes require coordinated PRs across multiple repos
- `pytracker-core` versioning adds overhead — a comm change requires bumping the version in every tracker that depends on it
- For a solo developer, this is multi-repo overhead without multi-team benefit

---

### Option B: Monorepo — All Personal Trackers Together

One repo contains all personal trackers and the shared layer.

```
github.com/frankrojas6591/pyTrackers         ← monorepo (personal)
├── core/                                    ← shared comm, auth, records, LLM, models
├── lifeTracker/                             ← PersonalAssistant orchestrator
├── houseTracker/                            ← (migrated from current houseTracker repo)
├── medicalTracker/
├── moneyTracker/
├── estateTracker/
├── emotionalTracker/
└── faithTracker/

github.com/wbgroupmgr/llcRentalTracker       ← stays separate (work account, business)
```

**Pro:**
- Shared code in `core/` is literally shared — no package, no versioning
- One `git push` commits changes across all trackers simultaneously
- Cross-tracker refactoring is a single PR
- Simpler for a solo developer at this stage — no dependency management
- `houseTracker` has no source code yet, so migration cost is low (docs only)

**Con:**
- One repo for everything can feel large (but for 7 solo projects, it stays manageable)
- `houseTracker` currently has its own GitHub remote — migration needed
- PA (PythonAnywhere) WSGI deployment needs to point to one repo, but only deploy specific tracker code

---

### Option C: Hybrid — Monorepo for New Trackers, Keep houseTracker Separate

```
github.com/frankrojas6591/pyTrackers         ← new monorepo (medicalTracker, moneyTracker, etc.)
├── core/
├── lifeTracker/
├── medicalTracker/
├── moneyTracker/
├── estateTracker/
├── emotionalTracker/
└── faithTracker/

github.com/frankrojas6591/houseTracker        ← stays separate (already has remote)
github.com/wbgroupmgr/llcRentalTracker        ← stays separate (work account)
```

**Pro:** No migration needed; houseTracker keeps its existing repo; new trackers go into the monorepo
**Con:** houseTracker is still isolated from the shared core; if `core/` changes, houseTracker must either import from a package or stay disconnected

---

## Recommendation: **Option B — Monorepo**

Rationale:
1. **Shared comm layer requires shared code.** The cleanest way to share code without versioning overhead is to put it in the same repo. For a solo developer, managing `pytracker-core` as a versioned pip package has all the overhead of a public library with none of the benefit.
2. **No source code exists yet in any personal tracker.** Migration cost is near zero — only docs need moving (or re-pointing).
3. **The PA deployment is one Flask app.** A monorepo maps naturally to one WSGI deployment.
4. **llcRentalTracker stays separate.** It is on a different GitHub account (work vs. personal), has a different deployment, and is a mature standalone system. It integrates with the PA via a narrow API, not shared code.

### Migration Steps

1. Create `github.com/frankrojas6591/pyTrackers` monorepo (personal account, SSH alias `github.com-fxr`)
2. Move `houseTracker/docs/` into `pyTrackers/houseTracker/docs/` (keep git history via subtree merge or fresh start — docs only, no source, so fresh start is fine)
3. Archive `frankrojas6591/houseTracker` repo (keep as read-only, point README to new location)
4. Update `houseTracker/CLAUDE.md` SSH remote to point to new monorepo
5. All new tracker development happens in `pyTrackers/`

### Monorepo Structure

```
pyTrackers/
├── CLAUDE.md                      ← workspace-level instructions
├── core/                          ← pytracker.core shared package
│   ├── comm/                      ← Twilio, Flask blueprints, web helpers
│   ├── auth/                      ← GPG user DB, session management
│   ├── records/                   ← UANS path resolution, git_store
│   ├── llm/                       ← IntentParser (Haiku), Synthesizer (Sonnet)
│   └── models/                    ← AgentResponse, ActionItem, TrackerBriefing
│
├── lifeTracker/                   ← PersonalAssistant orchestrator
│   ├── wsCmd.py                   ← CLI: --setup, --start, --checkin
│   ├── orchestrator.py            ← routes intents across trackers
│   ├── registry.py                ← TrackerRegistry (maps namespace → tracker)
│   └── docs/
│       └── personalAssistanceVision.md
│
├── houseTracker/                  ← home management
│   ├── agents/                    ← 16 discipline agents
│   ├── ui/                        ← Flask blueprint
│   └── docs/
│
├── medicalTracker/                ← health and care
│   ├── agents/
│   ├── ui/
│   └── docs/
│
├── moneyTracker/                  ← personal finance
│   ├── agents/
│   ├── ui/
│   └── docs/
│
├── estateTracker/                 ← estate management
│   ├── agents/
│   ├── ui/
│   └── docs/
│
├── emotionalTracker/              ← emotional health
│   ├── agents/
│   ├── ui/
│   └── docs/
│
├── faithTracker/                  ← spiritual practice
│   ├── agents/
│   ├── ui/
│   └── docs/
│
├── wsgi.py                        ← master Flask WSGI (registers all tracker blueprints)
├── setup_paths.py                 ← reads config.json; sets all path constants
├── config.json.example
└── requirements.txt               ← all tracker deps unified
```

### Data Repos Stay Separate

Each tracker keeps its own private data repo. Data repos are small (JSON only) and tracker-specific. There is no benefit to a data monorepo.

```
github.com/frankrojas6591/houseTracker-data    ← house records (existing)
github.com/frankrojas6591/medicalTracker-data   ← health records
github.com/frankrojas6591/moneyTracker-data     ← financial records
github.com/frankrojas6591/estateTracker-data    ← estate records
...
```

---

## Decision Checklist

- [ ] Approve Option B (monorepo) or choose alternative
- [ ] Create `pyTrackers` repo on personal GitHub (SSH: `github.com-fxr`)
- [ ] Migrate `houseTracker/docs/` to `pyTrackers/houseTracker/docs/`
- [ ] Archive `frankrojas6591/houseTracker` repo
- [ ] Update CLAUDE.md across all tracker directories
