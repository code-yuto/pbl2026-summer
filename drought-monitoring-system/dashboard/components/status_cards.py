from datetime import datetime
from html import escape

import streamlit as st


RISK_COPY = {
    "normal": (
        "Field conditions are within the configured operating range.",
        "normal",
    ),
    "medium": (
        "A gradual drying trend is developing. Continue close observation.",
        "",
    ),
    "high": (
        "Moisture and stored water are approaching critical thresholds.",
        "",
    ),
    "critical": (
        "Immediate field inspection and controlled irrigation are recommended.",
        "critical",
    ),
}


def render_page_header(
    title: str,
    subtitle: str,
    source: str,
    eyebrow: str = "Agricultural analytics",
) -> None:
    st.markdown(
        f"""
        <div class="page-header">
            <div>
                <div class="page-eyebrow">{escape(eyebrow)}</div>
                <h1 class="page-title">{escape(title)}</h1>
                <div class="page-subtitle">{escape(subtitle)}</div>
            </div>
            <div class="source-pill">
                <span class="status-dot"></span>{escape(source)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, kicker: str) -> None:
    st.markdown(
        f"""
        <div style="margin:.15rem 0 .65rem;">
            <div class="section-kicker">{escape(kicker)}</div>
            <div class="section-title">{escape(title)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_banner(risk_level: str, updated_at: datetime) -> None:
    normalized = risk_level.lower()
    copy, css_class = RISK_COPY.get(normalized, RISK_COPY["medium"])
    timestamp = updated_at.strftime("%d %b %Y · %H:%M UTC")

    st.markdown(
        f"""
        <div class="status-banner {css_class}">
            <div>
                <div class="status-heading">Current field assessment</div>
                <div class="status-copy">
                    {escape(copy)} Last updated {escape(timestamp)}.
                </div>
            </div>
            <div class="risk-chip">{escape(normalized)} risk</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alert_row(
    risk_level: str,
    message: str,
    created_at: datetime,
    status: str = "Delivered",
) -> None:
    normalized = risk_level.lower()
    marker = normalized if normalized in {"critical", "high", "medium"} else "medium"
    timestamp = created_at.strftime("%d %b · %H:%M UTC")

    st.markdown(
        f"""
        <div class="alert-row">
            <div class="alert-marker {marker}"></div>
            <div>
                <div class="alert-title">{escape(message)}</div>
                <div class="alert-meta">{escape(timestamp)} · LINE notification</div>
            </div>
            <div class="delivery-badge">{escape(status)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_advisory(
    title: str,
    explanation: str,
    risk_level: str,
    confidence: int | str,
) -> None:
    confidence_text = (
        f"{confidence}% confidence"
        if isinstance(confidence, int)
        else f"{str(confidence).title()} confidence"
    )
    st.markdown(
        f"""
        <div class="ai-advisory">
            <div class="ai-label">Gemini field advisory</div>
            <div class="ai-title">{escape(title)}</div>
            <div class="ai-copy">{escape(explanation)}</div>
            <div style="display:flex;gap:.6rem;margin-top:1rem;flex-wrap:wrap;">
                <div class="source-pill">{escape(risk_level.title())} risk</div>
                <div class="source-pill">{escape(confidence_text)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_recommendation(index: int, recommendation: str) -> None:
    st.markdown(
        f"""
        <div class="recommendation-card">
            <div class="recommendation-index">ACTION {index:02d}</div>
            <div class="recommendation-text">{escape(recommendation)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
