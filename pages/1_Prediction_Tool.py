import streamlit as st
from PIL import Image
import base64
import pathlib
from src.model_pipeline import (
    load_catboost_model, load_feature_order, load_best_threshold,
    encode_user_input, predict_proba, predict_label
)

st.set_page_config(layout="wide", initial_sidebar_state="expanded",
                   page_title="Prediction_MIND@WORK", page_icon="🏥")

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
LOGO_PATH_2 = "assert/logo2.png"  
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


# --- Sidebar/context ---
st.sidebar.caption(
    "This tool uses predictive models to forecast how different work conditions "
    "may affect employee overall mental well-being. "
    "⚠️ Results are for awareness and learning only, not for diagnosis or clinical use."
)

# --- Page title + intro ---
st.markdown("""
<h1 style="font-size: 48px; text-align: center; margin: 0; line-height: 1.0;">
    <span style="color:#31487A;">Mental Health Prediction Tool</span>
</h1>
<h3 style="font-size: 18px; text-align: center; margin-top: 0;">
    Estimate the probability of mental health risk based on work factors
</h3>""", unsafe_allow_html=True)
 

# --- Load model once ---
model = load_catboost_model()
if model is None:
    st.warning("⚠️ No model found in `models/catboost`. Please add `model.cbm` or `model.pkl`.")
    st.stop()

feature_order = load_feature_order()
tuned_default = load_best_threshold(default=0.52)

st.markdown(
    "<p style='color:#666'>Fill the fields below. The model estimates the probability of "
    "<b>mental health condition</b> based on your inputs.</p>",
    unsafe_allow_html=True,
)

# --- Form ---

with st.form("predict_form", clear_on_submit=False):
    left, right = st.columns(2, gap="large")

    with left:
        age = st.number_input(
            "Age",
            18, 80, 30, 1,
            help="Your current age in years. Used to estimate how age may influence mental health."
        )
        stress = st.selectbox(
            "Stress Level",
            ["Low", "Medium", "High"],
            help="Self-assessed level of stress."
        )
        productivity = st.selectbox(
            "Productivity Change",
            ["Decrease", "No Change", "Increase"],
            help="How your productivity changed compared to last month."
        )
        activity = st.selectbox(
            "Physical Activity",
            ["None", "Weekly", "Daily"],
            help="Frequency of physical exercise or movement during the week."
        )
        sleep = st.selectbox(
            "Sleep Quality",
            ["Poor", "Average", "Good"],
            help="Overall quality of your sleep in recent weeks."
        )

    with right:
        exp = st.slider(
            "Years of Experience",
            0, 40, 5,
            help="Total years of professional experience in your career."
        )
        hours = st.slider(
            "Hours Worked Per Week",
            10, 80, 40,
            help="Average number of working hours per week."
        )
        meetings = st.slider(
            "Virtual Meetings / week",
            0, 50, 5,
            help="Number of online meetings you typically attend each week."
        )
        isolation = st.slider(
            "Social Isolation Rating (1–5)",
            1, 5, 3,
            help="How isolated you feel socially (1 = not at all, 5 = very)."
        )
        support = st.slider(
            "Company Support for Remote Work (1–5)",
            1, 5, 3,
            help="How well your company supports remote employees (1 = poor, 5 = excellent)."
        )

    # ✅ Checkbox
    consent = st.checkbox(
        "I consent to entering my personal information and understand how it will be used."
    )

    # ✅ The *only* submit button
    submitted = st.form_submit_button("🔍 Predict Mental Health Condition")

st.markdown("### Decision Threshold")
mode = st.radio(
    "How should the threshold be chosen?",
    ["Use default threshold", "Set custom threshold"],
    index=0,
    help=(
            "This controls how strict the tool is.\n\n"
            "- Default: recommended setting.\n"
            "- Custom: move the slider yourself.\n\n"
            "Lower = more people shown 'at risk', Higher = fewer people shown 'at risk'."
        ),
    )
