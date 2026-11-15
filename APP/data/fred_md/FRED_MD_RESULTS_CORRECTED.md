# FRED-MD results for the WLadaLASSO project (corrected and complete)

This document collects the FRED-MD results of the earlier completed experiment (60 monthly one-step forecasts). It corrects four inconsistencies of the earlier file and adds results that were fitted earlier but never reported.
**No model was re-fitted for this document.** Everything is read from the saved checkpoints, forecasts and tables. Labels: **[V]** verified against saved forecasts or raw data in this package, **[S]** taken from a saved earlier file, **[N]** computed now from the saved forecasts (never in an earlier file), **[E]** exploratory (post hoc).

## 0. Corrections to `FRED_MD_COMPARATIVE_RESULTS.md` (all verified)
1. **Series and candidates.** The earlier file said 121 series and 1,452 candidates. The correct numbers are **122 series (121 predictors plus the target CPIAUCSL), 1,464 candidates (122 x 12 lags)**. Evidence: the raw file has 126 series, 4 are dropped (`fred.log`), 787 months x 122 series; every saved coefficient vector has length 1,464; `checks.txt`. The value `n_series = 121` in `config.json` counts predictors only.
2. **Mean number of selected variables of adaLASSO** is exactly **15.95** (the earlier table showed 15.9 and the text 16.0).
3. **Convergence check.** The earlier file said the 30,000-iteration check was done at a single origin. It was done at origin 727 for all 7 variants, and later at 6 evenly spaced origins for the 4 gamma = 1 methods, plus KKT / duality-gap checks of all 420 selected solutions (section 6).
4. **Gamma-selected variants.** They were fitted at every origin but not reported. They are reported now (sections 2 to 5, marked [N]).
5. **Not reproduced (documentation of an earlier claim).** `STEP1_INTERPRETATIONS.md` says the WLadaLASSO - adaLASSO differences are "within ~1-2.7 SE". The saved file gives a ratio of mean difference to its (iid) standard error of at most 1.40 for windows with at least 12 months (table in section 4). The statement "no sub-period difference is distinguishable from zero" still holds; the "2.7" could not be reproduced.

## 1. Experimental setup [S/V]
- **Data:** FRED-MD `current.csv` (2026-01 vintage), standard transformation codes; outliers (> 10 IQR from the past-only expanding median) set to missing; series with > 5% missing dropped (4 dropped); gaps filled. Sample 1960-03 to 2025-09 (787 months; 2025-09 is the last month with a complete panel). 122 series, 12 lags each, **1,464 candidate regressors**.
- **Target [V]:** monthly change of annualised CPI inflation, 1200 x dlog(CPIAUCSL) differenced once. Recomputed from the raw file: matches the saved actuals to 2e-15. Horizon h = 1.
- **Training window:** expanding; 715 observations at the first origin, 774 at the last.
- **Evaluation:** 60 forecast origins, 2020-10-01 to 2025-09-01 (the last 60 months). All methods use the same data, window and origins. Origins 2020-10 to 2021-01 come from an earlier pilot with the same configuration key.
- **Refitting:** every month (60 refits per method).
- **Methods:** LASSO, adaLASSO, WLadaLASSO, Ext1 with gamma = 1 fixed; and adaLASSO, WLadaLASSO, Ext1 with gamma chosen by BIC (gamma grid {0.5, 1, 1.5, 2}). Alpha grid {0, 0.05, 0.1, 0.2, 0.35, 0.5}, kappa grid {0, 0.5, 1, 2}. Lambda path of 100 values (eps 1e-4), solver cap 1,000 iterations, BIC selection of lambda, alpha and kappa (and gamma for the gamma-BIC variants). Deterministic: no random numbers.
- **Benchmark:** AR(p), p = 0..12 chosen by BIC on the same expanding window (p = 0 is the historical mean). BIC chose **p = 11 at every one of the 60 origins** [S].
- **Code that produced the results:** the earlier project code (`code/empirical.py`, `run_empirical_cfg.py`), not the standalone Colab notebook, which uses different default grids (more lambda values, other alpha/kappa grids).

