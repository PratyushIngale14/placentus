"""
Placentus — generative UI renderers.

Same philosophy as Sulcus's generative_ui.py: typed data in, styled HTML out,
no walls of raw text. Palette is Placentus's own — "Trust Lines" — a
sibling of Sulcus's neuro-industrial system, same architecture family,
different accent: teal-green for trust/verification instead of violet.
"""

from __future__ import annotations

import urllib.parse

from .schemas import (
    CategorizedEvent,
    ClientHealthSummary,
    EmployeeHealthSummary,
    RiskLevel,
    VisibilityTier,
)

# ----------------------------------------------------------------------------
# Palette
# ----------------------------------------------------------------------------

VOID = "#0A0E14"
PANEL = "#131822"
PANEL_RAISED = "#1A2130"
INK = "#E7EAF0"
MUTED = "#7C8699"
TRUST = "#2DD4BF"     # teal — verification, trust lines
TRUST_DIM = "#1B4B47"
ALERT = "#F0524B"
AMBER = "#F0B429"
BORDER = "#232B3A"

RISK_COLORS = {
    RiskLevel.HEALTHY: ("#1F8A5F", "#0F2A20"),
    RiskLevel.WATCH: (AMBER, "#332A0F"),
    RiskLevel.AT_RISK: ("#E07A2C", "#332210"),
    RiskLevel.CRITICAL: (ALERT, "#331414"),
}

TIER_COLORS = {
    VisibilityTier.STANDARD: (TRUST, TRUST_DIM),
    VisibilityTier.RESTRICTED: (AMBER, "#332A0F"),
    VisibilityTier.ESCALATE: (ALERT, "#331414"),
}


def _clean(html: str) -> str:
    """Collapse a multi-line HTML template to a single line.

    Streamlit's markdown renderer follows CommonMark: a blank line inside
    what looks like a raw HTML block ends that block, and any indented
    (4+ space) line that follows gets parsed as a literal code block
    instead of HTML. Templates with conditional empty inserts (e.g. an
    unused badge row) trigger exactly that, leaking raw tags as visible
    text. Flattening to one line sidesteps CommonMark's block rules.
    """
    return " ".join(line.strip() for line in html.strip().splitlines() if line.strip())


def section_label(text: str) -> str:
    return _clean(f"""
    <div style="font-family:'JetBrains Mono',monospace;font-size:10.5px;color:{MUTED};
                letter-spacing:0.25em;text-transform:uppercase;margin:18px 0 10px 0;
                border-bottom:1px solid {BORDER};padding-bottom:8px;">
        {text}
    </div>""")


def risk_pill(risk: RiskLevel) -> str:
    color, bg = RISK_COLORS[risk]
    label = risk.value.replace("_", " ").upper()
    return _clean(f"""<span style="background:{bg};color:{color};font-family:'JetBrains Mono',monospace;
        font-size:10px;letter-spacing:0.1em;padding:3px 9px;border-radius:20px;
        border:1px solid {color}40;">{label}</span>""")


def tier_pill(tier: VisibilityTier) -> str:
    color, bg = TIER_COLORS[tier]
    return _clean(f"""<span style="background:{bg};color:{color};font-family:'JetBrains Mono',monospace;
        font-size:9.5px;letter-spacing:0.1em;padding:2px 8px;border-radius:20px;
        border:1px solid {color}40;">{tier.value.upper()}</span>""")


def chat_fab_icon_data_uri() -> str:
    """Chat-bubble SVG for the floating PM Agent launcher, as a CSS data URI."""
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
        "stroke='#0A0E14' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
        "<path d='M4 5h16a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H9l-4 4v-4H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z'/>"
        "<circle cx='8' cy='10.5' r='1.1' fill='#0A0E14' stroke='none'/>"
        "<circle cx='12' cy='10.5' r='1.1' fill='#0A0E14' stroke='none'/>"
        "<circle cx='16' cy='10.5' r='1.1' fill='#0A0E14' stroke='none'/>"
        "</svg>"
    )
    return "data:image/svg+xml," + urllib.parse.quote(svg)


def client_card(client_name: str, industry: str, health: ClientHealthSummary, is_selected: bool = False) -> str:
    color, bg = RISK_COLORS[health.risk_level]
    border = f"2px solid {TRUST}" if is_selected else f"1px solid {BORDER}"
    return _clean(f"""
    <div style="background:{PANEL};border:{border};border-radius:12px;padding:16px 18px;
                margin-bottom:10px;position:relative;overflow:hidden;">
        <div style="position:absolute;top:0;left:0;width:3px;height:100%;background:{color};"></div>
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
                <div style="font-family:'Fraunces',serif;font-size:17px;color:{INK};font-weight:600;">{client_name}</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:{MUTED};
                            letter-spacing:0.08em;margin-top:2px;">{industry.upper()}</div>
            </div>
            {risk_pill(health.risk_level)}
        </div>
        <div style="display:flex;gap:18px;margin-top:12px;font-family:'JetBrains Mono',monospace;font-size:11px;color:{MUTED};">
            <span>{health.employee_count} FELLOWS</span>
            <span style="color:{AMBER if health.at_risk_count else MUTED};">{health.at_risk_count} AT RISK</span>
            <span style="color:{ALERT if health.escalation_count else MUTED};">{health.escalation_count} ESCALATIONS</span>
        </div>
    </div>""")


