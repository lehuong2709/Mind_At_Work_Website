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
import numpy as np
from itertools import combinations
from scipy.stats import chi2_contingency
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from src.diagnosistic_analysis import scan_categorical_relationships, plot_pvalue_heatmap, plot_satisfaction_by_work_location
from src.diagnosistic_analysis import plot_stress_productivity_by_access
from src.diagnosistic_analysis import scan_cat_num_relationships, plot_single_pvalue_heatmap, plot_meetings_by_work_location, plot_isolation_vs_balance



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
st.sidebar.caption("Explore relationships, compare groups to understand reasons behind")
st.markdown("""
<h1 style="font-size: 48px; text-align: center; margin: 0; line-height: 1.0;">
    <span style="color: #31487A;">Workplace Insights Explorer</span>
</h1>
<h3 style="font-size: 18px; text-align: center; margin-top: 0;">
    Explore patterns to understand connections
</h3>""", unsafe_allow_html=True)

# ---- Resolve data path (project-root relative) ----
ROOT_DIR = Path(__file__).resolve().parents[1]       # folder where app.py lives
DATA_PATH = ROOT_DIR / "data" / "mind@work" / "mental_health_dataset" / "Cleaned_remote_work.csv"  # keep folder name as-is
df = pd.read_csv(DATA_PATH)
st.markdown("<br><br>", unsafe_allow_html=True)


#----------------------------------#------ FUNCTIONS FOR CATEGORICAL RELATIONSHIPS----------------------
#----------------------------------
left, right = st.columns([2, 1])
with left: 
    st.markdown("""
    <h2 style="color:#31487A; font-size: 28px; font-weight: 700; margin: 1em 0 .5em 0;">
        Categorical Factors Relationships
    """, unsafe_allow_html=True)
    # ---- Run your analysis silently ----
    # 1) compute the p-values
    res = scan_categorical_relationships(
        df.drop(columns=["Gender", "Industry", "Region", "Sleep_Quality"], errors="ignore"),
        alpha=0.05
    )

    # 2) override color palette before plotting (your version used 'viridis_r')
    #    we'll switch it to a blue tone for nicer visuals
    sns.set_style("white")
    plt.rcParams["figure.facecolor"] = "white"

    if not res.empty:
        # Replace the viridis colormap with a soft blue palette
        def plot_pvalue_heatmap_blue(res, alpha=0.05):
            import numpy as np
            import pandas as pd
            import seaborn as sns
            import matplotlib.pyplot as plt

            vars_ = sorted(set(res["Var1"]).union(res["Var2"]))
            M = pd.DataFrame(1.0, index=vars_, columns=vars_)
            for _, r in res.iterrows():
                a, b, p = r["Var1"], r["Var2"], r["p_value"]
                M.loc[a, b] = M.loc[b, a] = p

            plt.figure(figsize=(1.2 * len(vars_), 1.0 * len(vars_)))
            mask = np.triu(np.ones_like(M, dtype=bool))
            ax = sns.heatmap(
                M, mask=mask, cmap="Blues",  # <-- blue theme
                annot=True, fmt=".3f", square=True,
                linewidths=0.4, linecolor="#f4f6f8",
                cbar_kws={"label": "p-value"}, vmin=0, vmax=1
            )
            ax.set_title("Categorical Relationship Significance (p-values)", fontsize=12, pad=8)
            plt.xticks(rotation=45, ha="right", fontsize=9)
            plt.yticks(rotation=0, fontsize=9)

            # --- Highlight significant p-values (bold + slightly bigger font) ---
            texts = ax.texts
            n = M.shape[0]
            coords = [(i, j) for i in range(n) for j in range(n) if not mask[i, j]]

            for (i, j), t in zip(coords, texts):
                p_val = M.iat[i, j]
                if np.isnan(p_val):
                    continue
                if p_val < alpha:
                    t.set_fontweight("bold")
                    t.set_fontsize(10.5)  # subtle bump
                else:
                    t.set_fontweight("normal")
                    t.set_fontsize(9)

            plt.tight_layout()
            return plt.gcf()

        # --- Call it ---
        fig = plot_pvalue_heatmap_blue(res, alpha=0.05)
        st.pyplot(fig, use_container_width=True)
    else:
        st.info("No valid categorical pairs found.")
