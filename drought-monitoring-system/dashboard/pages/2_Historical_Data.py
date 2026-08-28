import pandas as pd
import streamlit as st

from components.charts import (
    PLOTLY_CONFIG,
    combined_environment_chart,
    risk_distribution_chart,
    soil_moisture_chart,
    water_level_chart,
)
from components.metrics import render_kpi_card
from components.status_cards import render_page_header, render_section_header
from services.backend_client import load_dashboard_snapshot


snapshot = load_dashboard_snapshot()
history = snapshot.history.copy()

render_page_header(
    title="Historical analytics",
    subtitle=(
        "Explore long-term sensor movement, environmental relationships and "
        "risk distribution using a consistent time window."
    ),
    source=snapshot.source,
    eyebrow="Trend analysis",
)

control_columns = st.columns([1, 1, 1.5], gap="large")
with control_columns[0]:
    selected_range = st.selectbox(
        "Time window",
        ["Last 24 hours", "Last 7 days", "Last 30 days", "All available data"],
        index=2,
    )
with control_columns[1]:
    selected_device = st.selectbox(
        "Device",
        sorted(history["device_id"].dropna().unique().tolist()),
    )
with control_columns[2]:
    st.caption("Export the filtered dataset for further analysis or reporting.")

range_hours = {
    "Last 24 hours": 24,
    "Last 7 days": 24 * 7,
    "Last 30 days": 24 * 30,
}

filtered = history.loc[history["device_id"] == selected_device].copy()
if selected_range in range_hours:
    cutoff = filtered["created_at"].max() - pd.Timedelta(
        hours=range_hours[selected_range]
    )
    filtered = filtered.loc[filtered["created_at"] >= cutoff]

csv_data = filtered.to_csv(index=False).encode("utf-8")
with control_columns[2]:
    st.download_button(
        "Download filtered CSV",
        data=csv_data,
        file_name="terrapulse_historical_data.csv",
        mime="text/csv",
        width="stretch",
    )

summary_columns = st.columns(4, gap="large")
with summary_columns[0]:
    render_kpi_card(
        "Average moisture",
        f"{filtered['soil_moisture'].mean():.1f}",
        "%",
        f"Range {filtered['soil_moisture'].min():.1f}–{filtered['soil_moisture'].max():.1f}%",
        "neutral",
        "AVG",
    )
with summary_columns[1]:
    render_kpi_card(
        "Minimum water",
        f"{filtered['water_level'].min():.1f}",
        "%",
        "Lowest observed reserve",
        "negative" if filtered["water_level"].min() <= 8 else "neutral",
        "MIN",
    )
with summary_columns[2]:
    peak_temperature = filtered["temperature"].max()
    render_kpi_card(
        "Peak temperature",
        f"{peak_temperature:.1f}" if pd.notna(peak_temperature) else "N/A",
        "°C" if pd.notna(peak_temperature) else "",
        (
            "Highest matched Open-Meteo temperature"
            if pd.notna(peak_temperature)
            else "No matched weather snapshot"
        ),
        "negative" if pd.notna(peak_temperature) and peak_temperature >= 34 else "neutral",
        "MAX",
    )
with summary_columns[3]:
    elevated_count = int(filtered["risk_level"].isin(["high", "critical"]).sum())
    render_kpi_card(
        "Elevated readings",
        str(elevated_count),
        "",
        f"Across {len(filtered)} total readings",
        "negative" if elevated_count else "positive",
        "RSK",
    )

st.write("")
with st.container(border=True):
    render_section_header("Soil moisture history", selected_range)
    st.plotly_chart(
        soil_moisture_chart(filtered),
        width="stretch",
        config=PLOTLY_CONFIG,
    )

chart_left, chart_right = st.columns(2, gap="large")
with chart_left:
    with st.container(border=True):
        render_section_header("Water reserve history", selected_range)
        st.plotly_chart(
            water_level_chart(filtered),
            width="stretch",
            config=PLOTLY_CONFIG,
        )

with chart_right:
    with st.container(border=True):
        render_section_header("Risk composition", "Selected period")
        st.plotly_chart(
            risk_distribution_chart(filtered["risk_level"]),
            width="stretch",
            config=PLOTLY_CONFIG,
        )

with st.container(border=True):
    render_section_header("Temperature and humidity", "Environmental relationship")
    st.plotly_chart(
        combined_environment_chart(filtered),
        width="stretch",
        config=PLOTLY_CONFIG,
    )
