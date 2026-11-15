import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from components.theme import setup_page, header, note, COLORS
from components.navigation import sidebar_footer
from components import ui
from calculations import engine as en

setup_page("Live lab")
sidebar_footer()
header("Interactive", "Live lab: simulate a data set and fit all four methods",
       "Change the data design or the penalty settings; the app generates a fresh data set from the paper's equation (10) and fits LASSO, adaLASSO, WLadaLASSO and Ext1 "
       "right now, in your browser. See which variables each method picks, how the penalties differ, and how well each forecasts.")
note("This lab fits <b>one simulated data set</b> (or a few, in the last tab) with a compact re-implementation of the estimators. It is for building intuition and is "
     "<b>not</b> the study: the study's saved results average 1,000 such data sets and are in the Monte Carlo page.")

def _next_seed():
    st.session_state.seed += 1


if "seed" not in st.session_state:
    st.session_state.seed = 2016

with st.sidebar:
    st.markdown("### Data design")
    T = st.select_slider("Sample size T", [50, 100, 200, 500], value=50, help="Number of observations. T = 50 is the small-sample case where the paper expects the biggest gains.")
    L = st.select_slider("Lags L", [5, 10, 20], value=10, help="Every series enters with lags 1..L; 11·L candidate regressors.")
    rho = st.slider("Predictor persistence ρ (rho)", 0.0, 0.95, 0.9, 0.05, help="AR(1) coefficient of the ten predictors. High ρ ⇒ strongly correlated regressors.")
    err = st.radio("Error law", ["normal", "t5"], horizontal=True, format_func=lambda v: "Normal" if v == "normal" else "Student-t (5 df)")
    noise = st.slider("Noise level", 0.5, 3.0, 1.0, 0.25, help="Scale of the error in the y equation.")
    c1, c2 = st.columns([2, 1])
    c1.number_input("Random seed", min_value=0, step=1, key="seed")
    c2.button("🎲", help="New random draw", use_container_width=True, on_click=_next_seed)
    st.markdown("### Penalty settings")
    gamma = st.select_slider("γ (gamma): strength of adaptive weights", [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0], value=1.0, help="Exponent on the ridge-based weight. The paper uses γ = 1.")
    tune = st.radio("α (alpha) and κ (kappa)", ["Fixed by sliders", "Chosen by BIC over a grid"], help="BIC chooses α (alpha) and κ (kappa) from a 9- and a 6-value grid (the study uses 17 and 9). Slower.") .startswith("Chosen")
    alpha = st.select_slider("α (alpha): WLadaLASSO lag penalty", en.ALPHA_GRID, value=1.0, disabled=tune)
    kappa = st.select_slider("κ (kappa): Ext1 lag penalty", en.KAPPA_GRID, value=1.0, disabled=tune)


@st.cache_data(show_spinner=False, max_entries=60)
def run(seed, T, L, rho, err, noise, gamma, alpha, kappa, tune):
    return en.run_replication(seed, T, L, rho, err, noise, gamma=gamma, alpha=alpha, kappa=kappa, tune=tune)


with st.spinner("Simulating and fitting four methods…"):
    R = run(int(st.session_state.seed), T, L, rho, err, noise, gamma, alpha, kappa, tune)
res = R["res"]
mm = {"LASSO": "LASSO", "adaLASSO": "adaLASSO", "WLadaLASSO": "WLadaLASSO", "Ext1": "Ext1"}
best = min(res, key=lambda m: res[m]["msfe"])

items = []
for m in en.METHODS:
    r = res[m]; f = R["first"]["fits"][m]
    hyper = f"  ·  {'α (alpha)' if m == 'WLadaLASSO' else 'κ (kappa)'} = {f['hyper']:g}" if f["hyper"] is not None else ""
    items.append((f"{m}{hyper}", f"{r['msfe']:.3f}" + (" ★" if m == best else ""), f"recall {r['recall']:.0%} · irrelevant dropped {r['FIVE']:.0%} · {r['NIV']} selected", COLORS[m]))
