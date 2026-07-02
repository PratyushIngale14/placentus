"""
Placentus — categorization layer.

Design rule, non-negotiable: NOTHING IS EVER DELETED. This module only routes
raw text into a visibility tier (standard / restricted / escalate) and
produces a redacted display_text for the standard tier when needed. The raw
text is always preserved on the CategorizedEvent for audit purposes.

Two passes:
  1. Rule-based regex/keyword pass — fast, deterministic, explainable.
  2. Optional LLM pass (Claude) — catches things regex can't (tone, implied
     distress, scope-drift language) when an API key is available. Falls
     back gracefully to rule-based-only if no key is configured, so the
     product still works in a pure offline demo.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from .schemas import (
    CategorizationMatch,
    CategorizedEvent,
    RiskLevel,
    SourceType,
    VisibilityTier,
)

# ----------------------------------------------------------------------------
# Rule-based patterns
# ----------------------------------------------------------------------------

PII_PATTERNS: dict[str, re.Pattern] = {
    "pii_phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "pii_email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "pii_ssn_like": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "pii_credit_card_like": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
}

# Keyword heuristics for client-confidential content. Deliberately coarse —
# this is a first-pass filter, not a claim of perfect detection.
CLIENT_CONFIDENTIAL_KEYWORDS = [
    "api key", "api_key", "password", "credential", "secret key",
    "revenue of", "quarterly earnings", "internal roadmap", "unreleased",
    "acquisition", "merger", "layoffs", "lawsuit", "nda", "confidential",
    "proprietary", "trade secret", "source code for",
]

# Escalation language — surfaced FASTER, never hidden. This is the opposite
# direction of the other two categories: matching here increases visibility.
ESCALATION_KEYWORDS = [
    "harass", "discriminat", "unsafe", "unfair", "hostile", "yell",
    "threaten", "quit", "burn out", "burning out", "can't keep up",
    "overwhelmed", "retaliat", "inappropriate", "uncomfortable",
    "asked me to falsify", "asked me to lie", "out of scope", "unpaid",
]

SCOPE_DRIFT_KEYWORDS = [
    "not in my job description", "outside my role", "different project entirely",
    "wasn't hired for this", "scope creep",
]


def _find_matches(text: str, patterns: dict[str, re.Pattern]) -> list[CategorizationMatch]:
    matches = []
    for category, pattern in patterns.items():
        for m in pattern.finditer(text):
            matches.append(CategorizationMatch(
                category=category,
                matched_text=m.group(0)[:40],
                rule_type="rule_based",
            ))
    return matches


def _find_keyword_matches(text: str, keywords: list[str], category_prefix: str) -> list[CategorizationMatch]:
    lowered = text.lower()
    matches = []
    for kw in keywords:
        if kw in lowered:
            matches.append(CategorizationMatch(
                category=f"{category_prefix}:{kw.replace(' ', '_')}",
                matched_text=kw,
                rule_type="rule_based",
            ))
    return matches


def _redact(text: str, pii_matches: list[CategorizationMatch]) -> str:
    redacted = text
    for match in pii_matches:
        if match.matched_text:
            redacted = redacted.replace(match.matched_text, "[REDACTED]")
    return redacted


# ----------------------------------------------------------------------------
# Optional LLM pass
# ----------------------------------------------------------------------------

def _llm_classify(text: str, api_key: str | None) -> list[CategorizationMatch]:
    """
    Second-pass semantic classification via Claude. Only runs if an API key
    is supplied. Catches tone/implied-distress signals regex misses.
    Fails soft: any error just means we fall back to rule-based-only.
    """
    if not api_key:
        return []
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        system = (
            "You are a content classifier for an internal staffing-company "
            "check-in tool. Given a short employee or PM note, identify ONLY "
            "if it contains: (a) client-confidential business detail, or "
            "(b) language suggesting the employee is distressed, mistreated, "
            "or wants escalation, even if not using obvious keywords. "
            "Respond with ONLY a JSON object: "
            '{"client_confidential": true/false, "distress_signal": true/false, "reason": "one short phrase"}. '
            "No other text."
        )
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=150,
            system=system,
            messages=[{"role": "user", "content": text}],
        )
        raw = "".join(b.text for b in resp.content if hasattr(b, "text")).strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        import json
        parsed = json.loads(raw)
        matches = []
        if parsed.get("client_confidential"):
            matches.append(CategorizationMatch(
                category="client_confidential_semantic",
                matched_text=parsed.get("reason", "")[:40],
                rule_type="llm_classified",
            ))
        if parsed.get("distress_signal"):
            matches.append(CategorizationMatch(
                category="escalation_semantic",
                matched_text=parsed.get("reason", "")[:40],
                rule_type="llm_classified",
            ))
        return matches
    except Exception:
        return []


# ----------------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------------

def categorize(
    *,
    raw_text: str,
    employee_id: str,
    source: SourceType,
    timestamp: datetime,
    api_key: str | None = None,
) -> CategorizedEvent:
    """
    Routes a single piece of raw text (employee check-in answer or PM note)
    into a visibility tier. Raw text is always preserved.
    """
    pii_matches = _find_matches(raw_text, PII_PATTERNS)
    confidential_matches = _find_keyword_matches(raw_text, CLIENT_CONFIDENTIAL_KEYWORDS, "client_confidential")
    escalation_matches = _find_keyword_matches(raw_text, ESCALATION_KEYWORDS, "escalation")
    scope_matches = _find_keyword_matches(raw_text, SCOPE_DRIFT_KEYWORDS, "scope_drift")
    llm_matches = _llm_classify(raw_text, api_key)

    all_matches = pii_matches + confidential_matches + escalation_matches + scope_matches + llm_matches

    has_escalation = any(
        m.category.startswith("escalation") for m in all_matches
    )
    has_confidential = any(
        m.category.startswith("client_confidential") for m in all_matches
    )
    has_pii = len(pii_matches) > 0

    # Escalation always wins — surfaced faster, never suppressed.
    if has_escalation:
        tier = VisibilityTier.ESCALATE
        risk = RiskLevel.CRITICAL if len(escalation_matches) >= 2 else RiskLevel.AT_RISK
        display_text = raw_text  # escalation content is shown in full, not redacted
    elif has_confidential or has_pii:
        tier = VisibilityTier.RESTRICTED
        risk = RiskLevel.WATCH
        display_text = _redact(raw_text, pii_matches) if has_pii else "[Content archived — client-confidential material detected. Full text available to compliance-tier access.]"
    else:
        tier = VisibilityTier.STANDARD
        risk = RiskLevel.HEALTHY
        display_text = raw_text

    return CategorizedEvent(
        event_id=str(uuid.uuid4()),
        source=source,
        employee_id=employee_id,
        timestamp=timestamp,
        raw_text=raw_text,
        display_text=display_text,
        tier=tier,
        matches=all_matches,
        risk_level=risk,
    )
