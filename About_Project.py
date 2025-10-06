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

# ---- PARTNERS MAP ----
partners_df = pd.read_csv(COMPANY_FILE)

left, right = st.columns([1, 2], gap="large")
with left:
    st.markdown("""
    <h2 style="color:#31487A; font-size: 32px; font-weight: 700; margin: 1em 0 .5em 0;">
        Where we’ve collected data?
    </h2>
    """, unsafe_allow_html=True)
    city = st.selectbox("Choose a city", options=sorted(partners_df["city"].unique()), index=0)
    sel = partners_df[partners_df["city"] == city]
    st.markdown(f"**Partners in {city}:**")
    if sel.empty:
        st.caption("No partners listed yet.")
    else:
        st.markdown("\n".join(f"- {row.company}" for row in sel.itertuples()))

with right:
    view_state = pdk.ViewState(latitude=62.0, longitude=15.0, zoom=4.5, pitch=0)
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=partners_df,
        get_position='[lon, lat]',
        get_fill_color=[31, 119, 180, 200],
        get_line_color=[0, 0, 0],
        line_width_min_pixels=1,
        pickable=True,
        radius_min_pixels=6,
    )
    deck = pdk.Deck(layers=[layer], initial_view_state=view_state,
                    tooltip={"text": "{company}\n{city}"}, map_style="light")
    st.pydeck_chart(deck, use_container_width=True, height=600)

st.markdown("<br>", unsafe_allow_html=True)

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
