# Placentus — Question Bank

Two audiences, two flows. Below: the full brainstorm list first (everything a staffing company
could plausibly want to ask), then the **final concise set** actually used in the product —
because a 15-question form gets ignored and a 4-question DM gets answered.

---

## PART A — Employee (Fellow) check-in

### Full candidate list (the "could ask" list)

**Work / delivery**
1. What did you work on since your last check-in?
2. What are you working on this week?
3. What's blocking you right now, if anything?
4. Is anything you're working on outside the original scope of your role?
5. Do you have everything you need (access, information, tools) to do your job?
6. Are you on track with your current sprint/deliverables?
7. Has your workload changed recently — more, less, about the same?
8. Are you clear on what's expected of you this week?

**Relationship with the client**
9. How would you describe your working relationship with your client manager this week?
10. Do you feel included in client meetings and decisions relevant to your work?
11. Has anything happened this week that felt unclear, unfair, or uncomfortable?
12. Do you feel like your work is valued by the client team?
13. Has the client mentioned anything about extending, changing, or ending this engagement?

**Wellbeing**
14. How sustainable does your current workload feel? (sustainable / stressful / burning out)
15. How are you feeling about this engagement overall this week?
16. Is there anything making it hard to focus or do your best work right now?
17. Do you feel supported by your ProMazo/staffing team?

**Growth**
18. What's one thing you learned or improved on this week?
19. Is this engagement helping you grow the way you hoped?

**Escalation / safety valve**
20. Is there anything you'd like your ProMazo manager to step in on?
21. Is there anything you don't feel comfortable raising with the client directly?

That's 21 questions. Nobody answers 21 questions every week. Cut to what actually predicts risk.

### Final concise set — what the bot actually asks (4 questions, ~60 seconds)

> Sent as a single threaded Slack DM, one question at a time, answered in a sentence or two
> (text or voice memo). Takes under a minute.

**Q1 — Work.** *"What did you work on this week, and what's blocking you, if anything?"*
*(covers #1–3, #6 — the baseline status)*

**Q2 — Relationship.** *"How's it going with the client team this week — anything unclear, unfair, or worth flagging?"*
*(covers #9, #11, #13 — the account-health signal)*

**Q3 — Feeling.** *"On a scale from sustainable to burning out, how does your workload feel right now?"*
*(covers #14, #15 — the wellbeing pulse, kept forced-choice so it's fast and comparable week over week)*
Options: `Sustainable` · `A bit stretched` · `Stressful` · `Burning out`

**Q4 — Escalation.** *"Anything you'd like your ProMazo manager to know or step in on — no detail needed if you'd rather flag it privately?"*
*(covers #20, #21 — the safety valve; answering "yes, please call me" is a valid complete answer)*

Four questions. Every one maps back to a specific risk signal the dashboard tracks. Nothing asked "just because it'd be nice to know."

---

## PART B — PM / Account Manager notes

### Full candidate list

1. What did you cover with [Fellow] in today's/this week's standup?
2. Are there any deliverables at risk this sprint?
3. Has the client raised any concerns about [Fellow]'s work?
4. Has the client raised any concerns about the engagement in general?
5. Is the scope of work still matching the original contract?
6. Any signs the client relationship is strong, neutral, or strained?
7. Any renewal, extension, or termination signals from the client?
8. Does [Fellow] seem engaged, neutral, or checked out?
9. Anything you personally think ProMazo leadership should know?
10. Any action items you're tracking for next check-in?

### Final concise set — PM note-drop (freeform + 2 tags)

PMs don't fill out forms either. So it's a single freeform box plus two quick tags:

**Freeform note:** *"Anything from this standup worth logging — status, concerns, wins."* (plain text, paste or type, no structure required — this maps to Q1, Q2, Q9, Q10 above)

**Tag 1 — Engagement signal:** `Strong` · `Neutral` · `Strained` *(covers #6)*

**Tag 2 — Risk flag (optional, multi-select):** `Deliverable at risk` · `Scope drift` · `Client concern raised` · `Renewal signal (positive)` · `Renewal signal (negative)` *(covers #2, #3, #4, #5, #7)*

The freeform note is what gets run through the categorization layer (Part C of the build) — same as the employee's answers.

---

## Why this shape

Every question that survived to the "final" set does two things: it's fast to answer honestly, and it maps to something the Circadian pattern-detection layer actually watches for over time (recurring blocker, declining sustainability trend, strained-tag trend, unactioned escalation). Anything that didn't clearly serve the risk model got cut, even if it was "nice to know" — that's how you keep a weekly check-in from turning into a chore nobody does honestly by week four.