with right:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background-color: #f0f4f8; padding: 15px; border-radius: 8px;">
        <h3 style="color:#31487A; font-size: 20px; font-weight: 600; margin-top: 0;">
            About this analysis
        </h3>
        <p style="font-size: 14px; color: #333;">
            This section explores relationships between categorical variables in the dataset using Chi-squared tests.
            Each cell in the heatmap shows the p-value for the association between two categorical factors.
        </p>
        <p style="font-size: 14px; color: #333;">
            A low p-value (typically &lt; 0.05) indicates a statistically significant relationship, suggesting that the two factors are not independent.
            Significant p-values are highlighted in bold and slightly larger font for easy identification.
        </p>
        <p style="font-size: 14px; color: #333;">
            Use this analysis to identify interesting connections between workplace factors, mental health indicators.
        </p>
    </div>
    """, unsafe_allow_html=True)


#----------------------------------#------ FUNCTION DEFINITION FOR CATEGORICAL RELATIONSHIPS----------------------
#----------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<style>
.figtitle {
    height: 56px;                   /* equal height for both chart titles */
    display: flex;
    align-items: flex-end;
    font-size: 28px;
    font-weight: 700;
    color: #31487A;                 /* your brand color */
    line-height: 1.05;
    margin: 0 0 6px 0;
}
.caption-box {
    min-height: 80px;               /* keep captions aligned */
}
button[title="View fullscreen"] {
    visibility: hidden;             /* optional: hide zoom icon */
}
</style>
""", unsafe_allow_html=True)

# ---- LAYOUT ----
col1, col2 = st.columns(2, gap="large", vertical_alignment="top")

with col1:
    st.markdown('<div class="figtitle">Satisfaction by Work Location</div>', unsafe_allow_html=True)
    fig1 = plot_satisfaction_by_work_location(df)
    st.pyplot(fig1, use_container_width=True)
    st.caption(
        '<div class="caption-box">'
        '<p style="font-size:15px;">This chart shows how satisfaction levels vary by work location '
        '(Remote, Hybrid, Onsite). Onsite workers show the highest share of “Satisfied”, while Remote workers report fewer “Satisfied”.</p>'
        '</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="figtitle">Stress & Productivity by MH Access</div>', unsafe_allow_html=True)
    fig2 = plot_stress_productivity_by_access(df)
    st.pyplot(fig2, use_container_width=True)
    st.caption(
        '<div class="caption-box">'
        '<p style="font-size:15px;">This chart shows how stress levels and productivity vary based on '
        'access to mental health resources. Employees with access report lower stress and higher productivity.</p>'
        '</div>', unsafe_allow_html=True)
    