def employee_card(name: str, role: str, sprint: str, health: EmployeeHealthSummary) -> str:
    color, bg = RISK_COLORS[health.risk_level]
    trend_dots = "".join(
        f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
        f'background:{_sustainability_color(s.value)};margin-right:4px;"></span>'
        for s in health.sustainability_trend[-6:]
    )
    return _clean(f"""
    <div style="background:{PANEL_RAISED};border:1px solid {BORDER};border-radius:10px;
                padding:14px 16px;margin-bottom:8px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-family:'Geist',sans-serif;font-size:14px;color:{INK};font-weight:600;">{name}</div>
                <div style="font-family:'Geist',sans-serif;font-size:11.5px;color:{MUTED};margin-top:1px;">{role} · {sprint}</div>
            </div>
            {risk_pill(health.risk_level)}
        </div>
        <div style="margin-top:10px;display:flex;justify-content:space-between;align-items:center;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:9.5px;color:{MUTED};letter-spacing:0.08em;">
                SUSTAINABILITY TREND &nbsp;{trend_dots}
            </div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:{ALERT if health.open_escalations else MUTED};">
                {health.open_escalations} OPEN ESCALATION{'S' if health.open_escalations != 1 else ''}
            </div>
        </div>
        {f'<div style="margin-top:8px;font-family:JetBrains Mono,monospace;font-size:10px;color:{AMBER};">RECURRING BLOCKER · {health.recurring_blocker_weeks} WEEKS RUNNING</div>' if health.recurring_blocker_weeks >= 2 else ''}
    </div>""")


def _sustainability_color(level: str) -> str:
    mapping = {
        "Sustainable": "#1F8A5F",
        "A bit stretched": AMBER,
        "Stressful": "#E07A2C",
        "Burning out": ALERT,
    }
    return mapping.get(level, MUTED)


def event_card(event: CategorizedEvent, employee_name: str) -> str:
    color, bg = TIER_COLORS[event.tier]
    matches_html = ""
    if event.matches:
        badges = "".join(
            f'<span style="font-family:JetBrains Mono,monospace;font-size:9px;color:{MUTED};'
            f'background:{VOID};border:1px solid {BORDER};border-radius:4px;padding:1px 6px;margin-right:4px;">'
            f'{m.category}</span>'
            for m in event.matches[:4]
        )
        matches_html = f'<div style="margin-top:8px;">{badges}</div>'

    return _clean(f"""
    <div style="background:{PANEL};border:1px solid {BORDER};border-left:3px solid {color};
                border-radius:8px;padding:12px 14px;margin-bottom:8px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-family:'Geist',sans-serif;font-size:12.5px;color:{INK};font-weight:600;">{employee_name}</span>
            {tier_pill(event.tier)}
        </div>
        <div style="font-family:'Geist',sans-serif;font-size:12.5px;color:{MUTED};margin-top:6px;line-height:1.5;">
            {event.display_text}
        </div>
        {matches_html}
        <div style="font-family:'JetBrains Mono',monospace;font-size:9.5px;color:{MUTED};margin-top:8px;">
            {event.timestamp.strftime('%b %d · %H:%M')} · {event.source.value.replace('_',' ').upper()}
        </div>
    </div>""")


def trust_ledger_row(label: str, value: str, color: str = TRUST) -> str:
    """A single row in the always-visible Trust Ledger (Placentus's Transparency Center)."""
    return _clean(f"""
    <div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid {BORDER};
                font-family:'JetBrains Mono',monospace;font-size:11px;">
        <span style="color:{MUTED};">{label}</span>
        <span style="color:{color};font-weight:600;">{value}</span>
    </div>""")


def terminal_console(lines: list[str]) -> str:
    rendered = "".join(
        f'<div style="color:#8FE3D0;margin-bottom:3px;">&gt; {l}</div>' for l in lines[-14:]
    )
    return _clean(f"""
    <div style="background:#0D1117;border:1px solid {BORDER};border-radius:8px;padding:14px 16px;
                font-family:'JetBrains Mono',monospace;font-size:11px;max-height:220px;overflow-y:auto;">
        {rendered}
    </div>""")


def trust_line_header() -> str:
    """The literal 'trust line' motif — a thin teal connecting line used as a section divider."""
    return _clean(f"""
    <div style="height:1px;background:linear-gradient(90deg,{TRUST}00,{TRUST}66,{TRUST}00);
                margin:22px 0;"></div>""")
