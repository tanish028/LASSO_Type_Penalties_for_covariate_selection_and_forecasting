import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from components.theme import setup_page, header, note, COLORS, MUTED
from components.navigation import sidebar_footer
from components.explanations import EQUITY_DISCREPANCY
from components import charts, tables, ui
from utils import data_loader as dl
from utils.validation import DataProblem

setup_page("Equity premium")
sidebar_footer()
header("Explore", "Equity premium",
       "Annual one-step forecasts of the equity premium from the 14 Goyal-Welch predictors (1927 to 2005 sample), expanding window, benchmark: the historical mean. "
       "Out-of-sample R² is 1 − SSE(model)/SSE(historical mean): positive means better than the benchmark.")
note(EQUITY_DISCREPANCY, "warn")

design_lbl = st.radio("Experiment", ["Fixed γ (gamma) = 1 (main run)", "γ (gamma) chosen by BIC (separate run)"], horizontal=True)
design = "fixed" if design_lbl.startswith("Fixed") else "gamma_bic"
with st.sidebar:
    st.markdown("### Data version")
    version = st.radio("Version", list(dl.EQ_VERSIONS), format_func=dl.EQ_VERSIONS.get, label_visibility="collapsed")
    st.markdown('<p class="small">(a) 2005 vintage of the Goyal-Welch file with the index-based log premium; (b) current file with the premium from CRSP returns; '
                '(c) current file with the index-based premium. Predictors are differenced and the premium is kept in levels in all three.</p>', unsafe_allow_html=True)
try:
    D = dl.load_equity(design, version)
except DataProblem as e:
    st.error(f"Data problem: {e}"); st.stop()

r2 = D["r2os"].copy()
r2["label"] = r2.model.map(dl.EQ_MODELS).fillna(r2.model)
pen = dl.EQ_PENALISED + (dl.EQ_PENALISED_G if design == "gamma_bic" else [])
starts = sorted(r2.start.unique())

tab_exp, tab_main, tab_paper, tab_pred, tab_sel = st.tabs(["🎛️ Version explorer", "Penalised methods", "Comparison with the paper", "Single predictors and OLS", "Selected models"])

with tab_main:
    st.markdown(f"### Out-of-sample R², {dl.EQ_VERSIONS[version]}")
    d = r2[r2.model.isin(pen)]
    piv = d.pivot(index="label", columns="start", values="R2_OS").reindex([dl.EQ_MODELS[m] for m in pen])
    piv.columns = [f"start {c}" for c in piv.columns]
    st.plotly_chart(charts.heat(piv, "R²_OS", "R²_OS against the historical mean (blue positive, red negative)", zmid=0), width="stretch")
    pv = d.pivot(index="label", columns="start", values="p_MDM").reindex(piv.index)
    pv.columns = [f"p {c}" for c in pv.columns]
    out = pd.concat([piv, pv], axis=1).reset_index().rename(columns={"label": "method"})
    tables.show(out, fmt="%.3f", download=f"equity_{design}_{version}.csv", key="eq_main")
    npos = int((d.R2_OS > 0).sum())
    st.markdown(f'<p class="small">p = one-sided modified Diebold-Mariano p-value (Harvey, Leybourne and Newbold, 1997) against the historical mean. '
                f'Of {len(d)} penalised values shown, {npos} are positive; the largest is {d.R2_OS.max():.3f} and the smallest p-value is {d.p_MDM.min():.3f}. '
                f'With 21 to 51 forecasts the tests have little power, so a non-significant result does not show that methods are equivalent. "l = 1" uses one lag; "free l" lets BIC choose the lag order.</p>', unsafe_allow_html=True)
    if design == "gamma_bic":
        st.markdown("#### γ = 1 against γ chosen by BIC")
        rows = []
        for fam, a, b in [("adaLASSO (l=1)", "adalasso (l=1)", "adalasso_g (l=1)"), ("adaLASSO (free l)", "adalasso (free l)", "adalasso_g (free l)"),
                          ("WLadaLASSO (free l)", "wladalasso (free l)", "wladalasso_g (free l)"), ("Ext1 (free l)", "ext1 (free l)", "ext1_g (free l)")]:
            for st_ in starts:
                x = r2[(r2.model == a) & (r2.start == st_)].R2_OS.iloc[0]; y = r2[(r2.model == b) & (r2.start == st_)].R2_OS.iloc[0]
                rows.append(dict(method=fam, start=st_, **{"R²_OS γ = 1": x, "R²_OS γ by BIC": y, "difference": y - x}))
        cmpdf = pd.DataFrame(rows)
        fig = go.Figure()
        for st_ in starts:
            q = cmpdf[cmpdf.start == st_]
            fig.add_bar(x=q.method, y=q["difference"], name=f"start {st_}")
        fig.update_layout(barmode="group", height=380, title="Change in R²_OS when γ is chosen by BIC (negative = worse)", legend=dict(orientation="h", y=1.15))
        fig.add_hline(y=0, line_color=MUTED)
        st.plotly_chart(fig, width="stretch")
        tables.show(cmpdf, fmt="%.3f", key="eq_gcmp", download="equity_gamma_comparison.csv")
        st.markdown(f'<p class="small">R²_OS is lower with γ by BIC in {int((cmpdf["difference"] < 0).sum())} of {len(cmpdf)} comparisons in this version. '
                    'BIC picked the largest γ in the grid (3) in most fits (see Selected models), so the grid edge matters. The γ = 1 rows are identical to the main run.</p>', unsafe_allow_html=True)

