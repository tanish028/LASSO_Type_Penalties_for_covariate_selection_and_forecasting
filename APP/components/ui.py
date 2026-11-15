"""Reusable visual building blocks: hero, KPI tiles, glow cards, section dividers."""
import streamlit as st
from components.theme import recolor

UI_CSS = """
<style>
.hero { position:relative; overflow:hidden; border:1px solid #26382E; border-radius:18px; padding:2.1rem 2.2rem 1.8rem;
        background: radial-gradient(1200px 400px at 85% -20%, rgba(76,195,138,.28), transparent 60%),
                    radial-gradient(800px 380px at 0% 120%, rgba(184,220,107,.18), transparent 60%), #0F1C16; margin-bottom: 1.2rem; }
.hero h1 { font-size: 2.35rem; margin:.1rem 0 .5rem; background: linear-gradient(90deg,#EAF1E8,#A9E3C4 55%,#D2EC9C); -webkit-background-clip:text; background-clip:text; color:transparent; }
.hero p { color:#C3D2C4; font-size:1.05rem; max-width: 52rem; margin:0; }
.hero .pillrow { margin-top:1rem; display:flex; gap:.5rem; flex-wrap:wrap; }
.pill { font-size:.78rem; padding:.22rem .7rem; border-radius:999px; border:1px solid #2F4A3B; color:#C3D2C4; background:rgba(18,33,26,.7); }
.tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:.8rem; margin:.4rem 0 1.1rem; }
.tile { border:1px solid #26382E; border-radius:14px; padding:.85rem 1rem; background:linear-gradient(160deg,#14261D,#0F1E17); transition:all .18s ease; }
.tile:hover { transform:translateY(-2px); border-color:#4B7A5E; box-shadow:0 8px 24px rgba(0,0,0,.35); }
.tile .lab { font-size:.72rem; letter-spacing:.04em; color:#93A89A; }
.tile .val { font-family:'Source Serif 4',Georgia,serif; font-size:1.75rem; font-weight:600; line-height:1.25; }
.tile .sub { font-size:.8rem; color:#93A89A; }
.card { border:1px solid #26382E; border-radius:14px; padding:1rem 1.15rem; background:linear-gradient(160deg,#14261D,#0F1E17); height:100%; }
.card h4 { margin:.1rem 0 .35rem; font-size:1.02rem; }
.card p { color:#C3D2C4; font-size:.92rem; margin:0; }
.card .dot { display:inline-block; width:.6rem; height:.6rem; border-radius:50%; margin-right:.45rem; }
div[data-baseweb="tab-list"] { gap:.3rem; }
button[data-baseweb="tab"] { border-radius:10px 10px 0 0; padding:.45rem 1rem; }
.stButton>button { border-radius:10px; border:1px solid #2F4A3B; }
.stButton>button:hover { border-color:#4CC38A; color:#A9E3C4; }
</style>
"""


def inject():
    st.markdown(recolor(UI_CSS), unsafe_allow_html=True)


def hero(kicker, title, text, pills=()):
    inject()
    pr = "".join(f'<span class="pill">{p}</span>' for p in pills)
    st.markdown(recolor(f'<div class="hero"><div class="kicker">{kicker}</div><h1>{title}</h1><p>{text}</p><div class="pillrow">{pr}</div></div>'), unsafe_allow_html=True)


def tiles(items):
    """items: list of (label, value, sub, colour or None)."""
    inject()
    h = "".join(f'<div class="tile"><div class="lab">{l}</div><div class="val" style="color:{c or "#EAF1E8"}">{v}</div><div class="sub">{s}</div></div>' for l, v, s, c in items)
    st.markdown(recolor(f'<div class="tiles">{h}</div>'), unsafe_allow_html=True)


def card(title, text, colour="#4CC38A"):
    inject()
    st.markdown(recolor(f'<div class="card"><h4><span class="dot" style="background:{colour}"></span>{title}</h4><p>{text}</p></div>'), unsafe_allow_html=True)
