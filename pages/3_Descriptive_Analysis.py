from pathlib import Path
import streamlit as st
from PIL import Image
import base64
import pathlib
from src.analysis import render_more_analysis

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
APP_DIR = Path(__file__).resolve().parents[1]       # folder where app.py lives
DATA_PATH = APP_DIR / "data" / "mind@work" / "mental heath dataset" / "Cleaned_remote_work.csv"  # keep folder name as-is

# ---- Optional: let user pick the outcome column ----
target_col = st.sidebar.selectbox(
    "Outcome column",
    options=["Stress_Level", "Mental_Health_Condition"],
    index=0,
    help="Choose which column to treat as the outcome in the analysis."
)

# ---- Run analysis ----
if not DATA_PATH.exists():
    st.error(f"Data file not found: `{DATA_PATH}`")
    st.stop()

try:
    render_more_analysis(data_path=str(DATA_PATH), target_col=target_col)
except Exception as e:
    st.error("Couldn't run the analysis. Please check the dataset and target column.")
    st.exception(e)