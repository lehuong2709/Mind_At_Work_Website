# src/dashboard_insight.py
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Path to dataset
DATA_PATH = "data/mind@work/mental heath dataset/Cleaned_remote_work.csv"

def render_stress_donut(
    data_path: str = DATA_PATH,
    stress_col: str = "Stress_Level",
):
    """
    Load the dataset, compute Low/Medium/High stress shares,
    and render a nice donut chart + a short caption.
    """
    df = pd.read_csv(data_path)

    # normalize values
    s = (
        df[stress_col]
        .astype(str)
        .str.strip()
        .str.capitalize()
    )

    order = ["Low", "Medium", "High"]
    colors = {"Low": "#66c2a5", "Medium": "#fc8d62", "High": "#e78ac3"}

    counts = (
        s.value_counts()
         .reindex(order)
         .fillna(0)
         .astype(int)
    )
    total = int(counts.sum()) or 1
    pct_high = round(100 * counts.get("High", 0) / total, 1)

    fig = go.Figure(data=[go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.58,
        textinfo="label+percent",
        pull=[0, 0, 0.05],  # small emphasis on High
        marker=dict(colors=[colors.get(k, "#999999") for k in counts.index]),
    )])

    fig.update_layout(
        annotations=[dict(
            text=f"<b>{pct_high}%</b><br><span style='font-size:12px'>High stress</span>",
            x=0.5, y=0.5, showarrow=False
        )],
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Centered caption with HTML
    st.markdown(
        f"""
        <p style='text-align: center; color: gray;'>
        Estimated <b>{pct_high}%</b> of employees are in the <i>High stress</i>.
        </p>
        """,
        unsafe_allow_html=True)


# Consequence of stress section
import re
import pandas as pd
import streamlit as st
import plotly.express as px

def _normalize_stress(series):
    s = (
        series.astype(str)
        .str.strip()
        .str.lower()
        .replace({"hi": "high", "med": "medium", "lo": "low"})
        .replace({"high": "High", "medium": "Medium", "low": "Low"})
    )
    # keep only the three buckets
    s = s.where(s.isin(["Low", "Medium", "High"]))
    return s

def render_consequences_from_data(
    data_path: str,
    stress_col: str = "stress_level",
    max_features: int = 5,
):
    """
    Show outcomes that differ the most between High vs Low stress in your dataset.
    - data_path: path to Cleaned_remote_work.csv
    - stress_col: column with Low/Medium/High (any casing works)
    """
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        st.warning(f"Could not read data: {e}")
        return

    if stress_col not in df.columns:
        st.warning(f"Column '{stress_col}' not found in your data.")
        return

    df = df.copy()
    df["__stress__"] = _normalize_stress(df[stress_col])

    # numeric features only; drop columns that look like stress columns
    num_cols = df.select_dtypes("number").columns.tolist()
    num_cols = [c for c in num_cols if "stress" not in c.lower()]

    # need at least Low & High groups
    if df["__stress__"].nunique() < 2 or not set(["Low", "High"]).issubset(set(df["__stress__"].dropna().unique())):
        st.info("Need at least 'Low' and 'High' stress rows to compare outcomes.")
        return

    # group stats
    means = df.groupby("__stress__")[num_cols].mean(numeric_only=True)

    # keep only columns that exist in both groups
    if "Low" not in means.index or "High" not in means.index:
        st.info("Need both Low and High groups present.")
        return

    diff = (means.loc["High"] - means.loc["Low"]).dropna().sort_values(ascending=False)

    if diff.empty:
        st.info("No numeric outcomes to compare.")
        return

    # pick top features with biggest High-Low difference (positive = worse/higher under High)
    top = diff.head(max_features).reset_index()
    top.columns = ["Outcome", "High - Low (mean)"]

    # Pretty outcome names
    top["Outcome"] = top["Outcome"].apply(lambda x: re.sub(r"[_\-]+", " ", x).strip().title())


    fig = px.bar(
        top,
        x="High - Low (mean)",
        y="Outcome",
        orientation="h",
        text="High - Low (mean)",
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(
        xaxis_title="Difference in mean (High − Low)",
        yaxis_title="",
        margin=dict(l=10, r=10, t=10, b=10),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Small caption explaining the calculation
    st.caption(
        "Employees experiencing high stress in tend to work more hours per week, are generally older, and show slightly lower work–life balance and higher social isolation compared to those with low stress."
    )


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
