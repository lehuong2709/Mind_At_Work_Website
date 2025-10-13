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
 

# --- Load model once ----------
#-------------------------------
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


# --- Form CSS for primary button ---
#-----------------------------------
# This is a more specific selector to override Streamlit's default button styles
st.markdown("""
<style>
/* Stronger selector for Streamlit forms */
div.stButton > button[kind="primary"] {
    background-color: #2563EB;          /* soft blue */
    color: white;
    font-weight: 500;
    border: 1px solid #1E40AF;
    border-radius: 8px;
    padding: 0.45em 1.4em;
    font-size: 15px;
    transition: all 0.25s ease;
    box-shadow: 0 2px 6px rgba(37, 99, 235, 0.15);
}
div.stButton > button[kind="primary"]:hover {
    background-color: #1E40AF;
    border-color: #1E3A8A;
    box-shadow: 0 4px 10px rgba(30, 58, 138, 0.25);
    transform: translateY(-1px);
}
div.stButton > button[kind="primary"]:active {
    background-color: #1E3A8A;
    transform: translateY(0);
    box-shadow: 0 2px 6px rgba(30, 58, 138, 0.2);
}
</style>
""", unsafe_allow_html=True)


# --- Form ---
st.markdown("""
<style>
/* ---- Universal style for Submit button ---- */
div.stButton > button,
.stForm button {
    background-color: #31487A !important;      /* your brand deep blue */
    color: #FFFFFF !important;                 /* white text */
    font-weight: 600 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6em 1.6em !important;
    font-size: 15px !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 3px 8px rgba(49,72,122,0.25);
    transition: all 0.25s ease-in-out;
}

/* 🔥 Force all inner text elements to white (covers span, div, p) */
div.stButton > button * ,
.stForm button * {
    color: #FFFFFF !important;
}

/* ---- Hover + Active Effects ---- */
div.stButton > button:hover,
.stForm button:hover {
    background-color: #233464 !important;
    box-shadow: 0 5px 12px rgba(35,52,100,0.35);
    transform: translateY(-1px);
}
div.stButton > button:active,
.stForm button:active {
    background-color: #1c2b58 !important;
    transform: translateY(0);
    box-shadow: 0 3px 6px rgba(28,43,88,0.3);
}
</style>
""", unsafe_allow_html=True)


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

    # ✅ The submit button
    submitted = st.form_submit_button("Submit for Screening", type="primary")

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
    # --- consent gate ---
    if not consent:
        st.error("Please read and acknowledge the consent above to enable prediction.")
        st.stop()

    # --- build raw inputs exactly as your model expects ---
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

    # --- preprocess + predict ---
    df_one = encode_user_input(raw, feature_order=feature_order)   # your function
    proba  = predict_proba(model, df_one)                          # float in [0,1]
    label  = predict_label(proba, threshold)                       # 0/1

    # --- persist for the next page ---
    st.session_state.has_screening = True
    st.session_state.input_raw     = raw            # nice for display
    st.session_state.input_df      = df_one         # for SHAP/explanations
    st.session_state.proba         = float(proba)
    st.session_state.label         = int(label)
    st.session_state.threshold     = float(threshold)

    # --- quick metrics ---
    c1, c2, _ = st.columns(3)
    c1.metric("Prediction confidence score", f"{proba:.2%}")
    c2.metric("Threshold", f"{threshold:.2f}")

    # --- interpretation + recommendations ---
    st.markdown(
        f"""
        <div style="background-color:#f8f9fa; border-left: 4px solid #6c757d;
                    padding: 12px; border-radius: 6px; margin: 12px 0;">
            <b>ℹ️ How to interpret:</b><br>
            With a decision threshold of <b>{threshold:.2f}</b>, a probability of <b>{proba:.2%}</b>
            is classified as <b>{'likely to have a mental health condition' if label == 1 else 'unlikely to have a mental health condition'}.</b><br>
            Lower thresholds increase sensitivity (catch more true positives); higher thresholds do the opposite.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if label == 1:
        st.error("⚠️ Likely to have a mental health condition.")
        st.markdown("""
        ### Recommendations
        - Consider improving your sleep routine.
        - Try stress-reduction techniques such as meditation, yoga, or deep breathing.
        - Seek support from a mental-health professional or counselor.
        - Remember: this tool is a **screening aid**, not a diagnostic tool.
        """)
    else:
        st.success("✅ Unlikely to have a mental health condition.")
        st.markdown("""
        ### Recommendations
        - Maintain your healthy habits: regular exercise, good sleep, balanced diet.
        - Keep monitoring your wellbeing and reach out for support if you feel overwhelmed.
        - Remember: this tool is a **screening aid** and cannot replace professional advice.
        """)

    # --- Next button (manual navigation to explanation page) ---
    # divider + short lead text
    st.markdown("<hr style='margin:16px 0 8px 0;'>", unsafe_allow_html=True)
    st.markdown("If you'd like to understand how your result was made, click below.")


    # 2) Wrap + render the page link (no emoji icon)
    # ✅ Scoped highlight styling for this one link
    st.markdown("""
    <style>
    #next-pill a[data-testid="stPageLink"]{
    display:inline-block;
    background:#31487A;               /* brand blue */
    color:#FFFFFF !important;          /* white text */
    padding:8px 14px;
    border-radius:12px;                /* pill shape */
    font-weight:600;
    font-size:15px;
    text-decoration:none !important;
    transition:background .2s ease, transform .2s ease;
    line-height:1.2;
    }
    #next-pill a[data-testid="stPageLink"]:hover{
    background:#233464;                /* slightly darker on hover */
    transform:translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div id="next-pill">', unsafe_allow_html=True)
    st.page_link(
        "pages/2_Understand_the_Screening.py",
        label="Next – Understand the Screening",
        use_container_width=False,
    )
    st.markdown('</div>', unsafe_allow_html=True)  
    





# ---- CTA  Footer ----
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)

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



