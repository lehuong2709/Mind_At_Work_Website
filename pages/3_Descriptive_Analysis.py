from pathlib import Path
import streamlit as st
from PIL import Image
import base64
import pathlib
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from src.descriptive_analytics import plot_age_distribution, plot_stress_distribution, plot_sleep_by_work_location
from src.descriptive_analytics import experience_bar_line_satisfaction, plot_mh_heatmap, boxplot_explorer



st.set_page_config(layout="wide", initial_sidebar_state="expanded",
                   page_title="Descriptive_MIND@WORK", page_icon="🏥")

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

# ---- Sidebar context ----
st.sidebar.caption(
    "This section provides descriptive analysis with charts and summaries, "
    "highlighting patterns between work conditions and mental health."
)

# ---- Page title ----
# --- Page title + intro ---
st.markdown("""
<h1 style="font-size: 48px; text-align: center; margin: 0; line-height: 1.0;">
    <span style="color: #31487A;">Workplace Well-Being Overview</span>
</h1>
<h3 style="font-size: 18px; text-align: center; margin-top: 0;">
    Descriptive analysis of mental health and work factors
</h3>""", unsafe_allow_html=True)

# ---- Resolve data path (project-root relative) ----
ROOT_DIR = Path(__file__).resolve().parents[1]       # folder where app.py lives
DATA_PATH = ROOT_DIR / "data" / "mind@work" / "mental_health_dataset" / "Cleaned_remote_work.csv"  # keep folder name as-is
df = pd.read_csv(DATA_PATH)
st.markdown("<br><br>", unsafe_allow_html=True)

# ---- Two-column layout for next charts ----
left_col, right_col = st.columns([2, 1])   # ratio 2:1 → 2/3 vs 1/3 width

with left_col:
    # Custom title (HTML)
    st.markdown("""
    <h2 style="color:#31487A; font-size: 28px; font-weight: 700; margin: 1em 0 .5em 0;">
        Age Distribution by Gender
    </h2>
    """, unsafe_allow_html=True)

    try:
        fig = plot_age_distribution(DATA_PATH)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("""
        💡 **Insight:**  
        Most participants are between **26–55 years old**, with a relatively balanced gender distribution across age groups.  
        Younger (18–25) and older (56–65) segments are smaller but still diverse, indicating that engagement spans multiple life stages.  
        Hover over bars to explore detailed counts by gender within each age range.
        """)
    except FileNotFoundError:
        st.error(f"Data file not found at: {DATA_PATH}")
    except ValueError as e:
        st.error(str(e))

with right_col:
    st.markdown("""
    <h2 style="color:#31487A; font-size: 28px; font-weight: 700; margin: 1em 0 .5em 0;">
        Key Well-Being Indicators
    </h2>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h4 style="font-size: 18px; color:#31487A; margin: 0; line-height: 1.0;">
        Mental Health Issues
    </h4>
    <h5 style="font-size: 22px; margin-top: 0;">
        <b>3,804</b> <span style="color:#8FB3E2;">(76.1%)</span>
    </h5>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <h4 style="font-size: 18px; color:#31487A; margin: 0; line-height: 1.0;">
        Not Satisfied with Work
    </h4>
    <h5 style="font-size: 22px; margin-top: 0;">
        <b>1,677</b> <span style="color:#8FB3E2;">(33.5%)</span>
    </h5>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <h4 style="font-size: 18px; color:#31487A; margin: 0; line-height: 1.0;">
        Social Isolation
    </h4>
    <h5 style="font-size: 22px; margin-top: 0;">
        <b>1,989</b> <span style="color:#8FB3E2;">(39.8%)</span>
    </h5>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


left, right = st.columns([1, 1])
with left:
    # --- STRESS DISTRIBUTION (1/3 of width) ---
    st.markdown("""
    <h2 style="color:#31487A; font-size:28px; font-weight:700; margin-top:1em;">
        Stress Distribution in Remote workers
    </h2>
    """, unsafe_allow_html=True)

    try:
        fig_stress = plot_stress_distribution(DATA_PATH)
        st.plotly_chart(fig_stress, use_container_width=True)
        st.caption("""
        💡 **Insight:**  
        More than 70% of remote workers report experiencing stress.
        """)
    except Exception as e:
        st.error(str(e))
with right:
    st.markdown("""
    <h2 style="color:#31487A; font-size:28px; font-weight:700; margin-top:1em;">
        Sleep Quality by Work Location
    </h2>
    """, unsafe_allow_html=True)

    try:
        fig_sleep = plot_sleep_by_work_location(DATA_PATH)
        st.plotly_chart(fig_sleep, use_container_width=True)
        st.caption("""
        💡 **Insight:**  
        Sleep quality appears fairly balanced across work locations — remote, onsite, and hybrid employees report similar proportions of poor, average, and good sleep.
        """)
    except Exception as e:
        st.error(str(e))


#---- Full-width layout for next chart ----
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
        <h2 style="color:#31487A; font-size: 28px; font-weight: 700; margin: 1em 0 .5em 0;">
            Mental Health Issues by Work Hours and Virtual Meetings
        </h2>
        """, unsafe_allow_html=True)
