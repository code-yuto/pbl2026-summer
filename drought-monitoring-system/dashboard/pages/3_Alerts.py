import pandas as pd
import streamlit as st

from components.charts import PLOTLY_CONFIG, daily_alert_chart
from components.metrics import render_kpi_card
from components.status_cards import (
    render_alert_row,
    render_page_header,
    render_section_header,
)
from services.backend_client import load_dashboard_snapshot


snapshot = load_dashboard_snapshot(
    base_url=st.session_state.get("backend_url")
)
alerts = snapshot.alerts.copy()

render_page_header(
    title="Alert center",
    subtitle=(
        "Review current-session rule-based warnings and recent field events "
        "without waiting for the LLM response path."
    ),
    source=snapshot.source,
    eyebrow="Operational response",
)

critical_count = int((alerts["risk_level"] == "critical").sum()) if not alerts.empty else 0
high_count = int((alerts["risk_level"] == "high").sum()) if not alerts.empty else 0
delivery_rate = (
    float((alerts["status"] == "Delivered").mean() * 100)
    if not alerts.empty
    else 100.0
)

kpi_columns = st.columns(4, gap="large")
with kpi_columns[0]:
    render_kpi_card(
        "Total alerts",
        str(len(alerts)),
        "",
        "Current retained alert history",
        "neutral",
        "ALL",
    )
with kpi_columns[1]:
    render_kpi_card(
        "Critical",
        str(critical_count),
        "",
        "Immediate action required",
        "negative" if critical_count else "positive",
        "CRT",
    )
with kpi_columns[2]:
    render_kpi_card(
        "High risk",
        str(high_count),
        "",
        "Close monitoring required",
        "negative" if high_count else "positive",
        "HIGH",
    )
with kpi_columns[3]:
    render_kpi_card(
        "Delivery rate",
        f"{delivery_rate:.0f}",
        "%",
        "LINE API request status",
        "positive" if delivery_rate >= 95 else "negative",
        "API",
    )

st.write("")
chart_column, log_column = st.columns([1, 1.45], gap="large")

with chart_column:
    with st.container(border=True):
        render_section_header("Alert frequency", "Daily volume")
        st.plotly_chart(
            daily_alert_chart(alerts),
            width="stretch",
            config=PLOTLY_CONFIG,
        )

with log_column:
    with st.container(border=True):
        render_section_header("Notification log", "Most recent first")
        selected_levels = st.multiselect(
            "Risk level",
            ["critical", "high", "medium"],
            default=["critical", "high", "medium"],
            format_func=str.title,
        )

        filtered = alerts.loc[alerts["risk_level"].isin(selected_levels)]
        if filtered.empty:
            st.caption("No alerts match the selected risk levels.")
        else:
            for _, alert in filtered.iloc[::-1].iterrows():
                render_alert_row(
                    risk_level=str(alert["risk_level"]),
                    message=str(alert["message"]),
                    created_at=pd.Timestamp(alert["created_at"]).to_pydatetime(),
                    status=str(alert["status"]),
                )

st.write("")
with st.container(border=True):
    render_section_header("Alert policy", "Current prototype rules")
    policy_columns = st.columns(3, gap="large")
    with policy_columns[0]:
        st.markdown("**Immediate path**")
        st.caption("Critical thresholds trigger LINE before Gemini analysis.")
    with policy_columns[1]:
        st.markdown("**Cooldown**")
        st.caption("Repeated alerts are grouped to prevent message fatigue.")
    with policy_columns[2]:
        st.markdown("**Recovery**")
        st.caption("A recovery notice is sent when readings return to normal.")
