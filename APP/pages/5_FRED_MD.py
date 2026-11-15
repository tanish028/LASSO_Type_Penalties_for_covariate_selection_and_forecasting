import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from components.theme import setup_page, header, note, COLORS, MUTED
from components.navigation import sidebar_footer
from components import charts, tables, ui
from utils import data_loader as dl
from utils.validation import DataProblem

setup_page("FRED-MD")
sidebar_footer()
header("Explore", "FRED-MD: forecasting US inflation",
       "Sixty monthly one-step forecasts of US consumer price inflation from the FRED-MD database, against an autoregressive benchmark chosen by BIC.")
note("These results come from our <b>earlier completed run</b> (60 refits per method, nothing re-fitted for this page). The run in the final notebook was interrupted when the free Colab limit was reached "
     "and is <b>not used</b>. The earlier run used our earlier code, whose grids are coarser than the final notebook's.", "warn")
try:
    F = dl.load_fred()
except DataProblem as e:
    st.error(f"Data problem: {e}"); st.stop()

cfg = F["config"]
met = F["metrics_all_variants"]
tab_race, tab_setup, tab_perf, tab_tests, tab_sub, tab_diag = st.tabs(["🏇 Forecast race", "Setup", "Performance", "Statistical tests", "Sub-periods (exploratory)", "Convergence diagnostics"])

with tab_setup:
    st.markdown("### Experimental setup")
    st.markdown(f"""
- **Data.** FRED-MD `current.csv` (2026-01 vintage), standard transformation codes, outliers (more than 10 IQR from the past-only expanding median) set to missing, series with more than 5% missing dropped (4 of 126). Sample 1960-03 to {cfg['sample_end'][:7]}.
- **Candidates.** 122 series (121 predictors and the target CPIAUCSL) × 12 lags = **1,464 candidate regressors**.
- **Target.** Monthly change of annualised CPI inflation: 1200 × Δlog(CPIAUCSL), differenced once. Horizon h = {cfg['horizon']}. Recomputed from the raw file, it matches the saved actuals to 2 × 10⁻¹⁵.
- **Evaluation.** {cfg['n_origins']} forecast origins, 2020-10 to 2025-09, expanding window (715 to 774 observations), refit every month.
- **Methods.** LASSO, adaLASSO, WLadaLASSO and Ext1 with γ = 1, plus adaLASSO, WLadaLASSO and Ext1 with γ chosen by BIC over {cfg['grids']['gammas']}.
- **Grids.** α ∈ {cfg['grids']['alphas']}, κ ∈ {cfg['grids']['kappas']}, 100 λ values (ratio 10⁻⁴), solver cap 1,000 iterations, BIC for λ, α, κ (and γ). Deterministic: no random numbers.
- **Benchmark.** AR(p), p = 0 to 12 chosen by BIC on the same window; BIC chose p = 11 at every one of the 60 origins.
- **Metrics.** MSFE, MAE, and R²_OS = 1 − SSE(method)/SSE(AR(BIC)) (positive means better than the benchmark).
""")
    st.markdown('<p class="small">The file <code>config.json</code> of the earlier run lists 121 series because it counts predictors only; the correct count including the target is 122.</p>', unsafe_allow_html=True)

