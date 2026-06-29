# lifeTracker — RecordAgent Design

**Version:** 1.0
**Date:** June 2026
**Parent:** [Design Index](./lifeTracker_design.md)

---

## 1. Purpose

RecordAgent is the **sole read/write interface** between every discipline agent and the filesystem. No agent touches the filesystem directly. No agent accesses git directly. All I/O flows through RecordAgent.

Three responsibilities:

1. **Path derivation** — translate a UANS identifier into its filesystem path
2. **Read/write/git-push** — atomic write → git commit → git push, so git history IS the audit trail
3. **Provisioning** — create the full `records/agents/` directory tree for all namespaces on first run

Full ecosystem background: `recordAgent/docs/recordAgentDesign.md`
This doc focuses on implementation design for the Phase 1 build.

---

## 2. The UANS → Path Contract

Every record in the system is identified by a 4-segment dot-notation UANS:

```
<namespace>.<category>.<agent>.<record>
```

This maps to a filesystem path in `lifeTracker-data/`:

```
records/agents/<namespace>/<category>/<agent>/<record>.json
```

Examples:

| UANS | Filesystem path |
|---|---|
| `house.systems.hvac.maintenance_log` | `records/agents/house/systems/hvac/maintenance_log.json` |
| `medical.health.medications.current` | `records/agents/medical/health/medications/current.json` |
| `money.planning.rmd.schedule` | `records/agents/money/planning/rmd/schedule.json` |
| `life.pa.action_items.open` | `records/agents/life/pa/action_items/open.json` |

The `<record>` segment is optional in directory-level operations. When omitted, the UANS identifies a directory.

---

## 3. Data Repo — `lifeTracker-data`

A separate private GitHub repo: `github.com/frankrojas6591/lifeTracker-data`

Checked out locally at the path in `config.json["data_repo_path"]`. On PythonAnywhere, checked out at `/home/frankr6591/lifeTracker-data`.

```
lifeTracker-data/
└── records/
    └── agents/
        ├── house/
        │   ├── core/
        │   │   ├── records/
        │   │   ├── profile/
        │   │   └── comm/
        │   ├── systems/
        │   │   ├── hvac/
        │   │   ├── electrical/
        │   │   ├── plumbing/
        │   │   ├── roofing/
        │   │   ├── security/
        │   │   └── appliances/
        │   ├── designs/
        │   │   ├── architecture/
        │   │   ├── landscaping/
        │   │   └── interior/
        │   ├── finance/
        │   │   ├── budget/
        │   │   ├── tax/
        │   │   └── investment/
        │   └── life/
        │       └── accessibility/
        ├── medical/
        │   ├── health/
        │   │   ├── profile/
        │   │   ├── conditions/
        │   │   └── medications/
        │   ├── vitals/
        │   │   ├── labs/
        │   │   ├── bp/
        │   │   └── cpap/
        │   └── care/
        │       ├── appointments/
        │       └── directives/
        ├── money/
        │   ├── accounts/
        │   │   └── registry/
        │   ├── transactions/
        │   │   └── log/
        │   └── planning/
        │       ├── rmd/
        │       ├── runway/
        │       └── income/
        ├── estate/
        │   ├── assets/
        │   │   ├── registry/
        │   │   └── net_worth/
        │   ├── legal/
        │   │   ├── documents/
        │   │   └── beneficiaries/
        │   └── planning/
        │       └── runway/
        ├── emotional/
        │   ├── core/
        │   │   └── checkin/
        │   ├── relationships/
        │   ├── grief/
        │   │   └── companion/
        │   ├── legacy/
        │   │   └── review/
        │   └── stress/
        │       └── monitor/
        ├── faith/
        │   ├── core/
        │   │   └── practice/
        │   ├── examen/
        │   │   └── reflection/
        │   ├── sacraments/
        │   │   └── history/
        │   ├── community/
        │   │   └── life/
        │   └── legacy/
        │       └── ethical_will/
        └── life/
            └── pa/
                ├── briefings/
                └── action_items/
```

---

## 4. Implementation

### 4.1 UANS Path Derivation — `core/records/uans.py`

```python
from pathlib import Path

def uans_to_path(uans: str, data_repo_root: Path) -> Path:
    """
    Translate UANS string to filesystem path.
    'house.systems.hvac.maintenance_log' →
    data_repo_root / 'records/agents/house/systems/hvac/maintenance_log.json'
    """
    parts = uans.split(".")
    if len(parts) < 3:
        raise ValueError(f"UANS must have at least 3 segments: {uans}")
    if len(parts) == 4:
        namespace, category, agent, record = parts
        return data_repo_root / "records" / "agents" / namespace / category / agent / f"{record}.json"
    else:
        # 3-segment: returns directory path
        namespace, category, agent = parts[:3]
        return data_repo_root / "records" / "agents" / namespace / category / agent

def uans_to_dir(uans: str, data_repo_root: Path) -> Path:
    """Return directory path for a UANS (ignores record segment if present)."""
    parts = uans.split(".")[:3]
    namespace, category, agent = parts
    return data_repo_root / "records" / "agents" / namespace / category / agent
```

### 4.2 Git Store — `core/records/git_store.py`

