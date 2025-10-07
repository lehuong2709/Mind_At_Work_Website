# src/plot_age_distribution.py
from pathlib import Path
import pandas as pd
import plotly.express as px

def plot_age_distribution(data_path: Path):
    """
    Returns an interactive Plotly figure of Age Distribution by Gender.
    Hover to see counts, click to select (optional with streamlit-plotly-events).
    """
    # ---- Load data ----
    df = pd.read_csv(data_path)

    # ---- Prepare bins ----
    bins = [18, 25, 35, 45, 55, 65]
    labels = ['18–25', '26–35', '36–45', '46–55', '56–65']
    df['Age Group'] = pd.cut(df['Age'], bins=bins, labels=labels, include_lowest=True)

    # ---- Aggregate ----
    counts = (
        df.groupby(['Age Group', 'Gender'], observed=True)
          .size()
          .reset_index(name='Count')
          .sort_values(by='Age Group')
    )

    # ---- Build Plotly chart ----
    fig = px.bar(
        counts,
        x="Age Group", y="Count", color="Gender",
        barmode="group", template="plotly_white",
        color_discrete_sequence=["#c9ddff", "#7fb3ff", "#3a86ff", "#1f4db3"]
    )

    fig.update_traces(
        marker_line_color="white", marker_line_width=1.6, opacity=0.92,
        hovertemplate="<b>%{x}</b>Count: <b>%{y}</b><extra></extra>"
    )
    fig.update_layout(
        bargap=0.18,
        hovermode="x unified",
        yaxis=dict(title="Number of Participants", gridcolor="rgba(0,0,0,0.08)"),
        xaxis_title="Age Group",
    )

    return fig



#-------Stress distribution function-------------------

def plot_stress_distribution(data_or_path):
    """
    Returns an interactive pie chart showing distribution of mental health condition
    (e.g., stress vs. no stress) among remote workers only.

    Parameters
    ----------
    data_or_path : str | Path | pd.DataFrame
        DataFrame or path to CSV with columns:
        - Work_Location
        - Mental_Health_Condition
    """
    # ---- Load data ----
    if isinstance(data_or_path, (str, Path)):
        df = pd.read_csv(data_or_path)
    else:
        df = data_or_path.copy()

    # ---- Filter for remote workers ----
    remote_df = df[df["Work_Location"].str.lower() == "remote"].copy()

    # ---- Count & percentage ----
    mh_counts = remote_df["Mental_Health_Condition"].value_counts()
    mh_percent = (mh_counts / mh_counts.sum() * 100).round(1)
    data = pd.DataFrame({
        "Condition": mh_percent.index,
        "Percentage": mh_percent.values
    })

    # ---- Interactive pie (Plotly) ----
    fig = px.pie(
        data,
        names="Condition",
        values="Percentage",
        color="Condition",
        color_discrete_sequence=["#99CCFF", "#FFB3B3", "#FFCC99", "#D9D9D9"],
        hole=0.35  # donut look
    )

    fig.update_traces(
        textinfo="none",
        textposition="inside",
        pull=[0.05] * len(data),  # like explode
        hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>"
    )

    fig.update_layout(
        showlegend=True,
        legend_title_text="Condition"
    )

    return fig