#----------------------------------
#------ heatmap ----------------------------------
# ----------------------------------
col_1, col_2 = st.columns([1, 2])
with col_1:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background-color: #f0f4f8; padding: 15px; border-radius: 8px;">
        <h3 style="color:#31487A; font-size: 20px; font-weight: 600; margin-top: 0;">
            About this analysis
        </h3>
        <p style="font-size: 14px; color: #333;">
            This section examines relationships between categorical and numeric variables using the Kruskal–Wallis test.
            Each cell in the heatmap displays the p-value for the association between a categorical factor and a numeric measure.
        </p>
        <p style="font-size: 14px; color: #333;">
            A low p-value (typically &lt; 0.05) indicates a statistically significant relationship, suggesting that the numeric variable differs across categories of the factor.
            Significant p-values are highlighted in bold and slightly larger font for easy identification.
        </p>
        <p style="font-size: 14px; color: #333;">
            Use this analysis to uncover important connections between workplace factors and key numeric outcomes like stress, productivity, and satisfaction.
        </p>
    </div>
    """, unsafe_allow_html=True)
with col_2:
    st.markdown("""
        <h2 style="color:#31487A; font-size: 28px; font-weight: 700; margin: 1em 0 .5em 0;">
            Numeric–Categorical Factors Relationships
        </h2>
    """, unsafe_allow_html=True)

    cols_to_drop = [
        "Industry", "Job_Role", "Region",
        "Sleep_Quality", "Physical_Activity"
    ]
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

    # --- Run test and plot ---
    res = scan_cat_num_relationships(df, alpha=0.05)
    fig = plot_single_pvalue_heatmap(
        res,
        p_col="Kruskal_p",
        alpha=0.05,
        title="Kruskal–Wallis p-values (Categorical × Numeric)"
    )

    if fig is not None:
        st.pyplot(fig, use_container_width=True)
    else:
        st.info("No valid categorical–numeric pairs found after dropping selected features.")

#---------------------------------------- IGNORE ----------------------------------
# ------------------------------------------------------------------
st.markdown("<br><br>", unsafe_allow_html=True)
left, right = st.columns([1, 1])
with left:
    st.markdown("""
        <h2 style="color:#31487A; font-size: 28px; font-weight: 700; margin: 1em 0 .5em 0;">
            Meetings by Work Location
        </h2>
    """, unsafe_allow_html=True)

    fig = plot_meetings_by_work_location(df)
    st.pyplot(fig, use_container_width=True)

    st.caption(
        "This plot shows how the number of virtual meetings per week "
        "varies by work location. The white box highlights median and IQR, "
        "while blue dots represent group means."
    )

with right:
    st.markdown("""
        <h2 style="color:#31487A; font-size: 28px; font-weight: 700; margin: 1em 0 .5em 0;">
            Isolation vs Work-Life Balance
        </h2>
    """, unsafe_allow_html=True)

    fig = plot_isolation_vs_balance(df)
    st.pyplot(fig, use_container_width=True)

    st.caption(
        "Each line compares the average social isolation and work–life balance ratings "
        "for a given work location. Shorter lines suggest a better balance between "
        "isolation and work–life perception."
    )

#-------------------------
# ========= Group Comparison Lab (pick any two groups) =========
import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind, mannwhitneyu

st.markdown("""
<style>
.help-icon {
    display: inline-block;
    color: #6c757d;
    font-size: 18px;
    margin-left: 6px;
    cursor: help;
    position: relative;
}
.help-icon:hover::after {
    content: "Compare two groups on any numeric feature. Select a categorical variable (e.g. Work_Location), define Group A and Group B, then choose a numeric metric (e.g. Stress Level or Hours Worked). The lab runs a t-test or Mann–Whitney U test to show if differences are statistically significant.";
    position: absolute;
    background-color: #f0f2f6;
    color: #000;
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 13px;
    line-height: 1.4;
    width: 330px;
    top: 25px;
    left: 0;
    z-index: 100;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}
</style>

<h2 style="color:#31487A; font-size: 28px; font-weight: 700; margin: 1em 0 .5em 0;">
    Group Comparison Lab
    <span class="help-icon" title="Click for help">ℹ️</span>
