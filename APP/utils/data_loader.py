"""Loading of the saved experiment outputs in APP/data. Pages never compute research results; they only read these files.
Every loader returns a DataFrame or raises DataProblem (missing file, missing columns); pages catch it and show a message."""
import json, os
import pandas as pd
import streamlit as st
from utils.validation import DataProblem, require_columns, require_numeric, require_nonempty

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
ASSETS = os.path.join(ROOT, "assets")

MC_METHODS = {"lasso": "LASSO", "adalasso": "adaLASSO", "wladalasso": "WLadaLASSO", "ext1": "Ext1",
              "adalasso_g": "adaLASSO (γ by BIC)", "wladalasso_g": "WLadaLASSO (γ by BIC)", "ext1_g": "Ext1 (γ by BIC)"}
MC_METRICS = {  # column -> (label, higher_is_better or None)
    "fc_mse": ("MSFE (forecast mean squared error)", False), "fc_mae": ("MAE (forecast mean absolute error)", False),
    "FRVI": ("FRVI: fraction of relevant variables included", True), "FIVE": ("FIVE: fraction of irrelevant variables excluded", True),
    "FVCI": ("FVCI: fraction of variables correctly identified", True), "TMI": ("TMI: share of replications with the true model", True),
    "NIV": ("NIV: number of selected variables (true value 10)", None), "precision": ("Precision of selection", True),
    "recall": ("Recall of selection", True), "gmean": ("G-mean of selection", True),
    "coef_mse": ("Coefficient estimation error (MSE)", False), "coef_mae": ("Coefficient estimation error (MAE)", False)}


def path(*parts):
    return os.path.join(DATA, *parts)


def exists(*parts):
    return os.path.exists(path(*parts))


def _read(rel, name=None, **kw):
    p = path(rel)
    if not os.path.exists(p):
        raise DataProblem(f"{name or rel}: file not found ({os.path.relpath(p, ROOT)})")
    try:
        return pd.read_csv(p, **kw)
    except Exception as e:                                    # corrupt or unreadable file
        raise DataProblem(f"{name or rel}: cannot read file ({e})")


@st.cache_data(show_spinner=False)
def load_mc_replications(kind):
    """kind: 'fixed' (1,000 replications) or 'gamma_bic' (300 replications). Replication-level results."""
    folder = {"fixed": "monte_carlo", "gamma_bic": "gamma_bic_monte_carlo"}[kind]
    df = _read(f"{folder}/replication_metrics.csv.gz", f"Monte Carlo ({kind}) replications")
    require_columns(df, ["rho", "T", "L", "variant", "rep", "fc_mse", "fc_mae", "FRVI", "FIVE", "NIV"], kind)
    require_numeric(df, ["fc_mse", "fc_mae"], kind)
    df["method"] = df["variant"].map(MC_METHODS)
    if df["method"].isna().any():
        raise DataProblem(f"{kind}: unknown method names {sorted(df.loc[df.method.isna(), 'variant'].unique())}")
    return df


@st.cache_data(show_spinner=False)
def load_mc_completion(kind):
    folder = {"fixed": "monte_carlo", "gamma_bic": "gamma_bic_monte_carlo"}[kind]
    return require_columns(_read(f"{folder}/completion_by_scenario.csv"), ["rho", "T", "L", "reps_done", "reps_target", "complete"], "completion")


@st.cache_data(show_spinner=False)
def load_csv(rel):
    return require_nonempty(_read(rel), rel)


@st.cache_data(show_spinner=False)
def load_json(rel):
    p = path(rel)
    if not os.path.exists(p):
        raise DataProblem(f"{rel}: file not found")
    with open(p) as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_text(rel):
    p = path(rel)
    if not os.path.exists(p):
        raise DataProblem(f"{rel}: file not found")
    with open(p, encoding="utf-8") as f:
        return f.read()


