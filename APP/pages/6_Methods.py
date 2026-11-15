import streamlit as st
from components.theme import setup_page, header, note
from components.navigation import sidebar_footer, page_links
from components.explanations import METHODS

setup_page("Methods")
sidebar_footer()
header("Section 1", "Understanding the methods",
       "Four estimators, each a small change to the one before. Three come from Konzen and Ziegelmann (2016); the fourth, Ext1, is ours.")
note("Notation. y is the series we forecast, the k candidate regressors x<sub>j</sub> are lagged values of y and of the predictors (each lag counts as its own regressor), "
     "and n is the number of training observations. RSS is the residual sum of squares.")

prev = None
for i, (name, m) in enumerate(METHODS.items(), start=1):
    label, cls = m["tag"]
    st.markdown(f'## {i}. {name}<span class="tag {cls}">{label}</span>', unsafe_allow_html=True)
    st.latex(m["latex"])
    st.markdown("**What the terms mean**")
    for sym, txt in m["terms"]:
        st.markdown(f"- ${sym}$: {txt}")
    st.markdown(f"**Intuition.** {m['intuition']}")
    st.markdown(f"**How it differs from the previous method.** {m['difference']}")
    prev = name

st.markdown("## How the weighted problem is solved")
st.markdown("Each weighted problem is turned into an ordinary LASSO by dividing column j of the data by its weight, and solved with a standard LASSO path "
            "(scikit-learn). The penalty λ is chosen by BIC, $n\\log(\\text{RSS}/n)+\\hat k\\log n$ with $\\hat k$ the number of non-zero coefficients, over a grid of 200 log-spaced values. "
            "Fits with more than n/2 non-zero coefficients are excluded. The ridge penalty of the first stage is also chosen by BIC, with effective degrees of freedom limited to n/2. "
            "Weights are computed on the log scale, shifted by their minimum and capped, to keep them finite. In the experiments α has a grid of 17 values between 0 and 20, κ a grid of 9 values between 0 and 10.")
st.markdown("## What the paper proves, and what it does not")
st.markdown("The only theoretical result is Theorem 1, taken from Zou (2006): under conditions on the penalty size, adaLASSO selects exactly the relevant regressors with probability going to one "
            "and estimates them as if the relevant set were known (the 'oracle properties'). The paper gives no separate theorem for WLadaLASSO, and we did not prove one for Ext1. "
            "Our experiments choose λ by BIC at finite samples and do not check the rate conditions, so they are not a test of the theorem.")
st.markdown("---")
st.markdown("**Next:** change the parameters and see the penalties.")
page_links(3, skip="pages/6_Methods.py")
