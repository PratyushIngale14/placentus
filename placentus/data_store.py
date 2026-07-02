"""
Placentus — in-memory data store.

Loads data/seed.json, runs every raw employee/PM text through the
categorization layer once, and exposes typed query methods the dashboard
reads from. This mirrors Sulcus's state_engine pattern: build once,
query many times, everything typed.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from .categorization import categorize
from .schemas import (
    CalendarTask,
    CategorizedEvent,
    Client,
    ClientHealthSummary,
    Employee,
    EmployeeHealthSummary,
    RiskLevel,
    SourceType,
    SustainabilityLevel,
)

SEED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "seed.json")

_SUSTAINABILITY_RISK = {
    SustainabilityLevel.SUSTAINABLE: RiskLevel.HEALTHY,
    SustainabilityLevel.STRETCHED: RiskLevel.WATCH,
    SustainabilityLevel.STRESSFUL: RiskLevel.AT_RISK,
    SustainabilityLevel.BURNING_OUT: RiskLevel.CRITICAL,
}

_RISK_ORDER = [RiskLevel.HEALTHY, RiskLevel.WATCH, RiskLevel.AT_RISK, RiskLevel.CRITICAL]


class PlacentusStore:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.clients: dict[str, Client] = {}
        self.employees: dict[str, Employee] = {}
        self.calendar_tasks: list[CalendarTask] = []
        self.events: list[CategorizedEvent] = []
        self._load()

    def _load(self):
        with open(SEED_PATH) as f:
            raw = json.load(f)

        self.clients = {c["id"]: Client(**c) for c in raw["clients"]}
        self.employees = {e["id"]: Employee(**e) for e in raw["employees"]}
        self.calendar_tasks = [CalendarTask(**t) for t in raw["calendar_tasks"]]

        def _process_checkin(chk: dict) -> CategorizedEvent:
            ts = datetime.fromisoformat(chk["timestamp"])
            combined = (
                f"Work update: {chk['q1_work']} "
                f"Client relationship: {chk['q2_relationship']} "
                f"Sustainability: {chk['q3_sustainability']}. "
                f"{('Escalation request: ' + chk['q4_escalation']) if chk['q4_escalation'] else ''}"
            ).strip()
            ev = categorize(
                raw_text=combined,
                employee_id=chk["employee_id"],
                source=SourceType.EMPLOYEE_CHECKIN,
                timestamp=ts,
                api_key=self.api_key,
            )
            # Sustainability directly informs risk floor regardless of keyword matches
            floor = _SUSTAINABILITY_RISK[SustainabilityLevel(chk["q3_sustainability"])]
            if _RISK_ORDER.index(floor) > _RISK_ORDER.index(ev.risk_level):
                ev.risk_level = floor
            return ev

        def _process_note(note: dict) -> CategorizedEvent:
            ts = datetime.fromisoformat(note["timestamp"])
            return categorize(
                raw_text=f"PM note ({note['pm_name']}): {note['note']} [Engagement signal: {note['engagement_signal']}]",
                employee_id=note["employee_id"],
                source=SourceType.PM_NOTE,
                timestamp=ts,
                api_key=self.api_key,
            )

        # Each categorize() call makes its own network round-trip to Claude
        # for the optional semantic pass when an API key is set. Running
        # them sequentially made entering a key stall the whole dashboard
        # for as long as it took to make one request per check-in/note.
        # These calls are independent (no shared state), so a thread pool
        # is safe and turns that into one round-trip's worth of wall time.
        with ThreadPoolExecutor(max_workers=8) as pool:
            checkin_events = list(pool.map(_process_checkin, raw["checkins"]))
            note_events = list(pool.map(_process_note, raw["pm_notes"]))

        events = checkin_events + note_events
        events.sort(key=lambda e: e.timestamp, reverse=True)
        self.events = events

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def events_for_employee(self, employee_id: str) -> list[CategorizedEvent]:
        return [e for e in self.events if e.employee_id == employee_id]

    def events_for_client(self, client_id: str) -> list[CategorizedEvent]:
        emp_ids = {e.id for e in self.employees.values() if e.client_id == client_id}
        return [e for e in self.events if e.employee_id in emp_ids]

    def employee_health(self, employee_id: str) -> EmployeeHealthSummary:
        emp_events = sorted(self.events_for_employee(employee_id), key=lambda e: e.timestamp)
        checkin_events = [e for e in emp_events if e.source == SourceType.EMPLOYEE_CHECKIN]

        worst = RiskLevel.HEALTHY
        for e in emp_events:
            if _RISK_ORDER.index(e.risk_level) > _RISK_ORDER.index(worst):
                worst = e.risk_level

        trend = []
        for e in checkin_events:
            if "Sustainable" in e.raw_text:
                trend.append(SustainabilityLevel.SUSTAINABLE)
            elif "Burning out" in e.raw_text:
                trend.append(SustainabilityLevel.BURNING_OUT)
            elif "Stressful" in e.raw_text:
                trend.append(SustainabilityLevel.STRESSFUL)
            elif "A bit stretched" in e.raw_text:
                trend.append(SustainabilityLevel.STRETCHED)

        open_escalations = sum(1 for e in emp_events if e.tier.value == "escalate")

        # crude recurring-blocker detection: same key phrase appears across 2+ checkins
        blocker_weeks = 0
        texts = [e.raw_text.lower() for e in checkin_events]
        for phrase in ["snowflake access", "waiting on", "blocked on"]:
            count = sum(1 for t in texts if phrase in t)
            blocker_weeks = max(blocker_weeks, count)

        last_checkin = checkin_events[-1].timestamp if checkin_events else None

        return EmployeeHealthSummary(
            employee_id=employee_id,
            risk_level=worst,
            sustainability_trend=trend,
            open_escalations=open_escalations,
            recurring_blocker_weeks=blocker_weeks if blocker_weeks >= 2 else 0,
            last_checkin=last_checkin,
        )

    def client_health(self, client_id: str) -> ClientHealthSummary:
        emp_ids = [e.id for e in self.employees.values() if e.client_id == client_id]
        summaries = [self.employee_health(eid) for eid in emp_ids]

        worst = RiskLevel.HEALTHY
        at_risk = 0
        escalations = 0
        for s in summaries:
            if _RISK_ORDER.index(s.risk_level) > _RISK_ORDER.index(worst):
                worst = s.risk_level
            if s.risk_level in (RiskLevel.AT_RISK, RiskLevel.CRITICAL):
                at_risk += 1
            escalations += s.open_escalations

        return ClientHealthSummary(
            client_id=client_id,
            risk_level=worst,
            employee_count=len(emp_ids),
            at_risk_count=at_risk,
            escalation_count=escalations,
        )

    def employees_for_client(self, client_id: str) -> list[Employee]:
        return [e for e in self.employees.values() if e.client_id == client_id]

    def tasks_for_employee(self, employee_id: str) -> list[CalendarTask]:
        return [t for t in self.calendar_tasks if t.employee_id == employee_id]

    def tasks_for_client(self, client_id: str) -> list[CalendarTask]:
        emp_ids = {e.id for e in self.employees.values() if e.client_id == client_id}
        return [t for t in self.calendar_tasks if t.employee_id in emp_ids]

    def tier_breakdown(self) -> dict[str, int]:
        counts = defaultdict(int)
        for e in self.events:
            counts[e.tier.value] += 1
        return dict(counts)

    def total_events(self) -> int:
        return len(self.events)
