# src/dashboard_insight.py
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import math
import matplotlib.pyplot as plt

# Path to dataset
DATA_PATH = "data/mind@work/mental_health_dataset/Cleaned_remote_work.csv"


# --- put near your imports ---

from datetime import date

def render_context_panel():
    st.markdown(
        f"""
        <div style="font-size:13px; line-height:1.4">
        <div style="border:1px solid #ddd; border-radius:8px; padding:12px; margin-bottom:12px; background-color:#f8f9fa;">
            <h4 style="margin-top:0; margin-bottom:10px;">ℹ️ Context & References</h4>
            <ul style="padding-left:20px; margin:0;">
                <li>🌍 Based on <b>Kaggle</b> reporting on workplace mental health.</li>
                <li>📚 <b>Last updated:</b> {date.today():%b %Y}</li>
                <li>🔗 <b>Sources:</b> <a href="https://www.kaggle.com/datasets/waqi786/remote-work-and-mental-health" target="_blank">Mental health at work</a></li>
            </ul>
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )



def render_progress_tracker(partners_csv_path: str, current_country="Sweden"):
    st.markdown(
        f"""
        <div style="font-size:13px; line-height:1.4">
        <div style="border:1px solid #ddd; border-radius:8px; padding:12px; margin-bottom:12px; background-color:#f8f9fa;">
            <h4 style="margin-top:0; margin-bottom:10px;">🚀 Project Status</h4>
            <ul style="padding-left:20px; margin:0;">
                <li>📍 <b>Currently analyzing:</b> {current_country}</li>
                <li>🏢 <b>Partners onboard:</b> 20 organizations</li>
                <li>📈 <b>Next release:</b> New XAI model (feature at-risk group explanations)</li>
            </ul>
            <div style="height:8px; background:#eee; border-radius:5px; margin-top:8px;">
                <div style="width:60%; height:100%; background:#c41636; border-radius:5px;"></div>
            </div>
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_mh_prevalence_donut(
    data_path: str,
    condition_col: str = "Mental_Health_Condition",
    title_center: str = "Mental health\nproblems",
    show_breakdown: bool = True
):
    """
    Visualize prevalence of mental-health problems (Anxiety, Burnout, Depression, None)
    from Cleaned_remote_work.csv.

    Shows a donut chart (Problem vs None), and optionally a bar breakdown by type.
    """

    # --- Load data ---
    df = pd.read_csv(data_path)
    s = df[condition_col].astype(str).str.strip().str.title()  # normalize case

    # --- Define what counts as a "problem" ---
    problem_values = ["Anxiety", "Burnout", "Depression"]
    is_problem = s.isin(problem_values)

    n_problem = int(is_problem.sum())
    n_total = int(len(s)) or 1
    n_none = n_total - n_problem
    pct = round(100 * n_problem / n_total, 1)

    # --- “1 in N” text ---
    ratio = (n_total / n_problem) if n_problem else math.inf
    one_in = f"~1 in {int(round(ratio))}" if math.isfinite(ratio) else "0 in ∞"

    # --- Donut chart ---
    labels = ["Has problem", "No reported problem"]
    values = [n_problem, n_none]
    colors = ["#F68787", "#31487A"]  # coral & light blue

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.58,
        textinfo="label+percent",
        pull=[0.05, 0],
        marker=dict(colors=colors),
        sort=False,
    )])

    fig.update_layout(
        annotations=[dict(
            text=f"<b>{pct}%</b><br><span style='font-size:12px'>{title_center}</span>",
            x=0.5, y=0.5, showarrow=False
        )],
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)



# Consequences of mental-health condition (Present vs None)
import re
import pandas as pd
import streamlit as st
import plotly.express as px

def _flag_mh_present(series):
    s = series.astype(str).str.strip().str.title()
    return s.isin(["Anxiety", "Burnout", "Depression"])  # True = has condition

def render_consequences_mh_from_data(
    data_path: str,
    condition_col: str = "Mental_Health_Condition",
    max_features: int = 5,
    exclude_cols_like=("stress", "mental", "condition"),
):
    """
    Show numeric outcomes that differ most when a mental-health condition is present.
    - data_path: path to Cleaned_remote_work.csv
    - condition_col: column with values like Anxiety/Burnout/Depression/None
    - max_features: top features by absolute mean difference (Present − None)
    """

    # --- load ---
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        st.warning(f"Could not read data: {e}")
        return

    if condition_col not in df.columns:
        st.warning(f"Column '{condition_col}' not found in your data.")
        return

    df = df.copy()
    df["__mh_present__"] = _flag_mh_present(df[condition_col])

    # Need both groups
    if df["__mh_present__"].nunique() < 2:
        st.info("Need rows both with and without a mental-health condition to compare.")
        return

    # numeric features (drop the obvious drivers/IDs)
    num_cols = df.select_dtypes("number").columns.tolist()
    # exclude columns by name pattern (e.g., stress scores or IDs you don't want)
    patt = re.compile("|".join(map(re.escape, exclude_cols_like)), re.IGNORECASE) if exclude_cols_like else None
    if patt:
        num_cols = [c for c in num_cols if not patt.search(c)]

    if not num_cols:
        st.info("No numeric outcomes available to compare.")
        return

    # group means
    means = df.groupby("__mh_present__")[num_cols].mean(numeric_only=True)

    # compute Present − None differences and rank by absolute size
    if True not in means.index or False not in means.index:
        st.info("Both groups (Present and None) must be present.")
        return

    diff = (means.loc[True] - means.loc[False]).dropna()
    if diff.empty:
        st.info("No numeric outcomes to compare.")
        return

    top = (diff.reindex(diff.abs().sort_values(ascending=False).index)
               .head(max_features)
               .reset_index())
    top.columns = ["Outcome", "Present − None (mean)"]
    top["Outcome"] = top["Outcome"].apply(lambda x: re.sub(r"[_\-]+", " ", x).strip().title())

    # Plot (positive bars = higher when condition is present)
    fig = px.bar(
        top,
        x="Present − None (mean)",
        y="Outcome",
        orientation="h",
        color=("Present − None (mean)"),
        color_continuous_scale=["#8FB3E2", "#FF6B6B"],  # blue→coral
        text="Present − None (mean)",
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(
        coloraxis_showscale=False,
        xaxis_title="Difference in mean (Present − None)",
        yaxis_title="",
        margin=dict(l=10, r=10, t=10, b=10),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Caption explaining interpretation
    st.caption(
        "This chart compares employees with and without mental-health problems. Bars show which work factors are higher or lower among those reporting anxiety, burnout, or depression. "
        "Positive values mean that this factor tends to be higher among employees with mental-health difficulties, while negative values mean it’s lower."
    )