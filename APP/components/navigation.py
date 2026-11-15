"""Sidebar and page-level navigation helpers."""
import streamlit as st

PAGES = [("app.py", "Home"), ("pages/1_Lab.py", "Live lab"), ("pages/2_Penalty_Explorer.py", "Penalty explorer"),
         ("pages/3_Monte_Carlo.py", "Monte Carlo"), ("pages/4_Equity_Premium.py", "Equity premium"),
         ("pages/5_FRED_MD.py", "FRED-MD"), ("pages/6_Methods.py", "Methods")]


def sidebar_footer():
    with st.sidebar:
        st.markdown("---")
        st.markdown('<p class="small">Replication and extension of Konzen and Ziegelmann (2016). '
                    'Saved results of completed runs, except the Live lab and Penalty explorer, which compute small illustrative examples in your browser.', unsafe_allow_html=True)


def page_links(cols=3, skip=None):
    items = [p for p in PAGES if p[0] != skip and p[0] != "app.py"]
    columns = st.columns(cols)
    for i, (f, label) in enumerate(items):
        with columns[i % cols]:
            st.page_link(f, label=label)
