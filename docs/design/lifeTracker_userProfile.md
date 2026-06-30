# lifeTracker — User Profile Service Design

**Version:** 1.1
**Date:** June 2026
**Parent:** [Design Index](./lifeTracker_design.md)

---

## 1. Why User Profile Is a Separate Service

lifeTracker is designed to operate across a complex interrelated network of agents, ie **U users, each with H houses, M medical team members, and F faith advisors**. This demands that what a user *is* (auth: identity + passphrase) be separated from what a user *has* (profile: their houses, practitioners, advisors).

| Service | Knows | Stored |
|---|---|---|
| **Auth** (`core/auth/`) | who you are — `user_id` + passphrase hash | `~/.lifeTracker/users.json.gpg` — never in git |
| **User Profile** (`core/profile/`) | everything about you — houses, medical team, faith advisors, active agents | `<userData>/profile.json` — in Google Drive data folder |

This split lets the same deployment instance serve multiple users without any agent needing to know about individual user data. Every discipline agent receives a `UserContext` at query time; it never reads user data directly.

---

## 2. User Profile Schema

`<userData>/profile.json`

```json
{
  "user_id": "frankr6591",
  "display_name": "Frank Rojas",
  "email": "frankr6591@gmail.com",
  "dob": "1957-09-15",
  "phone": "+15125550100",
  "active_agents": ["house", "medical", "money", "estate", "emotional", "faith"],

  "houses": [
    {
      "house_id": "kingsway_dr",
      "label": "Wimberley Home",
      "address": "177 Kingsway Dr, Wimberley TX 78676",
      "county": "Hays",
      "parcel_id": "R33204",
      "purchase_date": "2022-12-31",
      "purchase_price": 335000,
      "is_primary": true,
      "active": true
    }
  ],

  "medical_team": [
    {
      "practitioner_id": "arc_primary",
      "role": "primary_care",
      "name": "",
      "practice": "Austin Regional Clinic",
      "system": "Epic",
      "fhir_endpoint": "",
      "active": true
    },
    {
      "practitioner_id": "arc_urology",
      "role": "urologist",
      "name": "",
      "practice": "Austin Regional Clinic",
      "system": "Epic",
      "fhir_endpoint": "",
      "active": true
    },
    {
      "practitioner_id": "cpap_resmed",
      "role": "sleep_specialist",
      "name": "",
      "practice": "ResMed myAir",
      "system": "myAir",
      "fhir_endpoint": "",
      "active": true
    }
  ],

  "faith_advisors": [
    {
      "advisor_id": "parish_priest",
      "role": "parish_priest",
      "name": "",
      "parish": "",
      "diocese": "Austin",
      "denomination": "Roman Catholic",
      "active": true
    }
  ],

  "created_at": "2026-06-29T00:00:00Z",
  "updated_at": "2026-06-29T00:00:00Z"
}
```

---

## 3. UserContext — The Runtime Object

After login, the system loads the user's profile and constructs a `UserContext`. This object travels with every request and is passed to all discipline agents.

```python
from dataclasses import dataclass, field

@dataclass
class HouseEntry:
    house_id: str
    label: str
    address: str
    is_primary: bool
    active: bool

@dataclass
class PractitionerEntry:
    practitioner_id: str
    role: str
    name: str
    practice: str
    system: str
    active: bool

@dataclass
class FaithAdvisorEntry:
    advisor_id: str
    role: str
    name: str
    parish: str
    diocese: str
    active: bool

@dataclass
class UserContext:
    user_id: str
    display_name: str
    email: str
    dob: str
    active_agents: list[str]
    houses: list[HouseEntry] = field(default_factory=list)
    medical_team: list[PractitionerEntry] = field(default_factory=list)
    faith_advisors: list[FaithAdvisorEntry] = field(default_factory=list)

    @property
    def primary_house(self) -> HouseEntry | None:
        return next((h for h in self.houses if h.is_primary and h.active), None)

    @property
    def active_houses(self) -> list[HouseEntry]:
        return [h for h in self.houses if h.active]

    @property
    def active_practitioners(self) -> list[PractitionerEntry]:
        return [p for p in self.medical_team if p.active]

    @property
    def active_faith_advisors(self) -> list[FaithAdvisorEntry]:
        return [a for a in self.faith_advisors if a.active]
```

