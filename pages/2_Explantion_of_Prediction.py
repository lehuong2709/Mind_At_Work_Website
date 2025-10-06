# pages/2_Explantion_of_Prediction.py
import base64
import math
import pathlib
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from catboost import Pool

# ----------------------------------------
# Page config & styles
# ----------------------------------------
st.set_page_config(layout="wide", initial_sidebar_state="expanded",
                   page_title="Explanation_MIND@WORK", page_icon="🏥")

st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #1E2E4F; color: white !important; }
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] li,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] a { color: #ffffff !important; }
        [data-testid="stSidebar"] a:hover { color: #ffdd00 !important; }
        .stApp { background-color: #ffffff; }
        h1, h2, h3, h4 { color: #002b5c; }
        p, li, span { color: #333333; }
        .main .block-container { padding-top: 0rem; padding-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------
# Sidebar logo (safe if file missing)
# ----------------------------------------
LOGO_PATH_2 = "assert/logo2.png"
try:
    b64 = base64.b64encode(pathlib.Path(LOGO_PATH_2).read_bytes()).decode()
    st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{
      position: relative;
      background-color: #1E2E4F;
    }}
    [data-testid="stSidebar"]::before {{
      content: "";
      display: block;
      height: 130px;
      margin-top: 5px;
      margin-bottom: -80px;
      background: url("data:image/png;base64,{b64}") center / 125px no-repeat;
      filter: drop-shadow(0 2px 4px rgba(0,0,0,.3));
      opacity: 0.95;
    }}
    </style>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ----------------------------------------
# Title
# ----------------------------------------
st.markdown("""
<h1 style="font-size: 48px; text-align: center; color:#31487A; margin: 0; line-height: 1.0;">
    Understand Mind@Work Prediction
</h1>
<h3 style="font-size: 18px; text-align: center; margin-top: 0;">
    An explanation of how our model predicts mental health conditions
</h3>""", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)

# ----------------------------------------
# Load model
# ----------------------------------------
from src.model_pipeline import load_catboost_model  # noqa: E402

@st.cache_resource
def get_model():
    return load_catboost_model()

model = get_model()

# ----------------------------------------
# Local explanation via CatBoost SHAP
# ----------------------------------------
def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))

def explain_single_with_catboost(cb_model, X_one_row_df: pd.DataFrame):
    """
    Local explanation for THIS user's input using CatBoost's built-in SHAP.
    Returns per-feature contributions and baseline on the model's raw (log-odds) scale.
    """
    assert len(X_one_row_df) == 1, "Pass a single-row DataFrame"
    pool = Pool(X_one_row_df)
    shap_mat = cb_model.get_feature_importance(pool, type="ShapValues")  # (1, n_features+1)
    contribs = shap_mat[0, :-1]
    base_raw = float(shap_mat[0, -1])
    pred_raw = base_raw + float(contribs.sum())
    return {
        "contribs": contribs,
        "base_raw": base_raw,
        "pred_raw": pred_raw,
        "base_prob": _sigmoid(base_raw),
        "pred_prob": _sigmoid(pred_raw),
    }

# ----------------------------------------
# Page body
# ----------------------------------------
if "input_df" in st.session_state:
    # Single-row DataFrame (already encoded/ordered on the Predict page)
    input_df: pd.DataFrame = st.session_state.input_df
    feature_names = list(input_df.columns)

    # Compute per-user explanation
    expn = explain_single_with_catboost(model, input_df)
    vals = expn["contribs"]
    base_raw = expn["base_raw"]
    pred_raw = expn["pred_raw"]
    base_prob = expn["base_prob"]
    pred_prob = expn["pred_prob"]

    # -------- Waterfall (stacked bars on raw model scale) --------
    st.markdown("""
    <h2 style="color:#31487A; font-size: 32px; font-weight: 700; margin: 1em 0 .5em 0;">
        Your interactive SHAP Waterfall Plot
    </h2>
    """, unsafe_allow_html=True)

    light_red = "#FF7F7F"
    light_blue = "#7FBFFF"
    colors = [light_red if v > 0 else light_blue for v in vals]

    # cumulative base positions for stacked bars (raw scale)
    cum = [base_raw]
    for v in vals[:-1]:
        cum.append(cum[-1] + v)

    row_vals = input_df.iloc[0].values
    bars = []
    for i, feat in enumerate(feature_names):
        bars.append(
            go.Bar(
                name=feat,
                x=[vals[i]],
                y=[feat],
                orientation="h",
                base=cum[i],
                marker=dict(color=colors[i]),
                hovertemplate=(
                    f"<b>{feat}</b><br>"
                    f"Value: {row_vals[i]}<br>"
                    f"Impact (model scale): {vals[i]:.4f}<br>"
                    "<extra></extra>"
                ),
            )
        )

    fig = go.Figure(data=bars)
    fig.update_layout(
    barmode="stack",
    title="Why the model predicted this way",
    xaxis_title="Model output (model scale)",
        yaxis=dict(autorange="reversed"),
        height=420,
        margin=dict(l=120, r=40, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Plain-language explainer ---
    st.markdown("""
    <div style="font-size:15px; color:#555; line-height:1.6;">
      <h5 style="color:#31487A;">💡 How to understand the SHAP chart?</h5>
      This diagram shows <b>which factors most influenced your stress prediction.</b>
      <ul>
        <li><b style="color:#cc4b4b;">Red bars</b> increased your predicted stress.</li>
        <li><b style="color:#4b86cc;">Blue bars</b> helped reduce it.</li>
        <li>The <b>longer</b> the bar, the <b>stronger</b> the effect.</li>
        <li>The chart starts from the model’s <b>average prediction</b> and adds or subtracts effects from your answers.</li>
      </ul>
      <p>👉 Think of this as a <b>balance</b>, some aspects of your work and lifestyle raise your score, others protect you from it. Together, they explain <i>why</i> the model gave this result for you.</p>
    </div>
    """, unsafe_allow_html=True)

    # -------- Global feature importance --------
    st.markdown("""
    <h2 style="color:#31487A; font-size: 32px; font-weight: 700; margin: 1em 0 .5em 0;">
        Feature Importance
    </h2>
    """, unsafe_allow_html=True)
    try:
        importances = model.get_feature_importance()  # length == n_features
        y_labels = getattr(model, "feature_names_", None) or feature_names
        if len(importances) != len(y_labels):
            y_labels = [f"f{i}" for i in range(len(importances))]

        fig2 = go.Figure(go.Bar(x=importances, y=y_labels, orientation="h"))
        fig2.update_layout(
            title="Global Feature Importance",
            xaxis_title="Importance Score",
            yaxis=dict(autorange="reversed"),
            height=400,
            margin=dict(l=120, r=40, t=40, b=40),
        )
        st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.info(f"Feature importance unavailable: {e}")

    st.markdown("""
    <div style="font-size:15px; color:#555; line-height:1.6;">
      <h5 style="color:#31487A;">💡 How to read the Feature Importance chart?</h5>
      This chart shows <b>which factors matter most overall</b> across many people (a global view).
      <ul>
        <li>Each bar is a factor used by the model.</li>
        <li>The <b>longer</b> the bar, the <b>more influence</b> it usually has on predictions.</li>
        <li>This summarizes general patterns; it is <b>not</b> specific to one person.</li>
      </ul>
      <p>👉 Use this to see which factors are <b>most important overall</b> in the Mind@Work model.</p>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("Please fill the form in the Predictive Analytics page first.")
