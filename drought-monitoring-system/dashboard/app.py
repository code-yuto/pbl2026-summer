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
            title="AI field reports",
            icon=":material/auto_awesome:",
        ),
    ]
}

navigation = st.navigation(pages, position="sidebar")

with st.sidebar:
    render_sidebar_status()
    if st.button(
        "Refresh live data",
        icon=":material/refresh:",
        width="stretch",
    ):
        st.cache_data.clear()
        st.rerun()
    st.caption("TerraPulse prototype · v0.2")

navigation.run()