---

## 4. UserProfile Service — `core/profile/user_profile.py`

```python
from core.records.git_store import read_json, write_json
from core.profile.models import UserContext, HouseEntry, PractitionerEntry, FaithAdvisorEntry
from datetime import datetime

class UserProfileService:
    def __init__(self, config: dict):
        self._config = config

    def load(self, user_id: str) -> UserContext | None:
        """Load and hydrate UserContext from profile.json. Returns None if not found."""
        data = read_json(f"users.{user_id}.profile", self._config)
        if not data:
            return None
        return self._hydrate(data)

    def save(self, ctx: UserContext) -> None:
        """Persist UserContext back to profile.json via RecordAgent (commits to data repo)."""
        write_json(
            f"users.{ctx.user_id}.profile",
            self._serialize(ctx),
            self._config,
            message=f"profile: update {ctx.user_id}"
        )

    def add_house(self, user_id: str, house: HouseEntry) -> UserContext:
        ctx = self.load(user_id)
        ctx.houses.append(house)
        ctx.updated_at = datetime.utcnow().isoformat() + "Z"
        self.save(ctx)
        return ctx

    def add_practitioner(self, user_id: str, practitioner: PractitionerEntry) -> UserContext:
        ctx = self.load(user_id)
        ctx.medical_team.append(practitioner)
        self.save(ctx)
        return ctx

    def add_faith_advisor(self, user_id: str, advisor: FaithAdvisorEntry) -> UserContext:
        ctx = self.load(user_id)
        ctx.faith_advisors.append(advisor)
        self.save(ctx)
        return ctx

    def _hydrate(self, data: dict) -> UserContext:
        return UserContext(
            user_id=data["user_id"],
            display_name=data["display_name"],
            email=data["email"],
            dob=data["dob"],
            active_agents=data["active_agents"],
            houses=[HouseEntry(**h) for h in data.get("houses", [])],
            medical_team=[PractitionerEntry(**p) for p in data.get("medical_team", [])],
            faith_advisors=[FaithAdvisorEntry(**a) for a in data.get("faith_advisors", [])],
        )

    def _serialize(self, ctx: UserContext) -> dict:
        return {
            "user_id": ctx.user_id,
            "display_name": ctx.display_name,
            "email": ctx.email,
            "dob": ctx.dob,
            "active_agents": ctx.active_agents,
            "houses": [h.__dict__ for h in ctx.houses],
            "medical_team": [p.__dict__ for p in ctx.medical_team],
            "faith_advisors": [a.__dict__ for a in ctx.faith_advisors],
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
```

---

## 5. Session Integration

After login succeeds in `ui/auth.py`, the User Profile is loaded and injected into the request context alongside the JWT:

```python
# ui/auth.py  — POST /login success path
user_ctx = profile_service.load(owner_id)
token = issue_token(owner_id, user_ctx.active_agents, config)
# Store serialized user_ctx in session (signed by flask_secret)
session["user_context"] = profile_service._serialize(user_ctx)
```

The `@login_required` decorator hydrates `UserContext` from the session and sets `request.user`:

```python
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = token_from_request(request)
        payload = verify_token(token, current_app.config) if token else None
        if not payload:
            return redirect(url_for('auth.login'))
        request.user = profile_service.load(payload["user_id"])
        return f(*args, **kwargs)
    return decorated
```

Every route handler accesses the full `UserContext` via `request.user`. No route reads the profile JSON directly.

---

## 6. Record Path Structure

All agent records live under `<userData>/agents/`. The `userData` path (from `config.json`) is already user-specific — no `users/<user_id>/` prefix needed. House records are further scoped by `house_id`; medical by `practitioner_id`.