All writes are atomic: write file → git add → git commit → git push.

```python
import json
import subprocess
from pathlib import Path

def write_json(uans: str, data: dict, config: dict, message: str = None) -> None:
    """
    Write data dict to UANS path and commit+push to lifeTracker-data.
    Raises if push fails — no silent fallback.
    """
    root = Path(config["data_repo_path"])
    path = uans_to_path(uans, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))

    commit_msg = message or f"record: update {uans}"
    _git(root, ["add", str(path)])
    _git(root, ["commit", "-m", commit_msg])
    _git(root, ["push", "origin", "main"])

def read_json(uans: str, config: dict) -> dict | None:
    """Return parsed JSON for UANS path, or None if file does not exist."""
    root = Path(config["data_repo_path"])
    path = uans_to_path(uans, root)
    if not path.exists():
        return None
    return json.loads(path.read_text())

def append_action_item(uans: str, item: dict, config: dict) -> None:
    """
    Append an action item to the UANS action_items list.
    Creates the file if it does not exist.
    """
    existing = read_json(uans, config) or {"action_items": []}
    existing["action_items"].append(item)
    write_json(uans, existing, config, f"action_item: {item.get('summary', uans)}")

def _git(repo: Path, args: list[str]) -> None:
    result = subprocess.run(["git"] + args, cwd=repo, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
```

### 4.3 RecordAgent — `core/records/record_agent.py`

```python
from pathlib import Path
from core.records.git_store import write_json, read_json, append_action_item
from core.records.uans import uans_to_dir

# All UANS directories that must exist across all agent namespaces.
AGENT_DIRECTORIES = [
    "house.core.records", "house.core.profile", "house.core.comm",
    "house.systems.hvac", "house.systems.electrical", "house.systems.plumbing",
    "house.systems.roofing", "house.systems.security", "house.systems.appliances",
    "house.designs.architecture", "house.designs.landscaping", "house.designs.interior",
    "house.finance.budget", "house.finance.tax", "house.finance.investment",
    "house.life.accessibility",
    "medical.health.profile", "medical.health.conditions", "medical.health.medications",
    "medical.vitals.labs", "medical.vitals.bp", "medical.vitals.cpap",
    "medical.care.appointments", "medical.care.directives",
    "money.accounts.registry", "money.transactions.log",
    "money.planning.rmd", "money.planning.runway", "money.planning.income",
    "estate.assets.registry", "estate.assets.net_worth",
    "estate.legal.documents", "estate.legal.beneficiaries", "estate.planning.runway",
    "emotional.core.checkin", "emotional.relationships",
    "emotional.grief.companion", "emotional.legacy.review", "emotional.stress.monitor",
    "faith.core.practice", "faith.examen.reflection",
    "faith.sacraments.history", "faith.community.life", "faith.legacy.ethical_will",
    "life.pa.briefings", "life.pa.action_items",
]

class RecordAgent:
    def __init__(self, config: dict):
        self._config = config
        self._root = Path(config["data_repo_path"])

    def provision(self) -> None:
        """Create the full records/agents/ directory tree. Safe to re-run."""
        for uans in AGENT_DIRECTORIES:
            uans_to_dir(uans, self._root).mkdir(parents=True, exist_ok=True)

    def write(self, uans: str, data: dict, message: str = None) -> None:
        write_json(uans, data, self._config, message)

    def read(self, uans: str) -> dict | None:
        return read_json(uans, self._config)

    def append_action_item(self, uans: str, item: dict) -> None:
        append_action_item(uans, item, self._config)
```

---

## 5. Who Owns What

Each JSON file belongs to exactly one agent — its sole writer. RecordAgent enforces this by design: agents request reads and writes through the RecordAgent API; they never touch the filesystem directly. Cross-agent reads go through RecordAgent too — one agent never imports from another.

| UANS prefix | Owning agent | Record types |
|---|---|---|
| `house.*` | houseAgent sub-agents | systems, profiles, maintenance logs, budgets |
| `medical.*` | medicalAgent sub-agents | health records, vitals, care history |
| `money.*` | moneyAgent sub-agents | account registry, transactions, planning |
| `estate.*` | estateAgent sub-agents | asset registry, legal documents, runway |
| `emotional.*` | emotionalAgent sub-agents | check-ins, relationships, grief, stress |
| `faith.*` | faithAgent sub-agents | practice log, examen, community |
| `life.pa.*` | PersonalAssistant | monthly briefings, action items queue |

---

## 6. Milestone Tests

```bash
# Phase 1 milestone: verify provisioning
python ltCmd.py --setup
ls ~/dev/pyTrackers/lifeTracker-data/records/agents/
# Should show: house/ medical/ money/ estate/ emotional/ faith/ life/

# Verify write + git commit
python -c "
from core.records.record_agent import RecordAgent
import json

config = json.load(open('~/.lifeTracker/config.json'))
ra = RecordAgent(config)
ra.write('house.core.profile.house_profile', {'address': '177 Kingsway Dr', 'year_built': 2006})
"

cd ~/dev/pyTrackers/lifeTracker-data
git log --oneline -3
# Should show: record: update house.core.profile.house_profile
```
