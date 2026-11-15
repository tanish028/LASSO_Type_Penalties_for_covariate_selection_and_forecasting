"""Colours, page set-up and CSS shared by all pages. Two colour themes: Forest (default) and Ocean."""
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio

THEMES = ["Forest (green and amber)", "Ocean (blue)"]

# Everything is written in Forest colours; recolor() swaps them to Ocean colours when that theme is selected.
_OCEAN = {"#0C1712": "#0B1426", "#12211A": "#101B33", "#0F1C16": "#0E1A33", "#14261D": "#111E3A", "#0F1E17": "#0D1830",
          "#142219": "#16213B", "#17291F": "#13223F", "#193126": "#15264A", "#1C3227": "#1B2B4A", "#26382E": "#22304D",
          "#2F4A3B": "#2B3D63", "#4B7A5E": "#3A5A94", "#EAF1E8": "#E3E9F4", "#C3D2C4": "#B9C6DD", "#93A89A": "#8FA1BF",
          "#9AA79F": "#9AA7BD", "#4CC38A": "#4FA3F7", "#B8DC6B": "#3FD0A0", "#A9E3C4": "#9CCBFA", "#D2EC9C": "#7BE5C0",
          "#8FD9B0": "#7DB9F5", "#2F8F63": "#2B6CB0", "#243D1E": "#12372F",
          "rgba(76,195,138": "rgba(79,163,247", "rgba(184,220,107": "rgba(63,208,160", "rgba(18,33,26": "rgba(16,27,51"}
_METHODS = {"Forest": {"LASSO": "#9AA79F", "adaLASSO": "#5FA8D3", "WLadaLASSO": "#F2A93B", "Ext1": "#B8DC6B"},
            "Ocean": {"LASSO": "#9AA7BD", "adaLASSO": "#E9A93B", "WLadaLASSO": "#4FA3F7", "Ext1": "#3FD0A0"}}


def current():
    return "Ocean" if str(st.session_state.get("theme", THEMES[0])).startswith("Ocean") else "Forest"


def recolor(text):
    """Return text with Forest colours replaced by the selected theme's colours."""
    if current() == "Forest" or not isinstance(text, str):
        return text
    for a, b in _OCEAN.items():
        text = text.replace(a, b).replace(a.lower(), b)
    return text


# one colour per method, used in every chart (updated in place when the theme changes)
COLORS = {"LASSO": "#9AA79F", "adaLASSO": "#5FA8D3", "WLadaLASSO": "#F2A93B", "Ext1": "#B8DC6B",
          "adaLASSO (γ by BIC)": "#F3CD85", "WLadaLASSO (γ by BIC)": "#A9E3C4", "Ext1 (γ by BIC)": "#9BE8CC",
          "AR(BIC)": "#E06C75", "AR(BIC) benchmark": "#E06C75"}
BG, PANEL, TEXT, MUTED, GRID = "#0C1712", "#12211A", "#EAF1E8", "#93A89A", "#26382E"


def _apply_palette():
    global BG, PANEL, TEXT, MUTED, GRID
    BG, PANEL, TEXT, MUTED, GRID = (recolor(c) for c in ("#0C1712", "#12211A", "#EAF1E8", "#93A89A", "#26382E"))
    COLORS.update(_METHODS[current()])
    if current() == "Ocean":
        COLORS.update({"adaLASSO (γ by BIC)": "#F3CD85", "WLadaLASSO (γ by BIC)": "#9CCBFA", "Ext1 (γ by BIC)": "#7BE5C0"})
    else:
        COLORS.update({"adaLASSO (γ by BIC)": "#9CC5E0", "WLadaLASSO (γ by BIC)": "#F3CD85", "Ext1 (γ by BIC)": "#D2EC9C"})
    pio.templates["wl"] = go.layout.Template(layout=dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, Helvetica, Arial, sans-serif", color=TEXT, size=14),
        colorway=list(COLORS.values()), margin=dict(l=60, r=20, t=50, b=50),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, title=dict(font=dict(size=13))),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, title=dict(font=dict(size=13))),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=13)), hoverlabel=dict(bgcolor=PANEL, font_color=TEXT)))
    pio.templates.default = "wl"


_apply_palette()