## 2. Main results [V for the three gamma = 1 methods and AR(BIC); N for the others]
MSFE = mean squared forecast error, MAE = mean absolute error, R2_OS = 1 - SSE(method)/SSE(AR(BIC)) (positive = better than the benchmark). The number of selected variables is the number of non-zero coefficients out of 1,464 (it equals the stored degrees of freedom at every origin [V]).

| method | MSFE | MAE | R2_OS | selected variables: mean (median, min-max) |
|---|---|---|---|---|
| AR(BIC) | 8.619 | 2.062 | 0.000 |  |
| LASSO | 9.039 | 2.044 | -0.049 | 14.90 (14, 11-21) |
| adaLASSO | 8.632 | 2.029 | -0.001 | 15.95 (15, 6-26) |
| adaLASSO (gamma by BIC) | 8.739 | 2.021 | -0.014 | 11.93 (12, 8-19) |
| WLadaLASSO | 8.898 | 2.082 | -0.032 | 16.33 (16, 13-23) |
| WLadaLASSO (gamma by BIC) | 8.640 | 2.055 | -0.002 | 16.15 (16, 13-21) |
| Ext1 | 8.816 | 2.060 | -0.023 | 18.48 (18, 13-22) |
| Ext1 (gamma by BIC) | 9.001 | 2.103 | -0.044 | 18.35 (18, 13-25) |

## 3. Statistical tests
### 3.1 Earlier tests, gamma = 1 methods [V: reproduced independently to 1e-16]
Mean difference of the loss, first minus second (negative = first method better). The CI is mean +/- 1.96 x Newey-West (3 lags) standard error. The p-value is the two-sided modified Diebold-Mariano test (Harvey, Leybourne and Newbold 1997) with h = 1. Note that the CI and the p-value use different variance estimators (the MDM variance for h = 1 has no autocorrelation terms).

| first | second | loss | mean difference (first - second) | 95% CI low | 95% CI high | MDM p (two-sided) | share of origins first is better |
|---|---|---|---|---|---|---|---|
| Ext1 | WLadaLASSO | squared error | -0.082 | -0.466 | 0.302 | 0.662 | 0.467 |
| Ext1 | WLadaLASSO | absolute error | -0.022 | -0.091 | 0.047 | 0.463 | 0.467 |
| Ext1 | adaLASSO | squared error | 0.184 | -0.072 | 0.441 | 0.264 | 0.500 |
| Ext1 | adaLASSO | absolute error | 0.031 | -0.034 | 0.095 | 0.364 | 0.500 |
| WLadaLASSO | adaLASSO | squared error | 0.266 | -0.062 | 0.594 | 0.168 | 0.500 |
| WLadaLASSO | adaLASSO | absolute error | 0.052 | -0.007 | 0.112 | 0.173 | 0.500 |

### 3.2 Each method against AR(BIC) [N; no earlier file tested this]
| method | loss | mean difference vs AR(BIC) | 95% CI low | 95% CI high | MDM p (two-sided) | share of origins better than AR |
|---|---|---|---|---|---|---|
| LASSO | squared error | 0.420 | -1.342 | 2.182 | 0.714 | 0.483 |
| LASSO | absolute error | -0.018 | -0.273 | 0.236 | 0.923 | 0.483 |
| adaLASSO | squared error | 0.013 | -1.900 | 1.925 | 0.992 | 0.500 |
| adaLASSO | absolute error | -0.033 | -0.314 | 0.248 | 0.869 | 0.500 |
| adaLASSO (gamma by BIC) | squared error | 0.120 | -2.054 | 2.294 | 0.932 | 0.550 |
| adaLASSO (gamma by BIC) | absolute error | -0.041 | -0.341 | 0.260 | 0.846 | 0.550 |
| WLadaLASSO | squared error | 0.279 | -1.655 | 2.213 | 0.832 | 0.483 |
| WLadaLASSO | absolute error | 0.019 | -0.256 | 0.295 | 0.925 | 0.483 |
| WLadaLASSO (gamma by BIC) | squared error | 0.021 | -2.093 | 2.135 | 0.988 | 0.500 |
| WLadaLASSO (gamma by BIC) | absolute error | -0.007 | -0.306 | 0.292 | 0.973 | 0.500 |
| Ext1 | squared error | 0.197 | -1.854 | 2.248 | 0.883 | 0.500 |
| Ext1 | absolute error | -0.002 | -0.296 | 0.291 | 0.991 | 0.500 |
| Ext1 (gamma by BIC) | squared error | 0.382 | -1.730 | 2.494 | 0.788 | 0.467 |
| Ext1 (gamma by BIC) | absolute error | 0.041 | -0.246 | 0.328 | 0.847 | 0.467 |

