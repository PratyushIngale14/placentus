"""
Placentus — core Pydantic v2 schemas.

Mirrors the Sulcus pattern: typed events in, typed guardrail reports out.
Nothing here is a dict-of-dicts. If it flows through the pipeline, it's a model.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ----------------------------------------------------------------------------
# Enums
# ----------------------------------------------------------------------------

class SourceType(str, Enum):
    EMPLOYEE_CHECKIN = "employee_checkin"
    PM_NOTE = "pm_note"
    SYSTEM = "system"


class SustainabilityLevel(str, Enum):
    SUSTAINABLE = "Sustainable"
    STRETCHED = "A bit stretched"
    STRESSFUL = "Stressful"
    BURNING_OUT = "Burning out"


class EngagementSignal(str, Enum):
    STRONG = "Strong"
    NEUTRAL = "Neutral"
    STRAINED = "Strained"


class RiskFlag(str, Enum):
    DELIVERABLE_AT_RISK = "Deliverable at risk"
    SCOPE_DRIFT = "Scope drift"
    CLIENT_CONCERN = "Client concern raised"
    RENEWAL_POSITIVE = "Renewal signal (positive)"
    RENEWAL_NEGATIVE = "Renewal signal (negative)"


class VisibilityTier(str, Enum):
    """Output of the categorization layer. Nothing is ever deleted — only routed."""
    STANDARD = "standard"          # normal work content, full staffing-company visibility
    RESTRICTED = "restricted"      # PII / client-confidential detected, archived + access-logged
    ESCALATE = "escalate"          # concerning content, surfaced with priority, never hidden


class RiskLevel(str, Enum):
    HEALTHY = "healthy"
    WATCH = "watch"
    AT_RISK = "at_risk"
    CRITICAL = "critical"


class SprintStatus(str, Enum):
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    BLOCKED = "blocked"
    COMPLETE = "complete"


# ----------------------------------------------------------------------------
# Core entities
# ----------------------------------------------------------------------------

class Client(BaseModel):
    id: str
    name: str
    industry: str
    engagement_start: date
    contract_value_band: str = Field(description="e.g. '$150K-$300K/yr' — a band, never an exact figure, kept coarse deliberately")
    account_manager: str


class Employee(BaseModel):
    id: str
    name: str
    role: str
    client_id: str
    sprint_name: str
    engagement_start: date
    pm_name: str = Field(description="the staffing company's internal PM assigned to this Fellow")


class CalendarTask(BaseModel):
    id: str
    employee_id: str
    date: date
    title: str
    status: SprintStatus
    hours: float = Field(ge=0, le=16)


# ----------------------------------------------------------------------------
# Raw ingested events (before categorization)
# ----------------------------------------------------------------------------

class EmployeeCheckin(BaseModel):
    id: str
    employee_id: str
    timestamp: datetime
    q1_work: str
    q2_relationship: str
    q3_sustainability: SustainabilityLevel
    q4_escalation: str = Field(description="empty string means 'nothing to flag'")


class PMNote(BaseModel):
    id: str
    pm_name: str
    employee_id: str
    timestamp: datetime
    note: str
    engagement_signal: EngagementSignal
    risk_flags: list[RiskFlag] = Field(default_factory=list)


# ----------------------------------------------------------------------------
# Categorization layer output
# ----------------------------------------------------------------------------

class CategorizationMatch(BaseModel):
    """A single rule/pattern that fired during categorization."""
    category: str = Field(description="e.g. 'pii_phone', 'client_confidential_keyword', 'escalation_language'")
    matched_text: str = Field(description="the specific span that triggered the rule, kept short")
    rule_type: str = Field(description="'rule_based' or 'llm_classified'")


class CategorizedEvent(BaseModel):
    """The routed, tiered version of a raw event. This is what the dashboard reads."""
    event_id: str
    source: SourceType
    employee_id: str
    timestamp: datetime
    raw_text: str = Field(description="the original, untouched content — never deleted")
    display_text: str = Field(description="what the STANDARD-tier viewer sees; redacted if needed")
    tier: VisibilityTier
    matches: list[CategorizationMatch] = Field(default_factory=list)
    risk_level: RiskLevel


# ----------------------------------------------------------------------------
# Evaluation / hallucination-guard layer (for the PM agent chatbot)
# ----------------------------------------------------------------------------

class GroundingCheck(BaseModel):
    claim: str
    grounded: bool
    supporting_event_ids: list[str] = Field(default_factory=list)


class AgentEvaluationReport(BaseModel):
    """Computed per chatbot answer — same pattern as Sulcus's Gate 2."""
    faithfulness_score: float = Field(ge=0.0, le=1.0)
    claims_checked: int
    claims_grounded: int
    grounding_checks: list[GroundingCheck] = Field(default_factory=list)
    status: str = Field(description="'PASSED' or 'WARNING' or 'BLOCKED'")


# ----------------------------------------------------------------------------
# Aggregate dashboard models
# ----------------------------------------------------------------------------

class EmployeeHealthSummary(BaseModel):
    employee_id: str
    risk_level: RiskLevel
    sustainability_trend: list[SustainabilityLevel] = Field(default_factory=list)
    open_escalations: int
    recurring_blocker_weeks: int = Field(default=0, description="how many consecutive weeks the same blocker language has appeared")
    last_checkin: Optional[datetime] = None


class ClientHealthSummary(BaseModel):
    client_id: str
    risk_level: RiskLevel
    employee_count: int
    at_risk_count: int
    escalation_count: int