with tab_perf:
    st.markdown("### Accuracy")
    t = met.copy()
    tables.show(t.rename(columns={"n_selected_mean": "selected (mean)", "n_selected_median": "selected (median)", "n_selected_min": "min", "n_selected_max": "max", "n_refits": "refits"}),
                fmt="%.3f", download="fred_md_metrics.csv", key="fred_met")
    c1, c2 = st.columns(2)
    with c1:
        m2 = met[met.method != "AR(BIC)"]
        fig = go.Figure(go.Bar(x=m2.R2_OS, y=m2.method, orientation="h", marker_color=[COLORS.get(x, "#888") for x in m2.method]))
        fig.update_layout(height=380, title="R²_OS against AR(BIC)", xaxis_title="R²_OS (all are zero or negative)", yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, width="stretch")
    with c2:
        fig = go.Figure(go.Bar(x=met.MSFE, y=met.method, orientation="h", marker_color=[COLORS.get(x, "#888") for x in met.method]))
        fig.update_layout(height=380, title="MSFE", xaxis_title="mean squared forecast error", yaxis=dict(autorange="reversed"))
        fig.update_xaxes(range=[min(met.MSFE) * 0.95, max(met.MSFE) * 1.02])
        st.plotly_chart(fig, width="stretch")
    st.markdown('<p class="small">The MSFE axis does not start at zero, to make small differences visible; they are small compared with the sampling uncertainty (see tests).</p>', unsafe_allow_html=True)
    st.markdown("### Forecasts through time")
    fc = F["forecasts_all_variants"].copy(); fc["date"] = pd.to_datetime(fc["date"])
    models = [c for c in fc.columns if c not in ("date", "actual", "AR(BIC)")]
    pick = st.multiselect("Methods", models, default=["adaLASSO", "WLadaLASSO", "Ext1"])
    fig = go.Figure()
    fig.add_scatter(x=fc.date, y=fc.actual, name="actual", line=dict(color="#EAF1E8", width=2))
    fig.add_scatter(x=fc.date, y=fc["AR(BIC)"], name="AR(BIC)", line=dict(color=COLORS["AR(BIC)"], width=2))
    for m in pick:
        fig.add_scatter(x=fc.date, y=fc[m], name=m, line=dict(color=COLORS.get(m), width=1.6, dash="dot"))
    fig.update_layout(height=420, yaxis_title="change in annualised CPI inflation", legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, width="stretch")
    st.markdown("### Cumulative squared error relative to AR(BIC)")
    fig = go.Figure()
    for m in pick:
        cum = ((fc.actual - fc[m]) ** 2 - (fc.actual - fc["AR(BIC)"]) ** 2).cumsum()
        fig.add_scatter(x=fc.date, y=cum, name=m, line=dict(color=COLORS.get(m), width=2.5))
    fig.add_hline(y=0, line_color=MUTED)
    fig.update_layout(height=400, yaxis_title="cumulative SE(method) − SE(AR)", legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, width="stretch")
    st.markdown('<p class="small">Computed here from the saved forecasts. Below zero means the method is ahead of AR(BIC) so far. All methods are ahead during the 2021-22 surge and fall behind afterwards.</p>', unsafe_allow_html=True)

with tab_tests:
    st.markdown("### Each method against AR(BIC)")
    A = F["tests_each_method_vs_AR_BIC"]
    loss = st.radio("Loss", ["squared error", "absolute error"], horizontal=True)
    a = A[A.loss == loss]
    tables.show(a[["first", "mean_diff_first_minus_second", "ci95_low", "ci95_high", "p_two_sided", "share_origins_first_better"]].rename(columns={
        "first": "method", "mean_diff_first_minus_second": "mean loss difference vs AR", "ci95_low": "95% CI low", "ci95_high": "95% CI high",
        "p_two_sided": "MDM p (two-sided)", "share_origins_first_better": "share of origins better than AR"}), fmt="%.3f", key="fred_t1", download="fred_md_tests_vs_ar.csv")
    st.markdown('<p class="small">Mean difference of the loss, method minus AR(BIC): positive means the method is worse. CI = mean ± 1.96 × Newey-West (3 lags) standard error. '
                'The p-value is the two-sided modified Diebold-Mariano test (Harvey, Leybourne and Newbold, 1997), h = 1. They use different variance estimators. '
                f'No method is significantly different from AR(BIC): the smallest p-value for squared error is {A[A.loss=="squared error"].p_two_sided.min():.2f}.</p>', unsafe_allow_html=True)
    st.markdown("### Pairwise comparisons between methods")
    Pw = F["tests_pairwise_all_variants"]
    a = Pw[Pw.loss == loss]
    tables.show(a[["first", "second", "mean_diff_first_minus_second", "ci95_low", "ci95_high", "p_two_sided", "share_origins_first_better"]], fmt="%.3f", key="fred_t2", download="fred_md_pairwise.csv")
    st.markdown(f'<p class="small">Smallest p-value over all {len(Pw)} pairwise rows: {Pw.p_two_sided.min():.3f}. No multiple-testing adjustment; 60 forecasts only. '
                'In particular WLadaLASSO is not better than adaLASSO (MSFE 8.90 against 8.63, p = 0.17) and Ext1 is not better than WLadaLASSO (p = 0.66).</p>', unsafe_allow_html=True)
    st.markdown("### Hyper-parameters chosen by BIC")
    C = F["selected_gamma_alpha_kappa_counts"]
    tables.show(C.rename(columns={"parameter": "parameter (alpha_or_kappa: α for WLadaLASSO, κ for Ext1)"}), fmt="%.3f", key="fred_cnt", download="fred_md_choices.csv", height=320)

