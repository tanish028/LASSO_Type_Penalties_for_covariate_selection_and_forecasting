"""Colours, page set-up and CSS shared by all pages."""
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio

# one colour per method, used in every chart
COLORS = {"LASSO": "#9AA7BD", "adaLASSO": "#E9A93B", "WLadaLASSO": "#4FA3F7", "Ext1": "#3FD0A0",
          "adaLASSO (γ by BIC)": "#F3CD85", "WLadaLASSO (γ by BIC)": "#9CCBFA", "Ext1 (γ by BIC)": "#9BE8CC",
          "AR(BIC)": "#E06C75", "AR(BIC) benchmark": "#E06C75"}
BG, PANEL, TEXT, MUTED, GRID = "#0B1426", "#101B33", "#E3E9F4", "#8FA1BF", "#22304D"

pio.templates["wl"] = go.layout.Template(layout=dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Segoe UI, Helvetica, Arial, sans-serif", color=TEXT, size=14),
    colorway=list(COLORS.values()), margin=dict(l=60, r=20, t=50, b=50),
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, title=dict(font=dict(size=13))),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, title=dict(font=dict(size=13))),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=13)), hoverlabel=dict(bgcolor=PANEL, font_color=TEXT)))
pio.templates.default = "wl"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:wght@500;600;700&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', 'Segoe UI', sans-serif; }}
.block-container {{ padding-top: 3.6rem; padding-bottom: 4rem; max-width: 1180px; }}
h1, h2, h3 {{ font-family: 'Source Serif 4', Georgia, serif; letter-spacing: 0.1px; color: {TEXT}; }}
h1 {{ font-size: 2.05rem; font-weight: 600; line-height: 1.2; margin-bottom: .3rem; }}
h2 {{ font-size: 1.45rem; font-weight: 600; margin-top: 2.2rem; padding-bottom: .35rem; border-bottom: 1px solid {GRID}; }}
h3 {{ font-size: 1.12rem; font-weight: 600; margin-top: 1.4rem; }}
p, li {{ line-height: 1.62; font-size: 1.0rem; }}
.kicker {{ text-transform: uppercase; letter-spacing: .12em; font-size: .72rem; color: #4FA3F7; font-weight: 600; margin-bottom: .2rem; }}
.lede {{ color: #B9C6DD; font-size: 1.08rem; max-width: 62rem; }}
.note {{ border-left: 3px solid #4FA3F7; padding: .5rem .9rem; color: #B9C6DD; background: rgba(79,163,247,.06); margin: .8rem 0; font-size: .95rem; }}
.warn {{ border-left: 3px solid #E9A93B; padding: .5rem .9rem; color: #E9D3A8; background: rgba(233,169,59,.07); margin: .8rem 0; font-size: .95rem; }}
.tag {{ display:inline-block; font-size:.72rem; padding:.08rem .5rem; border-radius:3px; margin-left:.5rem; vertical-align:middle;
        letter-spacing:.06em; text-transform:uppercase; font-weight:600; }}
.tag-paper {{ background:#1B2B4A; color:#9CCBFA; }}
.tag-ours {{ background:#12372F; color:#7BE5C0; }}
.tag-expl {{ background:#43361A; color:#F0CE86; }}
.small {{ color:{MUTED}; font-size:.86rem; }}
[data-testid="stMetricValue"] {{ font-size: 1.5rem; }}
[data-testid="stSidebar"] {{ border-right: 1px solid {GRID}; }}
[data-testid="stSidebarNav"] a {{ font-size: .95rem; }}
div[data-testid="stDataFrame"] {{ border: 1px solid {GRID}; }}
a {{ color: #7DB9F5 !important; }}
hr {{ border-color: {GRID}; }}
footer {{ visibility: hidden; }}
</style>
"""


def setup_page(title, icon=None):
    try:                                   # the entry point (app.py) has normally set this already
        st.set_page_config(page_title=f"{title} | LASSO Type Penalties", page_icon=icon, layout="wide", initial_sidebar_state="expanded")
    except st.errors.StreamlitAPIException:
        pass
    st.markdown(CSS, unsafe_allow_html=True)
    from components import ui
    ui.inject()


def header(kicker, title, lede=None):
    st.markdown(f'<div class="kicker">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    if lede:
        st.markdown(f'<p class="lede">{lede}</p>', unsafe_allow_html=True)


def note(text, kind="note"):
    st.markdown(f'<div class="{kind}">{text}</div>', unsafe_allow_html=True)