### 3.3 Other pairwise comparisons [N]
| first | second | loss | mean difference | 95% CI low | 95% CI high | MDM p (two-sided) | share of origins first is better |
|---|---|---|---|---|---|---|---|
| WLadaLASSO | adaLASSO | squared error | 0.266 | -0.062 | 0.594 | 0.168 | 0.500 |
| WLadaLASSO | adaLASSO | absolute error | 0.052 | -0.007 | 0.112 | 0.173 | 0.500 |
| Ext1 | adaLASSO | squared error | 0.184 | -0.072 | 0.441 | 0.264 | 0.500 |
| Ext1 | adaLASSO | absolute error | 0.031 | -0.034 | 0.095 | 0.364 | 0.500 |
| Ext1 | WLadaLASSO | squared error | -0.082 | -0.466 | 0.302 | 0.662 | 0.467 |
| Ext1 | WLadaLASSO | absolute error | -0.022 | -0.091 | 0.047 | 0.463 | 0.467 |
| LASSO | adaLASSO | squared error | 0.407 | -0.542 | 1.357 | 0.475 | 0.517 |
| LASSO | adaLASSO | absolute error | 0.015 | -0.084 | 0.113 | 0.793 | 0.517 |
| WLadaLASSO | LASSO | squared error | -0.141 | -1.073 | 0.791 | 0.820 | 0.450 |
| WLadaLASSO | LASSO | absolute error | 0.038 | -0.061 | 0.137 | 0.570 | 0.450 |
| Ext1 | LASSO | squared error | -0.223 | -1.285 | 0.840 | 0.746 | 0.500 |
| Ext1 | LASSO | absolute error | 0.016 | -0.121 | 0.153 | 0.831 | 0.500 |
| adaLASSO (gamma by BIC) | adaLASSO | squared error | 0.107 | -0.269 | 0.484 | 0.659 | 0.517 |
| adaLASSO (gamma by BIC) | adaLASSO | absolute error | -0.008 | -0.072 | 0.057 | 0.829 | 0.517 |
| WLadaLASSO (gamma by BIC) | WLadaLASSO | squared error | -0.258 | -0.729 | 0.214 | 0.291 | 0.483 |
| WLadaLASSO (gamma by BIC) | WLadaLASSO | absolute error | -0.027 | -0.082 | 0.029 | 0.417 | 0.483 |
| Ext1 (gamma by BIC) | Ext1 | squared error | 0.185 | -0.079 | 0.450 | 0.414 | 0.333 |
| Ext1 (gamma by BIC) | Ext1 | absolute error | 0.044 | -0.001 | 0.089 | 0.104 | 0.333 |
| WLadaLASSO (gamma by BIC) | adaLASSO (gamma by BIC) | squared error | -0.099 | -0.463 | 0.265 | 0.581 | 0.483 |
| WLadaLASSO (gamma by BIC) | adaLASSO (gamma by BIC) | absolute error | 0.034 | -0.031 | 0.099 | 0.389 | 0.483 |
| Ext1 (gamma by BIC) | adaLASSO (gamma by BIC) | squared error | 0.262 | -0.272 | 0.796 | 0.372 | 0.450 |
| Ext1 (gamma by BIC) | adaLASSO (gamma by BIC) | absolute error | 0.082 | -0.012 | 0.176 | 0.095 | 0.450 |
| Ext1 (gamma by BIC) | WLadaLASSO (gamma by BIC) | squared error | 0.361 | -0.048 | 0.770 | 0.098 | 0.517 |
| Ext1 (gamma by BIC) | WLadaLASSO (gamma by BIC) | absolute error | 0.048 | -0.014 | 0.110 | 0.098 | 0.517 |

