# LASSO Type Penalties for covariate selection and forecasting

A replication and extension of Konzen and Ziegelmann (2016), *LASSO-Type Penalties for Covariate Selection and Forecasting in Time Series* (Journal of Forecasting).

When you forecast with many predictors and many lags (11 series with 20 lags is already 220 regressors), you need a method that picks the useful ones. The paper's idea is that distant lags should usually pay a higher penalty than recent ones (WLadaLASSO). We re-ran their simulation and empirical experiments and added one idea of our own, **Ext1**, where the lag penalty is estimated from the data instead of being a fixed exponential.

The four methods compared: **LASSO**, **adaLASSO**, **WLadaLASSO** (from the paper) and **Ext1** (ours).

## What is in this repository

| Path | What it is |
|---|---|
| `LASSO_Type_Penalties.ipynb` | The full notebook: all code, unit tests, the Monte Carlo, equity premium and FRED-MD experiments, with checkpointing so long runs can resume. The outputs saved in it come from a short `quick_check` run, not from the study. |
| `APP/` | The interactive Streamlit app (separate from the notebook). Has its own README. |

## Live app

**Live link:** https://adaptive-penalty-forecasting.streamlit.app/

The app has a live lab (simulate data and fit all four methods in the browser), an animated workflow diagram, a penalty explorer, a Monte Carlo scenario map, the equity premium and FRED-MD results, and a methods page.

## Run the app on your own computer

You need Python 3.10 or newer.

```bash
git clone https://github.com/tanish028/LASSO_Type_Penalties_for_covariate_selection_and_forecasting.git
cd LASSO_Type_Penalties_for_covariate_selection_and_forecasting/APP
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501. Run the commands from inside the `APP` folder. The app only reads the saved results in `APP/data/`, apart from the live lab and penalty explorer, which compute small examples in your browser. It works offline.

## Run the notebook

**In Google Colab (recommended for the long runs):** upload `LASSO_Type_Penalties.ipynb`, then follow the step-by-step instructions at the top of the notebook. It asks for the `datasets.zip` that is included in this repository (the files are listed below). The first time, run the unit tests and the `quick_check` profile.

**On your own computer:** install Jupyter and the packages the first cells install (`numpy`, `pandas`, `scipy`, `scikit-learn`, `joblib`, `matplotlib`, `openpyxl`, `xlrd`), keep `datasets.zip` next to the notebook (it is in the repository root), and run the cells from top to bottom.

`datasets.zip` contains these files (the notebook finds them by name, so the folder layout inside does not matter). The data belong to their original authors; we only provide a copy so the notebook runs as it did for us:

| File | Source |
|---|---|
| `PredictorData_2005_original.xls` | Goyal and Welch equity premium data, original 2005 release |
| `PredictorData_current.xlsx` | Goyal and Welch, current file |
| `current.csv` | FRED-MD monthly database |
| `dataJBES.xlsx` | Real-time inflation vintages. The notebook loads and checks this file but no experiment uses it. |

Settings you can change in section 8 of the notebook:

- `PROFILE = "quick_check"`: a few minutes, only checks that everything works. Never a result.
- `PROFILE = "intermediate"`: all 12 scenarios with 100 replications and smaller grids, roughly a tenth of the standard time. Never a final result.
- `PROFILE = "standard"`: the study (1,000 replications). Takes many hours; use `USE_DRIVE = True` in Colab so progress survives disconnections.
- `PROFILE = "full"` with `RUN["robustness_gamma"] = True`: the version where BIC also chooses gamma.

If a run is interrupted, run the notebook again with the same settings: finished pieces are loaded from the checkpoints and only the missing ones are computed.

## Deploy your own copy of the app

1. Sign in at https://share.streamlit.io with GitHub and choose **Create app**.
2. Pick this repository, branch `main`, and set **Main file path** to `APP/app.py`.
3. Deploy. The first start installs `APP/requirements.txt` and takes a few minutes.

## Things to know

- Results of the main experiments (fixed gamma) and the gamma-by-BIC experiments come from separate runs and are never mixed.
- The gamma-by-BIC Monte Carlo finished 8 of its 12 scenarios; only those are shown.
- Equity premium: our results do not reproduce the published table. The cause is unresolved, and we do not conclude that the paper is wrong.
- FRED-MD: the app shows our earlier completed run (no method beat the AR(BIC) benchmark).
- The live lab uses its own compact solver, so it illustrates the methods but is not the code behind the saved results.

## Reference

Konzen, E. and Ziegelmann, F. A. (2016). LASSO-Type Penalties for Covariate Selection and Forecasting in Time Series. *Journal of Forecasting*, 35, 592–612, DOI 10.1002/for.2403.