with tab_sub:
    note("<b>Exploratory.</b> These windows were chosen after seeing the results, no p-values or confidence intervals were computed for them, and they should be read as a description, not as evidence.", "warn")
    S = F["subperiod_metrics_all_variants_EXPLORATORY"]
    piv = S.pivot(index="method", columns="window", values="R2_OS")
    order = ["full 2020-10..2025-09", "2020-10..2020-12", "2021", "2022", "2021-22 surge", "excluding 2021-22", "2023-01..2025-09"]
    piv = piv[[c for c in order if c in piv.columns]].drop(index="AR(BIC)", errors="ignore")
    st.plotly_chart(charts.heat(piv, "R²_OS", "R²_OS against AR(BIC) by window (exploratory)", zmid=0), width="stretch")
    tables.show(piv.reset_index(), fmt="%.3f", key="fred_sub", download="fred_md_subperiods.csv")
    ar = S[S.method == "AR(BIC)"][["window", "n", "MSFE", "MAE"]]
    st.markdown("AR(BIC) benchmark by window")
    tables.show(ar, fmt="%.3f", key="fred_ar")
    st.markdown('<p class="small">The gamma = 1 adaptive methods beat AR(BIC) in 2021-22 (R²_OS +0.055 to +0.077) and are clearly worse in the other 36 months (−0.37 to −0.45), so the overall figure near zero mixes two opposite regimes. '
                'The year 2022 contributes 67% of the benchmark\'s squared error. The three-month window is too short to be informative.</p>', unsafe_allow_html=True)
    st.markdown("Paired squared-error differences by window")
    tables.show(F["subperiod_paired_diffs_with_ratio"], fmt="%.3f", key="fred_spd")
    st.markdown('<p class="small">mean_over_SE is the mean difference divided by its plain (iid) standard error; it is a descriptive ratio, not a test.</p>', unsafe_allow_html=True)

with tab_diag:
    st.markdown("### Solver convergence")
    st.markdown("The solver reported its 1,000-iteration cap on a large share of the λ paths (415 of the 420 selected fits). We checked whether this matters:")
    K = F["kkt_check_summary_by_variant"]
    tables.show(K, fmt="%.2e", key="fred_kkt", download="fred_md_kkt.csv")
    st.markdown('<p class="small">KKT / duality-gap check of all 420 selected solutions (60 origins × 7 variants): the largest relative duality gap is 9.6 × 10⁻⁵ against a tolerance of 10⁻⁴, '
                'none exceeds the tolerance, and the largest KKT violation of the zero coefficients is 0. Rebuilt BIC equals stored BIC to 2 × 10⁻¹².</p>', unsafe_allow_html=True)
    H = F["highiter_6origins_comparison"]
    st.markdown("Re-solving at 30,000 iterations (6 evenly spaced origins, the 4 γ = 1 methods)")
    s = H.groupby("variant").agg(comparisons=("origin", "count"), same_choice=("same_choice", "all"), same_set=("same_set", "all"), max_abs_dcoef=("max_abs_dcoef", "max"), max_abs_dpred=("abs_dpred", "max")).reset_index()
    tables.show(s, fmt="%.2e", key="fred_hi")
    st.markdown('<p class="small">Identical choices, selected variable sets, coefficients and forecasts. The other 54 origins and the γ-BIC variants (except at origin 727) were not re-solved.</p>', unsafe_allow_html=True)
    st.markdown("Origin 727, all 7 variants, 30,000 iterations")
    tables.show(F["fred_convergence_origin0"].drop(columns=["seconds_30000_fit", "seconds_1000_fit"], errors="ignore"), fmt="%.2e", key="fred_o0")
    st.markdown("### Verification of the saved results")
    v = F["verification"]
    st.table(pd.DataFrame({"check": list(v.keys()), "value": [f"{x:.2e}" if isinstance(x, float) else str(x) for x in v.values()]}))
    st.markdown('<p class="small">No γ-BIC FRED-MD experiment with the final notebook exists; the γ-BIC variants shown here are those of the earlier completed run.</p>', unsafe_allow_html=True)


