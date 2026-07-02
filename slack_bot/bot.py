"""
Placentus Slack bot.

Lives in the STAFFING COMPANY'S OWN Slack workspace — never the client's.
Sends the 4-question check-in as a threaded DM, and lets PMs drop notes
into a channel or DM. Every submission is run through the same
categorization layer used by the dashboard (placentus.categorization)
before being written to the store.

Setup:
    1. Create a Slack app at https://api.slack.com/apps
    2. Enable Socket Mode, generate an app-level token (starts xapp-)
    3. Add bot scopes: chat:write, im:history, im:write, users:read
    4. Install to your workspace, grab the bot token (starts xoxb-)
    5. Set env vars: SLACK_BOT_TOKEN, SLACK_APP_TOKEN
    6. pip install -r slack_bot/requirements.txt
    7. python slack_bot/bot.py

This demo version writes accepted check-ins to data/live_checkins.json
so they can be picked up by a future dashboard refresh. It does not
require the full Streamlit app to be running.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler
except ImportError:
    print("Missing dependency. Run: pip install -r slack_bot/requirements.txt")
    raise

from placentus.categorization import categorize
from placentus.schemas import SourceType, SustainabilityLevel

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

LIVE_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "live_checkins.json")

QUESTIONS = [
    ("q1_work", "*1/4 — Work.* What did you work on this week, and what's blocking you, if anything?"),
    ("q2_relationship", "*2/4 — Relationship.* How's it going with the client team this week — anything unclear, unfair, or worth flagging?"),
    ("q3_sustainability", "*3/4 — Feeling.* How does your workload feel right now?\nReply with one of: `Sustainable` · `A bit stretched` · `Stressful` · `Burning out`"),
    ("q4_escalation", "*4/4 — Escalation.* Anything you'd like your ProMazo manager to know or step in on? Reply `none` if nothing right now."),
]

# in-memory per-user progress through the 4-question flow
_sessions: dict[str, dict] = {}

app = App(token=SLACK_BOT_TOKEN)


def _employee_id_for_user(user_id: str) -> str:
    """In a real deployment this maps Slack user ID -> Placentus employee_id
    via a lookup table populated at onboarding. Demo: use the Slack ID directly."""
    return f"slack-{user_id}"


def _save_checkin(employee_id: str, answers: dict, api_key: str | None):
    combined = (
        f"Work update: {answers['q1_work']} "
        f"Client relationship: {answers['q2_relationship']} "
        f"Sustainability: {answers['q3_sustainability']}. "
        f"{('Escalation request: ' + answers['q4_escalation']) if answers['q4_escalation'].lower() != 'none' else ''}"
    ).strip()

    event = categorize(
        raw_text=combined,
        employee_id=employee_id,
        source=SourceType.EMPLOYEE_CHECKIN,
        timestamp=datetime.now(),
        api_key=api_key,
    )

    record = {
        "id": str(uuid.uuid4()),
        "employee_id": employee_id,
        "timestamp": datetime.now().isoformat(),
        "answers": answers,
        "tier": event.tier.value,
        "risk_level": event.risk_level.value,
    }

    existing = []
    if os.path.exists(LIVE_DATA_PATH):
        with open(LIVE_DATA_PATH) as f:
            existing = json.load(f)
    existing.append(record)
    os.makedirs(os.path.dirname(LIVE_DATA_PATH), exist_ok=True)
    with open(LIVE_DATA_PATH, "w") as f:
        json.dump(existing, f, indent=2)

    return event


@app.event("app_home_opened")
def start_checkin_prompt(event, client):
    """Fires when a user opens the bot's Home tab — used here as the trigger
    to kick off a check-in for the demo. In production, trigger this on a
    schedule (e.g. every Friday at 4pm) via a cron job calling client.chat_postMessage."""
    user_id = event["user"]
    _sessions[user_id] = {"step": 0, "answers": {}}
    client.chat_postMessage(
        channel=user_id,
        text="Hey! Quick weekly check-in — 4 short questions, about a minute.\n\n" + QUESTIONS[0][1],
    )


@app.event("message")
def handle_dm_reply(event, client):
    user_id = event.get("user")
    text = event.get("text", "")
    if not user_id or event.get("bot_id"):
        return

    session = _sessions.get(user_id)
    if not session:
        return  # not mid check-in; ignore

    step = session["step"]
    key, _ = QUESTIONS[step]

    if key == "q3_sustainability":
        valid = {s.value.lower(): s.value for s in SustainabilityLevel}
        if text.strip().lower() not in valid:
            client.chat_postMessage(channel=user_id, text="Please reply with one of: Sustainable / A bit stretched / Stressful / Burning out")
            return
        session["answers"][key] = valid[text.strip().lower()]
    else:
        session["answers"][key] = text.strip()

    step += 1
    if step < len(QUESTIONS):
        session["step"] = step
        client.chat_postMessage(channel=user_id, text=QUESTIONS[step][1])
    else:
        employee_id = _employee_id_for_user(user_id)
        result_event = _save_checkin(employee_id, session["answers"], ANTHROPIC_API_KEY or None)
        del _sessions[user_id]

        if result_event.tier.value == "escalate":
            ack = "Thanks — logged. I noticed something in there that's being flagged for your ProMazo manager to reach out about directly. You're not alone in this."
        else:
            ack = "Thanks, logged! See you next week."
        client.chat_postMessage(channel=user_id, text=ack)


@app.command("/placentus-note")
def pm_note_command(ack, respond, command):
    """PM slash command to drop a freeform note: /placentus-note @employee <note text>"""
    ack()
    text = command.get("text", "")
    user_id = command.get("user_id")
    if not text.strip():
        respond("Usage: /placentus-note <employee name/id> <note text>")
        return

    parts = text.split(" ", 1)
    employee_ref = parts[0]
    note_text = parts[1] if len(parts) > 1 else ""

    event = categorize(
        raw_text=f"PM note (Slack user {user_id}): {note_text}",
        employee_id=employee_ref,
        source=SourceType.PM_NOTE,
        timestamp=datetime.now(),
        api_key=ANTHROPIC_API_KEY or None,
    )
    respond(f"Logged. Routed to: {event.tier.value.upper()} tier.")


if __name__ == "__main__":
    if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
        print("Set SLACK_BOT_TOKEN and SLACK_APP_TOKEN environment variables first. See module docstring for setup steps.")
        sys.exit(1)
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    print("Placentus Slack bot running (Socket Mode)...")
    handler.start()
