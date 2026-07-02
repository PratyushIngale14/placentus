"""
Placentus — staffing-company engagement intelligence dashboard.

A child product of Sulcus, same architecture family: typed events,
computed guardrails, generative UI. Applied here to staffing/consulting
account health instead of a product launch.
"""

from __future__ import annotations

import streamlit as st
from streamlit_calendar import calendar as st_calendar

from placentus.data_store import PlacentusStore
from placentus.evaluation import evaluate_answer
from placentus.schemas import RiskLevel, SourceType, VisibilityTier
from placentus import generative_ui as ui

st.set_page_config(
    page_title="Placentus — Engagement Intelligence",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# Global styling
# ----------------------------------------------------------------------------

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Geist:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'Geist', -apple-system, sans-serif;
}}
.stApp {{
    background-color: {ui.VOID};
}}
section[data-testid="stSidebar"] {{
    background-color: {ui.PANEL};
    border-right: 1px solid {ui.BORDER};
}}
h1, h2, h3 {{
    font-family: 'Fraunces', serif !important;
    color: {ui.INK} !important;
}}
p, div, span, label {{
    color: {ui.INK};
}}
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
}}
.stTabs [data-baseweb="tab"] {{
    background-color: {ui.PANEL};
    border-radius: 8px 8px 0 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.08em;
    color: {ui.MUTED};
}}
.stTabs [aria-selected="true"] {{
    color: {ui.TRUST} !important;
    border-bottom: 2px solid {ui.TRUST} !important;
}}
button[kind="secondary"], button[kind="primary"] {{
    border-radius: 8px !important;
}}
div[data-testid="stMetric"] {{
    background-color: {ui.PANEL};
    border: 1px solid {ui.BORDER};
    border-radius: 10px;
    padding: 12px 16px;
}}

/* Floating PM Agent launcher (SVG chat-bubble icon, bottom-right) */
.st-key-chat_fab {{
    position: fixed;
    bottom: 28px;
    right: 28px;
    z-index: 9999;
    width: 60px;
}}
.st-key-chat_fab button {{
    width: 60px !important;
    height: 60px !important;
    border-radius: 50% !important;
    background: {ui.TRUST} !important;
    border: none !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.45);
    padding: 0 !important;
}}
.st-key-chat_fab button p {{
    display: none;
}}
.st-key-chat_fab button::before {{
    content: "";
    display: block;
    width: 26px;
    height: 26px;
    margin: 0 auto;
    background-image: url("{ui.chat_fab_icon_data_uri()}");
    background-size: contain;
    background-repeat: no-repeat;
}}

/* Floating PM Agent chat popup */
.st-key-chat_panel {{
    position: fixed;
    bottom: 100px;
    right: 28px;
    width: 380px;
    max-height: 66vh;
    overflow-y: auto;
    background: {ui.PANEL};
    border: 1px solid {ui.BORDER};
    border-radius: 14px;
    padding: 16px 18px 8px 18px;
    z-index: 9998;
    box-shadow: 0 10px 40px rgba(0,0,0,0.55);
}}
.st-key-chat_panel button[kind="secondary"] {{
    border: none !important;
    background: transparent !important;
}}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Session state / store
# ----------------------------------------------------------------------------

if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_client" not in st.session_state:
    st.session_state.selected_client = None
if "selected_employee" not in st.session_state:
    st.session_state.selected_employee = None

@st.cache_resource
def load_store(api_key: str | None):
    return PlacentusStore(api_key=api_key or None)

store = load_store(st.session_state.api_key or None)

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------

st.markdown(f"""
<div style="display:flex;align-items:baseline;gap:14px;">
    <span style="font-family:'Fraunces',serif;font-size:32px;font-weight:700;color:{ui.INK};">Placentus</span>
    <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:{ui.MUTED};letter-spacing:0.15em;">
        ENGAGEMENT INTELLIGENCE · A SULCUS ARCHITECTURE PRODUCT
    </span>
</div>
<div style="font-family:'Geist',sans-serif;font-size:13.5px;color:{ui.MUTED};margin-top:4px;">
    Visibility into embedded consultants — sourced entirely from what they choose to share, never from client systems.
</div>
""", unsafe_allow_html=True)

