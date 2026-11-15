import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from components import ui
from components.theme import setup_page, header, note, COLORS
from components.navigation import sidebar_footer
from components import charts, tables
from utils import data_loader as dl
from utils.validation import DataProblem
from components.charts import scenario_label

setup_page("Monte Carlo")
sidebar_footer()
header("Explore", "Monte Carlo explorer",
       "Simulated data from the design of Konzen and Ziegelmann (2016, eq. 10): ten AR(1) predictors, one series y that depends on six of them and on its own past, "
       "so 10 of the 11L candidate regressors are relevant. Every method sees the same simulated series.")

design = st.radio("Experiment", ["Main experiment: γ (gamma) = 1, 1,000 replications", "Separate experiment: γ (gamma) chosen by BIC, 300 replications"], horizontal=True)
kind = "fixed" if design.startswith("Main") else "gamma_bic"
if kind == "gamma_bic":
    note("This is a <b>separate run</b>. It was stopped before finishing: only the 8 scenarios below with all 300 replications are shown "
         "(all six with ρ = 0.3, and ρ = 0.9, T = 50 with L = 5 and 10). Its numbers are not comparable with the 1,000-replication run, "
         "which averages over more replications.", "warn")

try:
    rep = dl.load_mc_replications(kind)
    comp = dl.load_mc_completion(kind)
except DataProblem as e:
    st.error(f"Data problem: {e}")
    st.stop()

variants_in = [m for m in dl.MC_METHODS.values() if m in rep.method.unique()]
default_methods = ["LASSO", "adaLASSO", "WLadaLASSO", "Ext1"] if kind == "fixed" else ["adaLASSO", "adaLASSO (γ by BIC)", "WLadaLASSO", "WLadaLASSO (γ by BIC)", "Ext1", "Ext1 (γ by BIC)"]

with st.sidebar:
    st.markdown("### Filters")
    Ts = st.multiselect("Sample size T", sorted(rep["T"].unique()), default=sorted(rep["T"].unique()))
    rhos = st.multiselect("Dependence ρ (rho)", sorted(rep.rho.unique()), default=sorted(rep.rho.unique()))
    Ls = st.multiselect("Lag order L", sorted(rep.L.unique()), default=sorted(rep.L.unique()))
    methods = st.multiselect("Methods", variants_in, default=[m for m in default_methods if m in variants_in])
    metric = st.selectbox("Metric", list(dl.MC_METRICS), format_func=lambda c: dl.MC_METRICS[c][0])
    stat = st.radio("Summary over replications", ["mean", "median"], horizontal=True)

sel = rep[rep["T"].isin(Ts) & rep.rho.isin(rhos) & rep.L.isin(Ls) & rep.method.isin(methods)]
if sel.empty or not methods:
    st.warning("The current filters leave nothing to show. Widen the selection in the sidebar.")
    st.stop()
label, better = dl.MC_METRICS[metric]
hint = {True: "higher is better", False: "lower is better", None: "the true value is 10"}[better]

tab_map, tab_sum, tab_box, tab_paired, tab_more = st.tabs(["🗺️ Scenario map", "Summary", "Replication-level distributions", "Paired comparisons", "Completion and diagnostics"])

with tab_sum:
    st.markdown(f"### {label}")
    st.markdown(f'<p class="small">{stat.capitalize()} over replications ({hint}). Scenarios: {sel.groupby(["rho","T","L"]).ngroups}; methods: {len(methods)}.</p>', unsafe_allow_html=True)
    agg = sel.groupby(["rho", "T", "L", "method"])[metric].agg(stat).rename("value").reset_index()
    st.plotly_chart(charts.bars_by_scenario(agg, label, methods, log_y=False), width="stretch")
    wide = agg.pivot_table(index=["T", "rho", "L"], columns="method", values="value")[methods].reset_index()
    best = wide[methods].idxmax(axis=1) if better else (wide[methods].idxmin(axis=1) if better is False else None)
    if best is not None:
        wide["best"] = best
    tables.show(wide, fmt="%.4f", download=f"monte_carlo_{kind}_{metric}_{stat}.csv", key="mc_dl")
    n_rep = sel.groupby(["rho", "T", "L", "method"]).rep.nunique()
    st.markdown(f'<p class="small">Each value averages {int(n_rep.min())} to {int(n_rep.max())} replications per scenario and method.</p>', unsafe_allow_html=True)
    if metric in ("fc_mse",) and kind == "fixed":
        st.markdown("#### Relative to adaLASSO")
        base = agg[agg.method == "adaLASSO"].set_index(["rho", "T", "L"]).value
        if "adaLASSO" in methods:
            rel = agg.copy()
            rel["value"] = rel.apply(lambda r: r.value / base[(r.rho, r["T"], r.L)], axis=1)
            st.plotly_chart(charts.bars_by_scenario(rel, "MSFE / MSFE of adaLASSO", methods), width="stretch")
            st.markdown('<p class="small">Values below 1 are better than adaLASSO (the same quantity as Figure 1 of the report).</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="small">Add adaLASSO to the selected methods to see the ratio.</p>', unsafe_allow_html=True)