with tab_paper:
    st.markdown("### Published values against ours")
    st.markdown('<p class="small">Published values are Table X of Konzen and Ziegelmann (2016), typed into the notebook for this comparison. The paper has no Ext1 row. '
                'Our columns are the data version selected in the sidebar.</p>', unsafe_allow_html=True)
    P = D["paper"].copy()
    P["model"] = P.row.map(dl.EQ_PAPER_NAMES)
    P = P.dropna(subset=["model"])
    which = st.radio("Rows", ["Penalised methods", "All rows"], horizontal=True)
    if which.startswith("Pen"):
        P = P[P.model.isin(["lasso (l=1)", "adalasso (l=1)", "lasso (free l)", "adalasso (free l)", "wladalasso (free l)"])]
    fig = go.Figure()
    for st_, sym in zip(sorted(P.start.unique()), ["circle", "square", "diamond"]):
        q = P[P.start == st_]
        fig.add_scatter(x=q.paper_R2, y=q.our_R2, mode="markers", name=f"start {st_}", marker=dict(size=10, symbol=sym),
                        text=q.row, hovertemplate="%{text}<br>paper %{x:.3f}<br>ours %{y:.3f}<extra></extra>")
    lo = float(min(P.paper_R2.min(), P.our_R2.min())); hi = float(max(P.paper_R2.max(), P.our_R2.max()))
    fig.add_scatter(x=[lo, hi], y=[lo, hi], mode="lines", line=dict(color=MUTED, dash="dash"), name="equal values", hoverinfo="skip")
    fig.update_layout(height=470, xaxis_title="published R²_OS", yaxis_title="our R²_OS", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, width="stretch")
    show = P[["row", "start", "paper_R2", "paper_p", "our_R2", "our_p", "gap"]].rename(columns={"row": "row", "paper_R2": "published R²", "paper_p": "published p", "our_R2": "our R²", "our_p": "our p", "gap": "our − published"})
    tables.show(show, fmt="%.3f", download=f"equity_vs_paper_{version}.csv", key="eq_paper")
    pp = P[P.row.isin(["LASSO (l=1)", "adaLASSO (l=1)", "LASSO (free l)", "adaLASSO (free l)", "WLadaLASSO (free l)"])]
    st.markdown(f'<p class="small">For the five penalised rows the paper reports R² between {pp.paper_R2.min():.3f} and {pp.paper_R2.max():.3f}; ours lie between {pp.our_R2.min():.3f} and {pp.our_R2.max():.3f}. '
                'We tested the code (14 unit tests), the data vintage, three premium definitions, a differenced premium and several constructions of the OLS rows; none brought the penalised values near the published ones. '
                'One variant (a differenced premium) reached the published size, but we found that this happens mechanically, so we do not treat it as a replication. These earlier checks used a coarser λ grid and are described in the report.</p>', unsafe_allow_html=True)

with tab_pred:
    st.markdown("### Individual predictors and the model with all 14 regressors")
    base = [m for m in dl.EQ_MODELS if m not in pen and m in r2.model.unique()]
    d = r2[r2.model.isin(base)]
    piv = d.pivot(index="label", columns="start", values="R2_OS").reindex([dl.EQ_MODELS[m] for m in base])
    piv.columns = [f"start {c}" for c in piv.columns]
    st.plotly_chart(charts.heat(piv, "R²_OS", "R²_OS of single-predictor regressions and OLS", zmid=0), width="stretch")
    pv = d.pivot(index="label", columns="start", values="p_MDM").reindex(piv.index); pv.columns = [f"p {c}" for c in pv.columns]
    tables.show(pd.concat([piv, pv], axis=1).reset_index().rename(columns={"label": "predictor"}), fmt="%.3f", key="eq_pred", download=f"equity_predictors_{version}.csv")
    st.markdown('<p class="small">The OLS rows also differ from the paper (all 14 predictors: about −0.22 to −0.40 here, −1.06 to −1.27 there).</p>', unsafe_allow_html=True)