# -------------------------------------------------------
# --------sleep quality by work location function-------------------
def plot_sleep_by_work_location(
    data_or_path, work_col="Work_Location", sleep_col="Sleep_Quality",
    work_filter=None, sleep_filter=None
):
    if isinstance(data_or_path, (str, Path)):
        df = pd.read_csv(data_or_path)
    else:
        df = data_or_path.copy()

    missing = [c for c in [work_col, sleep_col] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {missing}")

    work_order  = [v for v in ["Remote","Onsite","Hybrid"] if v in df[work_col].unique()]
    sleep_order = [v for v in ["Poor","Average","Good"] if v in df[sleep_col].unique()]

    if work_filter:
        df = df[df[work_col].isin(work_filter)]
    if sleep_filter:
        df = df[df[sleep_col].isin(sleep_filter)]

    g = df.groupby([work_col, sleep_col], observed=True).size().reset_index(name="Count")
    if g.empty:
        fig = px.bar(template="plotly_white"); fig.update_layout(xaxis_title="Work Location", yaxis_title="Percent (0%)")
        return fig

    totals = g.groupby(work_col)["Count"].transform("sum")
    g["Percent"] = (g["Count"] / totals * 100).round(1)

    fig = px.bar(
        g, x=work_col, y="Percent", color=sleep_col, barmode="stack", template="plotly_white",
        category_orders={work_col: work_order, sleep_col: sleep_order},
        color_discrete_sequence=["#6fa1ff","#a9c7ff","#dbe7ff"]  # Poor→Average→Good
    )
    fig.update_traces(marker_line_color="white", marker_line_width=1.2, opacity=0.95,
                      customdata=g["Count"],
                      hovertemplate="<b>%{x}</b><br>Sleep Quality: %{fullData.name}"
                                    "<br>Percent: <b>%{y:.1f}%</b>"
                                    "<br>Count: <b>%{customdata}</b><extra></extra>")
    fig.update_layout(yaxis=dict(title="Percent", ticksuffix="%"),
                      xaxis_title="Work Location", legend_title="Sleep Quality",
                      bargap=0.15, margin=dict(l=0,r=0,t=0,b=0),
                      hovermode="x unified", height=420)
    return fig


#-------------------------------------------------------
# --------Experience vs Satisfaction function-------------------
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def experience_bar_line_satisfaction(
    df: pd.DataFrame,
    exp_col: str = "Years_of_Experience",
    sat_col: str = "Satisfaction_with_Remote_Work",   # values like "Unsatisfied","Neutral","Satisfied"
    focus_level: str = "Satisfied",                    # pick: "Satisfied" | "Neutral" | "Unsatisfied"
    bins=(0,5,10,15,20,100),
    labels=("0–5 yrs","6–10 yrs","11–15 yrs","16–20 yrs","21+ yrs"),
):
    # 1) Bin experience
    d = df[[exp_col, sat_col]].dropna().copy()
    d["Experience_Range"] = pd.cut(d[exp_col], bins=bins, labels=labels,
                                   right=True, include_lowest=True)

    # 2) Denominator per bin
    den = (d.groupby("Experience_Range", observed=True)
             .size().reindex(labels, fill_value=0))

    # 3) Numerator per bin for chosen satisfaction level
    target = str(focus_level).strip().lower()
    num = (d.assign(hit = d[sat_col].astype(str).str.strip().str.lower() == target)
             .groupby("Experience_Range", observed=True)["hit"]
             .sum().reindex(labels, fill_value=0))

    # 4) Percent within bin
    pct = (num / den.replace(0, np.nan) * 100).fillna(0)

    # 5) Build figure
    fig = go.Figure()

    bar_color  = "#6AA9FF"   # blue
    line_color = "#1E2E4F"   # dark blue

    fig.add_trace(go.Bar(
        x=list(labels),
        y=den.values.astype(int),
        name="Number of people",
        marker_color=bar_color,
        hovertemplate="Range: %{x}<br>Count: %{y}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=list(labels),
        y=pct.values,
        name=f"% {focus_level}",
        mode="lines+markers+text",
        yaxis="y2",
        line=dict(color=line_color, width=3),
        marker=dict(color=line_color, size=8),
        text=[f"{v:.1f}%" for v in pct.values],
        textposition="top center",
        hovertemplate=f"Range: %{{x}}<br>% {focus_level}: %{{y:.1f}}%<extra></extra>"
    ))

    fig.update_layout(
        template="simple_white",
        yaxis=dict(title="Number of people", gridcolor="rgba(0,0,0,0.08)"),
        yaxis2=dict(title=f"% {focus_level}", overlaying="y", side="right", ticksuffix="%", rangemode="tozero"),
        legend=dict(orientation="h", y=1.12),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    return fig


#-------------------------------------------------------
#-mh by hours and meetings function-------------------

def plot_mh_heatmap(data_or_path,
                    hours_col="Hours_Worked_Per_Week",
                    meets_col="Number_of_Virtual_Meetings",
                    mh_col="Mental_Health_Condition"):
    """
    Returns a Plotly heatmap showing the % of people with any mental-health condition
    (Anxiety, Burnout, Depression) by Hours Worked × Number of Virtual Meetings.

    Parameters
    ----------
    data_or_path : pd.DataFrame | str | Path
        DataFrame or CSV path containing the three columns.
    """

    # --- Load data ---
    if isinstance(data_or_path, (str, Path)):
        df = pd.read_csv(data_or_path)
    else:
        df = data_or_path.copy()

    # --- Clean and prepare ---
    dfc = df.copy()
    dfc[mh_col] = (
        dfc[mh_col].astype("string").str.strip().str.title()
        .replace({"No Condition": "None", "Nan": "None", "Null": "None"})
    )

    # --- Define bins ---
    hours_bins = pd.cut(
        dfc[hours_col],
        bins=[0, 35, 40, 45, 50, 60, np.inf],
        labels=["<35", "35–40", "40–45", "45–50", "50–60", "60+"],
        include_lowest=True, right=False
    )
    meet_bins = pd.cut(
        dfc[meets_col],
        bins=[-np.inf, 2, 5, 8, np.inf],
        labels=["0–2", "3–5", "6–8", "9+"]
    )

    dfc = dfc.assign(hours_bin=hours_bins, meet_bin=meet_bins)
    dfc = dfc.dropna(subset=["hours_bin", "meet_bin"])

    # --- Compute % with any condition ---
    any_mask = dfc[mh_col].isin(["Anxiety", "Burnout", "Depression"])
    heat = (
        dfc.assign(any_condition=any_mask)
           .groupby(["meet_bin", "hours_bin"], as_index=False)["any_condition"]
           .mean()
           .assign(pct=lambda d: d["any_condition"] * 100)
    )

    heat_pivot = heat.pivot(index="meet_bin", columns="hours_bin", values="pct")

    # --- Create Plotly heatmap ---
    fig = px.imshow(
        heat_pivot,
        text_auto=".1f",
        aspect="auto",
        origin="lower",
        color_continuous_scale="RdBu_r",
        labels=dict(color="% with condition", x="Hours Worked / Week", y="Virtual Meetings"),
    )

    fig.update_layout(
        height=420,
        margin=dict(t=60, l=40, r=20, b=40),
        coloraxis_colorbar=dict(title="% with condition")
    )

    return fig



#--------------------------------------------------------
#--------Boxplot explorer function-------------------
import pandas as pd
import plotly.express as px
from pathlib import Path
from typing import Optional, Union, Dict, List

def boxplot_explorer(
    data_or_path: Union[str, Path, pd.DataFrame],
    value_col: str,
    filters: Optional[Dict[str, List]] = None,
    title: Optional[str] = None,
):
    """
    Build an interactive Plotly box plot for NUMERIC features only.
    No grouping — shows single-variable distribution with optional filters.

    Parameters
    ----------
    data_or_path : Path|str|pd.DataFrame
        CSV path or DataFrame
    value_col : str
        Numeric column to plot
    filters : dict, optional
        Optional dict {column: [allowed_values]} for filtering
    title : str, optional
        Custom chart title
    """
    # --- Load data ---
    if isinstance(data_or_path, (str, Path)):
        df = pd.read_csv(data_or_path)
    else:
        df = data_or_path.copy()

    # --- Apply filters ---
    if filters:
        for col, allowed in filters.items():
            if col in df.columns and allowed:
                df = df[df[col].isin(allowed)]

    # --- Ensure column is numeric ---
    if not pd.api.types.is_numeric_dtype(df[value_col]):
        try:
            df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
        except Exception:
            raise ValueError(f"Column '{value_col}' must be numeric.")
    df = df[[value_col]].dropna()

    # --- Build box plot ---
    fig = px.box(
        df,
        y=value_col,
        points="all",  # show individual points for detail
        template="plotly_white",
        color_discrete_sequence=["#3a86ff"]
    )
    fig.update_traces(marker=dict(opacity=0.5, size=6))
    fig.update_layout(
        title=title or f"Distribution of {value_col}",
        yaxis_title=value_col,
        showlegend=False,
        margin=dict(l=50, r=40, t=60, b=40)
    )
    return fig
