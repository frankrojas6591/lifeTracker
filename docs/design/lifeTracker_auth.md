# lifeTracker — Auth Service Design

**Version:** 1.0
**Date:** June 2026
**Parent:** [Design Index](./lifeTracker_design.md)

---

## 1. Overview

Auth is the first thing built in Phase 0. Nothing else runs without it. The lifeTracker auth service handles:

- **Owner identity** — who is allowed to use this system
- **Login** — passphrase verification against GPG-encrypted owner DB
- **Session** — JWT issued on login; verified on every request
- **Decorators** — `@login_required` gates all non-public routes
- **Setup wizard** — `ltCmd.py --setup` creates the owner DB on first run

There is one owner: Frank Rojas (`frankr6591`). The system is designed for one person. Multi-owner support is preserved in the data model but not a goal.

---

## 2. Owner DB — `owners.json.gpg`

The owner database is a GPG-encrypted JSON file stored at `~/.lifeTracker/owners.json.gpg`. It never touches git.

### Schema

```json
{
  "owners": [
    {
      "owner_id": "frankr6591",
      "display_name": "Frank Rojas",
      "email": "frankr6591@gmail.com",
      "passphrase_hash": "<bcrypt hash>",
      "active_agents": ["house", "medical", "money", "estate", "emotional", "faith"],
      "created_at": "2026-06-28T00:00:00Z"
    }
  ]
}
```

- `passphrase_hash` — bcrypt-hashed passphrase. Never stored in plaintext. Never sent over the network.
- `active_agents` — list of discipline agent namespaces active for this owner. Controls which agents are queried.
- GPG symmetric encryption wraps the entire JSON file. The GPG key ID is in `config.json`.

### File: `core/auth/gpg_users.py`

```python
def load_owners(config: dict) -> list[dict]:
    """Decrypt owners.json.gpg and return parsed list."""

def verify_owner(owner_id: str, passphrase: str, config: dict) -> bool:
    """Load owners; find owner_id; bcrypt verify passphrase."""

def add_owner(owner: dict, config: dict) -> None:
    """Add new owner to DB; re-encrypt and write."""

def list_owners(config: dict) -> list[str]:
    """Return list of owner_ids."""
```

---

## 3. JWT Session

### Token Design

On successful login, the server issues a JWT. The JWT is stored:
- **Browser sessions:** in a `Secure; HttpOnly; SameSite=Strict` cookie named `lt_session`
- **iOS app:** in the Keychain (via `mobileAudioIO`'s `AuthManager`)

JWT payload:
```json
{
  "owner_id": "frankr6591",
  "active_agents": ["house", "medical", "money"],
  "iat": 1719532800,
  "exp": 1722124800
}
```

- Expiry: 30 days for browser sessions, 30 days for iOS (silent refresh before expiry)
- Signed with `flask_secret` from `config.json` using `HS256`

### File: `core/auth/session.py`

```python
def issue_token(owner_id: str, active_agents: list[str], config: dict) -> str:
    """Create signed JWT; return token string."""

def verify_token(token: str, config: dict) -> dict | None:
    """Verify signature and expiry; return payload dict or None."""

def token_from_request(request) -> str | None:
    """Extract token from cookie (web) or Authorization header (iOS API)."""
```

---

## 4. Route Protection

### File: `core/auth/decorators.py`

```python
from functools import wraps
from flask import redirect, url_for, request, jsonify
from core.auth.session import token_from_request, verify_token

def login_required(f):
    """For web routes: redirect to /login if no valid session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = token_from_request(request)
        payload = verify_token(token, current_app.config) if token else None
        if not payload:
            return redirect(url_for('auth.login'))
        request.owner = payload
        return f(*args, **kwargs)
    return decorated

def api_auth_required(f):
    """For /api/* routes: return 401 JSON if no valid Bearer token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = token_from_request(request)
        payload = verify_token(token, current_app.config) if token else None
        if not payload:
            return jsonify({"error": "unauthorized"}), 401
        request.owner = payload
        return f(*args, **kwargs)
    return decorated
```

All web routes use `@login_required`. All `/api/*` routes use `@api_auth_required`.

---

## 5. Login Routes

### File: `ui/auth.py`

| Route | Method | Description |
|---|---|---|
| `/login` | GET | Render login form |
| `/login` | POST | Verify passphrase → issue JWT cookie → redirect to `/chat` |
| `/logout` | GET | Clear session cookie → redirect to `/login` |
| `/register` | GET/POST | Add new owner (admin only; guarded by existing session) |

### Login Flow

```
Browser → GET /login
         ← login.html (passphrase field)

Browser → POST /login {owner_id, passphrase}
         → verify_owner() against owners.json.gpg
         → issue_token() → set lt_session cookie
         ← redirect /chat

All subsequent requests:
         → @login_required reads cookie
         → verify_token() → sets request.owner
         → handler runs
```

### Twilio Caller-ID Login (voice channel)

When a call arrives on the Twilio voice webhook, the caller's phone number is used as a soft authentication signal. The `config.json` stores `owner_phone_numbers` — a list of known owner numbers. If the incoming call matches, the session is auto-established for the call duration. This is supplementary, not a replacement for full auth on the web channel.

```json
"owner_phone_numbers": ["+15125550100"]
```

---

## 6. `ltCmd.py --setup` Wizard

The setup wizard runs once per environment (PythonAnywhere and local Mac each run it separately). It is the only way to create the `config.json` and `owners.json.gpg`.

```
$ python ltCmd.py --setup

lifeTracker Setup Wizard
========================
Enter Flask secret key: [generated randomly if blank]
Enter Anthropic API key: sk-ant-...
Enter Twilio Account SID: AC...
Enter Twilio Auth Token: ...
Enter Twilio phone number: +1...
Enter path for lifeTracker-data checkout: ~/dev/pyTrackers/lifeTracker-data
Enter GPG key ID (or press Enter to use symmetric encryption): 

Creating owner...
  Owner ID [frankr6591]:
  Display name [Frank Rojas]:
  Email [frankr6591@gmail.com]:
  Passphrase: [hidden input]
  Confirm passphrase: [hidden input]

Writing ~/.lifeTracker/config.json ... done
Encrypting ~/.lifeTracker/owners.json.gpg ... done
Provisioning records directory tree ... done

Setup complete. Run: python ltCmd.py --start
```

### `ltCmd.py` commands

| Command | Description |
|---|---|
| `--setup` | First-run wizard: config, owner DB, data repo provisioning |
| `--start` | Start Flask dev server at `localhost:5000` |
| `--check` | Verify config, GPG DB, data repo, and all agent registrations |
| `--add-owner` | Add a new owner to the GPG DB |
| `--backup` | Push data repo to remote and log backup timestamp |

---

## 7. Config Schema

`~/.lifeTracker/config.json` — **never committed to git**.

`config.json.example` in the repo is a committed schema template with placeholder values.

```json
{
  "owner_id": "frankr6591",
  "flask_secret": "...",
  "flask_debug": false,
  "anthropic_api_key": "sk-ant-...",
  "twilio_account_sid": "AC...",
  "twilio_auth_token": "...",
  "twilio_phone_number": "+1...",
  "owner_phone_numbers": ["+1..."],
  "data_repo_path": "~/dev/pyTrackers/lifeTracker-data",
  "gpg_owner_db": "~/.lifeTracker/owners.json.gpg",
  "gpg_key_id": "",
  "jwt_expiry_days": 30
}
```

`setup_paths.py` reads this file at import time and exposes all path constants to every module. No other module reads `config.json` directly.
