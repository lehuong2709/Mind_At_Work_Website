import streamlit as st
from PIL import Image
import base64
import pathlib
import streamlit as st
import pandas as pd
import pickle
import plotly.graph_objects as go
import shap
from pathlib import Path


st.set_page_config(layout="wide", initial_sidebar_state="expanded",
                   page_title="Explanation_MIND@WORK", page_icon="🏥")

# --- CUSTOM STYLES ---
st.markdown("""
    <style>
        /* Sidebar background */
        [data-testid="stSidebar"] {
            background-color: #1E2E4F; /* dark blue */
            color: white !important;
        }

        /* Sidebar text (including captions, paragraphs, etc.) */
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] li,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] a {
            color: #ffffff !important;
        }

        /* Sidebar navigation hover and active */
        [data-testid="stSidebar"] a:hover {
            color: #ffdd00 !important; /* optional yellow hover */
        }

        /* Main page background */
        .stApp {
            background-color: #ffffff;
        }

        /* Main titles and text */
        h1, h2, h3, h4 {
            color: #002b5c;
        }
        p, li, span {
            color: #333333;
        }
    </style>
""", unsafe_allow_html=True)

# ---- tiny CSS tweak (optional) ----
st.markdown("""
<style>
.main .block-container { padding-top: 0rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar logo ---
LOGO_PATH_2 = "assert/logo2.png"   # <-- update if needed
b64 = base64.b64encode(pathlib.Path(LOGO_PATH_2).read_bytes()).decode()
# --- Inject logo ABOVE the auto-generated pages navigation ---
st.markdown(f"""
<style>
[data-testid="stSidebar"] {{
  position: relative;
  background-color: #1E2E4F;
}}

/* Logo at top, closer to navigation */
[data-testid="stSidebar"]::before {{
  content: "";
  display: block;
  height: 130px;                  /* controls total space occupied */
  margin-top: 5px;                /* space from top edge */
  margin-bottom: -80px;           /* reduce space before nav */
  background: url("data:image/png;base64,{b64}") center / 125px no-repeat;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,.3));
  opacity: 0.95;
}}
</style>
""", unsafe_allow_html=True)

#Page title
st.markdown("""
<h1 style="font-size: 48px; text-align: center; color:#31487A; margin: 0; line-height: 1.0;">
    Understand Mind@Work Prediction
</h1>
<h3 style="font-size: 18px; text-align: center; margin-top: 0;">
    An explanation of how our model predicts mental health conditions
</h3>""", unsafe_allow_html=True)


st.markdown("<br><br>", unsafe_allow_html=True)
# 👉 get your own loader
from src.model_pipeline import load_catboost_model

# ------------------ Load model & data ------------------

@st.cache_resource
def get_model():
    # returns an already-loaded CatBoost model (object), not a path
    return load_catboost_model()

@st.cache_data
def load_data():
    data_path = Path(__file__).parent.parent / "data/mind@work/mental_health_dataset/Cleaned_remote_work.csv"
    return pd.read_csv(data_path)

model = get_model()
df = load_data()

# ------------------ SHAP helpers ------------------

@st.cache_resource
def get_explainer(_model):
    # TreeExplainer works well for CatBoost
    return shap.TreeExplainer(_model)

def extract_shap_values(explainer, X):
    """
    Returns (values, base_value) for the positive class if it's a classifier,
    otherwise the single output.
    """
    sv = explainer.shap_values(X)
    base = explainer.expected_value

    # Some SHAP versions return list [class0, class1] for binary classification
    if isinstance(sv, list):
        # choose positive class (index 1)
        values = sv[1]
        base_val = base[1] if isinstance(base, (list, tuple)) else base
    else:
        values = sv
        base_val = base
    return values, base_val

# ------------------ Use the user input from previous page ------------------

if "input_df" in st.session_state:
    input_df = st.session_state.input_df  # 1-row DataFrame (already encoded/ordered)

    # If you prefer a fixed order, use input_df.columns to stay aligned with the model
    feature_names = list(input_df.columns)

    explainer = get_explainer(model)
    shap_values, base_val = extract_shap_values(explainer, input_df)

    # Ensure we have a 1D vector of contributions for the single row
    vals = shap_values[0]

    # -------- Plotly "waterfall-like" stacked bars --------
    st.markdown("""
    <h2 style="color:#31487A; font-size: 32px; font-weight: 700; margin: 1em 0 .5em 0;">
        Your interactive SHAP Waterfall Plot
    </h2>
    """, unsafe_allow_html=True)

    light_red = "#FF7F7F"
    light_blue = "#7FBFFF"
    colors = [light_red if v > 0 else light_blue for v in vals]

    # cumulative bases for stacked bars
    cum = [base_val]
    for v in vals[:-1]:
        cum.append(cum[-1] + v)

    bars = []
    row_vals = input_df.iloc[0].values
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
                    f"SHAP impact: {vals[i]:.4f}<br>"
                    "<extra></extra>"
                ),
            )
        )

    fig = go.Figure(data=bars)
    fig.update_layout(
        barmode="stack",
        title=f"Prediction Base Value: {base_val:.4f}",
        xaxis_title="Model output value",
        yaxis=dict(autorange="reversed"),
        height=420,
        margin=dict(l=120, r=40, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div style="font-size:15px; color:#555; line-height:1.6;">
    <h5 style="color:#31487A;">💡 How to understand the SHAP chart?</h5>
    This diagram shows <b>which factors most influenced your stress prediction.</b>
    <ul>
    <li><b style="color:#cc4b4b;">Red bars</b> show factors that <b>increased</b> your predicted stress level.</li>
    <li><b style="color:#4b86cc;">Blue bars</b> show factors that <b>helped reduce</b> it.</li>
    <li>The <b>longer</b> the bar, the <b>stronger</b> the impact of that factor.</li>
    <li>The chart starts from the model’s <b>average mental health condition</b> and adds or subtracts effects from your answers.</li>
    </ul>

    <p>👉 Think of this as a <b>balance</b>, some aspects of your work and lifestyle raise your stress score, others protect you from it.<br>
    Together, they explain <i>why</i> the model gave this result for you.</p>

    </div>
    """, unsafe_allow_html=True)


    # -------- Global feature importance from CatBoost --------
    st.markdown("""
    <h2 style="color:#31487A; font-size: 32px; font-weight: 700; margin: 1em 0 .5em 0;">
        Feature Importance
    </h2>
    """, unsafe_allow_html=True)
    try:
        importances = model.get_feature_importance()  # length == n_features
        fig2 = go.Figure(
            go.Bar(x=importances, y=feature_names, orientation="h")
        )
        fig2.update_layout(
            title="Global Feature Importance",
            xaxis_title="Importance Score",
            yaxis=dict(autorange="reversed"),
            height=400,
        )
        st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.info(f"Feature importance unavailable: {e}")

    st.markdown("""
    <div style="font-size:15px; color:#555; line-height:1.6;">
    <h5 style="color:#31487A;">💡 How to read Feature Importance chart?</h5>
    This chart shows **which factors matter most overall** for the model when predicting your mental health condition.
    <ul>
    <li>Each bar represents a factor used by the model (for example: <i>sleep quality</i>, <i>work hours</i>, or <i>social isolation</i>).</li>
    <li>The <b>longer</b> the bar, the <b>more influence</b> that factor usually has on predictions.</li>
    <li>This is calculated using the model's built-in your prediction model.</li>
    </ul>

    <p>👉 Use this to see which factors are <b>most important overall</b> in explaining mental health condition in the Mind@Work model.</p>

    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("Please fill the form in the Predictive Analytics page first.")

