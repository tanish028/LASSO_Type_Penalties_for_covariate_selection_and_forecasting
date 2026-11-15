"""Entry point and home page. Run with:  streamlit run app.py"""
import numpy as np
import streamlit as st
from components.theme import setup_page, header, note
from components.navigation import sidebar_footer
from components.explanations import PAPER, REPORT_TITLE
from components import ui, workflow
from utils import data_loader as dl
from utils.validation import DataProblem


def home():
    setup_page("Home")
    sidebar_footer()
    ui.hero("Covariate selection and forecasting · Konzen & Ziegelmann (2016)",
            "LASSO Type Penalties",
            "Should distant lags pay a higher price? With 11 series and 20 lags there are 220 candidate predictors and maybe 50 observations. WLadaLASSO adds a penalty that grows with the lag. "
            "Explore how it works, fit it live on simulated data, and see what our replication found.",
            pills=["LASSO", "adaLASSO", "WLadaLASSO", "Ext1 (our extension)", "Monte Carlo", "Equity premium", "FRED-MD"])

    # --- headline numbers, all computed from saved results
    try:
        s = dl.load_csv("monte_carlo/summary_all_metrics.csv")
        p = s.pivot_table(index=["T", "rho", "L"], columns="variant", values="fc_mse_mean")
        gain = 100 * (1 - p["wladalasso"] / p["adalasso"])
        g50 = gain.xs(50, level="T"); g500 = gain.xs(500, level="T")
        n_rep = int(s.n_rep.max())
        fm = dl.load_csv("fred_md/metrics_all_variants.csv")
        best_fred = fm[fm.method != "AR(BIC)"].R2_OS.max()
        ui.tiles([("Small samples (T = 50)", f"−{g50.min():.0f}% to −{g50.max():.0f}%", "forecast error of WLadaLASSO vs adaLASSO", "#4FA3F7"),
                  ("Large samples (T = 500)", f"−{g500.min():.1f}% to −{g500.max():.1f}%", "the advantage almost vanishes", "#9AA7BD"),
                  ("Simulation scale", f"12 × {n_rep:,}", "scenarios × replications per scenario", "#3FD0A0"),
                  ("FRED-MD vs AR(BIC)", f"{best_fred:+.3f}", "best R²OS of any method: none beats the benchmark", "#E06C75")])
    except DataProblem as e:
        st.error(str(e))

    st.markdown("## How it works: click through the pipeline")
    st.markdown('<p class="small" style="margin-top:-.4rem">Every experiment in this project runs the same nine steps. Click a step, switch the method chip, or press play.</p>', unsafe_allow_html=True)
    workflow.render(height=640)

    st.markdown("## Explore")
    c = st.columns(3)
    cards = [("pages/1_Lab.py", "🧪 Live lab", "Simulate data, change ρ, T, L, noise, γ, α, κ and watch the four methods select variables and forecast. Run it 40 times in one click.", "#4FA3F7"),
             ("pages/2_Penalty_Explorer.py", "🎚️ Penalty explorer", "Animate the lag penalty, see the weight map, and test which lags survive shrinkage.", "#E9A93B"),
             ("pages/3_Monte_Carlo.py", "🗺️ Monte Carlo", "A map of the 12 scenarios: where one method beats another, with drill-down into 1,000 replications.", "#3FD0A0"),
             ("pages/4_Equity_Premium.py", "📊 Equity premium", "R² out of sample across three data versions, significance stars, and the comparison with the paper.", "#9CCBFA"),
             ("pages/5_FRED_MD.py", "🏇 FRED-MD", "Race the methods against AR(BIC), month by month, in any window.", "#E06C75"),
             ("pages/6_Methods.py", "📘 Methods", "Equations and plain-language definitions of all four methods and the evaluation measures.", "#9AA7BD")]
    for i, (page, title, text, col) in enumerate(cards):
        with c[i % 3]:
            ui.card(title, text, col)
            st.page_link(page, label="Open →")
            st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    st.markdown("## What we found, in short")
    a, b = st.columns(2)
    with a:
        st.markdown("""
- **Simulations, T = 50.** WLadaLASSO had the lowest forecast error in all six scenarios and kept more of the truly relevant variables. With T = 500 the gain is at most about 2%.
- **Ext1** (our data-driven lag profile) sits between adaLASSO and WLadaLASSO at T = 50 and matches WLadaLASSO at T = 500.
- **Choosing γ by BIC** made forecasts worse at T = 50 and changed them by under 1% at T = 500 (8 of 12 scenarios finished).""")
    with b:
        st.markdown("""
- **Equity premium.** We could not reproduce the published table; the cause is unresolved and we do not conclude the paper is wrong.
- **FRED-MD.** No method beat the AR(BIC) benchmark and no difference between methods was significant.
- Fixed-γ and γ-by-BIC results come from separate runs and are never mixed.""")
    note("The Lab page fits fresh simulated data live with a compact re-implementation; every other page shows saved results of the completed runs. "
         "The FRED-MD page uses our earlier completed run; a later, interrupted run is not used.", "warn")
    st.markdown(f'<p class="small">Original paper: {PAPER}<br>Report: {REPORT_TITLE}</p>', unsafe_allow_html=True)


setup_page("Home")
nav = st.navigation([
    st.Page(home, title="Home", icon="🏠", default=True, url_path="home"),
    st.Page("pages/1_Lab.py", title="Live lab", icon="🧪", url_path="lab"),
    st.Page("pages/2_Penalty_Explorer.py", title="Penalty explorer", icon="🎚️", url_path="penalty-explorer"),
    st.Page("pages/3_Monte_Carlo.py", title="Monte Carlo", icon="🗺️", url_path="monte-carlo"),
    st.Page("pages/4_Equity_Premium.py", title="Equity premium", icon="📊", url_path="equity-premium"),
    st.Page("pages/5_FRED_MD.py", title="FRED-MD", icon="🏇", url_path="fred-md"),
    st.Page("pages/6_Methods.py", title="Methods", icon="📘", url_path="methods"),
])
nav.run()
