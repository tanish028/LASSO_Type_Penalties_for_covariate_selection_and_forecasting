"""Table helpers: consistent number formats and a download button."""
import pandas as pd
import streamlit as st


def show(df, fmt=None, height=None, key=None, download=None, index=False):
    """Show a DataFrame with 3-decimal floats; optional CSV download of exactly what is displayed."""
    df = df.copy()
    cfg = {}
    for c in df.columns:
        if pd.api.types.is_float_dtype(df[c]):
            cfg[c] = st.column_config.NumberColumn(format=(fmt or "%.3f"))
    kw = dict(height=height) if height else {}
    st.dataframe(df, hide_index=not index, width="stretch", column_config=cfg, **kw)
    if download:
        st.download_button("Download this table (CSV)", df.to_csv(index=index).encode(), file_name=download, mime="text/csv", key=key or download)


def p_fmt(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"
