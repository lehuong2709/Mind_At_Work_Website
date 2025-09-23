# src/catboost_model.py
from __future__ import annotations

import os, json, pickle
from typing import List

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report, confusion_matrix

from catboost import CatBoostClassifier, Pool

# ---------------------------------------------------------------------
# 0) Paths
# ---------------------------------------------------------------------
DATA_PATH    = "data/mind@work/mental heath dataset/Cleaned_remote_work.csv"

MODEL_DIR    = "models"
CBM_PATH     = os.path.join(MODEL_DIR, "catboost_model.cbm")
PKL_PATH     = os.path.join(MODEL_DIR, "catboost_model.pkl")
FEATURE_JSON = os.path.join(MODEL_DIR, "feature_order.json")
THRESH_JSON  = os.path.join(MODEL_DIR, "threshold.json")

os.makedirs(MODEL_DIR, exist_ok=True)

# ---------------------------------------------------------------------
# 1) Target + Features (12 total, chosen from your dataset)
#    - Numeric (6)
#    - Categorical (6)
# ---------------------------------------------------------------------
TARGET_COL: str = "Mental_Health_Condition"

NUM_COLS: List[str] = [
    "Age",
    "Years_of_Experience",
    "Hours_Worked_Per_Week",
    "Number_of_Virtual_Meetings",
    "Work_Life_Balance_Rating",   # ordinal 1–4 in your file; we treat as numeric
    "Social_Isolation_Rating",    # ordinal 1–5; we treat as numeric
]

CAT_COLS: List[str] = [
    "Satisfaction_with_Remote_Work",
    "Company_Support_for_Remote_Work",
    "Physical_Activity",
    "Sleep_Quality",
    "Productivity_Change",
    "Access_to_Mental_Health_Resources",
]

FEATURES: List[str] = NUM_COLS + CAT_COLS  # final column order for training/inference


# ---------------------------------------------------------------------
# 2) Data loading / preprocessing
# ---------------------------------------------------------------------
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # keep only what we need and make sure the target exists
    cols = [c for c in FEATURES + [TARGET_COL] if c in df.columns]
    df = df[cols].copy()
    df = df.dropna(subset=[TARGET_COL])
    return df


def make_binary_target(df: pd.DataFrame) -> pd.Series:
    """
    Convert 'Mental_Health_Condition' to binary:
      1 if Anxiety / Burnout / Depression; 0 if None (or anything else).
    """
    v = df[TARGET_COL].astype(str).str.strip().str.lower()
    return v.isin({"anxiety", "burnout", "depression"}).astype(int)


def preprocess_X(X: pd.DataFrame) -> pd.DataFrame:
    X = X.copy()

    # numeric: coerce to numeric and fill NaNs with median
    for c in NUM_COLS:
        if c in X.columns:
            X[c] = pd.to_numeric(X[c], errors="coerce")
            X[c] = X[c].fillna(X[c].median())

    # categoricals: fill + cast to string (CatBoost requirement)
    for c in CAT_COLS:
        if c in X.columns:
            X[c] = X[c].astype(str)
            # normalize typical "missing" tokens -> 'Unknown'
            X[c] = X[c].replace({"nan": "Unknown", "NaN": "Unknown", "None": "None"})
            X[c] = X[c].fillna("Unknown")

    return X


def cat_feature_indices(columns: pd.Index) -> list[int]:
    """Return integer indices for categorical features (by name) in the given column set."""
    return [columns.get_loc(c) for c in CAT_COLS if c in columns]


# ---------------------------------------------------------------------
# 3) Threshold tuning
# ---------------------------------------------------------------------
def best_threshold_f1(y_true: np.ndarray, proba_pos: np.ndarray) -> float:
    ts = np.linspace(0.0, 1.0, 101)
    scores = [f1_score(y_true, (proba_pos >= t).astype(int), average="macro") for t in ts]
    return float(ts[int(np.argmax(scores))])


# ---------------------------------------------------------------------
# 4) Train + evaluate + save
# ---------------------------------------------------------------------
def main() -> None:
    print(f"📂 Loading data: {DATA_PATH}")
    df = load_data(DATA_PATH)

    X = df[FEATURES].copy()
    y = make_binary_target(df)
    X = preprocess_X(X)

    print(f"🧾 Rows: {len(X):,} | Features: {len(FEATURES)}")
    print("🔎 Preview (top 3 rows, transposed):")
    print(X.head(3).T, "\n")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    cat_idx = cat_feature_indices(X.columns)

    train_pool = Pool(X_train, y_train, cat_features=cat_idx)
    valid_pool = Pool(X_test,  y_test,  cat_features=cat_idx)

    model = CatBoostClassifier(
        iterations=800,
        learning_rate=0.05,
        depth=6,
        l2_leaf_reg=10,
        loss_function="Logloss",
        eval_metric="F1",         # macro by default for binary in CB
        random_seed=42,
        verbose=100,
        early_stopping_rounds=50,
    )

    print("🚀 Training CatBoost …")
    model.fit(train_pool, eval_set=valid_pool, use_best_model=True)

    # Probabilities for positive class (index 1)
    y_proba = model.predict_proba(valid_pool)[:, 1]
    t = best_threshold_f1(y_test.values, y_proba)
    y_pred = (y_proba >= t).astype(int)

    print(f"\n🎯 Best threshold (F1_macro): {t:.2f}\n")
    print("📊 Classification report:")
    print(classification_report(y_test, y_pred, target_names=["No condition", "Condition"]))
    print("🧮 Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Save artifacts
    print(f"\n💾 Saving model (.cbm)     → {CBM_PATH}")
    model.save_model(CBM_PATH)

    print(f"💾 Saving model (pickle)    → {PKL_PATH}")
    with open(PKL_PATH, "wb") as f:
        pickle.dump(model, f)

    print(f"💾 Saving feature order     → {FEATURE_JSON}")
    with open(FEATURE_JSON, "w") as f:
        json.dump(FEATURES, f)

    print(f"💾 Saving tuned threshold   → {THRESH_JSON}")
    with open(THRESH_JSON, "w") as f:
        json.dump({"best_threshold": t}, f)

    print("\n✅ Training complete.")


if __name__ == "__main__":
    main()

 