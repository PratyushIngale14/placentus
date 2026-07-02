"""
Placentus — synthetic data generator.

Builds 5 fictional clients, 12 employees (Fellows), 36+ employee check-ins,
18 PM notes, and a month of calendar tasks. Deliberately includes a spread
of content that should route to STANDARD, RESTRICTED, and ESCALATE tiers —
this is a demo, and the categorization layer needs real cases to prove it
works, not just happy-path data.

Run directly to regenerate data/seed.json:
    python -m placentus.generator
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta

from .schemas import (
    CalendarTask,
    Client,
    Employee,
    EmployeeCheckin,
    EngagementSignal,
    PMNote,
    RiskFlag,
    SprintStatus,
    SustainabilityLevel,
)

BASE_DATE = date(2026, 6, 1)


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# ----------------------------------------------------------------------------
# Clients
# ----------------------------------------------------------------------------

CLIENTS = [
    Client(
        id="client-meridian",
        name="Meridian Health Systems",
        industry="Healthcare",
        engagement_start=date(2026, 2, 1),
        contract_value_band="$180K-$260K/yr",
        account_manager="Sarah Chen",
    ),
    Client(
        id="client-vantage",
        name="Vantage Logistics",
        industry="Logistics",
        engagement_start=date(2026, 3, 15),
        contract_value_band="$120K-$180K/yr",
        account_manager="James Okafor",
    ),
    Client(
        id="client-northbridge",
        name="Northbridge Financial",
        industry="Financial Services",
        engagement_start=date(2026, 1, 10),
        contract_value_band="$250K-$400K/yr",
        account_manager="Rachel Torres",
    ),
    Client(
        id="client-cascade",
        name="Cascade Retail Group",
        industry="Retail",
        engagement_start=date(2026, 4, 1),
        contract_value_band="$90K-$150K/yr",
        account_manager="Diana Frost",
    ),
    Client(
        id="client-ionis",
        name="Ionis Biotech",
        industry="Biotechnology",
        engagement_start=date(2026, 2, 20),
        contract_value_band="$200K-$320K/yr",
        account_manager="Carmen Vela",
    ),
]

# ----------------------------------------------------------------------------
# Employees
# ----------------------------------------------------------------------------

EMPLOYEES = [
    Employee(id="emp-aditi", name="Aditi Rao", role="Data Analyst", client_id="client-meridian",
              sprint_name="Claims Automation Q3", engagement_start=date(2026, 2, 3), pm_name="Sarah Chen"),
    Employee(id="emp-marcus", name="Marcus Webb", role="Software Engineer", client_id="client-meridian",
              sprint_name="Patient Portal Revamp", engagement_start=date(2026, 2, 10), pm_name="Sarah Chen"),

    Employee(id="emp-sam", name="Sam Rivera", role="Business Analyst", client_id="client-vantage",
              sprint_name="Fleet Optimization", engagement_start=date(2026, 3, 18), pm_name="James Okafor"),
    Employee(id="emp-priya", name="Priya Nair", role="Data Engineer", client_id="client-vantage",
              sprint_name="Warehouse ETL Pipeline", engagement_start=date(2026, 3, 20), pm_name="James Okafor"),

    Employee(id="emp-kevin", name="Kevin Park", role="Financial Analyst", client_id="client-northbridge",
              sprint_name="Risk Model v2", engagement_start=date(2026, 1, 15), pm_name="Rachel Torres"),
    Employee(id="emp-lily", name="Lily Tan", role="Software Engineer", client_id="client-northbridge",
              sprint_name="Compliance Dashboard", engagement_start=date(2026, 1, 20), pm_name="Rachel Torres"),
    Employee(id="emp-neil2", name="Neil Sharma", role="Backend Engineer", client_id="client-northbridge",
              sprint_name="Payments Reconciliation", engagement_start=date(2026, 2, 1), pm_name="Rachel Torres"),

    Employee(id="emp-dev", name="Dev Patel", role="Data Scientist", client_id="client-cascade",
              sprint_name="Demand Forecasting", engagement_start=date(2026, 4, 5), pm_name="Diana Frost"),
    Employee(id="emp-ananya", name="Ananya Rao", role="Product Analyst", client_id="client-cascade",
              sprint_name="Loyalty Program Redesign", engagement_start=date(2026, 4, 8), pm_name="Diana Frost"),

    Employee(id="emp-tom", name="Tom Bradley", role="ML Engineer", client_id="client-ionis",
              sprint_name="Trial Data Pipeline", engagement_start=date(2026, 2, 22), pm_name="Carmen Vela"),
    Employee(id="emp-neil", name="Neil Fernandes", role="Data Analyst", client_id="client-ionis",
              sprint_name="Lab Results Integration", engagement_start=date(2026, 2, 25), pm_name="Carmen Vela"),
    Employee(id="emp-mia", name="Mia Johnson", role="QA Engineer", client_id="client-ionis",
              sprint_name="Trial Data Pipeline", engagement_start=date(2026, 3, 1), pm_name="Carmen Vela"),
]

EMPLOYEE_BY_ID = {e.id: e for e in EMPLOYEES}


# ----------------------------------------------------------------------------
# Check-ins — 3 weekly rounds per employee, with deliberate tier variety
# ----------------------------------------------------------------------------

def _wk(n: int) -> datetime:
    return datetime.combine(BASE_DATE + timedelta(weeks=n, days=4), datetime.min.time()) + timedelta(hours=17)


CHECKIN_SCRIPTS: dict[str, list[dict]] = {
    # STANDARD-only employee: healthy, normal, nothing to flag
    "emp-aditi": [
        dict(q1="Finished the claims dedup logic and started on the reconciliation report. No blockers.",
             q2="Good week with the client team, clear priorities from the standup.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
        dict(q1="Shipped the reconciliation report, now validating against last quarter's numbers.",
             q2="Client PM gave positive feedback on the dashboard draft.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
        dict(q1="Started the automated alerts feature for claim anomalies.",
             q2="Smooth week, client included me in the planning call this time.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
    ],
    # Recurring blocker across 3 weeks — tests the pattern-detection story
    "emp-marcus": [
        dict(q1="Working on the patient portal login flow. Still waiting on the client to grant Snowflake read access.",
             q2="Fine otherwise, just stuck on the access request.",
             q3=SustainabilityLevel.STRETCHED, q4=""),
        dict(q1="Same as last week — still waiting on Snowflake access from the client's IT team, can't move the data layer forward.",
             q2="Raised it again in standup, they said they'd look into it.",
             q3=SustainabilityLevel.STRETCHED, q4=""),
        dict(q1="Third week now waiting on Snowflake access. I've built everything I can around it but the core task is fully blocked.",
             q2="Starting to feel like this isn't a priority for them even though it's blocking my whole sprint.",
             q3=SustainabilityLevel.STRESSFUL, q4="Could someone from ProMazo help escalate this access request? I don't think I can push harder from my side."),
    ],
    # Vantage — mostly fine, one PII slip
    "emp-sam": [
        dict(q1="Mapped the current fleet routing logic, starting the optimization model next.",
             q2="Good relationship with the client manager, very responsive.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
        dict(q1="Model is showing a 12% efficiency gain in early tests. If you need to reach the client lead directly his cell is 214-555-0148, easier than email.",
             q2="No concerns.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
        dict(q1="Presented the model results, client wants to expand scope to include the Texas warehouses too.",
             q2="Feels like more work than originally scoped but I'm excited about it.",
             q3=SustainabilityLevel.STRETCHED, q4=""),
    ],
    "emp-priya": [
        dict(q1="ETL pipeline is live for the first three warehouses, backfilling historical data now.",
             q2="Standups are efficient, client engineering lead is sharp and clear.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
        dict(q1="Backfill finished, now optimizing query performance on the warehouse layer.",
             q2="All good.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
    ],
    # Northbridge — a client-confidential slip and an escalation case
    "emp-kevin": [
        dict(q1="Refactored the risk scoring model, validation metrics look strong.",
             q2="Fine, standard week.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
        dict(q1="Client shared their unreleased Q3 revenue numbers to benchmark the risk model against — should probably not be in a status report but wanted it logged somewhere.",
             q2="Otherwise a normal week.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
        dict(q1="Model is in final review with the client's compliance team.",
             q2="Positive, they said the model is more thorough than their last vendor's.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
    ],
    "emp-lily": [
        dict(q1="Compliance dashboard front-end is 80% done, waiting on final design sign-off.",
             q2="Client design lead has been slow to respond this week.",
             q3=SustainabilityLevel.STRETCHED, q4=""),
        dict(q1="My client manager raised his voice at me in front of the whole team on a call yesterday over a deadline that was never actually confirmed in writing. It was humiliating and I still feel uncomfortable about it.",
             q2="I don't know how to bring this up without it affecting the relationship.",
             q3=SustainabilityLevel.STRESSFUL, q4="Yes — I would like someone from ProMazo to reach out to me about this, I don't want to handle it alone."),
    ],
    "emp-neil2": [
        dict(q1="Payments reconciliation module passing all test cases now.",
             q2="Good week, no issues.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
        dict(q1="Client asked me to also take over a completely separate reporting project that has nothing to do with my original scope — feels like scope creep, wasn't hired for this.",
             q2="Not sure if I should just say yes to keep things smooth.",
             q3=SustainabilityLevel.STRETCHED, q4=""),
    ],
    # Cascade — healthy
    "emp-dev": [
        dict(q1="Forecasting model backtested against 2 years of sales data, accuracy within target range.",
             q2="Great collaboration with the client's merchandising team.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
        dict(q1="Deployed the forecasting model to staging, client is reviewing outputs this week.",
             q2="No concerns.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
    ],
    "emp-ananya": [
        dict(q1="Loyalty program tiering logic finalized, moving to the rewards calculation engine.",
             q2="Client stakeholders are engaged and give fast feedback.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
        dict(q1="Rewards engine on track, minor delay from a shared dependency on the client's side.",
             q2="Fine, not a big deal.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
    ],
    # Ionis — burnout trend building
    "emp-tom": [
        dict(q1="Trial data pipeline ingesting from 2 of 4 sites, on schedule.",
             q2="Client PI is demanding but fair.",
             q3=SustainabilityLevel.STRETCHED, q4=""),
        dict(q1="Now ingesting from all 4 sites, but the QA cycle is taking longer than planned and eating into my weekends.",
             q2="Same as last week, high pressure but manageable so far.",
             q3=SustainabilityLevel.STRESSFUL, q4=""),
        dict(q1="Pipeline is stable but I've worked through the last two weekends to keep up with the QA backlog and I'm running on fumes.",
             q2="Nobody on the client side seems aware of how much overtime this has actually taken.",
             q3=SustainabilityLevel.BURNING_OUT, q4="I'd like to talk to my ProMazo manager about workload — I don't think this pace is sustainable long term."),
    ],
    "emp-neil": [
        dict(q1="Lab results integration mapped to the new schema, testing this week.",
             q2="Smooth week.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
        dict(q1="Integration passed QA, moving to production rollout next sprint.",
             q2="No issues.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
    ],
    "emp-mia": [
        dict(q1="Wrote the QA test suite for the trial data pipeline, found 3 edge cases in the ingestion logic.",
             q2="Good working relationship with Tom and the client QA lead.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
        dict(q1="Fixed the edge cases, pipeline now passing full regression suite.",
             q2="All good.",
             q3=SustainabilityLevel.SUSTAINABLE, q4=""),
    ],
}


PM_NOTES_SCRIPTS: dict[str, list[dict]] = {
    "emp-aditi": [dict(note="Standup covered claims dedup progress, on track. Aditi seems fully ramped up.",
                        signal=EngagementSignal.STRONG, flags=[])],
    "emp-marcus": [
        dict(note="Marcus flagged the Snowflake access blocker again this week — third time. I'm escalating to the client's engagement lead directly tomorrow.",
             signal=EngagementSignal.NEUTRAL, flags=[RiskFlag.DELIVERABLE_AT_RISK]),
    ],
    "emp-sam": [dict(note="Client wants to expand Sam's scope to Texas warehouses — good renewal signal, need to formalize a change order so Sam isn't doing unpaid scope expansion.",
                      signal=EngagementSignal.STRONG, flags=[RiskFlag.RENEWAL_POSITIVE, RiskFlag.SCOPE_DRIFT])],
    "emp-lily": [
        dict(note="Lily reported an uncomfortable interaction with her client manager raising his voice on a call. Scheduling a call with her directly and will loop in the account lead about the client manager's conduct.",
             signal=EngagementSignal.STRAINED, flags=[RiskFlag.CLIENT_CONCERN]),
    ],
    "emp-neil2": [dict(note="Neil raised scope concerns about being pulled into an unrelated reporting project. Need to clarify with client whether this is in-contract.",
                        signal=EngagementSignal.NEUTRAL, flags=[RiskFlag.SCOPE_DRIFT])],
    "emp-tom": [
        dict(note="Tom is showing burnout signs — worked two weekends in a row on the QA backlog. Need to have a direct conversation about workload and possibly bring in support before this becomes a retention risk.",
             signal=EngagementSignal.NEUTRAL, flags=[RiskFlag.DELIVERABLE_AT_RISK]),
    ],
    "emp-dev": [dict(note="Forecasting model deployed to staging smoothly, client merchandising team very happy.",
                      signal=EngagementSignal.STRONG, flags=[RiskFlag.RENEWAL_POSITIVE])],
    "emp-kevin": [dict(note="Risk model in final compliance review, client compared favorably to their last vendor. Strong renewal signal for Q4.",
                        signal=EngagementSignal.STRONG, flags=[RiskFlag.RENEWAL_POSITIVE])],
}


# ----------------------------------------------------------------------------
# Calendar tasks — a month of work items per employee
# ----------------------------------------------------------------------------

TASK_TITLES = [
    "Data pipeline build", "Sprint planning", "Client standup", "Code review",
    "Model validation", "Dashboard iteration", "QA pass", "Stakeholder demo",
    "Documentation", "Access/onboarding follow-up", "Retrospective", "Deployment",
]


def _generate_calendar_tasks() -> list[CalendarTask]:
    tasks = []
    for emp in EMPLOYEES:
        for day_offset in range(0, 28, 2):  # every other weekday-ish across ~4 weeks
            d = BASE_DATE + timedelta(days=day_offset)
            if d.weekday() >= 5:
                continue
            title = TASK_TITLES[(day_offset // 2 + hash(emp.id)) % len(TASK_TITLES)]
            status = SprintStatus.ON_TRACK
            if "Marcus" in emp.name and day_offset in (14, 16, 18):
                status = SprintStatus.BLOCKED
                title = "Data layer work (blocked on Snowflake access)"
            if "Tom" in emp.name and day_offset >= 20:
                status = SprintStatus.AT_RISK
            tasks.append(CalendarTask(
                id=_uid("task"),
                employee_id=emp.id,
                date=d,
                title=title,
                status=status,
                hours=round(4 + (hash(emp.id + str(day_offset)) % 5), 1),
            ))
    return tasks


# ----------------------------------------------------------------------------
# Build + serialize
# ----------------------------------------------------------------------------

def build_seed() -> dict:
    checkins: list[EmployeeCheckin] = []
    for emp_id, rounds in CHECKIN_SCRIPTS.items():
        for i, r in enumerate(rounds):
            checkins.append(EmployeeCheckin(
                id=_uid("chk"),
                employee_id=emp_id,
                timestamp=_wk(i),
                q1_work=r["q1"],
                q2_relationship=r["q2"],
                q3_sustainability=r["q3"],
                q4_escalation=r["q4"],
            ))

    pm_notes: list[PMNote] = []
    for emp_id, notes in PM_NOTES_SCRIPTS.items():
        emp = EMPLOYEE_BY_ID[emp_id]
        for i, n in enumerate(notes):
            pm_notes.append(PMNote(
                id=_uid("note"),
                pm_name=emp.pm_name,
                employee_id=emp_id,
                timestamp=_wk(i) + timedelta(hours=2),
                note=n["note"],
                engagement_signal=n["signal"],
                risk_flags=n["flags"],
            ))

    tasks = _generate_calendar_tasks()

    return {
        "clients": [c.model_dump(mode="json") for c in CLIENTS],
        "employees": [e.model_dump(mode="json") for e in EMPLOYEES],
        "checkins": [c.model_dump(mode="json") for c in checkins],
        "pm_notes": [n.model_dump(mode="json") for n in pm_notes],
        "calendar_tasks": [t.model_dump(mode="json") for t in tasks],
    }


def main():
    seed = build_seed()
    total_events = len(seed["checkins"]) + len(seed["pm_notes"])
    print(f"Generated {len(seed['clients'])} clients, {len(seed['employees'])} employees, "
          f"{len(seed['checkins'])} check-ins, {len(seed['pm_notes'])} PM notes "
          f"({total_events} total events), {len(seed['calendar_tasks'])} calendar tasks.")
    import os
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "seed.json")
    with open(out_path, "w") as f:
        json.dump(seed, f, indent=2, default=str)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
