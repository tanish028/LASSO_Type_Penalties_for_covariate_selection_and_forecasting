import numpy as np
import streamlit as st
import plotly.graph_objects as go
from components.theme import setup_page, header, note, COLORS, MUTED
from components.navigation import sidebar_footer
from components.explanations import METHODS
from calculations.penalty_weights import log_weights, PROFILES, LOGW_CAP

setup_page("Penalty explorer")
sidebar_footer()
header("Interactive", "Penalty explorer",
       "How much does each lag pay? Choose a method and its parameters; the curves and the explanation update immediately.")
note("These curves are <b>illustrative</b>. They apply the formulas of the methods to an invented 'ridge profile' that you choose below. "
     "They are not results of our experiments: in a real fit the ridge coefficients come from the data.", "warn")

with st.sidebar:
    st.markdown("### Controls")
    method = st.radio("Method", ["LASSO", "adaLASSO", "WLadaLASSO", "Ext1"], index=2)
    L = st.slider("Number of lags L", 2, 24, 12)
    gamma = st.slider("γ (gamma): adaptive exponent", 0.25, 3.0, 1.0, 0.25, disabled=(method == "LASSO"))
    alpha = st.slider("α (alpha): lag growth, WLadaLASSO", 0.0, 2.0, 0.5, 0.05, disabled=(method != "WLadaLASSO"))
    kappa = st.slider("κ (kappa): lag scale, Ext1", 0.0, 10.0, 1.0, 0.25, disabled=(method != "Ext1"))
    st.markdown("### Illustrative ridge profile")
    profile = st.selectbox("Shape of the mean |ridge coefficient| by lag", list(PROFILES))
    decay = st.slider("Decay per lag", 0.3, 0.95, 0.6, 0.05, disabled=(profile == "Flat"))
    st.caption(PROFILES[profile])

res = log_weights(method, L, gamma, alpha, kappa, profile, decay)
lags = res["lags"]

left, right = st.columns([3, 2], gap="large")
with left:
    view = st.radio("Show", ["Lag factor", "Full relative weight", "Both"], horizontal=True, index=2)
    logy = st.checkbox("Logarithmic vertical axis", value=(method in ("WLadaLASSO", "Ext1") and L > 8))
    fig = go.Figure()
    col = COLORS[method]
    if view in ("Lag factor", "Both"):
        fig.add_scatter(x=lags, y=res["lag_factor"], mode="lines+markers", name="lag factor",
                        line=dict(color=col, width=3), marker=dict(size=7),
                        hovertemplate="lag %{x}<br>lag factor %{y:.3f}<extra></extra>")
    if view in ("Full relative weight", "Both"):
        w = res["weight"] / res["weight"][0] if method != "LASSO" else res["weight"]
        fig.add_scatter(x=lags, y=w, mode="lines+markers", name="full weight ω (relative to lag 1)",
                        line=dict(color=col, width=2, dash="dot"), marker=dict(size=6, symbol="diamond"),
                        hovertemplate="lag %{x}<br>weight relative to lag 1: %{y:.3f}<extra></extra>")
    fig.update_layout(height=450, xaxis_title="lag order l", yaxis_title="penalty multiplier" + (" (log scale)" if logy else ""),
                      legend=dict(orientation="h", y=1.1), xaxis=dict(dtick=1 if L <= 12 else 2))
    if logy:
        fig.update_yaxes(type="log")
    st.plotly_chart(fig, width="stretch")
    st.markdown('<p class="small">A higher value means a heavier price for a regressor at that lag, so it is shrunk harder and more likely to be set to zero. '
                'The full weight combines the lag factor with the ridge part for an illustrative variable whose coefficients follow the chosen profile.</p>', unsafe_allow_html=True)