EQ_VERSIONS = {"original_2005": "Original 2005 vintage", "current_crsp": "Current file, CRSP premium", "current_index": "Current file, index premium"}
EQ_MODELS = {"d/p": "Dividend price ratio", "d/y": "Dividend yield", "e/p": "Earning price ratio", "d/e": "Dividend payout ratio",
             "svar": "Stock variance", "b/m": "Book to market", "ntis": "Net equity expansion", "tbl": "T-bill rate",
             "lty": "Long-term yield", "ltr": "Long-term return", "tms": "Term spread", "dfy": "Default yield spread",
             "dfr": "Default return spread", "infl": "Inflation", "All regressors": "All regressors (OLS)",
             "lasso (l=1)": "LASSO (l=1)", "adalasso (l=1)": "adaLASSO (l=1)", "adalasso_g (l=1)": "adaLASSO, γ by BIC (l=1)",
             "lasso (free l)": "LASSO (free l)", "adalasso (free l)": "adaLASSO (free l)", "adalasso_g (free l)": "adaLASSO, γ by BIC (free l)",
             "wladalasso (free l)": "WLadaLASSO (free l)", "wladalasso_g (free l)": "WLadaLASSO, γ by BIC (free l)",
             "ext1 (free l)": "Ext1 (free l)", "ext1_g (free l)": "Ext1, γ by BIC (free l)"}
EQ_PENALISED = ["lasso (l=1)", "adalasso (l=1)", "lasso (free l)", "adalasso (free l)", "wladalasso (free l)", "ext1 (free l)"]
EQ_PENALISED_G = ["adalasso_g (l=1)", "adalasso_g (free l)", "wladalasso_g (free l)", "ext1_g (free l)"]
EQ_PAPER_NAMES = {"Dividend price ratio": "d/p", "Dividend yield": "d/y", "Earning price ratio": "e/p", "Dividend payout ratio": "d/e",
                  "Stock variance": "svar", "Book to market": "b/m", "Net equity expansion": "ntis", "T-bill rate": "tbl",
                  "Long-term yield": "lty", "Long-term return": "ltr", "Term spread": "tms", "Default yield spread": "dfy",
                  "Default return spread": "dfr", "Inflation": "infl", "All regressors": "All regressors", "LASSO (l=1)": "lasso (l=1)",
                  "adaLASSO (l=1)": "adalasso (l=1)", "LASSO (free l)": "lasso (free l)", "adaLASSO (free l)": "adalasso (free l)",
                  "WLadaLASSO (free l)": "wladalasso (free l)"}


@st.cache_data(show_spinner=False)
def load_equity(design, version):
    """design: 'fixed' or 'gamma_bic'. Returns dict(r2os=..., paper=..., selection=..., per_origin=...)."""
    folder = {"fixed": "equity_premium", "gamma_bic": "gamma_bic_equity"}[design]
    r2 = require_columns(_read(f"{folder}/{version}_r2os_long.csv"), ["start", "model", "R2_OS", "p_MDM"], "equity R2_OS")
    return dict(r2os=r2, paper=_read(f"{folder}/{version}_comparison_with_paper.csv"),
                selection=_read(f"{folder}/{version}_selection_summary.csv"),
                per_origin=_read(f"{folder}/{version}_selection_per_origin.csv"))


@st.cache_data(show_spinner=False)
def load_fred():
    names = ["metrics_all_variants", "forecasts_all_variants", "tests_each_method_vs_AR_BIC", "tests_pairwise_all_variants",
             "selected_gamma_alpha_kappa_counts", "selection_per_origin_all_variants", "subperiod_metrics_all_variants_EXPLORATORY",
             "subperiod_paired_diffs_with_ratio", "kkt_check_summary_by_variant", "highiter_6origins_comparison", "fred_convergence_origin0"]
    out = {n: _read(f"fred_md/{n}.csv", n) for n in names}
    out["config"] = load_json("fred_md/config.json")
    out["verification"] = load_json("fred_md/verification_record.json")
    require_columns(out["forecasts_all_variants"], ["date", "actual", "AR(BIC)"], "fred forecasts")
    return out
