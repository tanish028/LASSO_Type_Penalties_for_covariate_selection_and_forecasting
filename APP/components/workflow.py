"""Animated, clickable workflow diagram (self-contained HTML/SVG/JS rendered with st.components.v1.html)."""
import json
import streamlit as st
from components.theme import recolor, current
import streamlit.components.v1 as components

STEPS = [
    dict(id="data", t="Data", ic="📈", sub="y and 10 predictors",
         d="Simulated: one series <b>y</b> and ten AR(1) predictors <b>x₁…x₁₀</b>, only six of them (plus y's own past) matter. Empirical: Goyal-Welch equity data, FRED-MD macro data.",
         f="y<sub>t</sub> = 0.8·y<sub>t−1</sub> + 0.6x<sub>1,t−1</sub> + 0.3x<sub>1,t−2</sub> − 0.5x<sub>2,t−1</sub> − … + ε<sub>t</sub>",
         k="10 of the 11·L candidate regressors are truly relevant."),
    dict(id="lags", t="Lag matrix", ic="🧱", sub="11·L regressors",
         d="Every series enters with lags 1…L. With 11 series and L = 20 that is <b>220 regressors</b>, more than the 50 observations in a small sample.",
         f="X = [ y<sub>t−1</sub>…y<sub>t−L</sub>, x<sub>1,t−1</sub>…x<sub>1,t−L</sub>, … ]",
         k="OLS cannot be computed when regressors outnumber observations."),
    dict(id="std", t="Standardise", ic="⚖️", sub="mean 0, sd 1",
         d="Columns are standardised and y is centred, so one penalty λ is comparable across regressors.",
         f="X̃<sub>j</sub> = (X<sub>j</sub> − mean) / sd,  ỹ = y − mean(y)", k="Coefficients are mapped back to the original scale for forecasting."),
    dict(id="ridge", t="Ridge stage", ic="🏔️", sub="size of effects",
         d="A ridge regression, with its own penalty chosen by BIC, gives a rough size <b>|b<sup>ridge</sup><sub>j</sub>|</b> for every regressor. It is used only to build the weights.",
         f="b<sup>ridge</sup> = argmin ‖ỹ − X̃b‖² + r‖b‖²   (r by BIC, df ≤ n/2)", k="Small ridge coefficient → the regressor will be penalised more."),
    dict(id="weights", t="Penalty weights", ic="🎚️", sub="methods differ",
         d="This is where the four methods differ. Each regressor j gets a weight w<sub>j</sub>; a larger weight makes it harder to be selected.",
         f="log w<sub>j</sub> = γ·(−log|b<sup>ridge</sup><sub>j</sub>|) + <b>extra<sub>j</sub></b>", k="γ (gamma) is the strength of the adaptive weights. Pick a method with the chips above to see its extra term."),
    dict(id="path", t="Weighted LASSO", ic="🛤️", sub="path over λ",
         d="For 60-200 values of λ the weighted LASSO is solved (by rescaling the columns and running coordinate descent). Large λ ⇒ few variables, small λ ⇒ many.",
         f="min<sub>b</sub> (1/2n)‖ỹ − X̃b‖² + λ·Σ w<sub>j</sub>|b<sub>j</sub>|", k="Solved as an ordinary LASSO on X̃<sub>j</sub>/w<sub>j</sub>."),
    dict(id="bic", t="BIC choice", ic="🎯", sub="λ (and α, κ, γ)",
         d="BIC picks the point on the path (and the tuning parameters α, κ or γ). BIC, not AIC, as in the paper. Fits with more than n/2 non-zero coefficients are not allowed.",
         f="BIC = n·ln(RSS/n) + k·ln(n)", k="k = number of non-zero coefficients."),
    dict(id="fc", t="Rolling forecast", ic="🔭", sub="expanding window",
         d="One-step-ahead forecasts using only data before each forecast date; the model is re-estimated every 5 forecasts (Monte Carlo) or every period (empirical studies).",
         f="ŷ<sub>t</sub> = intercept + Σ b̂<sub>j</sub>·X<sub>j,t</sub>", k="No look-ahead: a unit test checks this."),
    dict(id="eval", t="Evaluate", ic="🏁", sub="MSFE · R²OS · DM test",
         d="Monte Carlo: mean squared forecast error and variable-selection scores. Empirical: out-of-sample R² against a benchmark, and the modified Diebold-Mariano test.",
         f="R²<sub>OS</sub> = 1 − Σ(y−ŷ)² / Σ(y−ȳ<sub>benchmark</sub>)²", k="Positive R²OS = beats the benchmark (historical mean, or AR(BIC))."),
]
METHOD_EXTRA = {
    "LASSO": ("w<sub>j</sub> = 1 for every regressor", "No weights: one price for all. Everything below is the same as for the other methods.", "#9AA79F"),
    "adaLASSO": ("extra<sub>j</sub> = 0", "Weights come only from the ridge stage: weak ridge effects are charged more.", "#5FA8D3"),
    "WLadaLASSO": ("extra<sub>j</sub> = α·ℓ<sub>j</sub>", "Adds a factor e<sup>αℓ</sup> that grows with the lag ℓ: distant lags are charged more. α (alpha) = 0 gives adaLASSO.", "#F2A93B"),
    "Ext1": ("extra<sub>j</sub> = κ·π<sub>ℓ</sub>,  π<sub>ℓ</sub> = log m₁ − log m<sub>ℓ</sub>", "Our extension: the lag penalty comes from a decreasing (isotonic) fit m<sub>ℓ</sub> of the mean |ridge coefficient| by lag. κ (kappa) = 0 gives adaLASSO.", "#B8DC6B"),
}