with tab_box:
    st.markdown(f"### {label} in every replication")
    if sel.groupby(["rho", "T", "L"]).ngroups > 12:
        st.warning("Too many panels.")
    trim = st.checkbox("Cut the vertical axis at the 99th percentile of each panel (outliers are not drawn)", value=True)
    discrete = metric in ("TMI",)
    if discrete:
        st.info("TMI is 0 or 1 in each replication, so a boxplot is not informative. Use the Summary tab.")
    else:
        st.plotly_chart(charts.boxplots(sel, metric, label, methods, trim=trim), width="stretch")
        st.markdown('<p class="small">Box: quartiles. Line: median. Dashed line and diamond: mean. Each panel has its own vertical axis, so heights can be compared only inside a panel.</p>', unsafe_allow_html=True)
    if kind == "fixed":
        with st.expander("The consolidated 12-panel boxplot produced by the notebook (MSFE, all 12 scenarios)"):
            st.image(f"{dl.ASSETS}/mc_msfe_boxplots_1000.png", width="stretch")
            st.markdown('<p class="small">Saved figure from the main run, unchanged. Whiskers are 1.5 × IQR and each panel is cut at its 99th percentile.</p>', unsafe_allow_html=True)

with tab_paired:
    if kind == "fixed":
        st.markdown("### Paired comparisons on the same replications")
        p = dl.load_csv("monte_carlo/paired_msfe_comparisons.csv")
        p = p[p["T"].isin(Ts) & p.rho.isin(rhos) & p.L.isin(Ls)]
        contrast = st.selectbox("Comparison", sorted(p.contrast.unique()), index=sorted(p.contrast.unique()).index("WLadaLASSO vs adaLASSO"))
        q = p[p.contrast == contrast].sort_values(["T", "rho", "L"])
        show = q[["T", "rho", "L", "mean_first", "mean_second", "ratio", "share_first_lower", "share_tied", "mean_diff", "se_diff"]].rename(columns={
            "mean_first": "mean MSFE first", "mean_second": "mean MSFE second", "ratio": "ratio first/second",
            "share_first_lower": "share first lower", "share_tied": "share tied", "mean_diff": "mean diff", "se_diff": "s.e. of diff"})
        tables.show(show, fmt="%.4f", download="monte_carlo_paired.csv", key="mc_pd")
        st.markdown('<p class="small">Ratio below 1: the first method has the lower average MSFE. "Share first lower" counts replications where the first method is strictly better; '
                    'exact ties are shown separately. The standard error treats replications as independent; these are descriptive, and no multiple-testing adjustment is made.</p>', unsafe_allow_html=True)
        note("In Table 1 of the report, the last column (WLadaLASSO vs Ext1) counts exact ties as WLadaLASSO wins, so its percentages are 0.5 to 2.5 points higher than the strict shares here. The conclusions do not change.")
    else:
        st.markdown("### γ chosen by BIC against γ = 1, on identical replications")
        p = dl.load_csv("gamma_bic_monte_carlo/paired_gamma_bic_vs_gamma1.csv")
        p = p[p["T"].isin(Ts) & p.rho.isin(rhos) & p.L.isin(Ls)].copy()
        p["change in MSFE (%)"] = (p.ratio - 1) * 100
        fam = {"adalasso": "adaLASSO", "wladalasso": "WLadaLASSO", "ext1": "Ext1"}
        p["method"] = p.family.map(fam)
        fig = charts.grouped_bars(p.assign(scenario=scenario_label(p)).sort_values(["T", "rho", "L"]), "scenario", "change in MSFE (%)", "method",
                                  order=["adaLASSO", "WLadaLASSO", "Ext1"], title="Change in mean MSFE when γ is chosen by BIC (positive = worse)", yname="%")
        st.plotly_chart(fig, width="stretch")
        tables.show(p[["T", "rho", "L", "method", "mean_gamma1", "mean_gammaBIC", "change in MSFE (%)", "share_gammaBIC_lower", "p_paired_t_two_sided"]].sort_values(["method", "T", "rho", "L"]),
                    fmt="%.4f", download="gamma_bic_paired.csv", key="gb_pd")
        st.markdown('<p class="small">BIC is lower at the chosen γ by construction (γ = 1 is in the grid), but forecasts were worse at T = 50 in every scenario and changed by less than 1% at T = 500. '
                    'p-values are paired t-tests across replications, descriptive and unadjusted. The grid maximum γ = 3 was picked often (see below), so a wider grid is untested.</p>', unsafe_allow_html=True)
        g = dl.load_csv("gamma_bic_monte_carlo/summary_by_scenario.csv")
        g = g[g.variant.str.endswith("_g") & g["T"].isin(Ts) & g.rho.isin(rhos) & g.L.isin(Ls)].copy()
        g["method"] = g.variant.map(dl.MC_METHODS)
        st.markdown("#### Share of fits that chose γ = 3 (the largest value in the grid)")
        tables.show(g.pivot_table(index=["T", "rho", "L"], columns="method", values="share_gamma_3").reset_index(), fmt="%.2f", key="gb_g3")

