# lifeTracker — Web UI Communication Layer Design

**Version:** 1.0
**Date:** June 2026
**Parent:** [Design Index](./lifeTracker_design.md)

---

## 1. Overview

The Web UI layer is **Phase 2** — built after auth and RecordAgent are stable. It provides the browser-based interface to the PersonalAssistant: a text chat interface, a monthly check-in dashboard, and the Twilio voice webhook.

Three communication channels share the same Flask codebase. Channel detection sets the response format:

| Channel | Entry Point | Response Format |
|---|---|---|
| Browser `/chat` | POST form text | Full HTML with structured response |
| Twilio voice | POST `/voice` webhook | TwiML `<Say>` ≤ 3 sentences |
| iOS API | POST `/api/query` | JSON `{response_text, action_items}` |

---

## 2. Flask App Architecture

### App Factory — `wsgi.py`

```python
from flask import Flask
from ui.auth import auth_bp
from ui.chat import chat_bp
from ui.checkin import checkin_bp
from ui.api import api_bp
from houseAgent.ui.house_views import house_bp
from setup_paths import load_config

def create_app():
    app = Flask(__name__)
    config = load_config()
    app.secret_key = config["flask_secret"]
    app.config["LT_CONFIG"] = config

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(checkin_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(house_bp, url_prefix="/house")
    # Each discipline agent registers its own blueprint here as it is built

    return app

application = create_app()    # PythonAnywhere WSGI expects `application`
```

### Blueprint Summary

| Blueprint | Module | URL Prefix | Routes |
|---|---|---|---|
| `auth_bp` | `ui/auth.py` | `/` | `/login`, `/logout`, `/register` |
| `chat_bp` | `ui/chat.py` | `/` | `/chat` (GET + POST) |
| `checkin_bp` | `ui/checkin.py` | `/` | `/checkin` (GET) |
| `api_bp` | `ui/api.py` | `/api` | `/api/query`, `/api/auth/token`, `/api/notifications` |
| `house_bp` | `houseAgent/ui/house_views.py` | `/house` | `/house/records`, `/house/profile` |

---

## 3. PersonalAssistant Orchestrator — `life/pa.py`

The PA is the hub between the web layer and the discipline agents. The web layer never calls agents directly.

```python
from life.router import IntentParser
from life.synthesizer import ResponseSynthesizer
from life.models import AgentResponse, AgentBriefing
from core.records.record_agent import RecordAgent

class PersonalAssistant:
    def __init__(self, config: dict):
        self._config = config
        self._intent_parser = IntentParser(config)
        self._synthesizer = ResponseSynthesizer(config)
        self._record_agent = RecordAgent(config)
        self._agents: dict[str, object] = {}   # namespace → DisciplineAgent instance

    def register(self, namespace: str, agent: object) -> None:
        """Called at app startup. Each discipline agent registers itself."""
        self._agents[namespace] = agent

    def query(self, text: str, channel: str) -> dict:
        """
        Parse intent → route to agents → synthesize → return response dict.
        channel: 'web', 'voice', or 'ios_voice'
        """
        intent = self._intent_parser.parse(text)
        responses = []
        for ns in intent["agents"]:
            if ns in self._agents:
                r = self._agents[ns].query(intent["question"], context={})
                responses.append(r)
        voice_mode = channel in ("voice", "ios_voice")
        response_text = self._synthesizer.synthesize(responses, voice_mode=voice_mode)
        return {
            "response_text": response_text,
            "action_items": [item for r in responses for item in r.action_items],
            "agent_sources": intent["agents"],
        }

    def monthly_briefing(self) -> list[AgentBriefing]:
        """Collect brief() from every registered agent. Called by /checkin."""
        return [agent.brief() for agent in self._agents.values()]
```

### IntentParser — `life/router.py`

Calls Claude Haiku with a structured prompt. Returns a JSON object naming which agents to route to and what the distilled question is.

```python
System prompt (abbreviated):
  You are the intent parser for a personal life management system.
  Given the owner's input, identify:
    - agents: list of namespaces from ["house","medical","money","estate","emotional","faith"]
    - question: the distilled question for the agents
    - mode: "query" | "record" | "plan"
  Return JSON only. No explanation.

Input: "How are my finances and can I afford a new roof?"
Output: {"agents": ["money", "house"], "question": "current financial position and roof replacement affordability", "mode": "query"}
```

### ResponseSynthesizer — `life/synthesizer.py`

