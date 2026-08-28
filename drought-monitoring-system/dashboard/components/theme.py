import streamlit as st


PALETTE = {
    "background": "#07130F",
    "surface": "#0D2119",
    "surface_alt": "#123026",
    "border": "rgba(173, 214, 188, 0.14)",
    "text": "#EDF7F0",
    "muted": "#93AA9B",
    "green": "#5DDB8A",
    "green_soft": "#A7F3C2",
    "brown": "#B58A64",
    "amber": "#F2B95F",
    "red": "#FF7A7A",
}


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

        :root {
            --bg: #07130F;
            --surface: #0D2119;
            --surface-raised: #123026;
            --border: rgba(173, 214, 188, 0.14);
            --border-strong: rgba(93, 219, 138, 0.28);
            --text: #EDF7F0;
            --muted: #93AA9B;
            --green: #5DDB8A;
            --green-soft: #A7F3C2;
            --brown: #B58A64;
            --amber: #F2B95F;
            --red: #FF7A7A;
        }

        html, body, [class*="css"] {
            font-family: 'DM Sans', 'Inter', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 88% 4%, rgba(54, 154, 94, 0.12), transparent 25rem),
                radial-gradient(circle at 24% 95%, rgba(181, 138, 100, 0.07), transparent 28rem),
                var(--bg);
            color: var(--text);
        }

        .block-container {
            max-width: 1480px;
            padding: 2.2rem 2.4rem 4rem;
        }

        #MainMenu,
        footer,
        [data-testid="stToolbar"],
        [data-testid="stStatusWidget"],
        [data-testid="stDecoration"] {
            display: none !important;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        h1, h2, h3, h4 {
            font-family: 'Inter', 'DM Sans', sans-serif;
            color: var(--text);
            letter-spacing: -0.035em;
        }

        p, label, [data-testid="stCaptionContainer"] {
            color: var(--muted);
        }

        section[data-testid="stSidebar"] {
            width: 286px !important;
            background: linear-gradient(180deg, #0A1C15 0%, #081610 100%);
            border-right: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.2rem;
        }

        [data-testid="stSidebarNav"] {
            padding-top: 1.2rem;
        }

        [data-testid="stSidebarNav"] ul {
            gap: 0.42rem;
        }

        [data-testid="stSidebarNav"] a {
            min-height: 46px;
            padding: 0.72rem 0.85rem;
            border: 1px solid transparent;
            border-radius: 12px;
            color: #AFC2B5;
            font-size: 0.92rem;
            font-weight: 600;
            transition: all 160ms ease;
        }

        [data-testid="stSidebarNav"] a:hover {
            color: var(--text);
            background: rgba(93, 219, 138, 0.07);
            border-color: rgba(93, 219, 138, 0.12);
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] {
            color: var(--green-soft);
            background: linear-gradient(90deg, rgba(93, 219, 138, 0.16), rgba(93, 219, 138, 0.06));
            border-color: rgba(93, 219, 138, 0.24);
            box-shadow: inset 3px 0 0 var(--green);
        }

        .brand-lockup {
            display: flex;
            align-items: center;
            gap: 0.78rem;
            padding: 0.25rem 0.1rem 1.25rem;
            border-bottom: 1px solid var(--border);
        }

        .brand-mark {
            display: grid;
            width: 40px;
            height: 40px;
            place-items: center;
            border: 1px solid rgba(93, 219, 138, 0.34);
            border-radius: 12px;
            background: linear-gradient(145deg, rgba(93, 219, 138, 0.23), rgba(93, 219, 138, 0.07));
            color: var(--green);
            font-size: 1.3rem;
            box-shadow: 0 12px 34px rgba(0, 0, 0, 0.22);
        }

        .brand-name {
            color: var(--text);
            font-family: 'Inter', sans-serif;
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: -0.03em;
        }

        .brand-subtitle {
            margin-top: 0.1rem;
            color: var(--muted);
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .sidebar-status {
            margin-top: 1.1rem;
            padding: 0.85rem 0.9rem;
            border: 1px solid var(--border);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.018);
        }

        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            margin-right: 0.48rem;
            border-radius: 50%;
            background: var(--green);
            box-shadow: 0 0 0 4px rgba(93, 219, 138, 0.10);
        }

        .page-header {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 2rem;
            margin: 0.2rem 0 2rem;
        }

        .page-eyebrow {
            margin-bottom: 0.5rem;
            color: var(--green);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }

        .page-title {
            margin: 0;
            color: var(--text);
            font-family: 'Inter', sans-serif;
            font-size: clamp(2rem, 3vw, 2.8rem);
            font-weight: 700;
            line-height: 1.05;
            letter-spacing: -0.055em;
        }

        .page-subtitle {
            max-width: 680px;
            margin-top: 0.65rem;
            color: var(--muted);
            font-size: 0.98rem;
            line-height: 1.6;
        }

        .source-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.55rem 0.8rem;
            border: 1px solid var(--border-strong);
            border-radius: 999px;
            background: rgba(93, 219, 138, 0.08);
            color: var(--green-soft);
            font-size: 0.76rem;
            font-weight: 700;
            white-space: nowrap;
        }

        .kpi-card {
            min-height: 154px;
            padding: 1.25rem 1.3rem;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: linear-gradient(145deg, rgba(18, 48, 38, 0.80), rgba(13, 33, 25, 0.88));
            box-shadow: 0 18px 44px rgba(0, 0, 0, 0.20);
        }

        .kpi-topline {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .kpi-label {
            color: #A8BAAD;
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .kpi-icon {
            display: grid;
            width: 32px;
            height: 32px;
            place-items: center;
            border: 1px solid rgba(93, 219, 138, 0.20);
            border-radius: 10px;
            background: rgba(93, 219, 138, 0.08);
            color: var(--green-soft);
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 0.04em;
        }

        .kpi-value {
            margin-top: 1.05rem;
            color: var(--text);
            font-family: 'Inter', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.055em;
        }

        .kpi-unit {
            margin-left: 0.2rem;
            color: var(--muted);
            font-size: 0.86rem;
            font-weight: 600;
        }

        .kpi-trend {
            margin-top: 0.52rem;
            font-size: 0.78rem;
            font-weight: 600;
        }

        .trend-positive { color: var(--green-soft); }
        .trend-negative { color: var(--red); }
        .trend-neutral { color: var(--muted); }

        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--border) !important;
            border-radius: 18px !important;
            background: linear-gradient(145deg, rgba(13, 33, 25, 0.90), rgba(9, 26, 19, 0.88));
            box-shadow: 0 18px 44px rgba(0, 0, 0, 0.16);
        }

        [data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 0.35rem 0.45rem;
        }

        .section-kicker {
            color: var(--green);
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .section-title {
            margin: 0.25rem 0 0;
            color: var(--text);
            font-family: 'Inter', sans-serif;
            font-size: 1.05rem;
            font-weight: 650;
            letter-spacing: -0.025em;
        }

        .status-banner {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
            padding: 1rem 1.15rem;
            border: 1px solid rgba(242, 185, 95, 0.24);
            border-radius: 15px;
            background: linear-gradient(90deg, rgba(242, 185, 95, 0.10), rgba(242, 185, 95, 0.025));
        }

        .status-banner.critical {
            border-color: rgba(255, 122, 122, 0.28);
            background: linear-gradient(90deg, rgba(255, 122, 122, 0.12), rgba(255, 122, 122, 0.025));
        }

        .status-banner.normal {
            border-color: rgba(93, 219, 138, 0.24);
            background: linear-gradient(90deg, rgba(93, 219, 138, 0.10), rgba(93, 219, 138, 0.025));
        }

        .status-heading {
            color: var(--text);
            font-size: 0.93rem;
            font-weight: 700;
        }

        .status-copy {
            margin-top: 0.26rem;
            color: var(--muted);
            font-size: 0.82rem;
            line-height: 1.5;
        }

        .risk-chip {
            padding: 0.38rem 0.65rem;
            border-radius: 999px;
            background: rgba(242, 185, 95, 0.13);
            color: #FFD28A;
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            white-space: nowrap;
        }

        .alert-row {
            display: grid;
            grid-template-columns: 10px minmax(0, 1fr) auto;
            gap: 0.85rem;
            align-items: start;
            padding: 0.95rem 0;
            border-bottom: 1px solid var(--border);
        }

        .alert-row:last-child { border-bottom: 0; }
        .alert-marker { width: 8px; height: 8px; margin-top: 0.38rem; border-radius: 50%; }
        .alert-marker.critical { background: var(--red); box-shadow: 0 0 0 4px rgba(255, 122, 122, 0.08); }
        .alert-marker.high { background: var(--amber); box-shadow: 0 0 0 4px rgba(242, 185, 95, 0.08); }
        .alert-marker.medium { background: var(--brown); }
        .alert-title { color: var(--text); font-size: 0.86rem; font-weight: 650; }
        .alert-meta { margin-top: 0.25rem; color: var(--muted); font-size: 0.74rem; }
        .delivery-badge { color: var(--green-soft); font-size: 0.7rem; font-weight: 700; }

        .ai-advisory {
            padding: 1.5rem;
            border: 1px solid rgba(93, 219, 138, 0.24);
            border-radius: 18px;
            background:
                radial-gradient(circle at 94% 0%, rgba(93, 219, 138, 0.12), transparent 18rem),
                linear-gradient(145deg, rgba(18, 48, 38, 0.90), rgba(10, 28, 20, 0.96));
        }

        .ai-label {
            color: var(--green);
            font-size: 0.69rem;
            font-weight: 800;
            letter-spacing: 0.13em;
            text-transform: uppercase;
        }

        .ai-title {
            margin-top: 0.55rem;
            color: var(--text);
            font-family: 'Inter', sans-serif;
            font-size: 1.35rem;
            font-weight: 700;
            letter-spacing: -0.035em;
        }

        .ai-copy {
            margin-top: 0.7rem;
            color: #B8C8BD;
            font-size: 0.9rem;
            line-height: 1.7;
        }

        .recommendation-card {
            min-height: 130px;
            padding: 1.1rem;
            border: 1px solid var(--border);
            border-radius: 15px;
            background: rgba(255, 255, 255, 0.018);
        }

        .recommendation-index {
            color: var(--green);
            font-size: 0.7rem;
            font-weight: 800;
        }

        .recommendation-text {
            margin-top: 0.55rem;
            color: var(--text);
            font-size: 0.86rem;
            font-weight: 550;
            line-height: 1.55;
        }

        .stPlotlyChart {
            border-radius: 14px;
            overflow: hidden;
        }

        .stButton > button,
        .stDownloadButton > button {
            min-height: 42px;
            border: 1px solid var(--border-strong);
            border-radius: 11px;
            background: rgba(93, 219, 138, 0.08);
            color: var(--green-soft);
            font-weight: 700;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: var(--green);
            background: rgba(93, 219, 138, 0.14);
            color: white;
        }

        [data-baseweb="select"] > div,
        [data-testid="stDateInput"] > div > div,
        [data-testid="stTextInput"] input {
            border-color: var(--border) !important;
            border-radius: 11px !important;
            background: rgba(255, 255, 255, 0.025) !important;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 14px;
            overflow: hidden;
        }

        [data-testid="stChatMessage"] {
            margin: 0.7rem 0;
            padding: 0.9rem 1rem;
            border: 1px solid var(--border);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.022);
        }

        [data-testid="stChatMessage"] p {
            color: #D5E3D9;
            line-height: 1.65;
        }

        [data-testid="stChatInput"] {
            border-color: var(--border-strong) !important;
            border-radius: 14px !important;
            background: rgba(7, 19, 15, 0.78) !important;
        }

        [data-testid="stAlert"] {
            border-radius: 13px;
            border-color: var(--border) !important;
        }

        @media (max-width: 900px) {
            .block-container { padding: 1.4rem 1rem 3rem; }
            .page-header { align-items: flex-start; flex-direction: column; gap: 1rem; }
            .kpi-card { min-height: 138px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand() -> None:
    st.markdown(
        """
        <div class="brand-lockup">
            <div class="brand-mark">◒</div>
            <div>
                <div class="brand-name">TerraPulse</div>
                <div class="brand-subtitle">Field Intelligence</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_status() -> None:
    st.markdown(
        """
        <div class="sidebar-status">
            <div style="color:#DDE9E0;font-size:.78rem;font-weight:700;">
                <span class="status-dot"></span>Analytics workspace
            </div>
            <div style="margin-top:.35rem;color:#7F9787;font-size:.7rem;">
                USB Serial · Live APIs · Session memory
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