```
<userData>/                       ← ~/GDrive/Family/PersonalAssistant/
├── profile.json                  ← UserProfile (this service)
└── agents/
    ├── house/
    │   └── kingsway_dr/          ← house_id from UserContext
    │       ├── core/records/
    │       ├── core/profile/
    │       ├── systems/hvac/
    │       └── ...
    ├── medical/
    │   ├── arc_primary/          ← practitioner_id
    │   │   ├── health/conditions/
    │   │   └── care/appointments/
    │   └── arc_urology/
    ├── money/
    │   ├── accounts/registry/
    │   └── planning/rmd/
    ├── estate/
    │   └── assets/registry/
    ├── emotional/
    │   └── core/checkin/
    ├── faith/
    │   └── examen/reflection/
    └── life/
        └── pa/
            ├── briefings/
            └── action_items/
```

See `lifeTracker_records.md` for `uans_to_path()` implementation.

---

## 7. `wsCmd.py --setup` — Profile Creation Step

After auth setup, the wizard creates the initial user profile:

```
Creating user profile...
  Houses: Add a house? [Y/n]: Y
    House ID [kingsway_dr]:
    Label [Wimberley Home]:
    Address: 177 Kingsway Dr, Wimberley TX 78676
    Is this the primary residence? [Y/n]: Y
    Add another house? [y/N]: N

  Medical team: Add a practitioner? [Y/n]: Y
    Practitioner ID [arc_primary]:
    Role [primary_care]:
    Practice: Austin Regional Clinic
    System [Epic]:
    Add another? [y/N]: N

  Faith advisors: Add an advisor? [Y/n]: Y
    Advisor ID [parish_priest]:
    Role [parish_priest]:
    Parish: ...
    Diocese [Austin]:
    Add another? [y/N]: N

Writing <userData>/profile.json ... done
```

Profile is also editable at runtime via `/profile` web route (Phase 0b).

---

## 8. Files

```
core/
└── profile/
    ├── __init__.py
    ├── models.py           ← UserContext, HouseEntry, PractitionerEntry, FaithAdvisorEntry
    └── user_profile.py     ← UserProfileService: load, save, add_house, add_practitioner, add_faith_advisor
```

Routes (added to `ui/auth.py` blueprint or a new `ui/profile.py`):

| Route | Description |
|---|---|
| `GET /profile` | View current user profile |
| `POST /profile/houses` | Add a house |
| `POST /profile/medical` | Add a practitioner |
| `POST /profile/faith` | Add a faith advisor |

---

## 9. Adding a New Agent — Integration Checklist

New agents fall into two types. Choose the right type first — it determines which steps are required.

### Agent Types

| Type | Description | Example |
|---|---|---|
| **Flat** | No sub-entities; records are not scoped beyond the agent namespace | `emotionalAgent`, `moneyAgent`, `faithAgent` |
| **Scoped** | Has a list of sub-entities (vehicles, properties, accounts…); records are scoped by entity ID | `houseAgent` (house_id), `medicalAgent` (practitioner_id) |

---

### Type A — Flat Agent (5 steps, no profile schema change)

> *Example: adding a `vehicleAgent` that treats all vehicles as one pool with no per-vehicle scoping.*

**Step 1 — Register with PA** (`life/pa.py`)
```python
from vehicleAgent.vehicle_mgr import VehicleMgr
pa.register("vehicle", VehicleMgr(config, record_agent))
```

**Step 2 — Add to `active_agents` in `profile.json`**
```json
"active_agents": ["house", "medical", "money", "estate", "emotional", "faith", "vehicle"]
```

**Step 3 — Add UANS directories** (`core/records/record_agent.py`, `AGENT_DIRECTORIES`)
```python
"vehicle.core.profile", "vehicle.core.records",
"vehicle.maintenance.log", "vehicle.finance.insurance",
```

**Step 4 — Implement `DisciplineAgent`** (`vehicleAgent/vehicle_mgr.py`)
```python
class VehicleMgr(DisciplineAgent):
    def brief(self) -> AgentBriefing: ...
    def query(self, question, context) -> AgentResponse: ...
    def audit(self) -> list[ActionItem]: ...
    def record(self, event) -> None: ...
```

**Step 5 — Add `wsCmd.py --setup` prompt** (optional intro questions)
```
Vehicle agent: Track any vehicles? [Y/n]: Y
  → records stored in <userData>/agents/vehicle/
```

No changes to `UserProfile` schema, `UserContext`, or `UserProfileService`. Done.

