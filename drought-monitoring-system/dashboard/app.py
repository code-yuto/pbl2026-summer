import os

import streamlit as st

from components.theme import inject_theme, render_brand, render_sidebar_status


st.set_page_config(
    page_title="TerraPulse · Field Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None,
)

inject_theme()

with st.sidebar:
    render_brand()
    st.text_input(
        "FastAPI URL",
        value=os.getenv("BACKEND_URL", "http://localhost:8000"),
        key="backend_url",
        help=(
            "Paste the HTTPS ngrok URL for FastAPI, without a trailing slash."
        ),
        placeholder="https://example.ngrok-free.app",
    )

pages = {
    "Workspace": [
        st.Page(
            "pages/1_Live_Monitoring.py",
            title="Field overview",
            icon=":material/space_dashboard:",
            default=True,
        ),
        st.Page(
            "pages/2_Historical_Data.py",
            title="Historical analytics",
            icon=":material/monitoring:",
        ),
        st.Page(
            "pages/3_Alerts.py",
            title="Alert center",
            icon=":material/notifications_active:",
        ),
        st.Page(
            "pages/4_LLM_Reports.py",
            title="Forecast AI chat",
            icon=":material/auto_awesome:",
        ),
    ]
}

navigation = st.navigation(pages, position="sidebar")

with st.sidebar:
    render_sidebar_status()
    if st.button(
        "Connect and refresh",
        icon=":material/refresh:",
        width="stretch",
    ):
        st.cache_data.clear()
        st.rerun()
    st.caption("TerraPulse prototype · v0.4 · No database")

navigation.run()
