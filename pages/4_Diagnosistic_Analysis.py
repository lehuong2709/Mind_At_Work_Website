# pages/4_Diagnostics.py
from pathlib import Path
from typing import List
from PIL import Image
import base64
import pathlib

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from src.analysis import _load_csv  # your cached CSV loader

st.set_page_config(layout="wide", initial_sidebar_state="expanded",
                   page_title="Diagnosistic_MIND@WORK", page_icon="🏥")

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

# ── Page meta ──────────────────────────────────────────────────────────────────
st.sidebar.caption("Explore relationships, compare groups, and try simple clustering.")
st.markdown("""
<h1 style="font-size: 48px; text-align: center; margin: 0; line-height: 1.0;">
    <span style="color: #31487A;">Workplace Insights Explorer</span>
</h1>
<h3 style="font-size: 18px; text-align: center; margin-top: 0;">
    Explore patterns to understand connections
</h3>""", unsafe_allow_html=True)


# ── Paths / config ─────────────────────────────────────────────────────────────
APP_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA = APP_DIR / "data" / "mind@work" / "mental heath dataset" / "Cleaned_remote_work.csv"
DROP_COLS_DEFAULT: List[str] = ["Employee_ID"]

# ── ONE uploader (avoid duplicate IDs) ─────────────────────────────────────────
uploaded = st.sidebar.file_uploader("Upload CSV (optional)", type=["csv"], key="diag_csv")

# ── Load data (reuses your cached helper) ──────────────────────────────────────
if uploaded is not None:
    df = pd.read_csv(uploaded)
elif DEFAULT_DATA.exists():
    df = _load_csv(str(DEFAULT_DATA), DROP_COLS_DEFAULT)
else:
    st.error("⚠️ No dataset found. Upload a CSV or place the default file.")
    st.stop()

# Keep numeric columns numeric; only fill missing in categoricals
cat_cols_all = df.select_dtypes(include="object").columns.tolist()
if cat_cols_all:
    df[cat_cols_all] = df[cat_cols_all].fillna("Unknown")

st.caption(f"Loaded dataset: **{df.shape[0]:,} rows × {df.shape[1]} columns**")
st.dataframe(df.head(), use_container_width=True)

# ── Column lists ───────────────────────────────────────────────────────────────
numeric_cols = df.select_dtypes(include="number").columns.tolist()
cat_cols = df.select_dtypes(include="object").columns.tolist()

# ── 1) Correlation heatmap ─────────────────────────────────────────────────────
st.markdown(
    "<p style='font-size:28px; color:#31487A; font-weight:500;'>How Factors Relate</p>",
    unsafe_allow_html=True)
sel_corr = st.multiselect(
    "Select numeric factors (≥ 2) to compare",
    options=numeric_cols,
    default=numeric_cols[: min(8, len(numeric_cols))],
    help="Shows how strongly selected numeric features move together."
)
if len(sel_corr) >= 2:
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(df[sel_corr].corr(), annot=True, cmap="Reds", ax=ax)
    ax.set_title("Correlation heatmap")
    st.pyplot(fig, clear_figure=True)
else:
    st.info("Pick at least two numeric features.")

# ── 2) Box plot: group vs numeric ──────────────────────────────────────────────
st.markdown(
    "<p style='font-size:28px; color:#31487A; font-weight:500;'>Compare Across Categories</p>",
    unsafe_allow_html=True)
if cat_cols and numeric_cols:
    c1, c2 = st.columns(2)
    with c1:
        x_axis = st.selectbox("Group / category", cat_cols, index=0)
    with c2:
        y_axis = st.selectbox("Numeric feature", numeric_cols, index=0)

    fig, ax = plt.subplots(figsize=(6, 4))
    sns.boxplot(data=df, x=x_axis, y=y_axis, palette="Reds", ax=ax)
    ax.set_title(f"Distribution of {y_axis} by {x_axis}")
    plt.xticks(rotation=30, ha="right")
    st.pyplot(fig, clear_figure=True)
else:
    st.info("Need at least one categorical and one numeric column.")

# ── 3) KMeans clustering ───────────────────────────────────────────────────────
st.markdown(
    "<p style='font-size:28px; color:#31487A; font-weight:500;'>Group Employees by Patterns</p>",
    unsafe_allow_html=True)
cluster_features = st.multiselect(
    "Select numeric features (≥ 2) for grouping",
    options=numeric_cols,
    default=[c for c in ["Age", "Number_of_Virtual_Meetings", "Hours_Worked_Per_Week"] if c in numeric_cols]
)
k = st.slider("Number of groups", min_value=2, max_value=6, value=3)

clusters = None
X_index = None

if len(cluster_features) >= 2:
    # keep only rows where selected features are numeric and present
    X = df[cluster_features].copy()
    X = X.replace([pd.NA, float("inf"), float("-inf")], pd.NA).dropna()
    if X.empty:
        st.warning("Selected features have no usable numeric data after cleaning.")
    else:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)

        # 2D projection just for visualization
        pca = PCA(n_components=2, random_state=42)
        X_pca = pca.fit_transform(X_scaled)
        plot_df = pd.DataFrame({"PC1": X_pca[:, 0], "PC2": X_pca[:, 1], "Group": clusters})

        fig, ax = plt.subplots(figsize=(6, 4))
        sc = ax.scatter(plot_df["PC1"], plot_df["PC2"], c=plot_df["Group"], cmap="coolwarm", alpha=0.8)
        ax.set_title("Employee groups (2D projection)")
        ax.set_xlabel("Dimension 1")
        ax.set_ylabel("Dimension 2")
        st.pyplot(fig, clear_figure=True)

        with st.expander("Show group centers (average of selected features)"):
            centers = pd.DataFrame(
                scaler.inverse_transform(kmeans.cluster_centers_),
                columns=cluster_features
            ).round(2)
            st.dataframe(centers, use_container_width=True)

        X_index = X.index

# ── 4) Group summary table ─────────────────────────────────────────────────────
st.subheader("🧮 Group Summary")
if clusters is not None and X_index is not None:
    df_clustered = df.copy()
    df_clustered["Group"] = -1
    df_clustered.loc[X_index, "Group"] = clusters
    summary = df_clustered.groupby("Group")[cluster_features].mean(numeric_only=True).round(2)
    st.dataframe(summary, use_container_width=True)
else:
    st.info("Run clustering above to see group summaries.")

# ── Notes ──────────────────────────────────────────────────────────────────────
st.markdown(
    "> **Note:** Some fields contain ‘Unknown’ or inconsistent values. "
    "They are shown here to reflect raw patterns and will be cleaned in the modeling pipeline."
)
