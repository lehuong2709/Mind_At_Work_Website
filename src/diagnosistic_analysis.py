from itertools import combinations
from scipy.stats import chi2_contingency
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


#----------------------------------
#------ FUNCTIONS FOR CATEGORICAL RELATIONSHIPS-----------------
# ----------------------------------
# --- prettier blue-tone heatmap for p-values ---

from itertools import combinations
from scipy.stats import chi2_contingency

def scan_categorical_relationships(df_in, alpha=0.05):
    if not isinstance(df_in, pd.DataFrame):
        raise TypeError(f"Expected a pandas DataFrame, got {type(df_in)}. "
                        "Did you overwrite `df` earlier?")
    df = df_in.copy()

    # pick categorical-like columns
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    results = []
    for col1, col2 in combinations(cat_cols, 2):
        ct = pd.crosstab(df[col1].fillna("Missing"), df[col2].fillna("Missing"))
        if ct.shape[0] > 1 and ct.shape[1] > 1:
            chi2, p, dof, _ = chi2_contingency(ct)
            results.append({
                "Var1": col1, "Var2": col2,
                "Chi2": chi2, "dof": dof, "p_value": p,
                "Significant": p < alpha
            })

    res = pd.DataFrame(results)
    return res.sort_values("p_value") if not res.empty else res

def plot_pvalue_heatmap(res, alpha=0.05):
    """
    Draw a clean blue-tone heatmap of p-values from scan_categorical_relationships().
    Automatically scales to number of variables.
    Darker blue = smaller p-value (stronger relationship).
    Significant p-values (p < alpha) are bold and slightly larger.
    """
    import pandas as pd
    import numpy as np
    import seaborn as sns
    import matplotlib.pyplot as plt

    if res.empty:
        print("No categorical relationships to plot.")
        return

    # --- Build symmetric matrix of p-values ---
    vars_ = sorted(set(res["Var1"]).union(res["Var2"]))
    M = pd.DataFrame(1.0, index=vars_, columns=vars_)
    for _, r in res.iterrows():
        a, b, p = r["Var1"], r["Var2"], r["p_value"]
        M.loc[a, b] = M.loc[b, a] = p

    # --- Dynamic figure sizing ---
    n_vars = len(vars_)
    cell_size = 0.6  # adjust this if you want bigger/smaller cells
    fig_w = max(8, n_vars * cell_size)
    fig_h = max(8, n_vars * cell_size)

    # --- Plot ---
    plt.figure(figsize=(fig_w, fig_h))
    mask = np.triu(np.ones_like(M, dtype=bool))
    ax = sns.heatmap(
        M, mask=mask, cmap="Blues",
        annot=True, fmt=".3f", square=True,
        linewidths=0.4, linecolor="#f4f6f8",
        cbar_kws={"label": "p-value"}, vmin=0, vmax=1
    )

    # --- Labels & styling ---
    ax.set_xticklabels(ax.get_xticklabels(),
                       rotation=45, ha="right",
                       fontsize=12, weight="semibold")
    ax.set_yticklabels(ax.get_yticklabels(),
                       rotation=0,
                       fontsize=12, weight="semibold")

    # --- Highlight significant cells ---
    texts = ax.texts
    n = M.shape[0]
    coords = [(i, j) for i in range(n) for j in range(n) if not mask[i, j]]
    for (i, j), t in zip(coords, texts):
        p_val = M.iat[i, j]
        if np.isnan(p_val):
            continue
        if p_val < alpha:
            t.set_fontweight("bold")
            t.set_fontsize(13)
        else:
            t.set_fontweight("normal")
            t.set_fontsize(11)

    plt.tight_layout()
    plt.show()


#----------------------------------
#------ bar plot -----------------
# ----------------------------------
def plot_satisfaction_by_work_location(df, figsize=(7.8, 5.2)):
    import pandas as pd, matplotlib.pyplot as plt, seaborn as sns

    subset = df[df["Work_Location"].isin(["Remote", "Onsite"])].copy()
    share = (
        subset.groupby("Work_Location")["Satisfaction_with_Remote_Work"]
              .value_counts(normalize=True)
              .rename("Percent").reset_index()
    )

    fig, ax = plt.subplots(figsize=figsize)
    sns.barplot(
        data=share, x="Work_Location", y="Percent",
        hue="Satisfaction_with_Remote_Work", palette="Blues_r", ax=ax
    )

    # axis labels only (no inside title)
    ax.set_xlabel("Work Location", fontsize=11)
    ax.set_ylabel("Percent of respondents", fontsize=11)
    ax.set_ylim(0.25, 0.40)

    for c in ax.containers:
        ax.bar_label(c, fmt="%.2f", label_type="edge", fontsize=10, padding=2)

    # legend outside, same anchor as the other chart
    ax.legend(title="Satisfaction", frameon=False, bbox_to_anchor=(1.02, 1), loc="upper left")

    # identical margins for both charts
    fig.subplots_adjust(left=0.12, right=0.82, top=0.98, bottom=0.18)
    return fig


