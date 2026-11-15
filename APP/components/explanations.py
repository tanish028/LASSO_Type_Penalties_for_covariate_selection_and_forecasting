"""Text and formulas used on several pages (kept in one place so the pages stay consistent with the report)."""

PAPER = "Konzen, E. and Ziegelmann, F. A. (2016). LASSO-type penalties for covariate selection and forecasting in time series. Journal of Forecasting, 35(7), 592-612."
REPORT_TITLE = "Lag-Dependent Adaptive LASSO Penalties for Time Series Forecasting: A Replication and Extension of Konzen and Ziegelmann (2016)"

METHODS = {
    "LASSO": dict(
        tag=("From the paper", "tag-paper"),
        latex=r"\hat\beta^{\text{LASSO}}=\arg\min_{\beta_0,\ldots,\beta_k}\Big\{\sum_{i=1}^{n}\big(y_i-\beta_0-\sum_{j=1}^{k}\beta_j x_{ji}\big)^2+\lambda\sum_{j=1}^{k}|\beta_j|\Big\}",
        terms=[("y_i", "the series we forecast, at time i"), ("x_{ji}", "regressor j (a lag of y or of a predictor); every lag is its own regressor"),
               ("\\beta_j", "the coefficient of regressor j; regressors with a non-zero coefficient are the selected ones"),
               ("\\lambda\\ge 0", "the price of coefficient size. λ=0 is least squares, a large λ gives the empty model. Chosen by BIC")],
        intuition="Least squares breaks down when there are more regressors than observations. The L1 penalty has a corner at zero, so some coefficients come out exactly zero: estimation and variable selection happen in one step.",
        difference="This is the starting point. Every coefficient pays the same price per unit of size, so a large true coefficient is shrunk as much as a worthless one."),
    "adaLASSO": dict(
        tag=("From the paper", "tag-paper"),
        latex=r"\hat\beta^{\text{ada}}=\arg\min_{\beta}\Big\{\text{RSS}+\lambda\sum_{j=1}^{k}\omega_j|\beta_j|\Big\},\qquad \omega_j=|\hat\beta_j^{\text{ridge}}|^{-\gamma}",
        terms=[("\\omega_j", "a weight for each regressor. A large weight means a heavy price"),
               ("\\hat\\beta_j^{\\text{ridge}}", "coefficient from a first-stage ridge regression, which can be computed even when k > n"),
               ("\\gamma>0", "how strongly the ridge size matters. The paper uses γ = 1; our 'γ by BIC' variants let BIC choose it")],
        intuition="A regressor that looks important in the ridge fit gets a small weight and is penalised lightly; one that looks irrelevant gets a large weight and is pushed to zero.",
        difference="LASSO charged everybody the same. adaLASSO lets the data decide who is charged more, which is what gives it the 'oracle' selection property in the paper's Theorem 1."),
    "WLadaLASSO": dict(
        tag=("From the paper", "tag-paper"),
        latex=r"\omega_j=|\hat\beta_j^{\text{ridge}}|^{-\gamma}\;e^{\alpha\, l_j},\qquad \alpha\ge 0",
        terms=[("l_j", "the lag order of regressor j (1 for the last observation, 2 for the one before, and so on)"),
               ("\\alpha\\ge 0", "how fast the price grows with the lag. Chosen by BIC together with λ"),
               ("e^{\\alpha l_j}", "the lag factor: it multiplies the adaLASSO weight. With α (alpha) = 0 it equals one")],
        intuition="In forecasting one often expects distant lags to matter less, as in the Minnesota prior of Bayesian VARs. The factor makes the penalty grow geometrically with the lag.",
        difference="With α (alpha) = 0 this is exactly adaLASSO, so BIC can fall back to it. The lag factor is a modelling assumption: it helps when long lags are mostly noise (our simulation design) and can hurt when an important effect sits at a long lag, such as seasonality."),
    "Ext1": dict(
        tag=("Our extension", "tag-ours"),
        latex=r"\omega_j=|\hat\beta_j^{\text{ridge}}|^{-\gamma}\;e^{\kappa\,\pi_{l_j}},\qquad \pi_l=\log m_1-\log m_l\ \ge 0,\quad \kappa\ge 0",
        terms=[("m_l", "the mean of |ridge coefficient| over variables at lag l, smoothed by a non-increasing (isotonic regression) curve"),
               ("\\pi_l", "how far the profile has fallen at lag l relative to lag 1. Zero when the profile is flat"),
               ("\\kappa\\ge 0", "scale of the lag penalty, chosen by BIC along with λ (9 values from 0 to 10). κ (kappa) = 0 is adaLASSO")],
        intuition="The exponential factor forces the log-penalty to be a straight line in the lag. Ext1 lets the ridge coefficients suggest the shape instead: if they fall quickly, later lags are penalised more; if they are flat, Ext1 behaves like adaLASSO.",
        difference="WLadaLASSO assumes the shape (exponential) and estimates one number α (alpha). Ext1 estimates the shape from the data and keeps one scale κ. Its limits: the profile is estimated from ridge coefficients, which are noisy when n is small, it is forced to be monotone, and it adds a tuning parameter."),
}

# the text next to the equity premium discrepancy
EQUITY_DISCREPANCY = (
    "We could not reproduce the equity premium table of the original paper under any specification we tried. Our penalised out-of-sample R² values "
    "are close to zero or negative (of 18 per data version only three are positive, the largest 0.015, and no one-sided p-value is below 0.24), "
    "whereas the paper reports 0.07 to 0.47 with 9 of its 15 penalised values significant at 10%. The paper does not say which data file, which premium "
    "definition or whether the premium was differenced, so we ran three data versions. We do not claim that the original results are wrong; "
    "we report only that they were not reproduced under the specifications we tested and documented. The cause is unresolved.")