</h2>
""", unsafe_allow_html=True)

# ---- column discovery ----
cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
num_cols = df.select_dtypes(include=np.number).columns.tolist()

if not cat_cols or not num_cols:
    st.info("Need at least one categorical and one numeric column in the dataset.")
else:
    with st.expander("Pick variables", expanded=True):
        cat_var = st.selectbox("Categorical feature", cat_cols, index=cat_cols.index("Work_Location") if "Work_Location" in cat_cols else 0)
        # levels after dropna
        levels = df[cat_var].dropna().unique().tolist()
        if len(levels) < 2:
            st.warning(f"‘{cat_var}’ has fewer than 2 levels with data.")
            st.stop()

        c1, c2 = st.columns(2)
        with c1:
            g1 = st.selectbox("Group A", levels, index=0)
        with c2:
            g2 = st.selectbox("Group B", [l for l in levels if l != g1], index=0)

        metric = st.selectbox("Numeric metric", num_cols, index=num_cols.index("Number_of_Virtual_Meetings") if "Number_of_Virtual_Meetings" in num_cols else 0)
        test_choice = st.radio("Statistical test", ["t-test (independent)", "Mann–Whitney U"], horizontal=True)
        show_points = st.checkbox("Show individual points (swarm)", value=True)

    # ---- slice data ----
    sub = df[[cat_var, metric]].dropna()
    a = sub.loc[sub[cat_var] == g1, metric].astype(float).values
    b = sub.loc[sub[cat_var] == g2, metric].astype(float).values

    if len(a) < 3 or len(b) < 3:
        st.warning("Not enough data in one of the groups (need ≥3 observations each).")
    else:
        # ---- stats ----
        if test_choice.startswith("t-test"):
            tstat, p = ttest_ind(a, b, equal_var=False, nan_policy="omit")
            # Cohen's d (Hedges g correction optional)
            na, nb = len(a), len(b)
            pooled_sd = np.sqrt(((na-1)*np.var(a, ddof=1) + (nb-1)*np.var(b, ddof=1)) / (na+nb-2))
            d = (np.mean(a) - np.mean(b)) / pooled_sd if pooled_sd > 0 else np.nan
            eff_label = f"Cohen’s d = {d:.2f}"
            test_label = f"t = {tstat:.2f}, p = {p:.4f}"
        else:
            u, p = mannwhitneyu(a, b, alternative="two-sided")
            # Rank-biserial correlation
            na, nb = len(a), len(b)
            rbc = 1 - (2*u) / (na*nb)
            eff_label = f"Rank-biserial r = {rbc:.2f}"
            test_label = f"U = {u:.0f}, p = {p:.4f}"

        # ---- plot ----
        sns.set_theme(style="whitegrid", font_scale=0.85)  # smaller font for compactness
        fig, ax = plt.subplots(figsize=(4.8, 3.0))   
        palette = sns.color_palette("Blues", 3)

        # violin & box
        sns.violinplot(
            data=sub[sub[cat_var].isin([g1, g2])],
            x=cat_var, y=metric, order=[g1, g2],
            inner=None, cut=0, linewidth=0, palette=palette, ax=ax
        )
        sns.boxplot(
            data=sub[sub[cat_var].isin([g1, g2])],
            x=cat_var, y=metric, order=[g1, g2],
            width=0.25, showcaps=False,
            boxprops={"facecolor":"white","edgecolor":"#234A84","linewidth":1.3},
            whiskerprops={"color":"#234A84","linewidth":1.1},
            medianprops={"color":"#234A84","linewidth":1.6},
            showfliers=False, ax=ax
        )
        if show_points:
            sns.swarmplot(
                data=sub[sub[cat_var].isin([g1, g2])],
                x=cat_var, y=metric, order=[g1, g2],
                color="#1f3b6d", alpha=0.22, size=3, ax=ax
            )

        # means as dots
        means = sub[sub[cat_var].isin([g1, g2])].groupby(cat_var)[metric].mean()
        ax.scatter([0,1], means[[g1, g2]].values, s=85, c="white", edgecolors="#1f3b6d", zorder=5)

        # --- Prettify variable names ---
        pretty_metric = metric.replace("_", " ").title()
        pretty_cat = cat_var.replace("_", " ").title()

        # --- Add smaller but readable title ---
        ax.set_title(
            f"{pretty_metric}\n{g1} vs {g2} ({pretty_cat})",
            fontsize=9.5, weight="semibold", pad=4, color="#1f2937"
        )
        
        ax.set_xlabel(cat_var); ax.set_ylabel(metric)
        sns.despine(ax=ax)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)

        # ---- stats summary line ----
        st.caption(
            f"**{test_choice}** → {test_label}.  {eff_label}.  "
            f"n₁ = {len(a)}, n₂ = {len(b)}.  "
            f"Lower p-values indicate stronger evidence of a difference."
        )


# ---- CTA ----
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)
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


col1, col2 = st.columns([1, 1])
col2.markdown("""
<div style="text-align: right; font-size: 13px; color: gray;">
    © 2025 Mind@Work Project. All rights reserved. <br>
    Built by the Mind@Work project team <br>
    in collaboration with Karolinska Institutet & Stockholm University.
</div>
""", unsafe_allow_html=True)