fig_heat = plot_mh_heatmap(DATA_PATH)
st.plotly_chart(fig_heat, use_container_width=True, key="mh_heatmap")

st.caption("""
    💡 **Insight:**  
    Darker red cells indicate groups with higher prevalence of mental-health conditions.  
    Employees working longer hours and attending more virtual meetings tend to report more issues.
    """)



# ---- Full-width layout for next chart ----
st.markdown("<br><br>", unsafe_allow_html=True)
left_co, right_co = st.columns([2, 1])
with left_co:
    st.markdown("""
        <h2 style="color:#31487A; font-size: 28px; font-weight: 700; margin: 1em 0 .5em 0;">
        Years of Experience vs. Job Satisfaction
        </h2>
        """, unsafe_allow_html=True)
    # Optional dropdown for focus level
    focus_level = st.selectbox(
        "Select Satisfaction Level to Focus On:",
        ["Satisfied", "Neutral", "Unsatisfied"],
        index=0
    )
    # Create the figure
    try:
        fig_exp_sat = experience_bar_line_satisfaction(df, focus_level=focus_level)
        st.plotly_chart(fig_exp_sat, use_container_width=True, key="exp_sat_chart")
        st.caption("💡 Satisfaction levels remain relatively consistent across experience groups, ranging around 30–35%."
        "Employees with over 21 years of experience show the highest satisfaction, while mid-career (6–10 years) participants are slightly less satisfied."
        )
        st.caption("Blue bars show the number of participants per experience range, while the dark line shows the percentage of those with the selected satisfaction level.")
    except Exception as e:
        st.error(f"Error generating chart: {e}")

with right_co:
    st.markdown("""
        <h2 style="color:#31487A; font-size: 28px; font-weight: 700; margin: 1em 0 .5em 0;">
            Box Plot Explorer
        </h2>
        """, unsafe_allow_html=True)
    numeric_cols = sorted(df.select_dtypes(include="number").columns.tolist())
    value_col = st.selectbox("Select numeric feature:", numeric_cols)

# --- Optional filters ---
    with st.expander("Filters", expanded=False):
        filters = {}
        if "Work_Location" in df.columns:
            wl_opts = sorted(df["Work_Location"].dropna().unique())
            sel_wl = st.multiselect("Work Location", wl_opts, default=wl_opts)
            filters["Work_Location"] = sel_wl
        if "Sleep_Quality" in df.columns:
            sq_opts = sorted(df["Sleep_Quality"].dropna().unique())
            sel_sq = st.multiselect("Sleep Quality", sq_opts, default=sq_opts)
            filters["Sleep_Quality"] = sel_sq

# --- Show chart ---
    fig = boxplot_explorer(df, value_col=value_col, filters=filters)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Select different features from the dropdown to explore their relationship with stress levels.")
    st.caption("Boxes show the interquartile range (IQR), lines extend to 1.5×IQR, and dots are outliers.")