with tab_sel:
    st.markdown("### What the penalised models selected")
    sel = D["selection"].copy()
    tables.show(sel.drop(columns=["version"], errors="ignore"), fmt="%.3f", key="eq_sel", download=f"equity_selection_{version}.csv")
    per = D["per_origin"].copy()
    per["label"] = per.method.map({"lasso": "LASSO", "adalasso": "adaLASSO", "wladalasso": "WLadaLASSO", "ext1": "Ext1",
                                    "adalasso_g": "adaLASSO (γ by BIC)", "wladalasso_g": "WLadaLASSO (γ by BIC)", "ext1_g": "Ext1 (γ by BIC)"})
    st.markdown("#### Lag order chosen at each forecast origin (free-l fits)")
    labels = [l for l in per.label.dropna().unique()]
    pick = st.multiselect("Methods", labels, default=[l for l in ["adaLASSO", "WLadaLASSO", "Ext1"] if l in labels])
    fig = go.Figure()
    for l in pick:
        q = per[per.label == l]
        fig.add_scatter(x=q.year, y=q.L, mode="lines", name=l, line=dict(color=COLORS.get(l), width=2))
    fig.update_layout(height=380, xaxis_title="forecast origin (year)", yaxis_title="lag order L chosen by BIC", legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, width="stretch")
    if design == "gamma_bic":
        g = per[per.method.str.endswith("_g")].groupby("label").gamma.apply(lambda s: (s == 3).mean()).rename("share of fits with γ = 3").reset_index()
        st.markdown("#### γ chosen by BIC")
        tables.show(g, fmt="%.2f", key="eq_g3")
        st.markdown('<p class="small">γ = 3 is the largest value in the grid, so we cannot tell whether a wider grid would change the picture.</p>', unsafe_allow_html=True)
    st.markdown('<p class="small">The selection files cover the free-l fits from the first forecast origin (1955) onwards.</p>', unsafe_allow_html=True)


with tab_exp:
    st.markdown("### Does the data version change the story?")
    st.markdown("Choose methods and a significance level. Each bar is an out-of-sample R² (positive = beats the historical mean); a ★ marks values whose one-sided modified Diebold-Mariano p-value is below your level. "
                "The three data versions sit side by side so you can see how much the answer depends on the data treatment.")
    allD = {v: dl.load_equity(design, v)["r2os"] for v in dl.EQ_VERSIONS}
    avail = [m for m in (dl.EQ_PENALISED + (dl.EQ_PENALISED_G if design == "gamma_bic" else []) + ["All regressors", "tms", "svar", "d/p"]) if m in allD[version].model.unique()]
    c1, c2 = st.columns([3, 1])
    picks = c1.multiselect("Models", avail, default=[m for m in ["adalasso (free l)", "wladalasso (free l)", "ext1 (free l)"] if m in avail], format_func=lambda m: dl.EQ_MODELS.get(m, m))
    alpha_sig = c2.select_slider("Significance level", [0.01, 0.05, 0.10, 0.20], value=0.10)
    start_sel = st.radio("Evaluation starts in", starts, horizontal=True, index=0)
    if not picks:
        st.info("Pick at least one model.")
    else:
        fig = go.Figure()
        vcols = {"original_2005": "#A9E3C4", "current_crsp": "#4CC38A", "current_index": "#2F8F63"}
        stars = 0; total = 0
        for v, lab in dl.EQ_VERSIONS.items():
            d = allD[v][(allD[v].start == start_sel) & allD[v].model.isin(picks)].set_index("model").reindex(picks)
            txt = ["★" if p < alpha_sig else "" for p in d.p_MDM]
            stars += sum(1 for t in txt if t); total += len(txt)
            fig.add_bar(x=[dl.EQ_MODELS.get(m, m) for m in picks], y=d.R2_OS, name=lab, marker_color=vcols[v], text=txt, textposition="outside", textfont=dict(size=18, color="#E9A93B"),
                        hovertemplate="%{x}<br>" + lab + "<br>R²_OS %{y:.3f}<extra></extra>")
        fig.add_hline(y=0, line_color=MUTED)
        fig.update_layout(barmode="group", height=440, yaxis_title="R²_OS against the historical mean", legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig, width="stretch")
        best_row = pd.concat([allD[v].assign(ver=v) for v in dl.EQ_VERSIONS]).query("start == @start_sel and model in @picks").sort_values("R2_OS", ascending=False).iloc[0]
        ui.tiles([("Highest R²_OS shown", f"{best_row.R2_OS:+.3f}", f"{dl.EQ_MODELS.get(best_row.model, best_row.model)}, {dl.EQ_VERSIONS[best_row.ver]}", "#D2EC9C"),
                  (f"Significant at {alpha_sig:.0%}", f"{stars} of {total}", "unadjusted for multiple tests", "#E9A93B"),
                  ("Evaluation start", str(start_sel), f"{2005 - int(start_sel) + 1} annual forecasts", None)])
    st.markdown('<p class="small">With 21 to 51 annual forecasts the tests have little power. Bars are saved results; nothing is recomputed here.</p>', unsafe_allow_html=True)