**Interpretation.** No pairwise difference is statistically distinguishable from zero at the 5% level (smallest two-sided p-values about 0.095 to 0.10, for Ext1 with gamma by BIC against the other gamma-BIC methods; these go against Ext1). No test shows any method better than AR(BIC). No multiple-testing adjustment is made; 60 observations only.

## 4. Sub-period analysis [E: windows chosen after seeing the results]
R2_OS against AR(BIC) by window. The gamma = 1 methods were computed earlier (`fred_subperiod_metrics.csv`; every row reproduced in this package [V]); LASSO and the gamma-BIC variants are [N].

| method | full 2020-10..2025-09 | 2020-10..2020-12 | 2021 | 2022 | 2021-22 surge | excluding 2021-22 | 2023-01..2025-09 |
|---|---|---|---|---|---|---|---|
| AR(BIC) | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| LASSO | -0.049 | 0.425 | 0.204 | -0.036 | 0.010 | -0.326 | -0.507 |
| adaLASSO | -0.001 | 0.296 | 0.224 | 0.042 | 0.077 | -0.369 | -0.530 |
| adaLASSO (gamma by BIC) | -0.014 | 0.312 | 0.301 | 0.039 | 0.089 | -0.498 | -0.694 |
| WLadaLASSO | -0.032 | 0.198 | 0.206 | 0.022 | 0.058 | -0.454 | -0.612 |
| WLadaLASSO (gamma by BIC) | -0.002 | 0.174 | 0.227 | 0.049 | 0.084 | -0.406 | -0.547 |
| Ext1 | -0.023 | 0.154 | 0.195 | 0.022 | 0.055 | -0.390 | -0.522 |
| Ext1 (gamma by BIC) | -0.044 | 0.064 | 0.109 | 0.020 | 0.037 | -0.429 | -0.548 |

AR(BIC) benchmark by window:

| window | n | MSFE | MAE |
|---|---|---|---|
| full 2020-10..2025-09 | 60 | 8.619 | 2.062 |
| 2020-10..2020-12 | 3 | 5.889 | 1.975 |
| 2021 | 12 | 6.833 | 2.127 |
| 2022 | 12 | 28.701 | 4.268 |
| 2021-22 surge | 24 | 17.767 | 3.198 |
| excluding 2021-22 | 36 | 2.521 | 1.305 |
| 2023-01..2025-09 | 33 | 2.215 | 1.244 |

Excluding 2021-22 (MSFE, MAE, R2_OS):

| method | MSFE | MAE | R2_OS |
|---|---|---|---|
| AR(BIC) | 2.521 | 1.305 | 0.000 |
| adaLASSO | 3.452 | 1.469 | -0.369 |
| WLadaLASSO | 3.666 | 1.486 | -0.454 |
| Ext1 | 3.505 | 1.450 | -0.390 |

Paired squared-error differences by window (`fred_subperiod_paired_diffs.csv` with the ratio mean/SE added; SE is the plain iid standard error; n = 3 window is not informative):

| period | n | contrast | mean_dSE | se | mean_over_SE |
|---|---|---|---|---|---|
| full (2020-10..2025-09) | 60 | WLadaLASSO - adaLASSO | 0.266 | 0.191 | 1.396 |
| full (2020-10..2025-09) | 60 | Ext1 - WLadaLASSO | -0.082 | 0.186 | -0.440 |
| 2020-10..2020-12 | 3 | WLadaLASSO - adaLASSO | 0.581 | 0.985 | 0.590 |
| 2020-10..2020-12 | 3 | Ext1 - WLadaLASSO | 0.259 | 0.060 | 4.287 |
| 2021-01..2021-12 | 12 | WLadaLASSO - adaLASSO | 0.119 | 0.412 | 0.289 |
| 2021-01..2021-12 | 12 | Ext1 - WLadaLASSO | 0.078 | 0.463 | 0.169 |
| 2022-01..2022-12 | 12 | WLadaLASSO - adaLASSO | 0.567 | 0.592 | 0.958 |
| 2022-01..2022-12 | 12 | Ext1 - WLadaLASSO | -0.002 | 0.447 | -0.005 |
| 2021-01..2022-12 (surge) | 24 | WLadaLASSO - adaLASSO | 0.343 | 0.356 | 0.964 |
| 2021-01..2022-12 (surge) | 24 | Ext1 - WLadaLASSO | 0.038 | 0.315 | 0.121 |
| EXCL 2021-2022 | 36 | WLadaLASSO - adaLASSO | 0.215 | 0.215 | 0.997 |
| EXCL 2021-2022 | 36 | Ext1 - WLadaLASSO | -0.162 | 0.230 | -0.701 |
| 2023-01..2025-09 | 33 | WLadaLASSO - adaLASSO | 0.181 | 0.222 | 0.816 |
| 2023-01..2025-09 | 33 | Ext1 - WLadaLASSO | -0.200 | 0.251 | -0.797 |

