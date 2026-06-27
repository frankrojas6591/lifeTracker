# HouseMgr — Data, Config & Auth

**Version:** 0.4
**Date:** June 2026
**Parent:** [Design Index](./houseMgrAgent.md)

---

## 1. Storage Overview

The **private Git data repo** is the master store for all house records. PA and the local Mac each maintain a Git checkout of the data repo. Writes go to the local checkout first, then commit + push to Git immediately. Reads pull from Git at startup.

| Data Type | Location | In Git? |
|---|---|---|
| App code | `houseTracker/` (code repo, both PA and local) | Yes — code repo |
| Config & secrets | `~/.houseTracker/config.json` (each environment) | No — never committed |
| User auth DB | `~/.houseTracker/users.json.gpg` (each environment) | No — never committed |
| **HouseRecords (JSON)** | **`houseTracker-data/<house_id>/records/`** | **Yes — data repo (master)** |
| Documents (PDFs, photos) | `houseTracker-data/<house_id>/documents/` | No — too large; local filesystem only |

Two repos, one environment apiece:

```
github.com/<user>/houseTracker        ← code (Flask app, agents, UI)
github.com/<user>/houseTracker-data   ← records master (private)
```

---

## 2. Git Records Model

### Why Git as Master

Git gives records version history, branching for experiments, and a sync bus between PA and local Mac — with no additional infrastructure. Every record change is a commit; the log is the audit trail.

### Checkout Paths

| Environment | Data repo checkout path |
|---|---|
| PythonAnywhere | `/home/<pa_user>/houseTracker-data/` |
| Local Mac | `~/GDrive/dev/pyTrackers/houseTracker-data/` |

`config.json → data_repo_path` holds the environment-specific checkout path. `setup_paths.py` reads it and sets `DATA_REPO`, `RECORDS_DIR`, `DOCUMENTS_DIR`.

### Sync Protocol

```
On startup (both environments):
    git -C DATA_REPO pull --ff-only

On each agent write (house_records.py):
    git -C DATA_REPO add records/<house_id>/
    git -C DATA_REPO commit -m "auto: <agent> <event> <timestamp>"
    git -C DATA_REPO push origin main

On conflict:
    push fails → wsCmd.py --sync logs the error and halts
    owner resolves via: wsCmd.py --resolve (git pull --rebase + push)
```

Simultaneous writes from both PA and local are unlikely in normal use (single owner, one active session). The protocol surfaces conflicts explicitly rather than silently merging.

### What Lives in the Data Repo

```
houseTracker-data/
└── <house_id>/
    ├── records/
    │   └── agents/                    ← UANS path: agents/<category>/<agent>/
    │       ├── core/
    │       │   ├── records/           ← house.core.records
    │       │   ├── profile/           ← house.core.profile
    │       │   └── comm/              ← house.core.comm
    │       ├── systems/
    │       │   ├── hvac/              ← house.systems.hvac
    │       │   ├── electrical/        ← house.systems.electrical
    │       │   ├── plumbing/          ← house.systems.plumbing
    │       │   └── ...                ← roofing, security, appliances
    │       ├── designs/
    │       │   ├── architecture/      ← house.designs.architecture
    │       │   ├── landscaping/       ← house.designs.landscaping
    │       │   └── interior/          ← house.designs.interior
    │       ├── finance/
    │       │   ├── budget/            ← house.finance.budget
    │       │   ├── tax/               ← house.finance.tax
    │       │   └── investment/        ← house.finance.investment
    │       └── life/
    │           └── accessibility/     ← house.life.accessibility
    └── documents/                     ← NOT committed; filesystem only
        ├── permits/
        ├── invoices/
        └── photos/
```

`records/` is committed on every write. `documents/` is gitignored in the data repo — PDFs and photos stay on whichever filesystem they were uploaded to (PA or local Mac). Document metadata (filename, date, description) is stored in the agent's `knowledge.json` so both environments know what documents exist even if the file itself is remote.

---

## 3. Configuration Profile

`config.json` lives at `~/.houseTracker/config.json` on **each environment separately**. It is never committed. Paths, secrets, and environment identity differ between PA and local.

The code repo contains `config.json.example` with all keys and placeholder values.

### Schema