---

### Type B — Scoped Agent (9 steps, profile schema extended)

> *Example: `vehicleAgent` where records are scoped per vehicle — `vehicle_id: "tacoma_2019"` — so Frank can track his Tacoma and a future RV separately.*

**Step 1 — Add entity list to `profile.json` schema**
```json
"vehicles": [
  {
    "vehicle_id": "tacoma_2019",
    "label": "Tacoma",
    "make": "Toyota",
    "model": "Tacoma TRD",
    "year": 2019,
    "vin": "...",
    "is_primary": true,
    "active": true
  }
]
```

**Step 2 — Add dataclass** (`core/profile/models.py`)
```python
@dataclass
class VehicleEntry:
    vehicle_id: str
    label: str
    make: str
    model: str
    year: int
    vin: str
    is_primary: bool
    active: bool
```

**Step 3 — Extend `UserContext`** (`core/profile/models.py`)
```python
@dataclass
class UserContext:
    ...
    vehicles: list[VehicleEntry] = field(default_factory=list)   # ← add

    @property
    def primary_vehicle(self) -> VehicleEntry | None:
        return next((v for v in self.vehicles if v.is_primary and v.active), None)

    @property
    def active_vehicles(self) -> list[VehicleEntry]:
        return [v for v in self.vehicles if v.active]
```

**Step 4 — Add `add_vehicle()` to `UserProfileService`** (`core/profile/user_profile.py`)
```python
def add_vehicle(self, user_id: str, vehicle: VehicleEntry) -> UserContext:
    ctx = self.load(user_id)
    ctx.vehicles.append(vehicle)
    self.save(ctx)
    return ctx
```

**Step 5 — Update `_hydrate()` and `_serialize()`** (`core/profile/user_profile.py`)
```python
def _hydrate(self, data):
    return UserContext(
        ...
        vehicles=[VehicleEntry(**v) for v in data.get("vehicles", [])],
    )

def _serialize(self, ctx):
    return {
        ...
        "vehicles": [v.__dict__ for v in ctx.vehicles],
    }
```

**Step 6 — Handle scope_id in `uans_to_path()`** (`core/records/uans.py`)
```python
elif namespace == "vehicle" and scope_id:
    base = base / scope_id
```

**Step 7 — Add UANS directories** (`core/records/record_agent.py`)
```python
"vehicle.core.profile", "vehicle.core.records",
"vehicle.maintenance.log", "vehicle.finance.insurance",
```

**Step 8 — Implement `DisciplineAgent`** (`vehicleAgent/vehicle_mgr.py`)
```python
class VehicleMgr(DisciplineAgent):
    def query(self, question, context):
        vehicle_id = context.get("vehicle_id") or user_ctx.primary_vehicle.vehicle_id
        records = self._record_agent.read("vehicle.core.profile.vehicle_profile",
                                          scope_id=vehicle_id)
        ...
```

**Step 9 — Extend `wsCmd.py --setup`** wizard
```
Vehicles: Add a vehicle? [Y/n]: Y
  Vehicle ID [tacoma_2019]:
  Label [Tacoma]:
  Make: Toyota
  Model: Tacoma TRD
  Year: 2019
  Primary vehicle? [Y/n]: Y
  Add another? [y/N]: N
```

Web route: `POST /profile/vehicles` → `UserProfileService.add_vehicle()`

---

### Integration Decision Tree

```
Adding a new agent?
        │
        ▼
Does it need sub-entities in the profile?
(Multiple vehicles? Multiple clubs? Multiple properties?)
        │
   YES  │  NO
        │──────► Type A (5 steps) — just register + UANS dirs
        │
        ▼
  Type B (9 steps) — extend schema + models + service + uans_to_path
```

### Zero Breaking Changes Guarantee

- `profile.json` is additive: new fields are ignored by agents that don't know about them
- `UserContext._hydrate()` uses `data.get("vehicles", [])` — missing field → empty list
- Existing agents never import from `vehicleAgent` — the PA interface (`DisciplineAgent`) is the only contract
- `AGENT_DIRECTORIES` provisioning is idempotent — safe to re-run `wsCmd.py --setup` after adding a new agent