st.markdown("##### Forecast error (MSFE over 10 one-step forecasts) and selection quality, this data set")
ui.tiles(items)
st.markdown(f'<p class="small">p = {11 * L} candidate regressors, 10 truly relevant; training sample ≈ {T - 10} observations. ★ lowest forecast error on this draw. '
            'Press 🎲 or change a slider to see how noisy a single draw is.</p>', unsafe_allow_html=True)

t_sel, t_w, t_bic, t_fc, t_mc = st.tabs(["🧩 What was selected", "🎚️ Penalty weights", "🎯 BIC choice", "🔭 Forecasts", "🔁 Repeat many times"])

lag_order = R["first"]["lag_order"]
names = ["y"] + [f"x{i}" for i in range(1, 11)]


def grid(vec):
    return np.asarray(vec).reshape(11, L)


with t_sel:
    st.markdown("Each small square is one regressor: a series (row) at a lag (column). **Colour = estimated coefficient** (amber positive, blue negative, dark = zero). "
                "The **Truth** panel is the answer key; compare each method with it.")
    st.markdown('<p class="small"><b style="color:#FF7B72">✕</b> = false alarm (an irrelevant regressor was selected) &nbsp;·&nbsp; '
                '<b style="color:#fff">○</b> = missed (a relevant regressor was set to zero)</p>', unsafe_allow_html=True)
    T_ = grid(R["b_true"]) != 0
    panels = [("Truth (answer key)", R["b_true"])] + [(m, R["first"]["coef"][m]) for m in en.METHODS]
    titles = [panels[0][0]]
    for m, v in panels[1:]:
        S_ = grid(v) != 0
        titles.append(f"{m}<br><sup>found {int((S_ & T_).sum())}/{int(T_.sum())} · false alarms {int((S_ & ~T_).sum())}</sup>")
    zmax = min(max(0.8, max(np.abs(v).max() for _, v in panels)), 1.5)
    fig = make_subplots(rows=2, cols=3, subplot_titles=titles, vertical_spacing=0.2, horizontal_spacing=0.06)
    for i, (title, v) in enumerate(panels):
        r_, c_ = i // 3 + 1, i % 3 + 1
        G = grid(v)
        fig.add_trace(go.Heatmap(z=np.where(G == 0, np.nan, G), x=list(range(1, L + 1)), y=names, zmin=-zmax, zmax=zmax,
                                 colorscale=[[0, "#4F9FD0"], [0.5, "#CFE3D6"], [1, "#F2A93B"]], showscale=(i == 0),
                                 colorbar=dict(len=.4, y=.8, title="coef"), hovertemplate="%{y}, lag %{x}: %{z:.3f}<extra>" + title.split("<")[0] + "</extra>",
                                 xgap=2, ygap=2), row=r_, col=c_)
        if i > 0:
            S_ = G != 0
            fp = np.argwhere(S_ & ~T_); fn = np.argwhere(~S_ & T_)
            if len(fp):
                fig.add_trace(go.Scatter(x=fp[:, 1] + 1, y=[names[k] for k in fp[:, 0]], mode="markers", marker=dict(symbol="x", size=10, color="#FF7B72", line=dict(width=2, color="#FF7B72")), showlegend=False, hoverinfo="skip"), row=r_, col=c_)
            if len(fn):
                fig.add_trace(go.Scatter(x=fn[:, 1] + 1, y=[names[k] for k in fn[:, 0]], mode="markers", marker=dict(symbol="circle-open", size=12, color="#FFFFFF", line=dict(width=2.2, color="#FFFFFF")), showlegend=False, hoverinfo="skip"), row=r_, col=c_)
        fig.update_yaxes(autorange="reversed", row=r_, col=c_, tickfont=dict(size=10), showgrid=False)
        fig.update_xaxes(title_text="lag (periods back)" if r_ == 2 else None, row=r_, col=c_, dtick=max(1, L // 5), showgrid=False)
    fig.update_layout(height=700, margin=dict(t=70))
    st.plotly_chart(fig, width="stretch")
    st.markdown('<p class="small">Rows: "y" is the forecast variable\'s own past, x₁…x₁₀ are the predictors. Zero coefficients are left as dark empty squares. '
                'Truth: y\'s own lag 1, lags 1-2 of x₁, x₂, x₃ and lag 1 of x₄, x₅, x₆ are relevant (10 coefficients); x₇…x₁₀ and later lags are zero. '
                'Raise α (alpha) or κ (kappa) to see the lag-penalising methods zero out distant lags.</p>', unsafe_allow_html=True)

with t_w:
    st.markdown("Penalty weight w (shown as ln w) that each method assigned, **averaged by lag**. A higher weight means the regressor is charged more and is less likely to survive. "
                "The gap between the green line (truly relevant regressors) and the grey line (all regressors) shows whether weights separate relevant from irrelevant.")
    rel = R["b_true"] != 0
    fig = make_subplots(rows=1, cols=3, subplot_titles=["adaLASSO", "WLadaLASSO", "Ext1"], shared_yaxes=True)
    for i, m in enumerate(["adaLASSO", "WLadaLASSO", "Ext1"]):
        lw = R["first"]["fits"][m]["logw"]
        lags = np.arange(1, L + 1)
        allm = [lw[lag_order == l].mean() for l in lags]
        relm = [lw[(lag_order == l) & rel].mean() if np.any((lag_order == l) & rel) else np.nan for l in lags]
        fig.add_trace(go.Scatter(x=lags, y=allm, mode="lines+markers", name="all regressors", line=dict(color="#93A89A"), showlegend=(i == 0)), row=1, col=i + 1)
        fig.add_trace(go.Scatter(x=lags, y=relm, mode="lines+markers", name="truly relevant", line=dict(color="#B8DC6B"), showlegend=(i == 0)), row=1, col=i + 1)
        fig.update_xaxes(title_text="lag", row=1, col=i + 1)
    fig.update_yaxes(title_text="mean ln w (relative)", row=1, col=1)
    fig.update_layout(height=380, legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig, width="stretch")
    cap = [m for m in ("adaLASSO", "WLadaLASSO", "Ext1") if R["first"]["fits"][m]["logw"].max() >= en.LOGW_CAP - 1e-9]
    if cap:
        st.markdown(f'<p class="small">Weights of {", ".join(cap)} reached the cap of ln w = 25 used in the notebook for some regressors.</p>', unsafe_allow_html=True)

with t_bic:
    m = st.radio("Method", list(en.METHODS), horizontal=True, key="bicm")
    f = R["first"]["fits"][m]
    bic = np.where(np.isfinite(f["bic_path"]), f["bic_path"], np.nan)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=f["lams"], y=bic, mode="lines", line=dict(color=COLORS[m], width=2.5), name="BIC", hovertemplate="λ=%{x:.4f}<br>BIC=%{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[f["lams"][f["j"]]], y=[f["bic"]], mode="markers", marker=dict(size=13, color="#fff", line=dict(width=2, color=COLORS[m])), name=f"chosen: {f['k']} variables"))
    fig.update_xaxes(type="log", title="penalty λ (large ⇒ fewer variables)", autorange="reversed")
    fig.update_yaxes(title="BIC")
    fig.update_layout(height=380, legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, width="stretch")
    st.markdown(f'<p class="small">BIC is minimal at {f["k"]} non-zero coefficients. Gaps mean paths stopped once more than n/2 coefficients were non-zero (not allowed). '
                + ("α/κ was chosen by BIC over the grid." if tune and f["hyper"] is not None else "") + "</p>", unsafe_allow_html=True)

with t_fc:
    actual = R["actual"]
    fig = go.Figure()
    x = list(range(1, len(actual) + 1))
    fig.add_trace(go.Scatter(x=x, y=actual, mode="lines+markers", name="actual", line=dict(color="#EAF1E8", width=3)))
    for m in en.METHODS:
        fig.add_trace(go.Scatter(x=x, y=res[m]["pred"], mode="lines+markers", name=m, line=dict(color=COLORS[m], width=1.8, dash="dot")))
    fig.update_layout(height=400, xaxis_title="forecast #", yaxis_title="y", legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, width="stretch")
    st.dataframe(pd.DataFrame({m: dict(MSFE=res[m]["msfe"], MAE=res[m]["mae"], recall=res[m]["recall"], FIVE=res[m]["FIVE"], selected=res[m]["NIV"], precision=res[m]["precision"]) for m in en.METHODS}).T.round(3), width="stretch")

with t_mc:
    st.markdown("One data set is noisy. Repeat the experiment with new random draws and the **current** settings to see the typical outcome. "
                "(The study does this 1,000 times for every scenario.)")
    n_rep = st.slider("Number of repetitions", 5, 40, 10)
    est = R['seconds'] * n_rep
    st.markdown(f'<p class="small">Estimated time at these settings: about {est:.0f} s (this data set took {R["seconds"]:.1f} s to fit; finished repetitions are cached).</p>', unsafe_allow_html=True)
    if st.button("▶ Run repetitions", type="primary"):
        rows, bar = [], st.progress(0.0, text="running…")
        for k in range(n_rep):
            rr = run(int(st.session_state.seed) + 1000 + k, T, L, rho, err, noise, gamma, alpha, kappa, tune)["res"]
            for m in en.METHODS:
                rows.append(dict(method=m, rep=k, MSFE=rr[m]["msfe"], recall=rr[m]["recall"], FIVE=rr[m]["FIVE"], NIV=rr[m]["NIV"]))
            bar.progress((k + 1) / n_rep, text=f"repetition {k + 1} of {n_rep}")
        bar.empty()
        st.session_state["mc_rows"] = (pd.DataFrame(rows), (T, L, rho, err, noise, gamma, alpha, kappa, tune, n_rep))
    if "mc_rows" in st.session_state:
        df, sig = st.session_state["mc_rows"]
        if sig != (T, L, rho, err, noise, gamma, alpha, kappa, tune, n_rep):
            st.info("Settings changed since this run; press Run again to update.")
        c1, c2 = st.columns(2)
        fig = go.Figure()
        for m in en.METHODS:
            fig.add_trace(go.Box(y=df[df.method == m].MSFE, name=m, marker_color=COLORS[m], boxmean=True, boxpoints="all", jitter=.4, pointpos=0, marker_size=4))
        fig.update_layout(height=380, title="MSFE across repetitions", showlegend=False, yaxis=dict(rangemode="tozero"))
        c1.plotly_chart(fig, width="stretch")
        agg = df.groupby("method")[["MSFE", "recall", "FIVE", "NIV"]].mean().reindex(en.METHODS)
        fig2 = go.Figure()
        fig2.add_bar(x=agg.index, y=agg.recall, name="recall (relevant found)", marker_color="#B8DC6B")
        fig2.add_bar(x=agg.index, y=agg.FIVE, name="irrelevant dropped", marker_color="#4CC38A")
        fig2.update_layout(height=380, barmode="group", title="Selection quality (mean)", legend=dict(orientation="h", y=-0.15), yaxis=dict(range=[0, 1]))
        c2.plotly_chart(fig2, width="stretch")
        wins = df.pivot(index="rep", columns="method", values="MSFE").idxmin(axis=1).value_counts().reindex(en.METHODS).fillna(0).astype(int)
        st.markdown("**Lowest MSFE in how many repetitions:** " + " · ".join(f"{m} {int(wins[m])}" for m in en.METHODS))
        st.dataframe(agg.round(3), width="stretch")