Calls Claude Sonnet with collected agent responses.

```python
def synthesize(self, responses: list[AgentResponse], voice_mode: bool) -> str:
    """
    voice_mode=True: ≤3 sentences spoken prose, no markdown.
    voice_mode=False: full structured text, markdown OK.
    """
```

System prompt includes: owner context (age 68, life stage), voice constraint (if active), and all collected agent responses as context.

---

## 4. Routes

### `/chat` — `ui/chat.py`

The primary browser text interface. Protected by `@login_required`.

```
GET  /chat       → render chat.html with conversation history from session
POST /chat       → {text: "..."} → PA.query(text, channel="web") → render response
```

**Conversation history** is stored in the Flask session (not in RecordAgent). Sessions are signed with `flask_secret`; no history leaves the server.

### `/checkin` — `ui/checkin.py`

Monthly PA dashboard. Protected by `@login_required`.

```
GET  /checkin    → PA.monthly_briefing() → render checkin.html with all agent briefings
```

Shows:
- Status card per registered discipline agent
- Open action items from all agents
- Cross-domain alerts surfaced by PA
- Last check-in date

### `/voice` — Twilio webhook (in `ui/chat.py` or separate `ui/voice.py`)

Handles Twilio POST requests. No auth required (Twilio calls this server-side). Validated via Twilio signature header.

```
POST /voice     → gather speech (TwiML <Gather>) → STT transcript in next POST
POST /voice     → {SpeechResult: "..."} → PA.query(text, channel="voice") → TwiML <Say> response
```

Voice response constraint: ≤ 3 sentences, no markdown. Synthesizer enforces this via `voice_mode=True`.

---

## 5. Models — `life/models.py`

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ActionItem:
    id: str
    agent: str
    summary: str
    priority: str          # "high" | "medium" | "low"
    created_at: datetime
    resolved: bool = False

@dataclass
class AgentResponse:
    agent: str
    response_text: str
    action_items: list[ActionItem] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)

@dataclass
class AgentBriefing:
    agent: str
    summary: str           # 2-3 sentences
    status: str            # "ok" | "attention" | "urgent"
    action_item_count: int
    last_updated: datetime
```

---

## 6. Templates

All templates extend `base.html`. Minimal CSS — functional, not beautiful for v1.

```
ui/templates/
├── base.html          ← nav bar (Chat | Check-in | [agent tabs]), user info, flash messages
├── login.html         ← passphrase form
├── chat.html          ← text input, conversation history, agent source tags
└── checkin.html       ← agent briefing cards, action items table, last check-in timestamp
```

`base.html` nav bar adds an agent tab for each registered blueprint. As discipline agents are built and registered, their tab appears automatically.

---

## 7. Channel Detection

The `ResponseSynthesizer` receives the `channel` string from the calling route:

| Channel value | Source | Synthesizer behavior |
|---|---|---|
| `"web"` | `/chat` route | Full text, markdown permitted, no length limit |
| `"voice"` | Twilio `/voice` webhook | ≤ 3 sentences, prose only |
| `"ios_voice"` | `/api/query` iOS call | ≤ 3 sentences, prose only (same as voice) |

The web route always passes `"web"`. The Twilio webhook always passes `"voice"`. The iOS API route reads the `channel` field from the request JSON body.

---

## 8. Deployment Notes

### PythonAnywhere

`wsgi.py` is the entry point. PythonAnywhere looks for `application = create_app()`.

After any code change:
1. Push to GitHub
2. PA console → `git pull origin main`
3. Reload the web app (green "Reload" button or `touch /var/www/<app>_wsgi.py`)

Twilio webhook URL: `https://<username>.pythonanywhere.com/voice`
PA web URL: `https://<username>.pythonanywhere.com`

### Local Mac

```bash
python ltCmd.py --start
# Runs: flask --app wsgi run --port 5000 --debug
# Access at: http://localhost:5000
```

Local development does not receive Twilio voice calls (Twilio can't reach `localhost`). Use `ngrok` to expose local port if voice testing is needed, or defer voice testing to PA deployment.

---

## 9. Milestone Test

Phase 2 is complete when:

```
1. python ltCmd.py --start
2. Browser → http://localhost:5000 → redirects to /login ✓
3. Enter owner passphrase → logged in ✓
4. /chat → type "What is my house status?" →
     PA stub response: "I'm working on connecting to houseAgent." ✓
5. /checkin → page loads with placeholder briefing cards ✓
6. /logout → back to login ✓
```
