# lifeTracker — iOS API Layer Design

**Version:** 1.0
**Date:** June 2026
**Parent:** [Design Index](./lifeTracker_design.md)

---

## 1. Overview

The iOS API layer is **Phase 3** — three JSON endpoints added to the Flask app in `ui/api.py`. These endpoints are the only contract between the lifeTracker backend and the `mobileAudioIO` iPhone app. No other iOS-facing infrastructure is required.

The iPhone app handles STT and TTS on-device. Only text crosses the network.

---

## 2. Endpoints

### `POST /api/auth/token`

Issue a JWT for the iOS app to store in Keychain.

**Auth:** None (this IS the auth endpoint)

**Request:**
```json
{
  "owner_id": "frankr6591",
  "passphrase": "..."
}
```

**Response 200:**
```json
{
  "token": "eyJ...",
  "expires_at": "2026-07-28T00:00:00Z"
}
```

**Response 401:**
```json
{ "error": "invalid credentials" }
```

**Implementation:**

```python
@api_bp.route("/auth/token", methods=["POST"])
def get_token():
    data = request.get_json()
    owner_id = data.get("owner_id")
    passphrase = data.get("passphrase")
    config = current_app.config["LT_CONFIG"]

    if not verify_owner(owner_id, passphrase, config):
        return jsonify({"error": "invalid credentials"}), 401

    token = issue_token(owner_id, active_agents=["house", "medical", "money"], config=config)
    expiry = (datetime.utcnow() + timedelta(days=config["jwt_expiry_days"])).isoformat() + "Z"
    return jsonify({"token": token, "expires_at": expiry})
```

---

### `POST /api/query`

Send a text query; receive a PA response and any new action items.

**Auth:** `Authorization: Bearer <token>` — protected by `@api_auth_required`

**Request:**
```json
{
  "text": "How are my finances this month?",
  "channel": "ios_voice",
  "owner_id": "frankr6591"
}
```

`channel` must be `"ios_voice"` to get the ≤3-sentence voice-mode response. Any other value returns full web-mode text.

**Response 200:**
```json
{
  "response_text": "Your liquid savings are $42K, up from last month. The HVAC filter is overdue — the only active action item. You are in good shape overall.",
  "action_items": [
    {
      "id": "abc123",
      "agent": "house",
      "summary": "HVAC filter replacement overdue",
      "priority": "medium",
      "created_at": "2026-06-15T10:00:00Z"
    }
  ],
  "agent_sources": ["money", "house"],
  "session_id": "xyz789"
}
```

**Response 401:** `{ "error": "unauthorized" }`
**Response 503:** `{ "error": "PA unavailable", "detail": "..." }`

**Implementation:**

```python
@api_bp.route("/query", methods=["POST"])
@api_auth_required
def query():
    data = request.get_json()
    text = data.get("text", "").strip()
    channel = data.get("channel", "ios_voice")

    if not text:
        return jsonify({"error": "text is required"}), 400

    pa = current_app.config["PA_INSTANCE"]
    result = pa.query(text, channel=channel)
    return jsonify(result)
```

---

### `GET /api/notifications`

Return open action items for the iOS Notifications tab. Called on app launch and when app enters foreground.

**Auth:** `Authorization: Bearer <token>` — protected by `@api_auth_required`

**Response 200:**
```json
{
  "action_items": [
    {
      "id": "abc123",
      "agent": "house",
      "summary": "HVAC filter replacement overdue",
      "priority": "medium",
      "created_at": "2026-06-15T10:00:00Z"
    }
  ],
  "unread_count": 1
}
```

**Implementation:**

```python
@api_bp.route("/notifications", methods=["GET"])
@api_auth_required
def notifications():
    config = current_app.config["LT_CONFIG"]
    ra = RecordAgent(config)
    data = ra.read("life.pa.action_items.open") or {"action_items": []}
    open_items = [i for i in data["action_items"] if not i.get("resolved")]
    return jsonify({"action_items": open_items, "unread_count": len(open_items)})
```

---

## 3. `ui/api.py` Full Structure

```python
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from core.auth.gpg_users import verify_owner
from core.auth.session import issue_token, verify_token
from core.auth.decorators import api_auth_required
from core.records.record_agent import RecordAgent

api_bp = Blueprint("api", __name__)

# --- Auth ---
@api_bp.route("/auth/token", methods=["POST"])
def get_token(): ...

# --- PA query ---
@api_bp.route("/query", methods=["POST"])
@api_auth_required
def query(): ...

# --- Notifications ---
@api_bp.route("/notifications", methods=["GET"])
@api_auth_required
def notifications(): ...
```

---

## 4. Bearer Auth Middleware

`core/auth/session.py` — `token_from_request()` extracts token from either source:

```python
def token_from_request(request) -> str | None:
    # Web channel: HttpOnly cookie
    cookie = request.cookies.get("lt_session")
    if cookie:
        return cookie
    # iOS channel: Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None
```

`@api_auth_required` (in `core/auth/decorators.py`) calls this and returns 401 if the token is missing or invalid.

---

## 5. iOS App Side

These endpoints are consumed by `mobileAudioIO`. See:
- `pyTrackers/mobileAudioIO/docs/designAudioIO.md §5` — APIClient and AuthManager implementation
- `pyTrackers/mobileAudioIO/docs/mobileAudioIOVision.md §6` — integration table

**Development note:** When testing on a real iPhone against a local Mac server, the iPhone must use the Mac's LAN IP address (not `localhost`). The `mobileAudioIO` Settings screen has a server URL field for this.

```
Local Mac:   http://192.168.1.x:5000
PA deploy:   https://frankr6591.pythonanywhere.com
```

---

## 6. Milestone Test

Phase 3 is complete when:

```bash
# Start local server
python ltCmd.py --start

# 1. Get token
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"owner_id":"frankr6591","passphrase":"<your passphrase>"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# 2. Query
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"text":"How are my finances?","channel":"ios_voice","owner_id":"frankr6591"}'
# → {"response_text": "...", "action_items": [], "agent_sources": [...]}

# 3. Notifications
curl http://localhost:5000/api/notifications \
  -H "Authorization: Bearer $TOKEN"
# → {"action_items": [], "unread_count": 0}
```

After this, `mobileAudioIO` on a real device can complete an end-to-end voice query.