with tab_race:
    fc = F["forecasts_all_variants"].copy()
    fc["date"] = pd.to_datetime(fc["date"])
    cmap = {"adaLASSO (gamma by BIC)": COLORS["adaLASSO (γ by BIC)"], "WLadaLASSO (gamma by BIC)": COLORS["WLadaLASSO (γ by BIC)"], "Ext1 (gamma by BIC)": COLORS["Ext1 (γ by BIC)"]}
    colr = lambda m: cmap.get(m, COLORS.get(m, "#888"))
    methods_all = [c for c in fc.columns if c not in ("date", "actual", "AR(BIC)")]
    st.markdown("### Can any method beat the AR benchmark? Race it month by month")
    c1, c2 = st.columns([3, 2])
    pick = c1.multiselect("Methods in the race", methods_all, default=["LASSO", "adaLASSO", "WLadaLASSO", "Ext1"])
    lo_i, hi_i = c2.select_slider("Evaluation window (forecast origins)", options=list(range(len(fc))), value=(0, len(fc) - 1),
                                  format_func=lambda i: fc.date.iloc[i].strftime("%Y-%m"))
    w = fc.iloc[lo_i:hi_i + 1]
    se_ar = (w.actual - w["AR(BIC)"]) ** 2
    rows = []
    for m in pick:
        sse = ((w.actual - w[m]) ** 2).sum()
        rows.append((m, 1 - sse / se_ar.sum(), np.sqrt(((w.actual - w[m]) ** 2).mean()) / np.sqrt(se_ar.mean())))
    if rows:
        best_ = max(rows, key=lambda r: r[1])
        ui.tiles([("Months in window", str(len(w)), f"{w.date.iloc[0]:%Y-%m} to {w.date.iloc[-1]:%Y-%m}", None),
                  ("Best R²_OS vs AR(BIC)", f"{best_[1]:+.3f}", best_[0], colr(best_[0])),
                  ("Methods beating AR(BIC)", f"{sum(r[1] > 0 for r in rows)} of {len(rows)}", "in this window (exploratory if short)", "#E9A93B")])
    st.markdown("**Cumulative squared-error advantage over AR(BIC).** A line that climbs means the method is beating the benchmark so far; below zero means it is behind.")
    fig = go.Figure()
    for m in pick:
        adv = (se_ar - (w.actual - w[m]) ** 2).cumsum()
        fig.add_scatter(x=w.date, y=adv, mode="lines", name=m, line=dict(color=colr(m), width=2.6))
    fig.add_hline(y=0, line_color=COLORS["AR(BIC)"], line_dash="dash", annotation_text="AR(BIC)", annotation_position="top left")
    fig.update_layout(height=420, yaxis_title="Σ (AR error² − method error²)", legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, width="stretch")
    st.markdown("**Forecasts against the actual inflation change.**")
    fig = go.Figure()
    fig.add_scatter(x=w.date, y=w.actual, mode="lines+markers", name="actual", line=dict(color="#EAF1E8", width=3))
    fig.add_scatter(x=w.date, y=w["AR(BIC)"], mode="lines", name="AR(BIC)", line=dict(color=COLORS["AR(BIC)"], width=2, dash="dash"))
    for m in pick:
        fig.add_scatter(x=w.date, y=w[m], mode="lines", name=m, line=dict(color=colr(m), width=1.6), opacity=.9)
    fig.update_layout(height=420, yaxis_title="Δ annualised CPI inflation (pp)", legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, width="stretch")
    st.markdown('<p class="small">Saved forecasts of the earlier completed run. Short windows are post-hoc and exploratory; the confirmatory result is the full 60-month comparison (no method beat AR(BIC); no significant differences).</p>', unsafe_allow_html=True)
    sp = F["selection_per_origin_all_variants"].copy(); sp["date"] = pd.to_datetime(sp["date"])
    with st.expander("How many of the 1,464 candidate regressors did each method keep, month by month?"):
        fig = go.Figure()
        for m in pick:
            q = sp[sp.method == m]
            fig.add_scatter(x=q.date, y=q.n_selected, mode="lines", name=m, line=dict(color=colr(m), width=2))
        fig.update_layout(height=340, yaxis_title="selected regressors", legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig, width="stretch")