with right:
    st.markdown("### Equation")
    st.latex(METHODS[method]["latex"] if method != "LASSO" else r"\omega_j = 1")
    st.markdown("### What the parameters do")
    if method == "LASSO":
        st.markdown("Every coefficient pays the same price, so the curve is flat and γ (gamma), α (alpha) and κ (kappa) have no effect. "
                    "This is the benchmark the other three methods modify.")
    elif method == "adaLASSO":
        st.markdown(f"There is **no lag factor**: the weight depends only on the ridge coefficient, as $|\\hat\\beta^{{ridge}}|^{{-\\gamma}}$. "
                    f"With γ = {gamma:g}, a lag whose ridge coefficient is half as large pays {2 ** gamma:.2f} times as much. "
                    "Raising γ makes the weights more extreme.")
    elif method == "WLadaLASSO":
        if alpha == 0:
            st.markdown("With **α = 0** the lag factor equals one everywhere, so WLadaLASSO is exactly adaLASSO.")
        else:
            st.markdown(f"Each extra lag multiplies the price by $e^{{\\alpha}}$ = **{np.exp(alpha):.2f}**. "
                        f"Lag {L} pays **{res['lag_factor'][-1] / res['lag_factor'][0]:.3g}** times as much as lag 1, from the lag factor alone. "
                        "A larger α pushes long lags to zero faster; in the experiments BIC chooses α from a grid of 17 values between 0 and 20.")
    else:
        pi = res["log_extra"] / kappa if kappa > 0 else None
        if kappa == 0:
            st.markdown("With **κ = 0** the lag factor equals one everywhere, so Ext1 is exactly adaLASSO.")
        else:
            st.markdown(f"The lag factor is $e^{{\\kappa\\pi_l}}$ where $\\pi_l$ measures how far the isotonic profile has fallen relative to lag 1. "
                        f"For this profile, lag {L} has $\\pi$ = {pi[-1]:.2f} and factor **{res['lag_factor'][-1]:.3g}**. "
                        "The shape comes from the profile, not from a fixed exponential: a flat profile gives no lag penalty at all.")
    if res["capped"]:
        note("The full weight reaches the cap that the notebook applies to log-weights (25), so the curve is flattened at the top.", "warn")
    if method == "Ext1":
        st.markdown("### The profile behind Ext1")
        f2 = go.Figure()
        f2.add_scatter(x=lags, y=res["m_raw"], mode="markers", name="illustrative mean |ridge|", marker=dict(color=MUTED, size=8))
        f2.add_scatter(x=lags, y=res["m_fit"], mode="lines", name="isotonic (non-increasing) fit", line=dict(color=COLORS["Ext1"], width=3, shape="hv"))
        f2.update_layout(height=280, xaxis_title="lag l", yaxis_title="m_l", legend=dict(orientation="h", y=1.2), margin=dict(t=30))
        st.plotly_chart(f2, width="stretch")
        st.markdown('<p class="small">Dots: the invented mean ridge coefficient by lag. Line: the non-increasing curve fitted through them, from which $\\pi_l=\\log m_1-\\log m_l$ is computed. '
                    'A bump at a long lag is flattened by the monotone fit, which is the limit of Ext1 noted in the report.</p>', unsafe_allow_html=True)

st.markdown("## Compare the four methods at these settings")
fig = go.Figure()
for mm in ["LASSO", "adaLASSO", "WLadaLASSO", "Ext1"]:
    r = log_weights(mm, L, gamma, alpha, kappa, profile, decay)
    y = r["weight"] if mm == "LASSO" else r["weight"] / r["weight"][0]
    fig.add_scatter(x=r["lags"], y=y, mode="lines+markers", name=mm, line=dict(color=COLORS[mm], width=3 if mm == method else 1.6), opacity=1 if mm == method else .75)
fig.update_layout(height=380, xaxis_title="lag order l", yaxis_title="full weight, relative to lag 1 (log scale)", yaxis_type="log", legend=dict(orientation="h", y=1.12))
st.plotly_chart(fig, width="stretch")
st.markdown('<p class="small">All four curves use the same invented ridge profile, γ, α and κ. Illustration only; nothing here was estimated from data.</p>', unsafe_allow_html=True)

# ------------------------------------------------------------------ extra interactive views
st.markdown("## ▶ Watch the lag penalty grow")
st.markdown("Press play: α (alpha, WLadaLASSO) or κ (kappa, Ext1) sweeps over the grid used in the study, and the penalty each lag pays changes shape. Drag the slider to stop at any value.")
which = st.radio("Sweep", ["α (alpha) for WLadaLASSO", "κ (kappa) for Ext1"], horizontal=True)
if which.startswith("α"):
    grid_vals = [0.0, 0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]; mname = "WLadaLASSO"
else:
    grid_vals = [0.0, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.5, 10.0]; mname = "Ext1"


def _curve(v):
    r = log_weights(mname, L, gamma, v if mname == "WLadaLASSO" else 0.0, v if mname == "Ext1" else 0.0, profile, decay)
    return r["lag_factor"]


frames = [go.Frame(data=[go.Scatter(x=lags, y=_curve(v))], name=f"{v:g}") for v in grid_vals]
ymax = max(_curve(grid_vals[-1]).max(), 2)
fa = go.Figure(data=[go.Scatter(x=lags, y=_curve(grid_vals[0]), mode="lines+markers", line=dict(color=COLORS[mname], width=4), marker=dict(size=8), fill="tozeroy", fillcolor="rgba(79,163,247,.10)")], frames=frames)
fa.update_layout(height=420, xaxis_title="lag", yaxis_title="lag factor (penalty multiplier, log scale)", yaxis=dict(type="log", range=[-0.1, np.log10(ymax) + 0.1]),
                 updatemenus=[dict(type="buttons", direction="left", x=0.0, y=1.18, buttons=[
                     dict(label="▶ play", method="animate", args=[None, dict(frame=dict(duration=650, redraw=True), fromcurrent=True, transition=dict(duration=300))]),
                     dict(label="❚❚ pause", method="animate", args=[[None], dict(mode="immediate", frame=dict(duration=0))])])],
                 sliders=[dict(active=0, x=0.12, len=0.85, currentvalue=dict(prefix=("α (alpha) = " if mname == "WLadaLASSO" else "κ (kappa) = ")),
                               steps=[dict(label=f.name, method="animate", args=[[f.name], dict(mode="immediate", frame=dict(duration=0), transition=dict(duration=200))]) for f in frames])])
