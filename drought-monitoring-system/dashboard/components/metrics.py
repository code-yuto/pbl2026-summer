from html import escape

import streamlit as st


def render_kpi_card(
    label: str,
    value: str,
    unit: str = "",
    trend: str = "",
    trend_direction: str = "neutral",
    icon: str = "DATA",
) -> None:
    direction = trend_direction if trend_direction in {
        "positive",
        "negative",
        "neutral",
    } else "neutral"

    trend_html = (
        f'<div class="kpi-trend trend-{direction}">{escape(trend)}</div>'
        if trend
        else ""
    )

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-topline">
                <div class="kpi-label">{escape(label)}</div>
                <div class="kpi-icon">{escape(icon)}</div>
            </div>
            <div class="kpi-value">
                {escape(value)}<span class="kpi-unit">{escape(unit)}</span>
            </div>
            {trend_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def percentage_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return ((current - previous) / abs(previous)) * 100


def signed_trend(change: float, suffix: str = "vs previous period") -> str:
    arrow = "↗" if change > 0 else "↘" if change < 0 else "→"
    return f"{arrow} {abs(change):.1f}% {suffix}"
