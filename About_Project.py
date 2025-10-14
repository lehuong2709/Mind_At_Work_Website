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
    st.caption("Mind@Work is a prototype dashboard linking work conditions with employee mental health condition.\n")


# ---- Website title ----
#Page title
st.markdown("""
<h1 style="font-size: 48px; text-align: center; color:#31487A; margin: 0; line-height: 1.0;">
    Mind@<span style="color:#8FB3E2;">Work</span>
</h1>
<h3 style="font-size: 18px; text-align: center; margin-top: 0;">
    A data website for workplace mental health
</h3>""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)



#--------------------Introduction about Project-------------------------
#-----------------------------------------------------------------------
st.markdown("""
<style>
.how-container {
    background-color:#e7f2ff;
    padding: 50px 10px;
    border-radius: 10px;
    margin-top: 20px;
}

.how-title {
    text-align: center;
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 30px;
    color: #1c1c1c;
}

.step-card {
    background-color:#e7f2ff;
    border-radius: 12px;
    padding: 25px 18px;
    text-align: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    height: 100%;
}
.step-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.12);
}
.step-icon {
    font-size: 42px;
    margin-bottom: 10px;
}
.step-title {
    font-weight: 700;
    font-size: 18px;
    margin-bottom: 10px;
    color: #2B70E0;
}
.step-text {
    font-size: 15px;
    color: #333;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h2 style="color:#31487A; font-size: 32px; font-weight: 700; margin: 1em 0 .5em 0;">
    How do we work?
</h2>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="step-card">
        <div class="step-icon">🗂️</div>
        <div class="step-title">Data</div>
        <div class="step-text">
            We gather anonymous information from professionals about their work routines, stress levels, and lifestyle habits.  
            All inputs remain confidential and are used exclusively for well-being analysis.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="step-card">
        <div class="step-icon">📊</div>
        <div class="step-title">Analyze</div>
        <div class="step-text">
            Our models use artificial intelligence to detect early signs of mental strain and identify which work conditions
            may contribute to stress or lower satisfaction. Insights are transparent and evidence-based.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="step-card">
        <div class="step-icon">💬</div>
        <div class="step-title">Recommend</div>
        <div class="step-text">
            Results are summarized into actionable suggestions — from improving sleep and workload balance 
            to enhancing social support and HR policies. The aim: healthier, more resilient workplaces.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<style>
.info-bar {
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 14px 20px;
    margin-top: 25px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    flex-wrap: wrap;
    gap: 20px;
}
.info-item {
    font-size: 15px;
    color: #333;
    display: flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
}
.info-label {
    font-weight: 600;
    color: #1c1c1c;
}
@media (max-width: 768px) {
    .info-bar { flex-direction: column; align-items: flex-start; }
}
</style>

<div class="info-bar">
  <div class="info-item"><span class="info-label">Funding:</span> Sweden’s Public Health Agency</div>
  <div class="info-item"><span class="info-label">Version:</span> Mind@Work v1.0 - Oct 19, 2025</div>
  <div class="info-item"><span class="info-label">About our Team:</span> 3 Developers · 2 Testers · 1 Project Manager</div>
</div>
""", unsafe_allow_html=True)


st.markdown("""
<style>
.notice-box {
    background-color: white;
    border-left: 5px solid #2B70E0;
    border-radius: 8px;
    padding: 18px 22px;
    margin-top: 25px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.notice-title {
    font-weight: 700;
    font-size: 17px;
    margin-bottom: 6px;
    color: #1c2a55;
}
.notice-text {
    font-size: 15px;
    line-height: 1.55;
    color: #24335a;
}
.feedback-button {
    display: inline-block;
    margin-top: 10px;
    background-color: #2B70E0;
    color: white !important;
    font-size: 14px;
    font-weight: 500;
    padding: 8px 14px;
    border-radius: 8px;
    text-decoration: none;
    transition: background-color 0.2s ease;
}
.feedback-button:hover {
    background-color: #1f58b5;
}
</style>

<div class="notice-box">
    <div class="notice-title">🔧 Early Development Phase</div>
    <div class="notice-text">
    <b>Mind@Work v1.0 (October 2025)</b> is our first public release.  
    The model is still learning - results may not yet be fully optimized for every profile.  
    We’re continuously improving accuracy and fairness as more data becomes available.  
    Thank you for your trust and collaboration in shaping a better, more reliable tool.
    </div>
    <a href="mailto:info@explorestas.pl?subject=Mind@Work%20Feedback" class="feedback-button">
        💬 Share feedback or data
    </a>
</div>
""", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)



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
st.caption ("[1] World Health Organization. (2024). Mental Health at Work. https://www.who.int/news-room/fact-sheets/detail/mental-health-at-work")

left, right = st.columns(2)
with left:
    st.markdown("#### Mental Health Conditions in workplaces")
    render_mh_prevalence_donut(
        data_path=str(REMOTE_WORK_FILE),
        condition_col="Mental_Health_Condition",
        # If you’re in the dark-blue site theme, set bg_color="#192338"
    )
    st.markdown("<br><br>", unsafe_allow_html=True)

with right: 
    st.markdown("#### How outcomes differ when mental health condition is present")
    render_consequences_mh_from_data(
        data_path=str(REMOTE_WORK_FILE),
        condition_col="Mental_Health_Condition",
        max_features=5
    )

    st.markdown("<br><br>", unsafe_allow_html=True)

# Caption explaining interpretation
st.caption(
    "About 3 out of 4 people report a mental-health problem in this sample.<br>"
    "Those with a problem tend to work a bit more hours, have slightly less experience, fewer virtual meetings, and are a little younger on average.<br> "
    "Bars show which work factors are higher or lower among those reporting mental problem."
    , unsafe_allow_html=True)


# ---- VALUE PROPOSITION ----
st.markdown("""
<h2 style="color:#31487A; font-size: 32px; font-weight: 700; margin: 1em 0 .5em 0;">
    What Mind@Work adds
</h2>
""", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
c1.markdown("**Work conditions + outcomes**  \nLinks workload, control, support, and culture with mental health.")
c2.markdown("**Artificial Intelligence and Explainability**  \nUses machine learning with explainable outputs so leaders can see *why* risks appear.")
c3.markdown("**Decision support**  \nHighlights at-risk groups and actionable levers.")
st.caption("Mind@Work is a research prototype intended for awareness and planning, **not** clinical use.")

st.markdown("<br><br>", unsafe_allow_html=True)



# ---- HOW TO USE -----------------------------------------------
#---------------------------------------------------------------
st.markdown("""
    <h2 style="color:#31487A; font-size: 32px; font-weight: 700; margin: 1em 0 .5em 0;">
        How to Use Mind@Work?
    </h2>
    """, unsafe_allow_html=True)
st.write("Mind@Work helps you explore how work conditions relate to employees’ mental well-being. Each section has a clear purpose:")
    
st.markdown("""
<style>
/* make expander headers larger and on-brand */
.streamlit-expanderHeader {
  font-size: 18px !important;
  font-weight: 700 !important;
  color: #1e3a8a !important; /* deep blue */
}
.block-container .expander-content p {
  margin: 0 0 .5rem 0;
}
</style>
""", unsafe_allow_html=True)

# ---- Four dropdowns in a neat 2×2 grid (stacks on small screens) ----
left1, right1 = st.columns(2)
left2, right2 = st.columns(2)

with left1:
    with st.expander("🩺 Mental Health Screening", expanded=False):
        st.markdown("""
        Answer simple questions about your work and lifestyle.  
        The system uses artificial intelligence to give a wellbeing result and highlight key factors.
        """)

with right1:
    with st.expander("🧠 Understand the Screening", expanded=False):
        st.markdown("""
        Learn how the artificial intelligence made its decision.  
        See which answers influenced your result and why.
        """)

with left2:
    with st.expander("📊 Overview & Trends", expanded=False):
        st.markdown("""
        Discover overall patterns in wellbeing, stress, and work habits.  
        You can filter by job type, hours, or satisfaction levels.
        """)

with right2:
    with st.expander("🔍 Deep Dive Insights", expanded=False):
        st.markdown("""
        Explore relationships — for example, how sleep or workload connect with stress or happiness.  
        Helps find what truly matters.
        """)

# ---- Tip (unchanged content) ----
st.markdown("""
<div style="
    text-align:center; margin-top: 16px; font-size: 15px; color:#374151;
    background: linear-gradient(90deg, #f8fbff 0%, #edf5ff 100%);
    padding: 12px 18px; border-radius: 10px; border: 1px solid #d9e3f5;">
💡 <b>Tip:</b> Start with <b>Overview & Trends</b>, then explore <b>Deep Dive Insights</b>,
try your own situation in <b>Mental Health Screening</b>, and finally check
<b>Understand the Screening</b> to see how the system thinks.
</div>
""", unsafe_allow_html=True)


st.markdown("<br><br>", unsafe_allow_html=True)



# ---- Footer --------------------------------------------------
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
