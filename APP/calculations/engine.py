"""Small, dependency-light re-implementation of the study's estimators for the live Lab page.

It follows the notebook's definitions (section 6.4): standardised data, ridge first stage with its penalty chosen by BIC,
log w_j = gamma * (-log|ridge_j|) + extra_j (shifted by its minimum and capped at 25), the weighted LASSO solved as an ordinary
LASSO on X_j / w_j along a log-spaced lambda grid, BIC = n ln(RSS/n) + k ln n with k = number of non-zero coefficients and a
cap of n/2 non-zero coefficients. The LASSO solver is a numpy active-set coordinate descent (the notebook uses scikit-learn's).
This is for illustration of single simulated data sets. It is NOT the code that produced the saved results.
"""
import numpy as np
from scipy.signal import lfilter
from .penalty_weights import isotonic_nonincreasing

LOGW_CAP = 25.0
METHODS = ("LASSO", "adaLASSO", "WLadaLASSO", "Ext1")
ALPHA_GRID = [0.0, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0]
KAPPA_GRID = [0.0, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.5, 10.0]
# smaller grids used by the Lab when BIC chooses alpha / kappa (the study uses the full grids above)
LAB_ALPHA_GRID = [0.0, 0.1, 0.35, 0.75, 1.5, 3.0, 6.0, 10.0, 20.0]
LAB_KAPPA_GRID = [0.0, 0.5, 1.0, 2.0, 5.0, 10.0]


# ------------------------------------------------------------------ data (paper eq. 10)
def simulate_data(T, L, rho, err, rng, burn=100, noise_scale=1.0):
    n = T + L + burn
    draw = (lambda s: rng.standard_normal(s)) if err == "normal" else (lambda s: rng.standard_t(5, s))
    u = draw((n, 10))
    eps = noise_scale * draw(n)
    x = lfilter([1.0], [1.0, -rho], u, axis=0)
    y = np.zeros(n)
    for t in range(2, n):
        y[t] = (0.8 * y[t - 1] + 0.6 * x[t - 1, 0] + 0.3 * x[t - 2, 0] - 0.5 * x[t - 1, 1] - 0.2 * x[t - 2, 1]
                + 0.4 * x[t - 1, 2] + 0.3 * x[t - 2, 2] + 0.4 * x[t - 1, 3] - 0.3 * x[t - 1, 4] + 0.2 * x[t - 1, 5] + eps[t])
    return np.column_stack([y, x])[burn:]


def true_beta(L, K=10):
    B = np.zeros((K + 1, L))
    B[0, 0] = 0.8
    B[1, 0], B[1, 1] = 0.6, 0.3
    B[2, 0], B[2, 1] = -0.5, -0.2
    B[3, 0], B[3, 1] = 0.4, 0.3
    B[4, 0] = 0.4
    B[5, 0] = -0.3
    B[6, 0] = 0.2
    return B.ravel()


def lag_matrix(D, L):
    T, M = D.shape
    cols, lag_order = [], []
    for m in range(M):
        for l in range(1, L + 1):
            cols.append(D[L - l:T - l + 1, m]); lag_order.append(l)
    return np.column_stack(cols), np.array(lag_order)


def standardize(X, y):
    mu, sd = X.mean(0), X.std(0)
    sd = np.where(sd < 1e-12, 1.0, sd)
    return (X - mu) / sd, y - y.mean(), mu, sd, y.mean()


# ------------------------------------------------------------------ first stage and weights
def ridge_beta(Xs, yc, cap=0.5, n_grid=60):
    n, p = Xs.shape
    U, S, Vt = np.linalg.svd(Xs, full_matrices=False)
    Uty = U.T @ yc
    best, bb, fb = np.inf, None, None
    for lam in S[0] ** 2 * np.logspace(-8, 1, n_grid):
        beta = Vt.T @ ((S / (S ** 2 + lam)) * Uty)
        df = float(np.sum(S ** 2 / (S ** 2 + lam)))
        fb = beta
        if df > cap * n:
            continue
        crit = n * np.log(float(np.sum((yc - Xs @ beta) ** 2)) / n + 1e-12) + df * np.log(n)
        if crit < best:
            best, bb = crit, beta
    return bb if bb is not None else fb


def lag_profile(b, lag_order, L):
    lags = np.arange(1, L + 1)
    m = isotonic_nonincreasing(np.array([np.mean(np.abs(b[lag_order == l])) for l in lags]))
    return np.maximum(m, 1e-6 * m.max() + 1e-12)


def log_weight_vector(method, ridge, lag_order, L, gamma, alpha, kappa):
    p = len(lag_order)
    if method == "LASSO":
        return np.zeros(p)
    base = -np.log(np.abs(ridge) + 1e-8)
    if method == "adaLASSO":
        return gamma * base
    if method == "WLadaLASSO":
        return gamma * base + alpha * lag_order
    m = lag_profile(ridge, lag_order, L)
    return gamma * base + kappa * (np.log(m[0]) - np.log(m[lag_order - 1]))