st.plotly_chart(fa, width="stretch")

st.markdown("## 🔥 Weight map: how ridge size and lag combine")
st.markdown(f"Colour = ln of the penalty weight a regressor receives under **{method}**, as a function of its lag (x) and the size of its first-stage ridge coefficient (y). "
            "Bright = expensive. In adaLASSO the map changes only vertically; the lag-aware methods also tilt it horizontally.")
mag = np.geomspace(1e-3, 1.0, 40)
lagsg = np.arange(1, L + 1)
Z = np.zeros((len(mag), L))
for i, mg in enumerate(mag):
    for j, l in enumerate(lagsg):
        base = -gamma * np.log(mg + 1e-8) if method != "LASSO" else 0.0
        if method == "WLadaLASSO":
            ex = alpha * l
        elif method == "Ext1":
            ex = res["log_extra"][j]
        else:
            ex = 0.0
        Z[i, j] = base + ex
Z = Z - Z.min()
fh = go.Figure(go.Heatmap(z=Z, x=lagsg, y=mag, colorscale="Viridis", colorbar=dict(title="ln w"), hovertemplate="lag %{x}<br>|ridge| %{y:.3g}<br>ln w %{z:.2f}<extra></extra>"))
fh.update_layout(height=420, xaxis_title="lag", yaxis_title="|ridge coefficient| (log scale)", yaxis_type="log")
st.plotly_chart(fh, width="stretch")

st.markdown("## 🎛️ Who survives the penalty? A toy shrinkage experiment")
st.markdown("Each lag has one regressor with a **true** effect that follows your ridge profile (positive, decaying) plus estimation noise. "
            "With uncorrelated regressors a LASSO estimate is the observed effect shrunk by λ·weight and set to zero when it falls below that line. "
            "Raise λ and watch which lags survive under each method.")
c1, c2, c3 = st.columns(3)
lam_t = c1.slider("λ (lambda): overall penalty", 0.0, 0.8, 0.12, 0.01)
sig = c2.slider("Noise on each estimate", 0.0, 0.4, 0.08, 0.01)
seed_t = c3.number_input("Noise seed", 0, 999, 7)
rng = np.random.default_rng(int(seed_t))
true_eff = 0.9 * res["m_raw"]
xi = rng.standard_normal(L)
zobs = true_eff + sig * xi
fig = go.Figure()
from plotly.subplots import make_subplots
fs = make_subplots(rows=1, cols=4, subplot_titles=["LASSO", "adaLASSO", "WLadaLASSO", "Ext1"], shared_yaxes=True)
alive = {}
for k, mm in enumerate(["LASSO", "adaLASSO", "WLadaLASSO", "Ext1"]):
    r = log_weights(mm, L, gamma, alpha, kappa, profile, decay)
    w = r["weight"] / r["weight"].min() * (1.0 if mm == "LASSO" else 1.0)
    w = r["weight"] if mm == "LASSO" else np.exp(r["log_weight"] - r["log_weight"].min())
    est = np.sign(zobs) * np.maximum(np.abs(zobs) - lam_t * w, 0)
    alive[mm] = int((est != 0).sum())
    fs.add_trace(go.Bar(x=lagsg, y=true_eff, marker_color="rgba(143,161,191,.35)", name="true effect", showlegend=(k == 0)), row=1, col=k + 1)
    fs.add_trace(go.Bar(x=lagsg, y=est, marker_color=[COLORS[mm] if e != 0 else "rgba(0,0,0,0)" for e in est], name="estimate", showlegend=False), row=1, col=k + 1)
    fs.update_xaxes(title_text="lag", row=1, col=k + 1)
fs.update_layout(height=360, barmode="overlay", legend=dict(orientation="h", y=1.15))
st.plotly_chart(fs, width="stretch")
st.markdown("**Lags still in the model:** " + " · ".join(f"{m} {n}/{L}" for m, n in alive.items()) +
            '. <span class="small">Grey = true effect, colour = surviving estimate. An illustration of the mechanism (orthogonal regressors, weights from the formulas above); the real fits use correlated regressors and BIC.</span>', unsafe_allow_html=True)
