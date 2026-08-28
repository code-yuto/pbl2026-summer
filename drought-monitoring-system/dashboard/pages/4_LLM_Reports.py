import httpx
import pandas as pd
import streamlit as st

from components.metrics import render_kpi_card
from components.status_cards import (
    render_ai_advisory,
    render_page_header,
    render_recommendation,
    render_section_header,
)
from services.backend_client import BackendClient, load_dashboard_snapshot


backend_url = st.session_state.get("backend_url")
snapshot = load_dashboard_snapshot(base_url=backend_url)
reports = snapshot.reports
client = BackendClient(base_url=backend_url)

render_page_header(
    title="Forecast AI chat",
    subtitle=(
        "Explore saved drought forecasts and ask Gemini to explain the exact "
        "live sensor, Open-Meteo and calculated risk values in this session."
    ),
    source=(
        "Live sensor + Open-Meteo + Gemini"
        if snapshot.reports_live
        else "Waiting for a live assessment"
    ),
    eyebrow="Grounded decision support",
)
st.caption(snapshot.source_details)

status_column, action_column = st.columns([1.6, 1], gap="large")
with status_column:
    if snapshot.backend_online and snapshot.reports_live:
        st.success(
            "FastAPI is connected. Forecast reports and chat context are "
            "available in the current live session."
        )
    elif snapshot.backend_online and snapshot.history_live:
        st.warning(
            "Sensor data is connected, but no saved drought assessment is "
            "available yet. Generate one from the latest sensor reading."
        )
    else:
        st.warning(
            "The FastAPI ngrok URL is not returning live session data. "
            "Check the URL in the sidebar, then select Connect and refresh."
        )

with action_column:
    generate_disabled = not (
        snapshot.backend_online and snapshot.history_live
    )
    if st.button(
        "Generate latest forecast",
        icon=":material/refresh:",
        width="stretch",
        disabled=generate_disabled,
        help=(
            "Uses the newest in-memory sensor reading, fetches Open-Meteo, "
            "calculates risk, asks Gemini and keeps the linked forecast for "
            "the current FastAPI session."
        ),
    ):
        try:
            with st.spinner("Generating and saving the forecast..."):
                client.analyze_latest()
            st.cache_data.clear()
            st.success("The new forecast is available in this session.")
            st.rerun()
        except (httpx.HTTPError, ValueError, KeyError) as error:
            st.error(f"Forecast generation failed: {error}")

if not reports:
    st.info(
        "No live forecast exists yet. Send a sensor reading first, then select "
        "Generate latest forecast. Nothing is loaded from dummy data."
    )
    st.stop()

selected_index = st.selectbox(
    "Forecast used by the dashboard and chat",
    options=list(range(len(reports))),
    format_func=lambda index: (
        f"{pd.Timestamp(reports[index]['created_at']).strftime('%d %b %Y, %H:%M UTC')}"
        f" · {str(reports[index]['risk_level']).title()} risk"
        f" · score {float(reports[index].get('risk_score', 0)):.1f}/100"
    ),
    help="Choose a current-session assessment for Gemini to explain.",
)
selected_report = reports[selected_index]

confidence = selected_report.get("confidence", "low")
confidence_display = (
    f"{confidence}%" if isinstance(confidence, int) else str(confidence).title()
)
risk_score = selected_report.get("risk_score")
generated_at = pd.Timestamp(selected_report["created_at"])

metric_columns = st.columns(4, gap="large")
with metric_columns[0]:
    render_kpi_card(
        "Selected assessment",
        str(selected_report["risk_level"]).title(),
        "",
        "Risk level remains controlled by backend rules",
        (
            "negative"
            if selected_report["risk_level"] in {"high", "critical"}
            else "neutral"
        ),
        "AI",
    )
with metric_columns[1]:
    render_kpi_card(
        "Risk score",
        f"{float(risk_score):.1f}" if risk_score is not None else "N/A",
        "/100" if risk_score is not None else "",
        "Deterministic weighted calculation",
        (
            "negative"
            if risk_score is not None and float(risk_score) >= 50
            else "neutral"
        ),
        "RISK",
    )
