# LASSO Type Penalties: interactive app (Streamlit)

An interactive companion to the report *Lag-Dependent Adaptive LASSO Penalties for Time Series Forecasting: A Replication and Extension of Konzen and Ziegelmann (2016)*.
It lets you simulate data and fit the four methods live, explore the penalties, and browse the saved results of the experiments in the report.
**The Live lab and Penalty explorer compute small illustrative examples in the browser; every other page only reads saved results and never reruns an experiment.**

| Page | Content |
|---|---|
| Home | Animated workflow diagram, headline numbers, guide to the pages |
| Live lab | Simulate the paper's design, change ρ (rho), T, L, noise, γ (gamma), α (alpha), κ (kappa), and watch LASSO, adaLASSO, WLadaLASSO and Ext1 select variables and forecast |
| Penalty explorer | Animated α/κ sweep, weight map, toy shrinkage experiment. Illustrative, not results |
| Monte Carlo | Scenario map with drill-down; main run (γ = 1, 1,000 replications) and the separate γ-by-BIC run (300 replications; 8 of 12 scenarios finished) |
| Equity premium | Three data versions, fixed γ and γ by BIC, version explorer, comparison with the published table |
| FRED-MD | Earlier completed run: forecast race against AR(BIC), accuracy, tests, exploratory sub-periods, convergence checks |
| Methods | LASSO, adaLASSO, WLadaLASSO (paper) and Ext1 (ours): formulas and intuition |

## Run locally

```bash
cd APP
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open the URL printed in the terminal (normally http://localhost:8501). Python 3.10 or newer; Streamlit 1.51 or newer is required.
All paths are relative to this folder, so no local or Colab path needs editing.

## Folder layout

```
APP/
  app.py                  entry point and home page (registers the pages)
  requirements.txt  README.md  .gitignore  .streamlit/config.toml (theme)
  pages/                  1_Lab (live simulation), 2_Penalty_Explorer, 3_Monte_Carlo, 4_Equity_Premium, 5_FRED_MD, 6_Methods
  components/             theme (colours, CSS), ui, workflow (animated diagram), charts, tables, explanations, navigation
  calculations/           penalty_weights.py (formulas for the explorer), engine.py (compact estimators for the Live lab)
  utils/                  data_loader.py (cached loading + validation), validation.py
  assets/                 mc_msfe_boxplots_1000.png (figure saved by the notebook)
  data/
    monte_carlo/          1,000-replication run: replication-level metrics, summaries, paired comparisons, diagnostics
    gamma_bic_monte_carlo/ 300-replication γ-BIC run (complete scenarios only) and its summaries
    equity_premium/       fixed-γ R²_OS, p-values, comparison with the paper, selections (3 data versions)
    gamma_bic_equity/     the same for γ chosen by BIC
    fred_md/              earlier completed FRED-MD run (tables computed from the saved forecasts)
    PROVENANCE.json       source file and construction of every table
  tools/build_exports.py  how data/ was built from the result archives (not needed to run the app)
```

Files that must be present for the app to work: everything in `pages/`, `components/`, `calculations/`, `utils/`, `data/` (all subfolders), `assets/mc_msfe_boxplots_1000.png`, `app.py`, `requirements.txt`.
If a data file is missing or unreadable the page shows a message instead of a number; nothing is filled in.

## Deploy on Streamlit Community Cloud

1. Put the **contents of this `APP/` folder** in a GitHub repository (or keep `APP/` as a subfolder, as in the main repository, and set the path below). The whole app is about 3 MB.
2. Sign in at https://share.streamlit.io with GitHub and choose **Create app → Deploy a public app from GitHub**.
3. Select the repository and branch, and set **Main file path** to `app.py` (or `APP/app.py` if `APP/` is a subfolder).
4. Under *Advanced settings* choose Python 3.11 or newer. No secrets are needed.
5. Press **Deploy**. The first start installs `requirements.txt` and takes a few minutes. The resulting `https://<name>.streamlit.app` URL is the only thing an evaluator needs.

If the repository is private, grant Streamlit access to it when asked.

## Notes on the data

* Every number comes from a completed run. Fixed-γ and γ-by-BIC experiments are separate runs and are never mixed in one table.
* The γ-BIC Monte Carlo finished 8 of 12 scenarios; only those are shown. The scenario with 240 of 300 replications is excluded.
* FRED-MD uses the earlier completed run. A later run in the final notebook was interrupted and is not used.
* The share of replications where WLadaLASSO beats Ext1 is shown strictly (ties excluded); Table 1 of the report counts ties as wins, so its last column is 0.5 to 2.5 points higher. The conclusions do not change.
* The Live lab uses its own compact solver, not the notebook's. It matched the notebook's selected variables for three methods on a test dataset, but found a lower-BIC adaLASSO solution than the notebook's solver. Treat the lab as an illustration; only the saved results are findings.
* Equity premium: our results do not reproduce the published table and the cause is unresolved. We do not conclude that the paper is wrong.
* The FRED-MD run's `config.json` lists 121 series (predictors only); the correct count including the target is 122.

## Colour themes
The sidebar has a **Colour theme** switch: *Forest (green and amber)*, the default, and *Ocean (blue)*, the original look. The choice is kept while you move between pages.