- All gamma = 1 methods beat AR(BIC) in 2021-22 (R2_OS +0.055 to +0.077) and are clearly worse outside it (-0.37 to -0.45 excluding 2021-22; -0.52 to -0.61 from 2023). The overall R2_OS near 0 mixes these opposite regimes. [E]
- 2022 alone contributes 66.6% of the AR(BIC) total squared error; the largest single AR(BIC) squared error is July 2022 (142.0). [N]
- No p-values or CIs were ever computed for sub-periods.

## 5. Gamma-BIC variants
They were fitted at all 60 origins (stored in `fred_refit1.pkl` and in the per-origin checkpoints) but never reported before. Performance is in section 2, tests in sections 3.2 and 3.3, sub-periods in section 4. Selected values, counted from the 60 refits [N] (full per-origin table: `computed_from_saved_forecasts/selection_per_origin_all_variants.csv`):

| method | parameter | value | n_origins | share |
|---|---|---|---|---|
| adaLASSO | gamma | 1.000 | 60 | 1.000 |
| adaLASSO (gamma by BIC) | gamma | 1.500 | 2 | 0.033 |
| adaLASSO (gamma by BIC) | gamma | 2.000 | 58 | 0.967 |
| WLadaLASSO | gamma | 1.000 | 60 | 1.000 |
| WLadaLASSO | alpha_or_kappa | 0.050 | 29 | 0.483 |
| WLadaLASSO | alpha_or_kappa | 0.100 | 18 | 0.300 |
| WLadaLASSO | alpha_or_kappa | 0.200 | 8 | 0.133 |
| WLadaLASSO | alpha_or_kappa | 0.350 | 1 | 0.017 |
| WLadaLASSO | alpha_or_kappa | 0.500 | 4 | 0.067 |
| WLadaLASSO (gamma by BIC) | gamma | 1.500 | 37 | 0.617 |
| WLadaLASSO (gamma by BIC) | gamma | 2.000 | 23 | 0.383 |
| WLadaLASSO (gamma by BIC) | alpha_or_kappa | 0.050 | 32 | 0.533 |
| WLadaLASSO (gamma by BIC) | alpha_or_kappa | 0.100 | 27 | 0.450 |
| WLadaLASSO (gamma by BIC) | alpha_or_kappa | 0.500 | 1 | 0.017 |
| Ext1 | gamma | 1.000 | 60 | 1.000 |
| Ext1 | alpha_or_kappa | 0.500 | 7 | 0.117 |
| Ext1 | alpha_or_kappa | 1.000 | 51 | 0.850 |
| Ext1 | alpha_or_kappa | 2.000 | 2 | 0.033 |
| Ext1 (gamma by BIC) | gamma | 1.000 | 15 | 0.250 |
| Ext1 (gamma by BIC) | gamma | 1.500 | 29 | 0.483 |
| Ext1 (gamma by BIC) | gamma | 2.000 | 16 | 0.267 |
| Ext1 (gamma by BIC) | alpha_or_kappa | 0.500 | 13 | 0.217 |
| Ext1 (gamma by BIC) | alpha_or_kappa | 1.000 | 34 | 0.567 |
| Ext1 (gamma by BIC) | alpha_or_kappa | 2.000 | 13 | 0.217 |

gamma = 0.5 was never selected by any variant; adaLASSO with gamma by BIC never selected gamma = 1. Whether the gamma grid is wide enough was not tested.