def render(height=640):
    payload = json.dumps(dict(steps=STEPS, methods=METHOD_EXTRA))
    html = """
<div id="wf"></div>
<style>
 body{margin:0;background:transparent;font-family:Inter,'Segoe UI',Helvetica,Arial,sans-serif;color:#EAF1E8}
 #chips{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 6px 4px;align-items:center}
 .chip{cursor:pointer;border:1px solid #2F4A3B;border-radius:999px;padding:4px 12px;font-size:12.5px;color:#C3D2C4;background:#12211A;transition:all .15s}
 .chip.on{color:#0C1712;font-weight:600}
 #play{margin-left:auto;cursor:pointer;border:1px solid #2F4A3B;border-radius:8px;padding:4px 12px;font-size:12.5px;color:#A9E3C4;background:#12211A}
 #play:hover{border-color:#4CC38A}
 svg{width:100%;height:auto;display:block}
 .edge{stroke:#2F4A3B;stroke-width:2.2;fill:none}
 .flow{stroke:#4CC38A;stroke-width:2.4;fill:none;stroke-dasharray:6 14;animation:dash 1.1s linear infinite;opacity:.9}
 @keyframes dash{to{stroke-dashoffset:-20}}
 .node{cursor:pointer}
 .node rect{fill:#12211A;stroke:#2F4A3B;stroke-width:1.5;rx:14;transition:all .2s}
 .node:hover rect{stroke:#4CC38A;fill:#17291F}
 .node.act rect{stroke:var(--c);stroke-width:2.4;fill:#193126;filter:drop-shadow(0 0 10px var(--c))}
 .node.done rect{stroke:#B8DC6B}
 .node text{fill:#EAF1E8;text-anchor:middle;pointer-events:none}
 .ic{font-size:22px}.tt{font-size:13px;font-weight:600}.ss{font-size:10.5px;fill:#93A89A!important}
 .num{font-size:10px;fill:#93A89A!important}
 #panel{margin:10px 4px 0;border:1px solid #26382E;border-radius:14px;padding:12px 16px;background:linear-gradient(160deg,#14261D,#0F1E17);min-height:128px}
 #panel h3{margin:0 0 4px;font-size:16px;font-family:'Source Serif 4',Georgia,serif}
 #panel p{margin:4px 0;font-size:13.5px;line-height:1.5;color:#C3D2C4}
 #formula{font-family:'Cambria Math','Times New Roman',serif;font-size:16px;color:#A9E3C4;background:rgba(76,195,138,.07);border-left:3px solid var(--c);padding:6px 10px;margin:6px 0}
 .key{font-size:12.5px;color:#93A89A}
</style>
<script>
const P=__PAYLOAD__; const S=P.steps, M=P.methods; let cur=0, method="WLadaLASSO", timer=null;
const W=1100,H=330,pos=[];
for(let i=0;i<S.length;i++){const row=i<5?0:1; const col=row==0?i:i-5; const x=row==0?70+col*240:170+col*240; pos.push([x,row==0?55:225]);}
function build(){
 let h='<div id="chips">'+Object.keys(M).map(k=>`<span class="chip ${k==method?'on':''}" data-m="${k}" style="${k==method?'background:'+M[k][2]:''}">${k}</span>`).join('')+'<span style="font-size:12px;color:#93A89A;margin-left:6px">choose a method</span><span id="play">▶ play walkthrough</span></div>';
 h+=`<svg viewBox="0 0 ${W} ${H}">`;
 for(let i=0;i<S.length-1;i++){const [x1,y1]=pos[i],[x2,y2]=pos[i+1];
  let d; if(y1==y2){d=`M${x1+62},${y1+22} L${x2-62},${y2+22}`;} else {const ym=(y1+74+y2-30)/2; d=`M${x1},${y1+74} L${x1},${ym} L${x2},${ym} L${x2},${y2-30}`;}
  h+=`<path class="edge" d="${d}"/>`; if(i<cur) h+=`<path class="flow" d="${d}"/>`;}
 for(let i=0;i<S.length;i++){const [x,y]=pos[i], s=S[i], cl=i==cur?'act':(i<cur?'done':'');
  const col=(i==4)?M[method][2]:'#4CC38A';
  h+=`<g class="node ${cl}" data-i="${i}" style="--c:${col}"><rect x="${x-62}" y="${y-30}" width="124" height="104"/><text class="num" x="${x}" y="${y-15}">STEP ${i+1}</text><text class="ic" x="${x}" y="${y+10}">${s.ic}</text><text class="tt" x="${x}" y="${y+33}">${s.t}</text><text class="ss" x="${x}" y="${y+49}">${s.sub}</text></g>`;}
 h+='</svg><div id="panel"></div>';
 document.getElementById('wf').innerHTML=h; panel(); bind();}
function panel(){const s=S[cur]; const col=(cur==4)?M[method][2]:'#4CC38A'; let f=s.f, d=s.d, k=s.k;
 if(s.id=='weights'){f='log w<sub>j</sub> = γ·(−log|b<sup>ridge</sup><sub>j</sub>|) + '+(method=='LASSO'?'—':M[method][0].replace(/^[^=]*=/,''));
   if(method=='LASSO') f=M[method][0]; d='This is where the four methods differ. '+M[method][1]; k='Selected method: <b style="color:'+col+'">'+method+'</b>. Click another chip above to compare.';}
 document.getElementById('panel').innerHTML=`<h3 style="color:${col}">${s.ic} Step ${cur+1}: ${s.t}</h3><p>${d}</p><div id="formula" style="--c:${col}">${f}</div><p class="key">${k}</p>`;}
function bind(){document.querySelectorAll('.node').forEach(n=>n.onclick=()=>{cur=+n.dataset.i;stop();build();});
 document.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{method=c.dataset.m;cur=4;stop();build();});
 document.getElementById('play').onclick=()=>{if(timer){stop();return}cur=0;build();timer=setInterval(()=>{cur=(cur+1)%S.length;build();document.getElementById('play').textContent='■ stop';},2600);document.getElementById('play').textContent='■ stop';};}
function stop(){if(timer){clearInterval(timer);timer=null}}
build();
</script>
""".replace("__PAYLOAD__", payload)
    if current() == "Ocean":                        # swap the two method colours that differ between themes, then the rest
        html = html.replace("#5FA8D3", "@@A").replace("#F2A93B", "#4FA3F7").replace("@@A", "#E9A93B")
        html = recolor(html)
    if hasattr(st, "iframe"):                       # newer Streamlit: components.html is deprecated
        st.iframe(html, height=height)
    else:
        components.html(html, height=height, scrolling=False)