```json
{
  "env":                "pa",
  "default":            "ranch_house",
  "APP_SECRET_KEY":     "<flask signing key>",
  "APP_GPG_PASSPHRASE": "<gpg passphrase>",
  "data_repo_path":     "/home/<pa_user>/houseTracker-data",
  "auto_push":          true,
  "twilio_account_sid": "<Twilio SID>",
  "twilio_auth_token":  "<Twilio token>",
  "twilio_phone_number": "+15125550100",
  "houses": [
    {
      "house_id":   "ranch_house",
      "house_name": "Westwood Ranch",
      "address":    "123 Ranch Rd, Austin TX 78701",
      "owner_id":   "frank"
    }
  ],
  "owners": [
    {
      "owner_id":   "frank",
      "full_name":  "Frank Rojas",
      "email":      "frankr6591@gmail.com",
      "phone":      "+15125550101"
    }
  ]
}
```

**Key fields:**

| Key | Notes |
|---|---|
| `env` | `"pa"` or `"local"` — controls whether `/voice` route is registered |
| `data_repo_path` | Absolute path to the houseTracker-data Git checkout on this machine |
| `auto_push` | If `true`, `house_records.py` pushes to Git after every write |
| `twilio_*` | Only used when `env=pa`; ignored locally |
| `owner.phone` | Twilio caller ID for auto-login on voice channel |

`top_folder` is no longer in config.json — it is derived as `data_repo_path/<house_id>` by `setup_paths.py`.

---

## 4. Authentication & Login Layer

Follows the `llcRentalTracker` pattern, adapted for three channels and caller-ID auto-login.

### User DB

GPG-encrypted at `~/.houseTracker/users.json.gpg` — one copy per environment (PA and local Mac). Decrypted in-memory only; never plaintext on disk. Passphrase from `config.json → APP_GPG_PASSPHRASE`.

The two copies are independent; `wsCmd.py --setup` initializes each. If users are added on PA, they must be manually replicated to local (or exported/imported via `wsCmd.py --export-users / --import-users`).

### Roles

| Role | Access |
|---|---|
| `houseMgr` | Full admin — all houses, user management, configurator |
| `owner` | Full access to their associated house(s) |
| `viewer` | Read-only access to a house |

### Routes (`ui/houseLogin_auth.py`)

| Route | Channel | Description |
|---|---|---|
| `/login` | B, C | Credential check; sets session |
| `/logout` | B, C | Clears session |
| `/register` | B, C | `houseMgr` only — creates new user |
| `/select_house` | B, C | Multi-house owners pick active house |
| `/voice` | A | Twilio webhook — caller ID → auto-login or PIN; PA only |

### Flask Session

```python
session["logged_in"]  = True
session["username"]   = "frank"
session["role"]       = "owner"
session["house_id"]   = "ranch_house"
session["owner_id"]   = "frank"
session["channel"]    = "voice"    # "voice" | "web_pa" | "web_local"
```

`channel` drives `ResponseSynthesizer` output format: `voice` → ≤ 3 spoken sentences (TwiML); `web_*` → full HTML.

---

## 5. `setup_paths.py` Contract

```python
from setup_paths import (
    ENV,           # "pa" | "local"
    DATA_REPO,     # absolute path to houseTracker-data checkout
    RECORDS_DIR,   # DATA_REPO/<house_id>/records/
    DOCUMENTS_DIR, # DATA_REPO/<house_id>/documents/
    TWILIO_SID, TWILIO_TOKEN, TWILIO_NUMBER,  # None when env=local
)
```

`setup_paths.py` is the only module that reads `config.json`. It fails loudly if `config.json` is missing or `data_repo_path` does not exist. No silent fallbacks.

---

## 6. Implementation Plan (Data Scope)

### Phase 0 — Data Repo + Config Scaffold

- [ ] Create private `houseTracker-data` repo on GitHub; add `.gitignore` (`documents/`)
- [ ] `config.json.example` in code repo — all keys, inline comments
- [ ] `wsCmd.py --setup` (run on each environment): writes `~/.houseTracker/config.json`, clones data repo to `data_repo_path`, initializes GPG user DB
- [ ] `setup_paths.py`: reads config.json; derives all paths; registers Twilio constants only when `env=pa`

### Phase 1 — HouseRecords with Git Sync

- [ ] `agents/house_records.py`: `read_json(path)`, `write_json(path, data)` — write calls `git add + commit + push` when `auto_push=true`
- [ ] `wsCmd.py --pull`: manual `git pull` from data repo
- [ ] `wsCmd.py --push`: manual `git add/commit/push` to data repo
- [ ] `wsCmd.py --sync`: `git pull --rebase + push` for conflict resolution

### Phase 2 — Document Metadata Bridge

- [ ] Agent `knowledge.json` stores document metadata (`{filename, date, description, env_uploaded}`) so both PA and local know what documents exist even if the file is on the other machine's filesystem
- [ ] Future: optional rsync of documents between PA and local for full local copies