with metric_columns[2]:
    render_kpi_card(
        "Gemini confidence",
        confidence_display,
        "",
        "Structured assessment confidence",
        (
            "positive"
            if str(confidence).lower() in {"high", "90", "91", "94"}
            else "neutral"
        ),
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
    title=str(selected_report["title"]),
    explanation=str(selected_report["explanation"]),
    risk_level=str(selected_report["risk_level"]),
    confidence=confidence,
)

st.write("")
driver_column, factor_column = st.columns(2, gap="large")
with driver_column:
    with st.container(border=True):
        render_section_header("Why this risk was assigned", "Gemini drivers")
        drivers = list(selected_report.get("drivers", []))
        if drivers:
            for driver in drivers:
                st.markdown(f"- {driver}")
        else:
            st.caption("No structured drivers are available for this report.")

with factor_column:
    with st.container(border=True):
        render_section_header("Auditable risk factors", "Backend calculation")
        factors = dict(selected_report.get("risk_factors", {}))
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
recommendations = list(selected_report.get("recommendations", []))
if recommendations:
    recommendation_columns = st.columns(len(recommendations), gap="large")
    for index, recommendation in enumerate(recommendations, start=1):
        with recommendation_columns[index - 1]:
            render_recommendation(index, str(recommendation))
else:
    st.caption("No recommendations are available for this assessment.")

st.write("")
with st.container(border=True):
    render_section_header(
        "Ask about this forecast",
        "Gemini chat grounded in live sensor and weather values",
    )
    st.caption(
        "The assistant receives only the selected ESP32 reading, Open-Meteo "
        "snapshot and deterministic assessment. It cannot silently change "
        "the risk score."
    )

    assessment_id = selected_report.get("id")
    chat_enabled = snapshot.reports_live and isinstance(assessment_id, int)
    thread_key = str(assessment_id) if chat_enabled else "unavailable"
    threads = st.session_state.setdefault("forecast_chat_threads", {})
    messages = threads.setdefault(thread_key, [])

    suggestion_columns = st.columns(3, gap="small")
    suggestions = [
        "Why is this drought risk level assigned?",
        "What does the seven-day rain forecast mean?",
        "What actions should the farmer take first?",
    ]
    suggested_question = None
    for index, suggestion in enumerate(suggestions):
        with suggestion_columns[index]:
            if st.button(
                suggestion,
                key=f"forecast_suggestion_{thread_key}_{index}",
                width="stretch",
                disabled=not chat_enabled,
            ):
                suggested_question = suggestion

    if messages:
        clear_column, _ = st.columns([1, 4])
        with clear_column:
            if st.button(
                "Clear chat",
                key=f"clear_forecast_chat_{thread_key}",
            ):
                threads[thread_key] = []
                st.rerun()

    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    typed_question = st.chat_input(
        "Ask Gemini to explain this saved forecast...",
        disabled=not chat_enabled,
    )
    question = typed_question or suggested_question

    if not chat_enabled:
        st.info(
            "Connect the FastAPI URL and generate a live assessment before "
            "using chat."
        )
    elif question:
        history = [
            {"role": item["role"], "content": item["content"]}
            for item in messages[-8:]
        ]
        messages.append({"role": "user", "content": question})
        try:
            with st.spinner("Gemini is reading the selected live forecast..."):
                response = client.ask_forecast(
                    question=question,
                    assessment_id=assessment_id,
                    history=history,
                )
            messages.append(
                {"role": "assistant", "content": str(response["answer"])}
            )
        except (httpx.HTTPError, ValueError, KeyError) as error:
            messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "I could not reach the forecast chat service. Check "
                        f"the ngrok URL and Gemini API key. Details: {error}"
                    ),
                }
            )
        st.rerun()

st.write("")
with st.container(border=True):
    render_section_header("Report history", "Current FastAPI session")

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