#----------------------------------
#------ bar plot 2 -----------------
# ----------------------------------
def plot_stress_productivity_by_access(
    df, figsize=(7.8, 5.2),
    access_col="Access_to_Mental_Health_Resources",
    stress_col="Stress_Level", prod_col="Productivity_Change",
    stress_levels=("High", "Low"), prod_decrease_label="Decrease",
    stress_ylim=(45, 55)
):
    import seaborn as sns, matplotlib.pyplot as plt, pandas as pd

    subset = df[df[stress_col].isin(stress_levels)].copy()
    stress_share = (
        subset.groupby(access_col)[stress_col]
              .value_counts(normalize=True)
              .rename("Percent").reset_index()
    )
    stress_share["Percent"] *= 100

    total_n = len(df)
    prod_share = (
        df[df[prod_col] == prod_decrease_label]
        .groupby(access_col).size().reset_index(name="Count")
    )
    prod_share["Prod_Percent"] = prod_share["Count"] / total_n * 100

    fig, ax1 = plt.subplots(figsize=figsize)

    sns.barplot(
        data=stress_share, x=access_col, y="Percent",
        hue=stress_col, palette=["#1f77b4", "#aec7e8"], width=0.7, ax=ax1
    )
    ax1.set_ylabel("Stress level (%)", fontsize=11)
    ax1.set_xlabel("Access to Mental Health Resources", fontsize=11)
    if stress_ylim: ax1.set_ylim(*stress_ylim)

    for c in ax1.containers:
        ax1.bar_label(c, fmt="%.0f%%", fontsize=10, padding=2)

    ax2 = ax1.twinx()
    sns.lineplot(
        data=prod_share, x=access_col, y="Prod_Percent",
        color="#ff7f0e", linewidth=2.5, marker="o", markersize=8,
        markeredgecolor="black", ax=ax2
    )
    for _, r in prod_share.iterrows():
        ax2.text(r[access_col], r["Prod_Percent"] + 0.5,
                 f"{r['Prod_Percent']:.1f}%", color="#ff7f0e",
                 fontsize=11, ha="center", weight="bold")

    pad = max(2, 0.05 * prod_share["Prod_Percent"].max())
    ax2.set_ylim(prod_share["Prod_Percent"].min() - pad, prod_share["Prod_Percent"].max() + pad)
    ax2.set_ylabel("Productivity decrease (% of total)", fontsize=11, color="#ff7f0e")

    # legend outside, same anchor as the first chart
    ax1.legend(title="Stress Level", frameon=False, bbox_to_anchor=(1.02, 1), loc="upper left")

    # identical margins for both charts
    fig.subplots_adjust(left=0.12, right=0.82, top=0.98, bottom=0.18)
    return fig


#----------------------------------
#------ FUNCTION DEFINITION FOR CAT-NUM RELATIONSHIPS-----------------
#----------------------------------
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import f_oneway, kruskal


def scan_cat_num_relationships(df, alpha=0.05):
    # categorical: object, category, (optionally) bool
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns
    # numeric: any numpy number subtype
    num_cols = df.select_dtypes(include=np.number).columns

    results = []
    for cat in cat_cols:
        for num in num_cols:
            # groupby drops NaNs by default; collect numeric arrays per level
            groups = [g[num].dropna().values for _, g in df.groupby(cat, observed=True)]
            # need at least 2 groups with data
            if len(groups) > 1 and sum(len(g) > 0 for g in groups) > 1:
                # ANOVA (parametric)
                try:
                    fstat, p_anova = f_oneway(*groups)
                except Exception:
                    p_anova = np.nan
                # Kruskal–Wallis (nonparametric)
                try:
                    hstat, p_kruskal = kruskal(*groups)
                except Exception:
                    p_kruskal = np.nan
                results.append((cat, num, p_anova, p_kruskal))

    results_df = pd.DataFrame(
        results, columns=["Categorical", "Numeric", "ANOVA_p", "Kruskal_p"]
    )

    if results_df.empty:
        return results_df

    # ensure numeric; NaNs if any failures
    results_df["ANOVA_p"] = pd.to_numeric(results_df["ANOVA_p"], errors="coerce")
    results_df["Kruskal_p"] = pd.to_numeric(results_df["Kruskal_p"], errors="coerce")

    # significance flags (treat NaN as not significant)
    results_df["ANOVA_Significant"] = results_df["ANOVA_p"].lt(alpha).fillna(False)
    results_df["Kruskal_Significant"] = results_df["Kruskal_p"].lt(alpha).fillna(False)

    return results_df.sort_values("Kruskal_p", na_position="last")


