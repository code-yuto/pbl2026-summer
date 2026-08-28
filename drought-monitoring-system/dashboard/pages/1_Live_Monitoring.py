import pandas as pd
import streamlit as st

from components.charts import (
    PLOTLY_CONFIG,
    risk_distribution_chart,
    soil_moisture_chart,
    water_level_chart,
    weather_forecast_chart,
)
from components.metrics import (
    percentage_change,
    render_kpi_card,
    signed_trend,
)
from components.status_cards import (
    render_ai_advisory,
    render_alert_row,
    render_page_header,
    render_section_header,
    render_status_banner,
)
from services.backend_client import load_dashboard_snapshot


def number_or_none(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if pd.isna(number) else number


def display_value(value, suffix: str = "") -> str:
    number = number_or_none(value)
    if number is not None:
        return f"{number:.1f}{suffix}"
    if value is None or pd.isna(value):
        return "Not recorded"
    return f"{value}{suffix}"


snapshot = load_dashboard_snapshot()
history = snapshot.history.copy()
latest = history.iloc[-1]
comparison = history.iloc[-25] if len(history) > 24 else history.iloc[0]

render_page_header(
    title="Field overview",
    subtitle=(
        "A unified view of sensor readings, Open-Meteo conditions and the "
        "latest Gemini drought explanation."
    ),
    source=snapshot.source,
    eyebrow="Live operations",
)
st.caption(snapshot.source_details)

updated_at = pd.Timestamp(latest["created_at"]).to_pydatetime()
render_status_banner(str(latest["risk_level"]), updated_at)

soil_change = percentage_change(
    float(latest["soil_moisture"]),
    float(comparison["soil_moisture"]),
)
water_change = percentage_change(
    float(latest["water_level"]),
    float(comparison["water_level"]),
)
latest_temperature = number_or_none(latest.get("temperature"))
comparison_temperature = number_or_none(comparison.get("temperature"))
if latest_temperature is None and snapshot.weather_live:
    latest_temperature = number_or_none(
        snapshot.weather.iloc[-1].get("temperature_c")
    )
temperature_change = (
    latest_temperature - comparison_temperature
    if latest_temperature is not None and comparison_temperature is not None
    else None
)
recent_alerts = (
    snapshot.alerts[
        snapshot.alerts["created_at"]
        >= history["created_at"].max() - pd.Timedelta(hours=24)
    ]
    if not snapshot.alerts.empty
    else snapshot.alerts
)

kpi_columns = st.columns(4, gap="large")
with kpi_columns[0]:
    render_kpi_card(
        "Soil moisture",
        f"{float(latest['soil_moisture']):.1f}",
        "%",
        signed_trend(soil_change, "over 24h"),
        "positive" if soil_change >= 0 else "negative",
        "SM",
    )
with kpi_columns[1]:
    render_kpi_card(
        "Water reserve",
        f"{float(latest['water_level']):.1f}",
        "%",
        signed_trend(water_change, "over 24h"),
        "positive" if water_change >= 0 else "negative",
        "WL",
    )
with kpi_columns[2]:
    render_kpi_card(
        "Air temperature",
        f"{latest_temperature:.1f}" if latest_temperature is not None else "N/A",
        "°C" if latest_temperature is not None else "",
        (
            f"{'↗' if temperature_change > 0 else '↘'} "
            f"{abs(temperature_change):.1f}°C over 24h"
            if temperature_change is not None
            else "Awaiting a matched weather snapshot"
        ),
        "negative" if temperature_change is not None and temperature_change > 0 else "neutral",
        "TMP",
    )
with kpi_columns[3]:
    render_kpi_card(
        "Active risk",
        str(latest["risk_level"]).title(),
        "",
        f"{len(recent_alerts)} operational alerts in 24h",
        "negative" if str(latest["risk_level"]) in {"high", "critical"} else "neutral",
        "RSK",
    )

st.write("")
with st.container(border=True):
    render_section_header("Latest input data", snapshot.source_details)
    sensor_column, weather_column = st.columns(2, gap="large")

    with sensor_column:
        st.markdown("**Physical sensors and ESP32 metadata**")
        sensor_rows = [
            {"Variable": "Soil moisture", "Value": display_value(latest.get("soil_moisture"), "%"), "Source": "Calibrated sensor"},
            {"Variable": "Soil moisture raw", "Value": display_value(latest.get("soil_moisture_raw")), "Source": "ESP32 ADC"},
            {"Variable": "Water level", "Value": display_value(latest.get("water_level"), "%"), "Source": "Calibrated sensor"},
            {"Variable": "Water level raw", "Value": display_value(latest.get("water_level_raw")), "Source": "ESP32 ADC"},
            {"Variable": "Device status", "Value": display_value(latest.get("message_type")), "Source": "ESP32 rules"},
            {"Variable": "LED colour", "Value": display_value(latest.get("led_color")), "Source": "ESP32"},
            {"Variable": "Device uptime", "Value": display_value(latest.get("device_timestamp_ms"), " ms"), "Source": "ESP32"},
        ]
        st.dataframe(pd.DataFrame(sensor_rows), hide_index=True, width="stretch")

    with weather_column:
        st.markdown("**Weather and forecast inputs**")
        if snapshot.weather_live:
            weather_latest = snapshot.weather.iloc[-1]
            weather_rows = [
                {"Variable": "Temperature", "Value": display_value(weather_latest.get("temperature_c"), "°C"), "Source": "Open-Meteo"},
                {"Variable": "Humidity", "Value": display_value(weather_latest.get("humidity_percent"), "%"), "Source": "Open-Meteo"},
                {"Variable": "Current precipitation", "Value": display_value(weather_latest.get("precipitation_mm"), " mm"), "Source": "Open-Meteo"},
                {"Variable": "Rain, previous 7 days", "Value": display_value(weather_latest.get("recent_precipitation_7d_mm"), " mm"), "Source": "Open-Meteo"},
                {"Variable": "Rain forecast, 3 days", "Value": display_value(weather_latest.get("forecast_precipitation_3d_mm"), " mm"), "Source": "Open-Meteo"},
                {"Variable": "Rain forecast, 7 days", "Value": display_value(weather_latest.get("forecast_precipitation_7d_mm"), " mm"), "Source": "Open-Meteo"},
                {"Variable": "Evapotranspiration today", "Value": display_value(weather_latest.get("evapotranspiration_mm"), " mm"), "Source": "Open-Meteo"},
                {"Variable": "ET0 forecast, 7 days", "Value": display_value(weather_latest.get("forecast_evapotranspiration_7d_mm"), " mm"), "Source": "Open-Meteo"},
            ]
        else:
            weather_rows = [
                {"Variable": "Weather feed", "Value": "No live snapshot", "Source": "Demo fallback active"}
            ]
        st.dataframe(pd.DataFrame(weather_rows), hide_index=True, width="stretch")

st.write("")
top_left, top_right = st.columns([1.75, 1], gap="large")

with top_left:
    with st.container(border=True):
        render_section_header("Soil moisture movement", "Seven-day trend")
        st.plotly_chart(
            soil_moisture_chart(history.tail(24 * 7)),
            width="stretch",
            config=PLOTLY_CONFIG,
        )

with top_right:
    with st.container(border=True):
        render_section_header("Risk profile", "Reading distribution")
        st.plotly_chart(
            risk_distribution_chart(history.tail(24 * 7)["risk_level"]),
            width="stretch",
            config=PLOTLY_CONFIG,
        )

bottom_left, bottom_right = st.columns([1.25, 1], gap="large")

with bottom_left:
    with st.container(border=True):
        render_section_header("Water reserve", "Seven-day trend")
        st.plotly_chart(
            water_level_chart(history.tail(24 * 7)),
            width="stretch",
            config=PLOTLY_CONFIG,
        )

with bottom_right:
    with st.container(border=True):
        render_section_header(
            "Weather pressure",
            "Live Open-Meteo snapshots" if snapshot.weather_live else "Demo preview",
        )
        st.plotly_chart(
            weather_forecast_chart(snapshot.weather),
            width="stretch",
            config=PLOTLY_CONFIG,
        )

st.write("")
latest_report = snapshot.reports[0]
with st.container(border=True):
    render_section_header(
        "Gemini drought explanation",
        "Saved live assessment" if snapshot.reports_live else "Demo explanation",
    )
    render_ai_advisory(
        title=str(latest_report["title"]),
        explanation=str(latest_report["explanation"]),
        risk_level=str(latest_report["risk_level"]),
        confidence=latest_report.get("confidence", "low"),
    )
    driver_column, action_column = st.columns(2, gap="large")
    with driver_column:
        st.markdown("**Main drought drivers**")
        for driver in latest_report.get("drivers", []):
            st.markdown(f"- {driver}")
    with action_column:
        st.markdown("**Recommended actions**")
        for recommendation in latest_report.get("recommendations", []):
            st.markdown(f"- {recommendation}")

st.write("")
with st.container(border=True):
    render_section_header("Recent alert activity", "ESP32 and LINE status")

    if snapshot.alerts.empty:
        st.caption("No alerts have been generated for the selected period.")
    else:
        for _, alert in snapshot.alerts.tail(5).iloc[::-1].iterrows():
            render_alert_row(
                risk_level=str(alert["risk_level"]),
                message=str(alert["message"]),
                created_at=pd.Timestamp(alert["created_at"]).to_pydatetime(),
                status=str(alert["status"]),
            )
