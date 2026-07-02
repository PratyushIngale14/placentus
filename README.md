# Placentus

### Engagement intelligence for staffing & consulting companies — a Sulcus architecture product

Placentus gives a staffing company (ProMazo, Kipi, or similar) visibility into how their embedded
consultants ("Fellows") are actually doing at client sites — sourced entirely from what the Fellow
and their internal PM choose to share, never from the client's own tools. No client Slack access,
no meeting recording without consent, no surveillance. Just a fast weekly check-in, a categorization
layer that routes sensitive content without ever deleting it, and pattern detection that catches
what a busy PM tracking 30 people across 15 accounts would otherwise miss.

Same architecture family as **Sulcus**: typed Pydantic events in, a computed guardrail layer,
generative UI out. Applied here to account health instead of a product launch.

---

## The four pillars, same pattern as Sulcus

| Pillar | Module | What it does |
|---|---|---|
| **The Ears** | `slack_bot/bot.py` | 4-question weekly Slack DM check-in + a PM note slash-command — both self-reported, both inside the staffing company's own workspace |
| **The Shields** | `placentus/categorization.py` | Rule-based regex + optional Claude semantic pass. Routes every event to STANDARD / RESTRICTED / ESCALATE. **Nothing is ever deleted** — only routed and access-tiered |
| **The Circadian pattern layer** | `placentus/data_store.py` | Detects recurring blockers across weeks, sustainability trends, and open escalations per Fellow — the thing a manual spreadsheet never catches |
| **The Mouth** | `placentus/generative_ui.py` + `app.py` | Clickable client/employee cards, a real calendar view, and a Claude-powered PM agent that only answers what it can ground in real events |

---

## Run it

```bash
pip install -r requirements.txt
python -m placentus.generator      # regenerate data/seed.json if needed (already included)
streamlit run app.py
```

Opens at `http://localhost:8501`. Drop an Anthropic API key in the header field to enable the PM
agent chat — without it, everything else (dashboard, categorization, calendar) still works fully,
since the demo data is pre-categorized on load.

---

## What's in the demo data

5 fictional clients, 12 Fellows, 37 real events (29 check-ins + 8 PM notes) — deliberately built
with a spread of cases so the categorization layer has something real to prove itself against:

- **A recurring blocker** (Marcus, 3 weeks waiting on client Snowflake access) — tests the
  pattern-detection layer
- **A burnout trajectory** (Tom, sustainability trending from "stretched" to "burning out" across
  3 weeks) — tests the sustainability trend chart
- **An escalation case** (Lily, a client manager conduct issue) — tests that escalation content is
  surfaced faster, never hidden
- **PII slips** (a phone number dropped into a status update) — tests redaction without deletion
- **Client-confidential slips** (unreleased revenue numbers mentioned in a check-in) — tests the
  RESTRICTED tier and archival-not-deletion
- **Scope drift** (being pulled into out-of-contract work) — tests the risk-flag taxonomy

All of it visible on the **Trust Ledger** tab, with the specific rule/category that caused each
routing decision shown next to the event.

---

## The categorization layer — the design rule that matters most

Every piece of content gets a visibility tier, never a deletion:

- **STANDARD** — normal work content, full staffing-company visibility
- **RESTRICTED** — PII or client-confidential language detected. Redacted in the standard view,
  full text preserved and access-logged for a compliance-tier viewer
- **ESCALATE** — language suggesting distress, mistreatment, or an explicit ask for help. Surfaced
  **faster**, never suppressed — this tier exists to protect the Fellow, not hide them

The rule-based pass (regex + keyword heuristics) runs first and always works offline. An optional
second pass through Claude catches tone and implied-distress signals regex can't — it only runs if
an API key is present, and fails soft to rule-based-only if it errors or isn't configured.

---

## The evaluation layer — stopping hallucination in the PM agent

`placentus/evaluation.py` runs the same token-grounding math as Sulcus's Gate 2: every sentence the
PM agent produces gets checked against the actual event corpus it was given. If a claim isn't
grounded in real check-in or note content, the faithfulness score drops and, below a threshold, the
agent declines to answer rather than guessing. This score is shown under every agent reply in the
UI — it's computed per-answer, not a fixed number.

---

## Setting up the real Slack bot

See the docstring at the top of `slack_bot/bot.py` for full setup steps. Short version:

1. Create a Slack app in **your own staffing company's workspace** (never the client's)
2. Enable Socket Mode, grab the bot token and app token
3. `pip install -r slack_bot/requirements.txt`
4. `SLACK_BOT_TOKEN=xoxb-... SLACK_APP_TOKEN=xapp-... python slack_bot/bot.py`

The bot's questions match exactly what's documented in `questions.md`, and every submission runs
through the same `categorization.py` module the dashboard uses — one pipeline, two entry points.

---

## Honest scope notes

- The demo data is static and pre-generated for repeatability. The Slack bot writes live check-ins
  to `data/live_checkins.json` — wiring that into the live dashboard view is the natural next step,
  not yet done here.
- Employee-to-Slack-user mapping is a placeholder (`slack-<user_id>`) — a real deployment needs an
  onboarding step that links Slack identity to a Placentus employee record.
- This has not been reviewed by an employment lawyer. See `questions.md` and the product discussion
  that shaped this build for the consent/retention principles it was designed around — verify them
  with counsel before using this on real employees.
