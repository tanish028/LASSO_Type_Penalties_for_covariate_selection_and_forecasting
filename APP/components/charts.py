"""Plotly figures. All take plain DataFrames and return a figure; no data loading here."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from components.theme import COLORS, GRID, MUTED


def scenario_label(df):
    return "T=" + df["T"].astype(str) + ", ρ=" + df["rho"].astype(str) + ", L=" + df["L"].astype(str)


def bars_by_scenario(summary, metric_label, methods, log_y=False):
    """Grouped bars: one group per scenario, one bar per method. summary has rho,T,L,method,value."""
    s = summary[summary.method.isin(methods)].copy()
    s["scenario"] = scenario_label(s)
    order = s.sort_values(["T", "rho", "L"]).scenario.unique()
    fig = go.Figure()
    for m in methods:
        d = s[s.method == m].set_index("scenario").reindex(order)
        fig.add_bar(x=order, y=d["value"], name=m, marker_color=COLORS.get(m), hovertemplate="%{x}<br>" + m + ": %{y:.4f}<extra></extra>")
    fig.update_layout(barmode="group", height=430, yaxis_title=metric_label, xaxis_title=None, legend=dict(orientation="h", y=1.12))
    if log_y:
        fig.update_yaxes(type="log")
    return fig


def boxplots(rep, metric, metric_label, methods, trim=True):
    """Replication-level boxplots, one panel per scenario. trim: y-range from 0 to the 99th percentile of the panel."""
    sc = rep[["rho", "T", "L"]].drop_duplicates().sort_values(["T", "rho", "L"]).values.tolist()
    n = len(sc); ncol = min(4, n); nrow = int(np.ceil(n / ncol))
    titles = [f"T={int(t)}, ρ={r}, L={int(l)}" for r, t, l in sc]
    fig = make_subplots(rows=nrow, cols=ncol, subplot_titles=titles, horizontal_spacing=0.05, vertical_spacing=0.14 if nrow > 1 else 0.1)
    for i, (r, t, l) in enumerate(sc):
        d = rep[(rep.rho == r) & (rep["T"] == t) & (rep.L == l)]
        hi = d[metric].quantile(0.99)
        for m in methods:
            y = d.loc[d.method == m, metric]
            fig.add_trace(go.Box(y=y, name=m, marker_color=COLORS.get(m), line=dict(width=1.2), boxmean=True, boxpoints=False,
                                 showlegend=(i == 0), legendgroup=m), row=i // ncol + 1, col=i % ncol + 1)
        if trim and metric in ("fc_mse", "fc_mae", "coef_mse", "coef_mae", "NIV"):
            fig.update_yaxes(range=[0, hi * 1.02], row=i // ncol + 1, col=i % ncol + 1)
        fig.update_xaxes(showticklabels=False, row=i // ncol + 1, col=i % ncol + 1)
    fig.update_layout(height=330 * nrow + 80, legend=dict(orientation="h", y=1.04), margin=dict(t=90))
    fig.update_annotations(font_size=12)
    return fig


def heat(df, value, title, zmid=0, fmt=".3f", colorscale="RdBu"):
    """df: rows x columns pivot. Diverging colours centred at zmid."""
    fig = go.Figure(go.Heatmap(z=df.values, x=list(df.columns), y=list(df.index), zmid=zmid, colorscale=colorscale, reversescale=False,
                               text=np.vectorize(lambda v: format(v, fmt))(df.values), texttemplate="%{text}", textfont=dict(size=12),
                               colorbar=dict(title=value), hovertemplate="%{y}<br>%{x}: %{z:.4f}<extra></extra>"))
    fig.update_layout(title=title, height=max(300, 34 * len(df) + 120), yaxis=dict(autorange="reversed"))
    return fig


def grouped_bars(df, x, y, color, order=None, title=None, yname=None, colors=None):
    fig = go.Figure()
    for c in (order or df[color].unique()):
        d = df[df[color] == c]
        fig.add_bar(x=d[x], y=d[y], name=str(c), marker_color=(colors or COLORS).get(c))
    fig.update_layout(barmode="group", title=title, yaxis_title=yname, height=400, legend=dict(orientation="h", y=1.15))
    fig.add_hline(y=0, line_color=MUTED, line_width=1)
    return fig