# ------------------------------------------------------------------ weighted LASSO path (active-set coordinate descent)
def _cd_path(G, c, lams, kmax, tol=1e-9, max_sweeps=2000):
    p = len(c)
    B = np.full((p, len(lams)), np.nan)
    b = np.zeros(p)
    diag = np.diag(G).copy()
    for k, lam in enumerate(lams):
        active = set(np.flatnonzero(b))
        for _ in range(60):                                    # active-set growth rounds
            act = np.array(sorted(active), dtype=int)
            for _s in range(max_sweeps):
                dmax = 0.0
                for j in act:
                    if diag[j] < 1e-14:
                        continue
                    r = c[j] - G[j] @ b + diag[j] * b[j]
                    new = np.sign(r) * max(abs(r) - lam, 0.0) / diag[j]
                    d = abs(new - b[j])
                    if d > dmax:
                        dmax = d
                    b[j] = new
                if dmax < tol:
                    break
            grad = c - G @ b
            viol = np.flatnonzero((np.abs(grad) > lam * (1 + 1e-9) + 1e-12) & (diag > 1e-14))
            viol = [j for j in viol if j not in active]
            if not viol:
                break
            active.update(viol)
        B[:, k] = b
        if np.count_nonzero(b) > kmax:
            break
    return B


def wl_fit(Xs, yc, log_w, n_lambda=60, eps=1e-3, df_cap=0.5):
    """BIC-best weighted LASSO fit. Returns beta (standardised scale), the BIC along the path and diagnostics."""
    n, p = Xs.shape
    lw = np.minimum(log_w - np.min(log_w), LOGW_CAP)
    w = np.exp(lw)
    Xw = Xs / w
    G, c = Xw.T @ Xw / n, Xw.T @ yc / n
    lam_max = float(np.max(np.abs(c)))
    lams = np.geomspace(lam_max, lam_max * eps, n_lambda) if lam_max > 1e-12 else np.full(n_lambda, 1e-12)
    B = _cd_path(G, c, lams, kmax=int(df_cap * n))
    ok = ~np.isnan(B[0])
    beta = np.where(ok[None, :], B, 0.0) / w[:, None]
    rss = ((yc[:, None] - Xs @ beta) ** 2).sum(0)
    k = (beta != 0).sum(0)
    bic = n * np.log(rss / n + 1e-12) + k * np.log(n)
    bic = np.where(~ok | (k > df_cap * n), np.inf, bic)
    j = int(np.argmin(bic))
    return dict(beta=beta[:, j], bic=float(bic[j]), bic_path=bic, lams=lams, j=j, k=int(k[j]), w=w)


def fit_methods(Xs, yc, lag_order, L, gamma=1.0, alpha=1.0, kappa=1.0, tune=False, alphas=None, kappas=None):
    """Fit the four methods on one standardised sample. tune=True lets BIC choose alpha / kappa over a grid."""
    ridge = ridge_beta(Xs, yc)
    out = {}
    for m in METHODS:
        if m == "WLadaLASSO" and tune:
            cands = [(a, wl_fit(Xs, yc, log_weight_vector(m, ridge, lag_order, L, gamma, a, 0.0))) for a in (alphas or LAB_ALPHA_GRID)]
        elif m == "Ext1" and tune:
            cands = [(k_, wl_fit(Xs, yc, log_weight_vector(m, ridge, lag_order, L, gamma, 0.0, k_))) for k_ in (kappas or LAB_KAPPA_GRID)]
        else:
            a = alpha if m == "WLadaLASSO" else None
            k_ = kappa if m == "Ext1" else None
            cands = [(a if a is not None else k_, wl_fit(Xs, yc, log_weight_vector(m, ridge, lag_order, L, gamma, alpha, kappa)))]
        h, f = min(cands, key=lambda t: t[1]["bic"])
        f["hyper"] = h if m in ("WLadaLASSO", "Ext1") else None
        f["logw"] = np.log(f["w"])
        out[m] = f
    return out


def selection_metrics(b_hat, b_true):
    sel, rel = b_hat != 0, b_true != 0
    tp, fp = int(np.sum(sel & rel)), int(np.sum(sel & ~rel))
    return dict(recall=float(sel[rel].mean()), FIVE=float((~sel[~rel]).mean()), NIV=int(sel.sum()),
                precision=(tp / (tp + fp)) if (tp + fp) else float("nan"), TP=tp, FP=fp)


def run_replication(seed, T, L, rho, err, noise, n_test=10, refit_every=5, gamma=1.0, alpha=1.0, kappa=1.0, tune=False):
    """One simulated data set: selection quality from the first fit, forecast errors from rolling one-step forecasts."""
    import time
    _t0 = time.time()
    rng = np.random.default_rng(seed)
    D = simulate_data(T, L, rho, err, rng, noise_scale=noise)
    N = len(D)
    Z, lag_order = lag_matrix(D, L)
    y = D[:, 0]
    bt = true_beta(L)
    pred = {m: [] for m in METHODS}
    first, coefs = None, None
    for i, t in enumerate(range(N - n_test, N)):
        if i % refit_every == 0:
            Xs, yc, mu, sd, ym = standardize(Z[0:t - L], y[L:t])
            fits = fit_methods(Xs, yc, lag_order, L, gamma, alpha, kappa, tune)
            coefs = {m: (f["beta"] / sd, float(ym - mu @ (f["beta"] / sd))) for m, f in fits.items()}
            if first is None:
                first = dict(fits=fits, coef={m: v[0] for m, v in coefs.items()}, lag_order=lag_order)
        for m in METHODS:
            b, b0 = coefs[m]
            pred[m].append(float(Z[t - L] @ b + b0))
    actual = y[N - n_test:]
    res = {}
    for m in METHODS:
        e = actual - np.array(pred[m])
        res[m] = dict(msfe=float(np.mean(e ** 2)), mae=float(np.mean(np.abs(e))), pred=np.array(pred[m]),
                      **selection_metrics(first["coef"][m], bt))
    return dict(res=res, actual=actual, first=first, b_true=bt, L=L, seconds=time.time() - _t0)
