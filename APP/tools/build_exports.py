"""Build the compact, application-ready data exports in APP/data from the saved experiment outputs.
Nothing is re-fitted. Every table is either a copy of a saved file or a deterministic re-summary of saved
replication-level results. Sources are written to APP/data/PROVENANCE.json (and shown in the app).
Paths RES and FRED below point to the unpacked result archives; edit them to re-run. Not needed to run the app."""
import sys, os, glob, json, pickle, shutil, hashlib
import numpy as np, pandas as pd

RES = "/home/claude/w/res/WLadaLASSO_results"
FRED = "/home/claude/w/fred/fred_md_package_v2"
OUT = "/home/claude/w/APP/data"
prov = {}

def note(path, source, how, extra=None):
    prov[os.path.relpath(path, OUT)] = dict(source=source, how=how, **(extra or {}))

def save(df, rel, source, how, **kw):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    df.to_csv(p, index=False, **kw)
    note(p, source, how, dict(rows=len(df)))

def cp(src, rel, how="copied unchanged"):
    p = os.path.join(OUT, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    shutil.copyfile(src, p); note(p, os.path.relpath(src, os.path.dirname(os.path.dirname(src))) if False else src.replace("/home/claude/w/", ""), how)

# ------------------------------------------------------------------ 1. main Monte Carlo (1,000 replications)
R1 = f"{RES}/monte_carlo/standard/standard_5bbd41f57a"
S1 = f"{RES}/monte_carlo/summaries/standard_5bbd41f57a"
meta = json.load(open(f"{R1}/run_metadata.json"))
assert meta["status"] == "completed" and meta["settings"]["monte_carlo"]["n_rep"] == 1000
comp = pd.read_csv(f"{R1}/completion_by_scenario.csv")
assert comp.complete.all() and (comp.reps_done == 1000).all()
rep = pd.read_csv(f"{R1}/replication_results.csv.gz")
assert rep.groupby(["rho", "T", "L", "variant"]).rep.nunique().eq(1000).all()
assert not rep.duplicated(["rho", "T", "L", "variant", "rep"]).any()
keep = ["rho", "T", "L", "variant", "rep", "fc_mse", "fc_mae", "FRVI", "FIVE", "FVCI", "TMI", "NIV", "precision",
        "recall", "gmean", "coef_mse", "coef_mae"]
save(rep[keep].round(6), "monte_carlo/replication_metrics.csv.gz", "monte_carlo/standard/standard_5bbd41f57a/replication_results.csv.gz",
     "selected columns, rounded to 6 decimals (replication level, 12 scenarios x 4 methods x 1,000 replications)", compression="gzip")
cp(f"{S1}/summary_all_metrics.csv", "monte_carlo/summary_all_metrics.csv")
cp(f"{S1}/boundary_diagnostics_by_scenario.csv", "monte_carlo/boundary_diagnostics_by_scenario.csv")
cp(f"{R1}/completion_by_scenario.csv", "monte_carlo/completion_by_scenario.csv")
cp(f"{R1}/run_metadata.json", "monte_carlo/run_metadata.json")
os.makedirs(f"{OUT}/../assets", exist_ok=True)
shutil.copyfile(f"{RES}/monte_carlo/figures/standard_5bbd41f57a/mc_msfe_boxplots_standard_standard_5bbd41f57a.png",
                f"{OUT}/../assets/mc_msfe_boxplots_1000.png")
note(f"{OUT}/../assets/mc_msfe_boxplots_1000.png", "monte_carlo/figures/standard_5bbd41f57a/mc_msfe_boxplots_standard_standard_5bbd41f57a.png", "copied unchanged")

# paired comparison of MSFE (same replications): WLadaLASSO vs adaLASSO and Ext1 (re-summary of replication results)
def paired(rep, a, b, label, col="fc_mse"):
    rows = []
    for (rho, T, L), g in rep.groupby(["rho", "T", "L"]):
        w = g.pivot(index="rep", columns="variant", values=col)
        d = w[a] - w[b]
        rows.append(dict(rho=rho, T=T, L=L, contrast=label, mean_first=w[a].mean(), mean_second=w[b].mean(),
                         ratio=w[a].mean() / w[b].mean(), share_first_lower=(w[a] < w[b]).mean(), share_tied=(w[a] == w[b]).mean(),
                         share_first_lower_or_tied=(w[a] <= w[b]).mean(),
                         mean_diff=d.mean(), se_diff=d.std(ddof=1) / np.sqrt(len(d)), n=len(d)))
    return rows
rows = []
for a, b, lab in [("wladalasso", "adalasso", "WLadaLASSO vs adaLASSO"), ("wladalasso", "ext1", "WLadaLASSO vs Ext1"),
                  ("ext1", "adalasso", "Ext1 vs adaLASSO"), ("wladalasso", "lasso", "WLadaLASSO vs LASSO"),
                  ("adalasso", "lasso", "adaLASSO vs LASSO")]:
    rows += paired(rep, a, b, lab)
save(pd.DataFrame(rows), "monte_carlo/paired_msfe_comparisons.csv", "monte_carlo/standard/standard_5bbd41f57a/replication_results.csv.gz",
     "computed here from replication-level fc_mse: ratio of means, share of replications where the first method has the strictly lower MSFE (and the share of exact ties), mean paired difference and its iid standard error")

# ------------------------------------------------------------------ 2. gamma-BIC Monte Carlo (300 replications; built from chunk checkpoints)
G2 = f"{RES}/02_Gamma_BIC_Monte_Carlo/checkpoints/monte_carlo/full_474381fe50_gamma_cross"
m2 = json.load(open(f"{RES}/02_Gamma_BIC_Monte_Carlo/monte_carlo/gamma_robustness/full_474381fe50_gamma_cross/run_metadata.json"))
frames, comp2 = [], []
for d in sorted(glob.glob(f"{G2}/rho*_T*_L*")):
    name = os.path.basename(d); rho = float(name.split("_")[0][3:]); T = int(name.split("_")[1][1:]); L = int(name.split("_")[2][1:])
    fs = sorted(glob.glob(f"{d}/chunk_*.pkl"))
    dfs = []
    for f in fs:
        try:
            o = pickle.load(open(f, "rb"))
        except Exception as e:
            print("corrupt chunk skipped", f, e); continue
        dfs.append(o)
    df = pd.concat(dfs, ignore_index=True)
    df.insert(0, "rho", rho); df.insert(1, "T", T); df.insert(2, "L", L)
    n_rep = df.rep.nunique()
    comp2.append(dict(rho=rho, T=T, L=L, reps_done=n_rep, reps_target=300, complete=bool(n_rep == 300), chunks_found=len(fs)))
    frames.append(df)
done = {(c['rho'], c['T'], c['L']) for c in comp2 if c['complete']}
allg = pd.concat(frames, ignore_index=True)
assert not allg.duplicated(["rho", "T", "L", "variant", "rep"]).any()
# scenarios not run at all
for rho in (0.3, 0.9):
    for T in (50, 500):
        for L in (5, 10, 20):
            if not any(c["rho"] == rho and c["T"] == T and c["L"] == L for c in comp2):
                comp2.append(dict(rho=rho, T=T, L=L, reps_done=0, reps_target=300, complete=False, chunks_found=0))
comp2 = pd.DataFrame(comp2).sort_values(["rho", "T", "L"])
save(comp2, "gamma_bic_monte_carlo/completion_by_scenario.csv", "02_Gamma_BIC_Monte_Carlo/checkpoints (chunk files, manifests)", "counted from chunk checkpoints")
allg = allg[allg.set_index(["rho", "T", "L"]).index.isin(list(done))]
assert set(allg.variant.unique()) == {"lasso", "adalasso", "wladalasso", "ext1", "adalasso_g", "wladalasso_g", "ext1_g"}
keep2 = keep[:3] + ["variant", "rep", "fc_mse", "fc_mae", "FRVI", "FIVE", "FVCI", "TMI", "NIV", "precision", "recall", "gmean",
                     "coef_mse", "coef_mae", "gamma0", "hyper0", "flag_gamma_at_upper"]
save(allg[keep2].round(6), "gamma_bic_monte_carlo/replication_metrics.csv.gz", "02_Gamma_BIC_Monte_Carlo/checkpoints chunk_*.pkl",
     "concatenated chunk checkpoints of the 8 scenarios with 300 complete replications (the 240-replication scenario is excluded); selected columns",
     compression="gzip")
# check: fixed-gamma columns equal first 300 replications of the 1,000-replication run
chk = allg.merge(rep, on=["rho", "T", "L", "variant", "rep"], suffixes=("_g", "_m"))
chk = chk[chk.variant.isin(["lasso", "adalasso", "wladalasso", "ext1"])]
prov["_checks"] = dict(gamma_bic_fixed_columns_vs_main_run_max_abs_diff_fc_mse=float((chk.fc_mse_g - chk.fc_mse_m).abs().max()),
                       n_compared=len(chk))
print("gamma-bic vs main fixed columns max diff:", prov["_checks"])
agg = {c: ["mean", "std"] for c in ["fc_mse", "fc_mae", "FRVI", "FIVE", "NIV", "TMI", "coef_mse"]}
summ = allg.groupby(["rho", "T", "L", "variant"]).agg(agg)
summ.columns = [f"{a}_{b}" for a, b in summ.columns]
summ["n_rep"] = allg.groupby(["rho", "T", "L", "variant"]).rep.nunique()
summ = summ.reset_index()
gam = allg[allg.variant.isin(["adalasso_g", "wladalasso_g", "ext1_g"])].copy()
share3 = gam.assign(g3=(gam.gamma0 == 3.0)).groupby(["rho", "T", "L", "variant"]).g3.mean().rename("share_gamma_3").reset_index()
summ = summ.merge(share3, on=["rho", "T", "L", "variant"], how="left")
save(summ, "gamma_bic_monte_carlo/summary_by_scenario.csv", "02_Gamma_BIC_Monte_Carlo/checkpoints chunk_*.pkl",
     "computed here: mean and sd over the 300 replications for each scenario and method; share_gamma_3 = share of fits whose BIC-chosen gamma was 3 (grid maximum)")
gcount = gam.groupby(["rho", "T", "L", "variant", "gamma0"]).size().rename("n_fits").reset_index()
save(gcount, "gamma_bic_monte_carlo/gamma_choice_counts.csv", "02_Gamma_BIC_Monte_Carlo/checkpoints chunk_*.pkl", "computed here: counts of the first-origin gamma chosen by BIC (gamma0)")
# paired: gamma by BIC vs gamma = 1 for each family
rows = []
for fam in ["adalasso", "wladalasso", "ext1"]:
    for (rho, T, L), g in allg.groupby(["rho", "T", "L"]):
        w = g.pivot(index="rep", columns="variant", values="fc_mse")
        d = w[fam + "_g"] - w[fam]
        rows.append(dict(rho=rho, T=T, L=L, family=fam, mean_gamma1=w[fam].mean(), mean_gammaBIC=w[fam + "_g"].mean(),
                         ratio=w[fam + "_g"].mean() / w[fam].mean(), share_gammaBIC_lower=(w[fam + "_g"] < w[fam]).mean(),
                         mean_diff=d.mean(), se_diff=d.std(ddof=1) / np.sqrt(len(d)), n=len(d)))
pg = pd.DataFrame(rows)
pg["t_stat"] = pg.mean_diff / pg.se_diff
from scipy import stats
pg["p_paired_t_two_sided"] = 2 * stats.t.sf(np.abs(pg.t_stat), pg.n - 1)
save(pg, "gamma_bic_monte_carlo/paired_gamma_bic_vs_gamma1.csv", "02_Gamma_BIC_Monte_Carlo/checkpoints chunk_*.pkl",
     "computed here: gamma chosen by BIC vs gamma = 1 on identical replications (paired t-test across replications, descriptive, no multiplicity adjustment)")
json.dump(m2, open(f"{OUT}/gamma_bic_monte_carlo/run_metadata.json", "w"), indent=1)
note(f"{OUT}/gamma_bic_monte_carlo/run_metadata.json", "02_Gamma_BIC_Monte_Carlo/monte_carlo/gamma_robustness/.../run_metadata.json",
     "copied unchanged (its status says 'running (or interrupted)': the run was stopped before finishing)")

# ------------------------------------------------------------------ 3/4. equity premium (fixed gamma and gamma by BIC)
versions = {
    "original_2005": ("equity_premium/original_2005/standard_original_2005_index_A_primary_c9b6b78424",
                      "03_Gamma_BIC_Empirical/equity_premium/original_2005/full_original_2005_index_A_primary_90abe266bc"),
    "current_crsp": ("equity_premium/current_crsp/standard_current_crsp_A_primary_c8c86ed433",
                     "03_Gamma_BIC_Empirical/equity_premium/current_crsp/full_current_crsp_A_primary_26c4893acd"),
    "current_index": ("equity_premium/current_index/standard_current_index_A_primary_162308516d",
                      "03_Gamma_BIC_Empirical/equity_premium/current_index/full_current_index_A_primary_aa75c1a78b"),
}
for ver, (fx, gb) in versions.items():
    for tag, rel, folder in [("fixed", fx, "equity_premium"), ("gammabic", gb, "gamma_bic_equity")]:
        d = f"{RES}/{rel}"
        mm = json.load(open(f"{d}/run_metadata.json")); assert mm["status"] == "completed"
        long = pd.read_csv(f"{d}/r2os_and_mdm_pvalues_long.csv"); long.insert(0, "version", ver)
        save(long, f"{folder}/{ver}_r2os_long.csv", rel + "/r2os_and_mdm_pvalues_long.csv", "copied, version column added")
        cmp_ = pd.read_csv(f"{d}/comparison_with_paper_table_X.csv"); cmp_.insert(0, "version", ver)
        save(cmp_, f"{folder}/{ver}_comparison_with_paper.csv", rel + "/comparison_with_paper_table_X.csv", "copied, version column added")
        sel = pd.read_csv(f"{d}/selection_summary.csv"); sel.insert(0, "version", ver)
        save(sel, f"{folder}/{ver}_selection_summary.csv", rel + "/selection_summary.csv", "copied, version column added")
        per = []
        for f in sorted(glob.glob(f"{d}/selection_per_origin_*.csv")):
            x = pd.read_csv(f); x.insert(0, "method", os.path.basename(f)[len("selection_per_origin_"):-4]); per.append(x)
        per = pd.concat(per); per.insert(0, "version", ver)
        save(per, f"{folder}/{ver}_selection_per_origin.csv", rel + "/selection_per_origin_*.csv", "concatenated, method column added")
        json.dump(mm, open(f"{OUT}/{folder}/{ver}_run_metadata.json", "w"), indent=1)
        note(f"{OUT}/{folder}/{ver}_run_metadata.json", rel + "/run_metadata.json", "copied unchanged")
# check fixed-gamma rows identical in the gamma-BIC run
mx = 0.0
for ver in versions:
    a = pd.read_csv(f"{OUT}/equity_premium/{ver}_r2os_long.csv").set_index(["start", "model"])
    b = pd.read_csv(f"{OUT}/gamma_bic_equity/{ver}_r2os_long.csv").set_index(["start", "model"])
    common = a.index.intersection(b.index)
    mx = max(mx, float((a.loc[common, "R2_OS"] - b.loc[common, "R2_OS"]).abs().max()))
prov["_checks"]["equity_fixed_rows_vs_gammabic_run_max_abs_diff_R2OS"] = mx
print("equity fixed rows max diff:", mx)
# stray duplicate folder in the archive
a = f"{RES}/03_Gamma_BIC_Empirical/equity_premium/original_2005/full_original_2005_index_A_primary_90abe266bc"
b = f"{RES}/03_Gamma_BIC_Empirical/equity_premium/current_index/original_2005/full_original_2005_index_A_primary_90abe266bc"
same = all(open(f"{a}/{os.path.basename(f)}", "rb").read() == open(f, "rb").read() for f in glob.glob(f"{b}/*.csv"))
prov["_checks"]["stray_duplicate_folder_current_index/original_2005_csv_identical_to_original_2005"] = bool(same)
print("duplicate csv identical:", same)

# ------------------------------------------------------------------ 5. FRED-MD (earlier completed run)
P = f"{FRED}/computed_from_saved_forecasts"; O = f"{FRED}/original_files"
for f in ["forecasts_all_variants", "metrics_all_variants", "selected_gamma_alpha_kappa_counts", "selection_per_origin_all_variants",
          "subperiod_metrics_all_variants_EXPLORATORY", "subperiod_paired_diffs_with_ratio", "tests_each_method_vs_AR_BIC",
          "tests_pairwise_all_variants"]:
    cp(f"{P}/{f}.csv", f"fred_md/{f}.csv", "copied unchanged (computed from saved forecasts by the earlier package; nothing re-fitted)")
cp(f"{P}/verification_record.json", "fred_md/verification_record.json")
for f in ["kkt_check_summary_by_variant", "highiter_6origins_comparison", "fred_convergence_origin0", "ar_bic_order_per_origin"]:
    cp(f"{O}/{f}.csv", f"fred_md/{f}.csv")
cp(f"{O}/config.json", "fred_md/config.json")
cp(f"{FRED}/FRED_MD_RESULTS_CORRECTED.md", "fred_md/FRED_MD_RESULTS_CORRECTED.md")

json.dump(prov, open(f"{OUT}/PROVENANCE.json", "w"), indent=1)
print("done;", len(prov), "entries")
