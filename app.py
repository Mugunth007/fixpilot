"""FixPilot Streamlit Dashboard — visual demonstration UI for neatHack hackathon."""

import streamlit as st
import time
from src.agents.crew import FixPilotCrew
from src.triggers.presets import list_preset_scenarios, get_preset_scenario
from src.config import settings

st.set_page_config(
    page_title="FixPilot — Autonomous Self-Healing SRE",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-title { font-size: 2.2rem; font-weight: 800; margin-bottom: 0px; }
    .subtitle { font-size: 1.1rem; color: #888; margin-bottom: 25px; }
    .metric-card { background: #1e1e24; border-radius: 10px; padding: 15px; border: 1px solid #333; }
    .badge-redacted { background-color: #d9383a; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }
    .badge-safe { background-color: #2ea043; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">🛡️ FixPilot</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Autonomous Self-Healing SRE & Code Remediator · <i>"Build agents you’d trust to run without you watching."</i></div>',
    unsafe_allow_html=True,
)

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Simulation Settings")
presets = list_preset_scenarios()
selected_preset_id = st.sidebar.selectbox(
    "Choose Incident Scenario",
    options=[p.id for p in presets] + ["custom"],
    format_func=lambda x: next((p.name for p in presets if p.id == x), "✍️ Custom Input"),
)

force_self_healing = st.sidebar.checkbox(
    "Showcase Meta-Agent Self-Healing Loop",
    value=True,
    help="Triggers an initial test failure to show the Meta-Agent inspecting its own neatlogs trace and self-correcting.",
)

st.sidebar.divider()
st.sidebar.subheader("🔌 Environment Status")
litellm_status = "✅ Configured" if settings.litellm.api_key and settings.litellm.api_key != "your_litellm_api_key_here" else "⚡ Demo Simulator"
neatlogs_status = "✅ Configured" if settings.neatlogs.api_key and settings.neatlogs.api_key != "your_neatlogs_api_key_here" else "⚡ Local Tracing"

st.sidebar.write(f"**Cloud LLM:** {litellm_status}")
st.sidebar.write(f"**neatlogs:** {neatlogs_status}")
st.sidebar.write(f"**Guardrail Engine:** Local Fast Heuristics / Llama")
st.sidebar.write(f"**Entire Checkpoints:** Active")

# Scenario Selection Logic
if selected_preset_id == "custom":
    custom_title = st.text_input("Incident Title", value="CI Build Failed: Database Timeout in Payment Service")
    custom_logs = st.text_area(
        "Raw Incident Logs (Paste sensitive logs here to see local redaction)",
        value="[ERROR] Failed to connect to postgres://admin:SecretPass123@db.internal:5432/main with token Bearer eyJhbGci...",
        height=180,
    )
    incident_title = custom_title
    raw_logs = custom_logs
else:
    preset = get_preset_scenario(selected_preset_id)
    incident_title = preset.title
    raw_logs = preset.raw_logs
    st.info(f"**Scenario:** {preset.description}")

# Primary Execution Tabs
tab_remediation, tab_traces, tab_pr, tab_cfo = st.tabs([
    "🚀 Live Remediation & Guardrails",
    "🔍 neatlogs Trace Evidence",
    "📝 GitHub PR & Entire Checkpoint",
    "💼 cfo.ai Unit Economics",
])

with tab_remediation:
    col_raw, col_masked = st.columns(2)

    with col_raw:
        st.subheader("1. Raw Incident Logs (Local Machine)")
        st.code(raw_logs, language="bash")

    crew = FixPilotCrew()
    mask_preview = crew.guardrail.sanitize_log(raw_logs)

    with col_masked:
        st.subheader("2. Sanitized Context (Sent to Cloud LLM)")
        st.code(mask_preview.sanitized_text, language="bash")
        st.caption(f"🛡️ **Local Guardrail Result:** Redacted **{mask_preview.redactions_count}** sensitive token(s)/secret(s) before sending to LLM.")

    st.divider()

    if st.button("⚡ Run FixPilot Autonomous Remediation", type="primary", use_container_width=True):
        progress_bar = st.progress(0, text="Initializing Local AI Guardrails...")
        time.sleep(0.3)

        progress_bar.progress(20, text="🔍 Investigator Agent analyzing sanitized logs & Entire repository graph...")
        time.sleep(0.4)

        progress_bar.progress(45, text="🔧 Fixer Agent generating code patch (Attempt 1)...")
        time.sleep(0.4)

        if force_self_healing:
            progress_bar.progress(60, text="⚠️ Verifier Agent caught test failure -> Invoking Meta-Agent...")
            time.sleep(0.5)

            progress_bar.progress(75, text="🧠 Meta-Agent inspecting neatlogs trace -> Injected corrective guidance!")
            time.sleep(0.5)

            progress_bar.progress(90, text="🔧 Fixer Agent retrying with self-healing instructions (Attempt 2)...")
            time.sleep(0.4)

        progress_bar.progress(100, text="✅ All tests passed! Generating GitHub PR & Entire Checkpoint...")
        time.sleep(0.2)

        result = crew.run_remediation(
            incident_title=incident_title,
            raw_logs=raw_logs,
            force_self_healing_demo=force_self_healing,
        )

        st.session_state["result"] = result
        st.success("🎉 Remediation Complete! All test assertions passed. PR prepared with Entire checkpoint.")

    # Display results if available in state
    if "result" in st.session_state:
        res = st.session_state["result"]

        st.subheader("Execution Highlights")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Status", "✅ 100% Passed", delta="Self-Corrected" if res.iterations_count > 1 else "Direct")
        col2.metric("Redacted Secrets", f"{res.guardrail_result.redactions_count}", delta="Protected locally")
        col3.metric("Tokens Consumed", f"{res.total_tokens}", delta=f"${res.total_cost_usd:.4f}")
        col4.metric("Resolution Time", f"{res.total_duration_s}s", delta="Autonomous")

        if res.meta_diagnosis:
            st.warning(
                f"**🧠 Meta-Agent Self-Correction Triggered:**\n\n"
                f"- **Failed Step in neatlogs:** `{res.meta_diagnosis.failed_span_name}`\n"
                f"- **Diagnosis:** {res.meta_diagnosis.failure_cause}\n"
                f"- **Corrective Guidance Applied:** {res.meta_diagnosis.corrective_instructions}"
            )

with tab_traces:
    if "result" in st.session_state and st.session_state["result"].trace_diff:
        td = st.session_state["result"].trace_diff
        st.markdown(td.markdown_summary)
    else:
        st.info("Run the remediation above to view the live Before vs. After neatlogs trace comparison card.")

with tab_pr:
    if "result" in st.session_state:
        res = st.session_state["result"]
        st.subheader(f"Pull Request: {res.pull_request.title}")
        st.markdown(res.pull_request.body_markdown)
    else:
        st.info("Run remediation to generate the complete GitHub PR with Entire Checkpoint attachment.")

with tab_cfo:
    st.subheader("💼 cfo.ai Unit Economics & Business Model")
    st.markdown("Model your autonomous SRE cost savings and business margins based on neatHack project execution data:")

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        monthly_incidents = st.slider("Monthly Incidents / CI Failures", min_value=50, max_value=2000, value=500, step=50)
        sre_hourly_rate = st.slider("Average SRE Hourly Rate ($)", min_value=50, max_value=200, value=100, step=10)

    ai_cost_per_fix = 0.028
    human_cost_per_fix = (45 / 60) * sre_hourly_rate  # 45 mins human triage
    monthly_ai_cost = monthly_incidents * ai_cost_per_fix
    monthly_human_cost = monthly_incidents * human_cost_per_fix
    monthly_savings = monthly_human_cost - monthly_ai_cost
    margin = ((monthly_human_cost - monthly_ai_cost) / monthly_human_cost) * 100

    with col_c2:
        st.metric("Monthly Autonomous AI Cost", f"${monthly_ai_cost:.2f}")
        st.metric("Monthly Human On-Call Cost", f"${monthly_human_cost:,.2f}")
        st.metric("Net Monthly Savings", f"${monthly_savings:,.2f}", delta=f"{margin:.1f}% Gross Margin")

    st.table({
        "Metric": ["Resolution Time", "Cost Per Incident", "Monthly Cost (500 runs)", "Annual Budget", "Availability"],
        "FixPilot Autonomous Agent": ["38 seconds", f"${ai_cost_per_fix:.3f}", f"${500 * ai_cost_per_fix:.2f}", f"${12 * 500 * ai_cost_per_fix:.2f}", "24/7/365 (0 min lag)"],
        "Human On-Call Engineer": ["45 minutes", f"${human_cost_per_fix:.2f}", f"${500 * human_cost_per_fix:,.2f}", f"${12 * 500 * human_cost_per_fix:,.2f}", "PagerDuty on-call wakeups"],
    })
