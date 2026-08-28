import pandas as pd
import streamlit as st

from components.metrics import render_kpi_card
from components.status_cards import (
    render_ai_advisory,
    render_page_header,
    render_recommendation,
    render_section_header,
)
from services.backend_client import load_dashboard_snapshot


snapshot = load_dashboard_snapshot()
reports = snapshot.reports
latest_report = reports[0]

render_page_header(
    title="AI field reports",
    subtitle=(
        "Gemini explains the deterministic drought score using saved sensor "
        "measurements and Open-Meteo forecast conditions."
    ),
    source=(
        "Gemini reports from live data"
        if snapshot.reports_live
        else "Gemini demonstration report"
    ),
    eyebrow="Decision support",
)
st.caption(snapshot.source_details)

confidence = latest_report.get("confidence", "low")
confidence_display = (
    f"{confidence}%" if isinstance(confidence, int) else str(confidence).title()
)
risk_score = latest_report.get("risk_score")
generated_at = pd.Timestamp(latest_report["created_at"])

metric_columns = st.columns(4, gap="large")
with metric_columns[0]:
    render_kpi_card(
        "Current assessment",
        str(latest_report["risk_level"]).title(),
        "",
        "Risk level remains controlled by backend rules",
        "negative" if latest_report["risk_level"] in {"high", "critical"} else "neutral",
        "AI",
    )
with metric_columns[1]:
    render_kpi_card(
        "Risk score",
        f"{float(risk_score):.1f}" if risk_score is not None else "N/A",
        "/100" if risk_score is not None else "",
        "Deterministic weighted calculation",
        "negative" if risk_score is not None and float(risk_score) >= 50 else "neutral",
        "RISK",
    )
with metric_columns[2]:
    render_kpi_card(
        "Gemini confidence",
        confidence_display,
        "",
        "Structured assessment confidence",
        "positive" if str(confidence).lower() in {"high", "90", "91", "94"} else "neutral",
        "CONF",
    )
with metric_columns[3]:
    render_kpi_card(
        "Generated",
        generated_at.strftime("%H:%M"),
        "UTC",
        generated_at.strftime("%d %b %Y"),
        "neutral",
        "TIME",
    )

st.write("")
render_ai_advisory(
    title=str(latest_report["title"]),
    explanation=str(latest_report["explanation"]),
    risk_level=str(latest_report["risk_level"]),
    confidence=confidence,
)

st.write("")
driver_column, factor_column = st.columns(2, gap="large")
with driver_column:
    with st.container(border=True):
        render_section_header("Why this risk was assigned", "Gemini drivers")
        drivers = list(latest_report.get("drivers", []))
        if drivers:
            for driver in drivers:
                st.markdown(f"- {driver}")
        else:
            st.caption("No structured drivers are available for this report.")

with factor_column:
    with st.container(border=True):
        render_section_header("Auditable risk factors", "Backend calculation")
        factors = dict(latest_report.get("risk_factors", {}))
        if factors:
            factor_frame = pd.DataFrame(
                [
                    {
                        "Factor": key.replace("_", " ").title(),
                        "Stress score": f"{float(value):.1f}/100",
                    }
                    for key, value in factors.items()
                ]
            )
            st.dataframe(factor_frame, hide_index=True, width="stretch")
        else:
            st.caption("No saved factor breakdown is available for this report.")

st.write("")
render_section_header("Recommended actions", "Prioritised response")
recommendations = list(latest_report.get("recommendations", []))
if recommendations:
    recommendation_columns = st.columns(len(recommendations), gap="large")
    for index, recommendation in enumerate(recommendations, start=1):
        with recommendation_columns[index - 1]:
            render_recommendation(index, str(recommendation))
else:
    st.caption("No recommendations are available for this assessment.")

st.write("")
with st.container(border=True):
    render_section_header("Report history", "Saved Gemini assessments")

    for report in reports:
        report_time = pd.Timestamp(report["created_at"])
        report_confidence = report.get("confidence", "low")
        label = (
            f"{report_time.strftime('%d %b %Y · %H:%M UTC')} · "
            f"{str(report['risk_level']).title()} risk · "
            f"{str(report_confidence).title()} confidence"
        )
        with st.expander(label):
            st.markdown(f"**{report['title']}**")
            st.write(report["explanation"])
            report_drivers = list(report.get("drivers", []))
            if report_drivers:
                st.markdown("**Main drivers**")
                for driver in report_drivers:
                    st.markdown(f"- {driver}")
            st.markdown("**Recommended actions**")
            for recommendation in report.get("recommendations", []):
                st.markdown(f"- {recommendation}")

st.caption(
    "Gemini explains and recommends actions. The deterministic backend score "
    "remains authoritative for drought risk and critical alerts."
)