# --- make sure it's a clean branch ---
if mode.strip() == "Use default threshold":
    threshold = tuned_default
    st.info(f"Using default threshold: **{threshold:.2f}**")

elif mode.strip() == "Set custom threshold":
    threshold = st.slider(
        "Custom threshold (0–1)",
        min_value=0.05,
        max_value=0.95,
        value=float(tuned_default),
        step=0.01,
        help="Lower = more positives (higher sensitivity). Higher = fewer positives (higher specificity).",
        )


# --- Inference ---
if submitted:
    if not consent:
        st.error("Please read and acknowledge the consent above to enable prediction.")
        st.stop()
    else:
        raw = {
            "Age": age,
            "Years_of_Experience": exp,
            "Hours_Worked_Per_Week": hours,
            "Number_of_Virtual_Meetings": meetings,
            "Stress_Level": stress,
            "Productivity_Change": productivity,
            "Social_Isolation_Rating": isolation,
            "Company_Support_for_Remote_Work": support,
            "Physical_Activity": activity,
            "Sleep_Quality": sleep,
        }
        df = encode_user_input(raw, feature_order=feature_order)
        proba = predict_proba(model, df)
        label = predict_label(proba, threshold)

        st.session_state.input_df = df
        st.session_state.proba = proba
        st.session_state.label = label
        st.session_state.threshold = float(threshold)

        c1, c2, c3 = st.columns(3)
        c1.metric("Prediction confidence score", f"{proba:.2%}")
        c2.metric("Threshold", f"{threshold:.2f}")

            # --- Result message and recommendations ---
        if label == 1:
            st.error("⚠️ Likely to have a mental health condition.")
            st.markdown(
            f"""
            <div style="background-color:#f8f9fa; border-left: 4px solid #6c757d;
                        padding: 12px; border-radius: 4px; margin-top: 12px;">
                <b>ℹ️ How to interpret:</b><br>
                With a decision threshold of <b>{threshold:.2f}</b>, a probability of <b>{proba:.2%}</b>
                is classified as <b>{"likely to have a mental health condition." if label else "unlikely to have a mental health condition."}</b>.<br>
                Lower thresholds increase sensitivity (catch more people with mental health problem);
                higher thresholds do the opposite.
            </div>
            """,
            unsafe_allow_html=True,
        )
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("""
                ### Recommendations
                - Consider improving your sleep routine.  
                - Try stress-reduction techniques such as meditation, yoga, or deep breathing.  
                - Seek support from a mental-health professional or counselor.  
                - Remember: this tool is a **screening aid** and **not a diagnostic tool**.  
                Always consult a qualified healthcare provider for diagnosis and treatment.
            """)
            
            
        else:
            st.success("✅ Unlikely to have a mental health condition.")
            st.markdown("""
                ### Recommendations
                - Maintain your healthy habits: regular exercise, good sleep, balanced diet.  
                - Keep monitoring your wellbeing and reach out for support if you feel overwhelmed.  
                - Remember: this tool is a **screening aid** and cannot replace professional advice.
            """)


# ---- CTA ----
st.markdown("""
<h2 style="color:#31487A; font-size: 32px; font-weight: 700; margin: 1em 0 .5em 0;">
    Interested in piloting Mind@Work?
</h2>
""", unsafe_allow_html=True)
cta_col1, cta_col2 = st.columns([1, 3])
with cta_col1:
    try:
        st.link_button("Get in touch", "mailto:team@mindatwork.example?subject=Mind@Work%20pilot")
    except Exception:
        st.markdown("[👉 Get in touch](mailto:team@mindatwork.example?subject=Mind@Work%20pilot)")
with cta_col2:
    st.markdown("We’re looking for organizations to co-develop metrics, validate insights, and shape ethical use guidelines.")

st.markdown("<br><hr>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 1])
col2.markdown("""
<div style="text-align: right; font-size: 13px; color: gray;">
    © 2025 Mind@Work Project. All rights reserved. <br>
    Built by the Mind@Work project team <br>
    in collaboration with Karolinska Institutet & Stockholm University.
</div>
""", unsafe_allow_html=True)