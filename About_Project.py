from pathlib import Path
import os
import pandas as pd
import pydeck as pdk
import streamlit as st
from PIL import Image

from src.dashboard_insight import (
    render_mh_prevalence_donut,
    render_consequences_mh_from_data
)
    


############ Page Settings #############################################
st.set_page_config(layout="wide", initial_sidebar_state="expanded",
                   page_title="MIND@WORK", page_icon="🏥")

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



# ---- PATH HELPERS (use project-relative paths) ----
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data" / "mind@work"
COMPANY_FILE = DATA_DIR / "company_lists" / "partners_sweden.csv"
REMOTE_WORK_FILE = DATA_DIR / "mental_health_dataset" / "Cleaned_remote_work.csv"  # keep your folder name as-is

# ---- SIDEBAR (context) ----
import base64, pathlib
import streamlit as st

# --- Encode your logo once ---
LOGO_PATH = "assert/logo.png"   # <-- update if needed
b64 = base64.b64encode(pathlib.Path(LOGO_PATH).read_bytes()).decode()

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


with st.sidebar:
    st.caption("Mind@Work is a prototype dashboard linking work conditions with employee mental health condition.\n"
               "⚠️ Insights only, no diagnosis or clinical use.")


# ---- Website title ----
#Page title
st.markdown("""
<h1 style="font-size: 48px; text-align: center; color:#31487A; margin: 0; line-height: 1.0;">
    Mind@<span style="color:#8FB3E2;">Work</span>
</h1>
<h3 style="font-size: 18px; text-align: center; margin-top: 0;">
    A prototype dashboard for workplace mental health
</h3>""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)


col1, col2, col3 = st.columns(3)

with col1:
    with st.expander("📌 About the Project"):
        st.markdown("""
        **Mind@Work** is a cutting-edge research initiative running from **Sept 3 to Oct 22, 2025**, funded by Sweden’s Public Health Agency.
        
        - 🎯 **Objective**: Enhance workplace well-being via remote work data  
        - 📊 **Methodology**: Descriptive, predictive & prescriptive analytics  
        - 📁 **Dataset**: Synthetic mental health data (Kaggle)  
        - 🛠️ **Tech Stack**: Python, Streamlit, Scikit-learn, SHAP, Pandas  
        """)

with col2:
    with st.expander("👥 Who’s Involved"):
        st.markdown("""
        - 🧑‍🏫 Internal: Academic supervisors & mentors  
        - 🏛️ External: Public Health Agency, Insurers  
        - 👩‍💼 Team: Isha, Harish, Patricija, Karin, Le  
        - 🔄 Roles: Analysts, developers, testers, PM rotation  
        """)

with col3:
    with st.expander("🎯 Project Goals"):
        st.markdown("""
        - Analyze how work setups affect well-being  
        - Predict mental health risks early  
        - Ensure explainable AI for transparency  
        - Deliver actionable insights to stakeholders  
        - Provide HR recommendations  
        """)

col4, col5, col6 = st.columns(3)

with col4:
    with st.expander("💼 Project Scope"):
        st.markdown("""
        ✅ In Scope: Data analysis, EDA, prediction, dashboards  
        ❌ Out of Scope: Real user data, clinical diagnosis, production AI  
        """)

with col5:
    with st.expander("💸 Budget & Resources"):
        st.markdown("""
        - Budget: 154,913 SEK  
        - Funded by Public Health Agency   
        - Team: 3 devs, 2 testers, rotating PM  
        """)

with col6:
    with st.expander("📅 Timeline"):
        st.markdown("""
        | Phase                  | Dates            |  
        |------------------------|------------------|  
        | Setup & Requirements   | Sept 3 – Sept 12 |  
        | EDA & Development      | Sept 12 – Sept 21|  
        | Prototype & Testing    | Sept 21 – Sept 29|  
        | Refinement & Writing   | Oct 8 – Oct 13   |  
        | Report Delivery        | Oct 13 – Oct 22  |  
        """)

col7, col8 = st.columns(2)

with col7:
    with st.expander("⚠️ Risks & Mitigations"):
        st.markdown("""
        | Risk                    | Mitigation                      |
        |-------------------------|--------------------------------|
        | Data quality issues      | Backup datasets + preprocessing|
        | Time constraints        | Weekly reviews + buffer period |
        | Model performance       | Try multiple models + tuning   |
        | Streamlit bugs          | Early MVP + regular testing    |
        | Team workload/illness   | Role rotation + open communication |
        """)

with col8:
    with st.expander("🌟 Why This Matters"):
        st.markdown("""
        Mental health challenges affect **15% of the workforce worldwide**, leading to over **12 billion lost workdays** annually.
        Through insightful data analysis, **Mind@Work** aims to help organizations foster supportive, productive, and mentally healthy workplaces.
        """)

# ---- WHY / EVIDENCE ----
st.markdown("""
<h2 style="color:#31487A; font-size: 32px; font-weight: 700; margin: 1em 0 .5em 0;">
    Why workplace mental health matters
</h2>
""", unsafe_allow_html=True)

st.write("""
According to the World Health Organization, **depression and anxiety** cause an estimated
**12 billion lost workdays each year**, costing the global economy nearly **$1 trillion USD annually [1]**.
Our data suggests **more than 70% employee** report having mental health problems, which linked to their work environment.
""")


st.markdown("#### Mental Health Conditions in workplaces")
render_mh_prevalence_donut(
    data_path=str(REMOTE_WORK_FILE),
    condition_col="Mental_Health_Condition",
    # If you’re in the dark-blue site theme, set bg_color="#192338"
)

st.markdown("<br><br>", unsafe_allow_html=True)

st.markdown("#### How outcomes differ when mental health condition is present")
render_consequences_mh_from_data(
    data_path=str(REMOTE_WORK_FILE),
    condition_col="Mental_Health_Condition",
    max_features=5
)

st.markdown("<br><br>", unsafe_allow_html=True)

# ---- VALUE PROPOSITION ----
st.markdown("""
<h2 style="color:#31487A; font-size: 32px; font-weight: 700; margin: 1em 0 .5em 0;">
    What Mind@Work adds
</h2>
""", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
c1.markdown("**Work conditions + outcomes**  \nLinks workload, control, support, and culture with mental health.")
c2.markdown("**ML + XAI**  \nUses machine learning with explainable outputs so leaders can see *why* risks appear.")
c3.markdown("**Decision support**  \nHighlights at-risk groups and actionable levers.")
st.caption("Mind@Work is a research prototype intended for awareness and planning, **not** clinical use.")

st.markdown("<br><br>", unsafe_allow_html=True)

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