with tab_more:
    st.markdown("### Completion by scenario")
    tables.show(comp.sort_values(["rho", "T", "L"]), key="mc_comp", download=f"completion_{kind}.csv")
    if kind == "gamma_bic":
        st.markdown('<p class="small">The scenario with 240 of 300 replications is incomplete and excluded from all results; the three ρ = 0.9, T = 500 scenarios were not run.</p>', unsafe_allow_html=True)
    if kind == "fixed":
        st.markdown("### Boundary diagnostics")
        st.markdown('<p class="small">Share of fits whose selected tuning value lay on the edge of its grid (diagnostic only; nothing was changed).</p>', unsafe_allow_html=True)
        b = dl.load_csv("monte_carlo/boundary_diagnostics_by_scenario.csv")
        b = b[b["T"].isin(Ts) & b.rho.isin(rhos) & b.L.isin(Ls)]
        tables.show(b, fmt="%.3f", key="mc_bd", download="boundary_diagnostics.csv")
    meta = dl.load_json(f"{'monte_carlo' if kind == 'fixed' else 'gamma_bic_monte_carlo'}/run_metadata.json")
    s = meta["settings"]
    st.markdown("### Settings of this run")
    st.markdown(f"- Seed {s['seed']}; criterion {s['criterion']}; γ grid {s['gamma_grid']}\n- α grid ({len(s['alpha_grid'])} values) {s['alpha_grid'][0]} to {s['alpha_grid'][-1]}; κ grid ({len(s['kappa_grid'])} values) {s['kappa_grid'][0]} to {s['kappa_grid'][-1]}\n"
                f"- λ grid: {s['lambda_grid']['n_lambda']} log-spaced values, ratio {s['lambda_grid']['eps']:g}\n- Replications per scenario: {s['monte_carlo']['n_rep']}; one-step forecasts of the last {s['monte_carlo']['n_test']} observations, refit every {s['monte_carlo']['refit_every']} forecasts; normal errors\n"
                f"- Run status in the file: {meta['status']}" + ("  (the run was stopped before finishing; see the completion table)" if meta["status"] != "completed" else ""))


