"""
Placentus — evaluation / hallucination-guard layer.

Same computed-not-decorative pattern as Sulcus's Gate 2: every claim the PM
agent makes gets checked for token-level grounding against the actual
categorized events it was given as context. If a claim isn't supported by
anything in the corpus, it's flagged, and the aggregate faithfulness score
drops. This is what lets the dashboard say "the agent's answer was 0.91
faithful" and mean something specific, not a vibe.
"""

from __future__ import annotations

import re

from .schemas import AgentEvaluationReport, CategorizedEvent, GroundingCheck

_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "to", "of", "in", "on",
    "and", "or", "for", "with", "this", "that", "it", "their", "they",
    "has", "have", "had", "be", "as", "at", "by", "from", "about", "we",
    "you", "i", "he", "she", "them", "his", "her", "its", "not", "no",
}


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9']+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def _split_claims(answer: str) -> list[str]:
    """Naive sentence split — good enough for short agent answers."""
    parts = re.split(r"(?<=[.!?])\s+", answer.strip())
    return [p.strip() for p in parts if len(p.strip()) > 3]


def evaluate_answer(answer: str, context_events: list[CategorizedEvent]) -> AgentEvaluationReport:
    """
    For each sentence in the agent's answer, check whether its meaningful
    tokens are substantially grounded in at least one context event's
    display_text. This mirrors Sulcus's token-overlap faithfulness math.
    """
    corpus_by_event: dict[str, set[str]] = {
        ev.event_id: _tokenize(ev.display_text) for ev in context_events
    }

    claims = _split_claims(answer)
    checks: list[GroundingCheck] = []

    for claim in claims:
        claim_tokens = _tokenize(claim)
        if not claim_tokens:
            continue
        best_overlap = 0.0
        supporting: list[str] = []
        for event_id, event_tokens in corpus_by_event.items():
            if not event_tokens:
                continue
            overlap = len(claim_tokens & event_tokens) / len(claim_tokens)
            if overlap >= 0.35:
                supporting.append(event_id)
            best_overlap = max(best_overlap, overlap)
        grounded = best_overlap >= 0.35
        checks.append(GroundingCheck(
            claim=claim[:120],
            grounded=grounded,
            supporting_event_ids=supporting[:3],
        ))

    total = len(checks)
    grounded_count = sum(1 for c in checks if c.grounded)
    score = round(grounded_count / total, 2) if total else 1.0

    if score >= 0.75:
        status = "PASSED"
    elif score >= 0.4:
        status = "WARNING"
    else:
        status = "BLOCKED"

    return AgentEvaluationReport(
        faithfulness_score=score,
        claims_checked=total,
        claims_grounded=grounded_count,
        grounding_checks=checks,
        status=status,
    )