def _css():
    return recolor(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:wght@500;600;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', 'Segoe UI', sans-serif; }}
.block-container {{ padding-top: 3.6rem; padding-bottom: 4rem; max-width: 1180px; }}
h1, h2, h3 {{ font-family: 'Source Serif 4', Georgia, serif; letter-spacing: 0.1px; color: {TEXT}; }}
h1 {{ font-size: 2.05rem; font-weight: 600; line-height: 1.2; margin-bottom: .3rem; }}
h2 {{ font-size: 1.45rem; font-weight: 600; margin-top: 2.2rem; padding-bottom: .35rem; border-bottom: 1px solid {GRID}; }}
h3 {{ font-size: 1.12rem; font-weight: 600; margin-top: 1.4rem; }}
p, li {{ line-height: 1.62; font-size: 1.0rem; }}
.kicker {{ text-transform: uppercase; letter-spacing: .12em; font-size: .72rem; color: #4CC38A; font-weight: 600; margin-bottom: .2rem; }}
.lede {{ color: #C3D2C4; font-size: 1.08rem; max-width: 62rem; }}
.note {{ border-left: 3px solid #4CC38A; padding: .5rem .9rem; color: #C3D2C4; background: rgba(76,195,138,.06); margin: .8rem 0; font-size: .95rem; }}
.warn {{ border-left: 3px solid #E9A93B; padding: .5rem .9rem; color: #E9D3A8; background: rgba(233,169,59,.07); margin: .8rem 0; font-size: .95rem; }}
.tag {{ display:inline-block; font-size:.72rem; padding:.08rem .5rem; border-radius:3px; margin-left:.5rem; vertical-align:middle;
        letter-spacing:.06em; text-transform:uppercase; font-weight:600; }}
.tag-paper {{ background:#1C3227; color:#A9E3C4; }}
.tag-ours {{ background:#243D1E; color:#D2EC9C; }}
.tag-expl {{ background:#43361A; color:#F0CE86; }}
.small {{ color:{MUTED}; font-size:.86rem; }}
[data-testid="stMetricValue"] {{ font-size: 1.5rem; }}
[data-testid="stSidebar"] {{ border-right: 1px solid {GRID}; }}
[data-testid="stSidebarNav"] a {{ font-size: .95rem; }}
div[data-testid="stDataFrame"] {{ border: 1px solid {GRID}; }}
a {{ color: #8FD9B0 !important; }}
hr {{ border-color: {GRID}; }}
footer {{ visibility: hidden; }}
</style>
""")


def setup_page(title, icon=None):
    try:                                   # the entry point (app.py) has normally set this already
        st.set_page_config(page_title=f"{title} | LASSO Type Penalties", page_icon=icon, layout="wide", initial_sidebar_state="expanded")
    except st.errors.StreamlitAPIException:
        pass
    _apply_palette()
    st.markdown(_css(), unsafe_allow_html=True)
    st.markdown(_theme_overrides(), unsafe_allow_html=True)
    from components import ui
    ui.inject()


def header(kicker, title, lede=None):
    st.markdown(f'<div class="kicker">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    if lede:
        st.markdown(f'<p class="lede">{lede}</p>', unsafe_allow_html=True)


def note(text, kind="note"):
    st.markdown(f'<div class="{kind}">{text}</div>', unsafe_allow_html=True)


def _theme_overrides():
    """Ocean theme: override the Streamlit base colours that config.toml sets for Forest."""
    if current() == "Forest":
        return ""
    return """<style>
.stApp { background:#0B1426; color:#E3E9F4; }
[data-testid="stSidebar"], [data-testid="stSidebar"] > div { background:#101B33; }
[data-testid="stHeader"] { background:rgba(11,20,38,.0); }
[data-testid="stSlider"], div[data-baseweb="tab-list"], [data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within { filter: hue-rotate(62deg); }
[data-baseweb="select"] > div { background-color:#0E1A33; }
[data-baseweb="tab-highlight"] { background-color:#4FA3F7 !important; }
button[data-baseweb="tab"][aria-selected="true"], button[data-baseweb="tab"][aria-selected="true"] p { color:#4FA3F7 !important; }
[data-testid="stPlotlyChart"], [data-testid="stPlotlyChart"] .main-svg { background: transparent !important; }
[data-testid="stNavSectionHeader"], [data-testid="stSidebarNav"] a[aria-current="page"] { background:rgba(79,163,247,.14); }
div[role="radiogroup"] label > div:first-child { border-color:#4FA3F7; }
</style>"""