def plot_single_pvalue_heatmap(res, p_col="Kruskal_p", alpha=0.05, title=None):
    import pandas as pd, numpy as np, seaborn as sns, matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    if res is None or (hasattr(res, "empty") and res.empty):
        return None

    heatmap_data = res.pivot(index="Categorical", columns="Numeric", values=p_col)
    if heatmap_data.empty:
        return None

    cmap = LinearSegmentedColormap.from_list("soft_blue", ["#f8f9fa", "#bcd2e8", "#4f83cc"])

    fig_w = max(8, 1.2 * len(heatmap_data.columns))
    fig_h = max(4.5, 0.8 * len(heatmap_data.index))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))  # ← create fig/ax and return fig

    sns.heatmap(
        heatmap_data, cmap=cmap, vmin=0, vmax=1, annot=False,
        linewidths=0.4, linecolor="white", cbar_kws={"label": "p-value"}, ax=ax
    )

    # annotate
    for i, row in enumerate(heatmap_data.index):
        for j, col in enumerate(heatmap_data.columns):
            val = heatmap_data.loc[row, col]
            if pd.isna(val): 
                continue
            is_sig = val < alpha
            ax.text(j + 0.5, i + 0.5, f"{val:.3f}",
                    ha="center", va="center",
                    fontsize=10 if is_sig else 8.5,
                    fontweight="bold" if is_sig else "normal",
                    color="black")

    ax.set_title(title or f"{p_col.replace('_',' ').title()} Heatmap (Categorical × Numeric)",
                 fontsize=13, weight="bold", pad=12)
    ax.set_xlabel("Numeric Variables", fontsize=11)
    ax.set_ylabel("Categorical Variables", fontsize=11)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    plt.setp(ax.get_yticklabels(), rotation=0)
    fig.tight_layout()
    return fig

#----------------------------------
#------  ----------------------------------
#----------------------------------
def plot_meetings_by_work_location(df):
    """
    Plot the distribution of the number of virtual meetings per week by work location.

    Combines a violin plot (overall shape), a white boxplot (IQR + median),
    and a semi-transparent swarmplot (individual points), with group means shown
    as white dots edged in dark blue.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain 'Work_Location' (categorical) and 'Number_of_Virtual_Meetings' (numeric).
    """

    # --- Data cleaning ---
    df = df.copy()
    if "Number_of_Virtual_Meetings" not in df.columns or "Work_Location" not in df.columns:
        raise ValueError("DataFrame must include 'Work_Location' and 'Number_of_Virtual_Meetings' columns.")

    df["Number_of_Virtual_Meetings"] = pd.to_numeric(df["Number_of_Virtual_Meetings"], errors="coerce")
    df = df.dropna(subset=["Work_Location", "Number_of_Virtual_Meetings"])

    # --- Aesthetic theme ---
    sns.set_theme(style="whitegrid", font_scale=1.1)
    palette = sns.color_palette("Blues", 3)  # light→dark blues

    # --- Base violin plot ---
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.violinplot(
        data=df,
        x="Work_Location",
        y="Number_of_Virtual_Meetings",
        palette=palette,
        inner=None, cut=0, linewidth=0, ax=ax
    )

    # --- White boxplot overlay (IQR + median) ---
    sns.boxplot(
        data=df,
        x="Work_Location",
        y="Number_of_Virtual_Meetings",
        width=0.22,
        showcaps=False,
        boxprops={"facecolor": "white", "edgecolor": "#234A84", "linewidth": 1.4},
        whiskerprops={"color": "#234A84", "linewidth": 1.2},
        medianprops={"color": "#234A84", "linewidth": 1.8},
        showfliers=False,
        ax=ax
    )

    # --- Swarmplot overlay (individual points) ---
    sns.swarmplot(
        data=df,
        x="Work_Location",
        y="Number_of_Virtual_Meetings",
        color="#1f3b6d",
        alpha=0.25,
        size=3,
        ax=ax
    )

    # --- Add group means as white dots with dark blue edge ---
    group_means = df.groupby("Work_Location")["Number_of_Virtual_Meetings"].mean()
    xticks = ax.get_xticks()
    ax.scatter(xticks, group_means.values, s=80, c="white", edgecolors="#1f3b6d", zorder=5)

    # --- Titles and labels ---
    ax.set_xlabel("Work Location", fontsize=11)
    ax.set_ylabel("Number of Meetings per Week", fontsize=11)

    sns.despine()
    fig.tight_layout()
    return fig

#----------------------------------
#------  ----------------------------------
#----------------------------------
def plot_isolation_vs_balance(df: pd.DataFrame):
    """
    Dumbbell-style comparison of mean Social Isolation vs Work–Life Balance by Work_Location.
    Returns a Matplotlib Figure.
    """
    required = ["Work_Location", "Social_Isolation_Rating", "Work_Life_Balance_Rating"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    grp = (
        df.groupby("Work_Location")[["Social_Isolation_Rating", "Work_Life_Balance_Rating"]]
          .mean()
          .dropna()
    )
    if grp.empty:
        raise ValueError("No data after grouping by Work_Location.")

    sns.set_theme(style="whitegrid", font_scale=1.1)
    fig, ax = plt.subplots(figsize=(7, 5))

    for i, (loc, row) in enumerate(grp.iterrows()):
        ax.plot(
            [row["Social_Isolation_Rating"], row["Work_Life_Balance_Rating"]],
            [i, i],
            "o-",
            color="#1f77b4",
            lw=2,
            markersize=8
        )

    ax.set_yticks(range(len(grp)))
    ax.set_yticklabels(grp.index)
    ax.set_xlabel("Average Rating (1–5)", fontsize=11)
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig


#----------------------------------#------  ----------------------------------
#----------------------------------     
