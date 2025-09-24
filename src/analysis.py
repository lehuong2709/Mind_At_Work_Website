# src/analysis_board.py
from __future__ import annotations
import pandas as pd
import streamlit as st
import plotly.express as px
from typing import Optional, Iterable

PRIMARY_COLOR = "#7b241c"   # your red
TARGET_COL_DEFAULT = "Stress_Level"
DROP_COLS_DEFAULT: Iterable[str] = ("Employee_ID",)

@st.cache_data(show_spinner=False)
def _load_csv(path: str, drop_cols: Iterable[str]) -> pd.DataFrame:
    df = pd.read_csv(path)
    # drop if present
    drop_cols = [c for c in drop_cols if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)
    return df

def render_more_analysis(
    data_path: Optional[str] = None,
    df: Optional[pd.DataFrame] = None,
    target_col: str = TARGET_COL_DEFAULT,
    drop_cols: Iterable[str] = DROP_COLS_DEFAULT,
    title: str = "📊 Simple Descriptive Board",
):
    """
    Render the 'More Analysis' page.
    - Pass either `df` (preferred) or `data_path`.
    - `target_col` controls the Stress/target distribution block.
    """
    if df is None:
        if not data_path:
            st.error("No dataset provided. Pass a DataFrame or a CSV `data_path`.")
            return
        df = _load_csv(data_path, drop_cols)

    st.title(title)

    # Top stat
    st.markdown(
        f"""
        <div style='padding:10px;background-color:{PRIMARY_COLOR};border-radius:6px;margin-bottom:8px'>
            <span style='color:white;font-weight:bold;'>Loaded:</span>
            <span style='color:white'>{df.shape[0]} rows × {df.shape[1]} columns</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Preview -----------------------------------------------------------
    st.subheader("Dataset Preview")
    st.dataframe(df.head(), use_container_width=True)

    # ---- Univariate --------------------------------------------------------
    st.subheader("Univariate")
    col = st.selectbox("Pick a column", df.columns)
    if pd.api.types.is_numeric_dtype(df[col]):
        fig = px.histogram(df, x=col, nbins=50, title=f"Distribution of {col}")
        fig.update_traces(marker_color=PRIMARY_COLOR)
        fig.update_layout(bargap=0.05)
    else:
        counts = df[col].value_counts(dropna=False).reset_index()
        counts.columns = [col, "count"]
        fig = px.bar(counts, x=col, y="count",
                     title=f"Counts of {col}",
                     color_discrete_sequence=[PRIMARY_COLOR])
    st.plotly_chart(fig, use_container_width=True)

    # ---- Bivariate (cat → mean num) ---------------------------------------
    st.subheader("Bivariate")
    cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if cat_cols and num_cols:
        c1, c2, c3 = st.columns(3)
        with c1:
            cat_col = st.selectbox("Categorical column", cat_cols, key="bi_cat")
        with c2:
            num_col = st.selectbox("Numeric column", num_cols, key="bi_num")
        grouped = df.groupby(cat_col, dropna=False)[num_col].mean().reset_index()
        fig2 = px.bar(grouped, x=cat_col, y=num_col,
                      title=f"Average {num_col} by {cat_col}",
                      color_discrete_sequence=[PRIMARY_COLOR])
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Need at least one categorical and one numeric column for bivariate plot.")

    # ---- Multivariate (cat×cat → mean num) --------------------------------
    st.subheader("Multivariate")
    if len(cat_cols) >= 2 and num_cols:
        st.markdown("### 📊 Grouped Average by Two Categorical Columns")
        m1, m2, m3 = st.columns(3)
        with m1:
            cat_col1 = st.selectbox("First categorical", cat_cols, key="mv_cat1")
        with m2:
            cat_col2 = st.selectbox("Second categorical",
                                    [c for c in cat_cols if c != cat_col1], key="mv_cat2")
        with m3:
            num_col_mv = st.selectbox("Numeric", num_cols, key="mv_num")

        grouped_mv = df.groupby([cat_col1, cat_col2], dropna=False)[num_col_mv].mean().reset_index()
        fig_mv = px.bar(
            grouped_mv, x=cat_col1, y=num_col_mv, color=cat_col2, barmode="group",
            title=f"Avg. {num_col_mv} by {cat_col1} and {cat_col2}",
            color_discrete_sequence=[
                "#7b241c", "#922b21", "#a93226", "#c0392b", "#cd6155", "#e6b0aa", "#f1948a"
            ]
        )
        st.plotly_chart(fig_mv, use_container_width=True)
    else:
        st.info("Need two categorical columns and one numeric column for multivariate plot.")

    # ---- Target distribution (Stress) -------------------------------------
    st.subheader(f"{target_col} Distribution")
    if target_col in df.columns:
        # if you want a fixed order for Stress_Level
        order = ["High", "Medium", "Low"]
        prev = df[target_col].value_counts().reindex(order).fillna(0).reset_index()
        prev.columns = [target_col, "count"]
        fig3 = px.bar(prev, x=target_col, y="count", text="count",
                      title=f"{target_col} Distribution",
                      color_discrete_sequence=[PRIMARY_COLOR])
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning(f"Column '{target_col}' not found in dataset.")