# ------------------------------------------------------------------ interactive scenario map and drill-down
with tab_map:
    four = [m for m in ["LASSO", "adaLASSO", "WLadaLASSO", "Ext1"] if m in rep.method.unique()]
    st.markdown("### Where does one method beat another?")
    st.markdown("Pick two methods and a metric. Each cell is one simulation scenario; the colour shows how much the first method changes the average of the metric relative to the second. "
                "<b>Blue = the first method is better</b>. Pick a scenario below the map to drill into its 1,000 replications.", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    A = c1.selectbox("First method", four, index=min(2, len(four) - 1))
    B = c2.selectbox("Compared with", [m for m in four if m != A], index=min(1, len(four) - 2))
    mk = c3.selectbox("Metric ", list(dl.MC_METRICS)[:10], format_func=lambda c: dl.MC_METRICS[c][0].split(":")[0].split(" (")[0], key="mapmetric")
    lab_m, better_m = dl.MC_METRICS[mk]
    g = rep[rep.method.isin([A, B])].groupby(["T", "rho", "L", "method"])[mk].mean().unstack("method").dropna()
    g["pct"] = 100 * (g[A] / g[B] - 1)
    sign = -1 if better_m in (False, None) else 1          # lower-is-better metrics: a negative change is an improvement
    g["good"] = sign * g["pct"]
    g = g.reset_index()
    g["col"] = "T=" + g["T"].astype(int).astype(str) + ", ρ=" + g.rho.astype(str)
    cols = sorted(g.col.unique(), key=lambda c: (int(c.split(",")[0][2:]), float(c.split("=")[-1])))
    Zm = g.pivot(index="L", columns="col", values="good").reindex(columns=cols)
    Tx = g.pivot(index="L", columns="col", values="pct").reindex(columns=cols)
    lim = max(5, float(np.nanmax(np.abs(Zm.values))))
    fig = go.Figure(go.Heatmap(z=Zm.values, x=cols, y=[f"L={int(l)}" for l in Zm.index], zmin=-lim, zmax=lim, colorscale=[[0, "#E06C75"], [0.5, "#142219"], [1, "#4CC38A"]],
                               text=[[f"{v:+.1f}%" for v in row] for row in Tx.values], texttemplate="%{text}", textfont=dict(size=15, color="#FFFFFF"), xgap=3, ygap=3,
                               colorbar=dict(title="better →"), hovertemplate="%{y}, %{x}<br>%{text}<extra></extra>"))
    fig.update_layout(height=330, yaxis=dict(autorange="reversed"), title=f"{A} vs {B}: change in mean {lab_m.split(':')[0].split(' (')[0]} (blue = {A} better)")
    st.plotly_chart(fig, width="stretch")
    st.markdown('<p class="small">Percent change of the mean over the 1,000 replications of each scenario. A tiny blue or red cell means a negligible difference; see the paired comparisons tab for how consistent a difference is.</p>', unsafe_allow_html=True)

    st.markdown("### Drill into one scenario")
    d1, d2, d3 = st.columns(3)
    Tq = d1.select_slider("T", sorted(rep["T"].unique()), value=50)
    rq = d2.select_slider("ρ (rho)", sorted(rep.rho.unique()), value=0.9)
    Lq = d3.select_slider("L", sorted(rep.L.unique()), value=10)
    sub = rep[(rep["T"] == Tq) & (rep.rho == rq) & (rep.L == Lq) & rep.method.isin([A, B])]
    wide = sub.pivot(index="rep", columns="method", values="fc_mse").dropna().sort_index()
    if len(wide) == 0:
        st.warning("No replications for this scenario in the selected run.")
    else:
        diff = wide[A] - wide[B]
        share = float((diff < 0).mean()); tie = float((diff == 0).mean())
        ui.tiles([(f"Mean MSFE {A}", f"{wide[A].mean():.3f}", f"median {wide[A].median():.3f}", COLORS[A]),
                   (f"Mean MSFE {B}", f"{wide[B].mean():.3f}", f"median {wide[B].median():.3f}", COLORS[B]),
                   (f"{A} lower in", f"{share:.0%}", f"of {len(wide)} replications" + (f" ({tie:.1%} tied)" if tie else ""), "#D2EC9C"),
                   ("Mean paired difference", f"{diff.mean():+.3f}", f"s.e. {diff.std() / np.sqrt(len(diff)):.3f}", None)])
        left, right = st.columns(2)
        with left:
            fh = go.Figure(go.Histogram(x=diff.clip(diff.quantile(0.01), diff.quantile(0.99)), nbinsx=50, marker_color="#4CC38A"))
            fh.add_vline(x=0, line_color="#fff", line_dash="dash")
            fh.update_layout(height=340, title=f"MSFE({A}) − MSFE({B}), same data, each replication", xaxis_title="negative = first method better (1%-99% range shown)", yaxis_title="replications", bargap=0.04)
            st.plotly_chart(fh, width="stretch")
        with right:
            n_show = st.slider("Replications used so far", 10, len(wide), len(wide), step=10, key="mc_nshow")
            cm = wide.expanding().mean()
            fr = go.Figure()
            for m in (A, B):
                fr.add_scatter(x=cm.index[:n_show] + 1 if cm.index.min() == 0 else cm.index[:n_show], y=cm[m].iloc[:n_show], mode="lines", name=m, line=dict(color=COLORS[m], width=2.5))
            fr.update_layout(height=290, title="Running mean MSFE as replications accumulate", xaxis_title="replications", yaxis_title="mean MSFE", legend=dict(orientation="h", y=1.18))
            st.plotly_chart(fr, width="stretch")
            st.markdown(f'<p class="small">After {n_show} replications the means are {wide[A].iloc[:n_show].mean():.3f} ({A}) and {wide[B].iloc[:n_show].mean():.3f} ({B}). '
                        'This is why the study uses 1,000 replications: early averages are noisy.</p>', unsafe_allow_html=True)