st.markdown(ui.trust_line_header(), unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Sidebar — client selector
# ----------------------------------------------------------------------------

with st.sidebar:
    st.markdown(ui.section_label("Clients"), unsafe_allow_html=True)
    for client in store.clients.values():
        health = store.client_health(client.id)
        is_selected = st.session_state.selected_client == client.id
        st.markdown(ui.client_card(client.name, client.industry, health, is_selected), unsafe_allow_html=True)
        if st.button(f"View {client.name.split()[0]}", key=f"select_{client.id}", use_container_width=True):
            st.session_state.selected_client = client.id
            st.session_state.selected_employee = None
            st.rerun()

    st.markdown(ui.trust_line_header(), unsafe_allow_html=True)
    st.markdown(ui.section_label("Portfolio Snapshot"), unsafe_allow_html=True)
    tiers = store.tier_breakdown()
    st.markdown(ui.trust_ledger_row("Total events", str(store.total_events())), unsafe_allow_html=True)
    st.markdown(ui.trust_ledger_row("Standard visibility", str(tiers.get("standard", 0)), ui.TRUST), unsafe_allow_html=True)
    st.markdown(ui.trust_ledger_row("Restricted / archived", str(tiers.get("restricted", 0)), ui.AMBER), unsafe_allow_html=True)
    st.markdown(ui.trust_ledger_row("Escalated", str(tiers.get("escalate", 0)), ui.ALERT), unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Main area
# ----------------------------------------------------------------------------

if not st.session_state.selected_client:
    st.session_state.selected_client = list(store.clients.keys())[0]

client = store.clients[st.session_state.selected_client]
client_health = store.client_health(client.id)
employees = store.employees_for_client(client.id)

tab_overview, tab_employees, tab_calendar, tab_trust = st.tabs(
    ["Overview", "Employees", "Calendar", "Trust Ledger"]
)

# ---- OVERVIEW TAB ----
with tab_overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Account Health", client_health.risk_level.value.replace("_", " ").upper())
    c2.metric("Fellows on account", client_health.employee_count)
    c3.metric("At risk", client_health.at_risk_count)
    c4.metric("Open escalations", client_health.escalation_count)

    st.markdown(ui.section_label(f"{client.name} · {client.industry} · Account Manager: {client.account_manager}"), unsafe_allow_html=True)

    events = store.events_for_client(client.id)
    emp_names = {e.id: e.name for e in employees}
    for ev in events[:12]:
        st.markdown(ui.event_card(ev, emp_names.get(ev.employee_id, "Unknown")), unsafe_allow_html=True)

# ---- EMPLOYEES TAB ----
with tab_employees:
    st.markdown(ui.section_label("Fellows on this account — click to view detail"), unsafe_allow_html=True)
    cols = st.columns(2)
    for i, emp in enumerate(employees):
        health = store.employee_health(emp.id)
        with cols[i % 2]:
            st.markdown(ui.employee_card(emp.name, emp.role, emp.sprint_name, health), unsafe_allow_html=True)
            if st.button(f"View {emp.name}'s record", key=f"emp_{emp.id}", use_container_width=True):
                st.session_state.selected_employee = emp.id
                st.rerun()

    if st.session_state.selected_employee and st.session_state.selected_employee in {e.id for e in employees}:
        emp = store.employees[st.session_state.selected_employee]
        st.markdown(ui.trust_line_header(), unsafe_allow_html=True)
        st.markdown(f"### {emp.name}")
        st.caption(f"{emp.role} · {emp.sprint_name} · engaged since {emp.engagement_start}")
        emp_events = store.events_for_employee(emp.id)
        for ev in emp_events:
            st.markdown(ui.event_card(ev, emp.name), unsafe_allow_html=True)

# ---- CALENDAR TAB ----
with tab_calendar:
    st.markdown(ui.section_label(f"{client.name} — task calendar (color-coded by status)"), unsafe_allow_html=True)

    view_mode = st.radio("View", ["Month", "Week"], horizontal=True, label_visibility="collapsed")
    initial_view = "dayGridMonth" if view_mode == "Month" else "timeGridWeek"

    status_colors = {
        "on_track": "#1F8A5F",
        "at_risk": "#E07A2C",
        "blocked": ui.ALERT,
        "complete": ui.TRUST,
    }

    emp_names = {e.id: e.name for e in employees}
    tasks = store.tasks_for_client(client.id)
    cal_events = [
        {
            "title": f"{emp_names.get(t.employee_id, '')[:1]}. {t.title}",
            "start": t.date.isoformat(),
            "end": t.date.isoformat(),
            "color": status_colors.get(t.status.value, ui.MUTED),
        }
        for t in tasks
    ]

    st_calendar(
        events=cal_events,
        options={
            "initialView": initial_view,
            "initialDate": "2026-06-01",
            "height": 620,
            "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
        },
        custom_css=f"""
        .fc {{ background-color: {ui.PANEL}; border-radius: 10px; padding: 8px; }}
        .fc-toolbar-title {{ color: {ui.INK}; font-family: 'Fraunces', serif; }}
        .fc-col-header-cell {{ background-color: {ui.PANEL_RAISED}; color: {ui.MUTED}; }}
        .fc-daygrid-day, .fc-timegrid-slot {{ background-color: {ui.VOID}; }}
        .fc-daygrid-day-number, .fc-timegrid-slot-label {{ color: {ui.MUTED}; }}
        .fc-button {{ background-color: {ui.PANEL_RAISED} !important; border: 1px solid {ui.BORDER} !important; }}
        """,
        key=f"cal_{client.id}_{view_mode}",
    )

    legend_html = " &nbsp; ".join(
        f'<span style="color:{color};font-family:JetBrains Mono,monospace;font-size:10px;">● {label.replace("_"," ").upper()}</span>'
        for label, color in status_colors.items()
    )
    st.markdown(f'<div style="margin-top:10px;">{legend_html}</div>', unsafe_allow_html=True)

# ---- TRUST LEDGER TAB ----
with tab_trust:
    st.markdown(ui.section_label("How the categorization layer routed every event — nothing is deleted, only routed"), unsafe_allow_html=True)

    tiers = store.tier_breakdown()
    c1, c2, c3 = st.columns(3)
    c1.metric("Standard visibility", tiers.get("standard", 0))
    c2.metric("Restricted / archived", tiers.get("restricted", 0))
    c3.metric("Escalated (surfaced faster)", tiers.get("escalate", 0))

    st.markdown(ui.trust_line_header(), unsafe_allow_html=True)
    st.markdown(ui.section_label("Restricted & escalated events across the whole portfolio"), unsafe_allow_html=True)
    emp_names_all = {e.id: e.name for e in store.employees.values()}
    flagged = [e for e in store.events if e.tier != VisibilityTier.STANDARD]
    for ev in flagged:
        st.markdown(ui.event_card(ev, emp_names_all.get(ev.employee_id, "Unknown")), unsafe_allow_html=True)
        if ev.matches:
            reasons = ", ".join(f"`{m.category}`" for m in ev.matches)
            st.caption(f"Routed because: {reasons}")

# ----------------------------------------------------------------------------
# Floating PM agent chat — popup, scoped to the currently viewed client
# ----------------------------------------------------------------------------

with st.container(key="chat_fab"):
    if st.button(" ", key="chat_fab_btn", help="Open PM Agent"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()

if st.session_state.chat_open:
    with st.container(key="chat_panel"):
        head_col, close_col = st.columns([5, 1])
        with head_col:
            st.markdown(
                f'<div style="font-family:JetBrains Mono,monospace;font-size:11px;color:{ui.TRUST};'
                f'letter-spacing:0.1em;padding-top:6px;">SULCUS PM AGENT · {client.name.upper()}</div>',
                unsafe_allow_html=True,
            )
        with close_col:
            if st.button("✕", key="chat_close_btn"):
                st.session_state.chat_open = False
                st.rerun()
        st.caption(f"Grounded to {client.name} only — I won't answer about other client accounts.")

        if not st.session_state.api_key:
            st.session_state.api_key = st.text_input(
                "Anthropic API Key", value=st.session_state.api_key, type="password",
                placeholder="sk-ant-...", key="chat_api_key_input",
                help="Needed to power this chat. Used only for this session, nothing is stored.",
            )

        for role, text, evalr in st.session_state.chat_history[-8:]:
            with st.chat_message(role):
                st.write(text)
                if evalr is not None:
                    color = ui.TRUST if evalr.status == "PASSED" else (ui.AMBER if evalr.status == "WARNING" else ui.ALERT)
                    st.markdown(
                        f'<div style="font-family:JetBrains Mono,monospace;font-size:10px;color:{color};">'
                        f'Faithfulness {evalr.faithfulness_score:.2f} · {evalr.status} · '
                        f'{evalr.claims_grounded}/{evalr.claims_checked} claims grounded</div>',
                        unsafe_allow_html=True,
                    )

        with st.form(key="chat_form", clear_on_submit=True):
            prompt = st.text_input(
                "Message", placeholder=f"Ask about {client.name}'s Fellows...",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Send", use_container_width=True)

        if submitted and prompt:
            st.session_state.chat_history.append(("user", prompt, None))

            # Scoped strictly to the client currently open on the dashboard —
            # both in the context we feed the model and in the system prompt,
            # so a PM viewing one account can't pull data on another.
            client_events = store.events_for_client(client.id)
            client_emp_names = {e.id: e.name for e in employees}

            if not st.session_state.api_key:
                answer = "Enter an Anthropic API key above to enable the PM agent."
                evalr = None
            else:
                try:
                    import anthropic
                    client_sdk = anthropic.Anthropic(api_key=st.session_state.api_key)
                    context_text = "\n".join(
                        f"- [{client_emp_names.get(e.employee_id, 'Unknown')}] {e.display_text}"
                        for e in client_events[:40]
                    )
                    fellow_names = ", ".join(e.name for e in employees) or "none on this account"
                    system = (
                        "You are the Placentus PM agent for a staffing/consulting company. "
                        f"You are currently scoped to ONE client account: {client.name} "
                        f"({client.industry}). The only Fellows you may discuss are: {fellow_names}. "
                        "Answer questions using ONLY the context events provided below, which "
                        "already belong to this account. If asked about any other client, "
                        "another company, or a person not in the list above, politely decline "
                        "and say you're scoped to this account only. Be concise and direct. If "
                        "the answer isn't in the context, say so plainly rather than guessing.\n\n"
                        f"CONTEXT EVENTS ({client.name} only):\n{context_text}"
                    )
                    resp = client_sdk.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=500,
                        system=system,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    answer = "".join(b.text for b in resp.content if hasattr(b, "text"))
                    evalr = evaluate_answer(answer, client_events)
                    if evalr.status == "BLOCKED":
                        answer = (
                            "I couldn't ground a confident answer to that in this account's event "
                            "log, so I'm not going to guess. Try asking about a specific Fellow on "
                            f"{client.name} by name."
                        )
                except Exception as exc:
                    answer = f"Agent error: {exc}"
                    evalr = None

            st.session_state.chat_history.append(("assistant", answer, evalr))
            st.rerun()