## 6. Convergence and diagnostics
- **Path-level warning [S].** The solver hit its 1,000-iteration cap on a large share of the lambda paths: 415 of the 420 selected fits (60 origins x 7 variants) and 91% to 100% (mean 96.6%) of all candidate paths per origin carry the warning. No selected fit lies at the end of the lambda path.
- **KKT / duality gap of the 420 selected solutions [V from `kkt_check_selected_solutions.csv`].** Rebuilt BIC equals stored BIC (max difference 1.8e-12), rebuilt df equals stored df in all 420. Inactive coordinates: maximum KKT violation 0.0. Active coordinates: maximum relative violation 0.0031 (median 0.0003). Relative duality gap: maximum 9.6e-5 against the solver tolerance 1e-4; 0 of 420 above tolerance, 41 above half of it. Results by variant:

| variant | n | max_abs_dBIC | df_mismatch | max_kkt_active_rel | max_kkt_inactive_rel | max_rel_gap | n_gap_gt_1e4 | n_path_warned |
|---|---|---|---|---|---|---|---|---|
| adalasso | 60 | 0.000 | 0 | 0.001 | 0.000 | 0.000 | 0 | 60 |
| adalasso_g | 60 | 0.000 | 0 | 0.001 | 0.000 | 0.000 | 0 | 60 |
| ext1 | 60 | 0.000 | 0 | 0.001 | 0.000 | 0.000 | 0 | 60 |
| ext1_g | 60 | 0.000 | 0 | 0.003 | 0.000 | 0.000 | 0 | 56 |
| lasso | 60 | 0.000 | 0 | 0.000 | 0.000 | 0.000 | 0 | 60 |
| wladalasso | 60 | 0.000 | 0 | 0.001 | 0.000 | 0.000 | 0 | 60 |
| wladalasso_g | 60 | 0.000 | 0 | 0.003 | 0.000 | 0.000 | 0 | 59 |

- **30,000-iteration re-solves.** At origin 727, all 7 variants including gamma-BIC: same hyper-parameters, variable sets, coefficients and BIC (`fred_convergence_origin0.csv`) [S]. At 6 evenly spaced origins (727, 739, 751, 762, 774, 786), 4 methods with gamma = 1 (24 comparisons): identical choice, variable set, coefficients (max difference 0.0), BIC and forecast; path warnings 24 of 24 become 0 of 24 [V from `highiter_6origins_comparison.csv`]. Not re-solved: the other 54 origins, and the gamma-BIC variants at the 5 other origins.
- **Other checks [V].** 0 missing or non-finite forecasts; metrics rebuilt from `forecasts.csv` agree to 1.8e-15; forecasts in `fred_refit1.pkl` agree with `forecasts.csv` to 3e-15; the AR(BIC) benchmark was reproduced from the saved forecasts (`fred_ar_bic_order.py`).
- Full verification record of this package: `computed_from_saved_forecasts/verification_record.json`.

## 7. Interpretation
**Supported.** In this window none of the methods forecasts better than AR(BIC): all R2_OS are zero or negative (adaLASSO -0.001, WLadaLASSO with gamma by BIC -0.002, WLadaLASSO -0.032, Ext1 -0.023, LASSO -0.049). Differences between the methods are small and not significant, so the lag-penalty methods (WLadaLASSO, Ext1) show no demonstrated gain over adaLASSO here, and choosing gamma by BIC shows no consistent gain either. The selected solutions are optimal to the solver tolerance, and a larger iteration limit changed nothing at the origins re-solved. [E] The overall result hides a gain in 2021-22 and a loss afterwards.

**Not supported / limits.** Only 60 forecasts in one window (including the pandemic recovery and the 2021-22 inflation surge), one data vintage, one target, one benchmark; p-values rely on asymptotic approximations with n = 60 and are not adjusted for multiple comparisons; the sub-period windows are post hoc; the evidence for convergence of the gamma-BIC variants is the KKT check and the origin-727 re-solve only. The earlier simulation advantage of WLadaLASSO at small T does not carry over to this large-sample setting; this is a description of one data set and says nothing about the paper's claims.

## 8. Files in this package
See `INDEX.md`.
