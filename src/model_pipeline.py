# There are several components in this file: buiding blocks for prediction pages, from isha model pipeline
# Reusable mappings for categorical features
# An encoder to transform UI input into the model’s schema
# A cached CatBoost model loader (supports .cbm or .pkl)
# Convenience helpers to predict probability and label with a threshold
#A single pipeline function can call from prediction page

# src/model_pipeline.py
from __future__ import annotations
import os, json, pickle
from typing import Dict, Any, Optional, List
import pandas as pd
from catboost import CatBoostClassifier  # type: ignore

# ---------- Paths ----------
MODEL_DIR     = "models/catboost"
CBM_PATH      = os.path.join(MODEL_DIR, "model.cbm")
PKL_PATH      = os.path.join(MODEL_DIR, "model.pkl")
FEATURE_JSON  = os.path.join(MODEL_DIR, "feature_order.json")
THRESH_JSON   = os.path.join(MODEL_DIR, "threshold.json")

# ---------- The 10 features your model was trained on ----------
# (from your screenshot)
TRAIN_FEATURES: List[str] = [
    "Age",
    "Years_of_Experience",
    "Hours_Worked_Per_Week",
    "Number_of_Virtual_Meetings",
    "Stress_Level",
    "Productivity_Change",
    "Social_Isolation_Rating",
    "Company_Support_for_Remote_Work",
    "Physical_Activity",
    "Sleep_Quality",
]

# Which are numeric vs. categorical-for-this-model
NUMERIC_COLS = {
    "Age",
    "Years_of_Experience",
    "Hours_Worked_Per_Week",
    "Number_of_Virtual_Meetings",
    "Social_Isolation_Rating",
    "Company_Support_for_Remote_Work",
}
CATEGORICAL_COLS = {
    "Stress_Level",
    "Productivity_Change",
    "Physical_Activity",
    "Sleep_Quality",
}

# Mappings your model expects (based on your notes)
CAT_MAPPINGS: Dict[str, Dict[Any, Any]] = {
    "Stress_Level": {"Low": 1, "Medium": 2, "High": 3},
    "Productivity_Change": {"Decrease": -1, "No Change": 0, "Increase": 1},
    "Physical_Activity": {"None": 0, "Weekly": 1, "Daily": 2},
    "Sleep_Quality": {"Poor": 0, "Average": 1, "Good": 2},
}

# ---------- Loaders ----------
def load_catboost_model() -> Optional[CatBoostClassifier]:
    if os.path.exists(CBM_PATH):
        m = CatBoostClassifier()
        m.load_model(CBM_PATH)
        return m
    if os.path.exists(PKL_PATH):
        with open(PKL_PATH, "rb") as f:
            return pickle.load(f)
    return None

def load_feature_order() -> Optional[List[str]]:
    if os.path.exists(FEATURE_JSON):
        with open(FEATURE_JSON, "r") as f:
            return json.load(f)
    return None

def load_best_threshold(default: float = 0.52) -> float:
    if os.path.exists(THRESH_JSON):
        with open(THRESH_JSON, "r") as f:
            return float(json.load(f).get("best_threshold", default))
    return default

# ---------- Encoding ----------
def encode_user_input(raw: Dict[str, Any], feature_order: Optional[List[str]] = None) -> pd.DataFrame:
    """Coerce UI inputs into the exact schema the model expects."""
    # 1) Start with only the features your model trained on
    row: Dict[str, Any] = {}

    for col in TRAIN_FEATURES:
        v = raw.get(col, None)

        if col in CAT_MAPPINGS:
            # map strings to numeric codes; fallback to None if not in mapping
            if v is None:
                row[col] = None
            else:
                row[col] = CAT_MAPPINGS[col].get(v, None)
        elif col in NUMERIC_COLS:
            # cast to float where possible
            try:
                row[col] = float(v)
            except Exception:
                row[col] = None
        else:
            # unseen column type: keep as-is
            row[col] = v

    df = pd.DataFrame([row])

    # 2) Align to feature order (from training) if available
    order = feature_order or TRAIN_FEATURES
    for col in order:
        if col not in df.columns:
            df[col] = None
    df = df[order]

    # 3) Safety: fill numeric NaNs with 0, categoricals with 'Unknown'
    for col in df.columns:
        if col in NUMERIC_COLS:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        else:
            # If model expects numeric for this col (e.g., mapped), still coerce
            if col in CAT_MAPPINGS:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
            else:
                df[col] = df[col].fillna("Unknown")

    return df

# ---------- Prediction helpers ----------
def predict_proba(model: CatBoostClassifier, input_df: pd.DataFrame) -> float:
    return float(model.predict_proba(input_df)[0][1])

def predict_label(proba: float, threshold: float) -> int:
    return int(proba >= threshold)
