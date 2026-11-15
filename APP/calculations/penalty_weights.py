"""Illustrative penalty weights, written from the formulas in the report and in the notebook (cell 6.4).

The estimators solve a weighted LASSO with penalty  lambda * sum_j w_j |b_j|  and
    log w_j = gamma * base_j + extra_j,        base_j = -log |ridge coefficient_j|
    extra_j = 0                    adaLASSO
            = alpha * l_j          WLadaLASSO          (l_j = lag order of regressor j, l = 1, 2, ...)
            = kappa * pi_(l_j)     Ext1                (pi_l = log m_1 - log m_l, m = isotonic fit of the mean |ridge| by lag)
LASSO has w_j = 1.  The notebook also shifts the log-weights by their minimum and caps them at 25.
Nothing here is an experimental result: the 'ridge profile' is something the visitor chooses."""
import numpy as np

LOGW_CAP = 25.0

PROFILES = {
    "Geometric decay (typical)": "Mean |ridge coefficient| shrinks by a constant factor with every lag.",
    "Two relevant lags, then noise": "Large coefficients at lags 1-2, small and equal ones afterwards (like the simulation design).",
    "Flat": "All lags look equally important.",
    "Bump at a seasonal lag": "Decay, plus a large coefficient at lag 12 (a seasonal effect).",
}


def raw_profile(kind, L, decay=0.6):
    """Illustrative mean |ridge coefficient| at lags 1..L (first lag scaled to 1)."""
    l = np.arange(1, L + 1)
    if kind == "Flat":
        m = np.ones(L)
    elif kind == "Two relevant lags, then noise":
        m = np.where(l <= 2, 1.0, 0.05)
    elif kind == "Bump at a seasonal lag":
        m = decay ** (l - 1)
        if L >= 12:
            m = m.copy(); m[11] = max(m[11], 0.6)
    else:
        m = decay ** (l - 1)
    return np.asarray(m, float)


def isotonic_nonincreasing(y):
    """Pool-adjacent-violators fit of a non-increasing sequence (same result as sklearn IsotonicRegression(increasing=False))."""
    y = np.asarray(y, float)
    blocks = []                      # each block: [sum, count]
    for v in y:
        blocks.append([v, 1])
        # non-increasing fit: merge while a later block has a larger mean than the earlier one
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] < blocks[-1][0] / blocks[-1][1]:
            s, c = blocks.pop(); blocks[-1][0] += s; blocks[-1][1] += c
    return np.concatenate([[s / c] * c for s, c in blocks])


def ext1_lag_penalty(m_raw):
    """pi_l = log m_1 - log m_l >= 0 with m the isotonic (non-increasing) fit of the mean |ridge| by lag."""
    m = isotonic_nonincreasing(m_raw)
    m = np.maximum(m, 1e-6 * m.max() + 1e-12)       # same positivity guard as the notebook
    return np.log(m[0]) - np.log(m), m


def log_weights(method, L, gamma=1.0, alpha=0.0, kappa=0.0, profile="Geometric decay (typical)", decay=0.6):
    """Return a dict with the lag factor, the full relative weight and diagnostics for one illustrative variable per lag."""
    lags = np.arange(1, L + 1)
    m_raw = raw_profile(profile, L, decay)
    base = -np.log(np.abs(m_raw) + 1e-8)                  # -log |ridge coefficient|
    m_fit = None
    if method == "LASSO":
        extra = np.zeros(L); lw = np.zeros(L)
    elif method == "adaLASSO":
        extra = np.zeros(L); lw = gamma * base
    elif method == "WLadaLASSO":
        extra = alpha * lags; lw = gamma * base + extra
    elif method == "Ext1":
        pi, m_fit = ext1_lag_penalty(m_raw)
        extra = kappa * pi; lw = gamma * base + extra
    else:
        raise ValueError(method)
    lw_shift = np.minimum(lw - lw.min(), LOGW_CAP)        # notebook: shift by the minimum, cap at 25
    capped = bool(np.any(lw - lw.min() > LOGW_CAP))
    return dict(lags=lags, m_raw=m_raw, m_fit=m_fit, lag_factor=np.exp(extra), log_extra=extra,
                weight=np.exp(lw_shift), log_weight=lw_shift, capped=capped)
