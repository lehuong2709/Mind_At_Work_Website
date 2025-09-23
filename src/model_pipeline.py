# There are several components in this file: buiding blocks for prediction pages, from isha model pipeline
# Reusable mappings for categorical features
# An encoder to transform UI input into the model’s schema
# A cached CatBoost model loader (supports .cbm or .pkl)
# Convenience helpers to predict probability and label with a threshold
#A single pipeline function can call from prediction page


"""
Model pipeline: load model + encode inputs + predict.

Typical usage (e.g., in app.py under the 'Prediction' tab):
-----------------------------------------------------------
from src.model_pipeline import (
    load_catboost_model, load_feature_order, load_best_threshold,
    encode_user_input, predict_proba_positive, predict_label, run_pipeline
)

model = load_catboost_model()  # looks in models/catboost by default
feat_order = load_feature_order()          # list[str] or None
best_t = load_best_threshold(default=0.52) # float

raw = {...}                                # values from Streamlit form
result = run_pipeline(model, raw, feature_order=feat_order, threshold=best_t)

st.metric("Probability", f"{result['proba']:.2%}")
st.metric("Predicted", "Condition" if result["label"] else "No condition")
st.dataframe(result["input_df"])
"""

from __future__ import annotations
import os
import json
import pickle
from typing import Any, Dict, List, Optional

import pandas as pd

# Optional Streamlit cache (silently no-op if not in Streamlit)
try:
    import streamlit as st
    _cache_resource = st.cache_resource
except Exception:  # pragma: no cover
    def _cache_resource(func):  # type: ignore
        return func

# CatBoost
from catboost import CatBoostClassifier  # type: ignore


# ---------------------------------------------------------------------
# Defaults - aligned with your notebook save locations
# ---------------------------------------------------------------------
DEFAULT_DIR = os.path.join("models", "catboost")
DEFAULT_CBM = os.path.join(DEFAULT_DIR, "model.cbm")
DEFAULT_PKL = os.path.join(DEFAULT_DIR, "model.pkl")
FEATURE_JSON = os.path.join(DEFAULT_DIR, "feature_order.json")
THRESH_JSON  = os.path.join(DEFAULT_DIR, "threshold.json")

# If you know some features are numeric, list them here so we cast safely.
NUMERIC_FEATURES = {
    "Age",
    "Years_of_Experience",
    "Hours_Worked_Per_Week",
    "Number_of_Virtual_Meetings",
    "Social_Isolation_Rating",
}


# ---------------------------------------------------------------------
# Artifact loaders
# ---------------------------------------------------------------------
def load_feature_order(path: str = FEATURE_JSON) -> Optional[List[str]]:
    """Load feature order from JSON if present; otherwise return None."""
    if os.path.exists(path):
        with open(path, "r") as f:
            feats = json.load(f)
        if isinstance(feats, list) and all(isinstance(x, str) for x in feats):
            return feats
    return None


def load_best_threshold(path: str = THRESH_JSON, default: float = 0.5) -> float:
    """Load tuned threshold from JSON if present; otherwise return default."""
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            val = float(data.get("best_threshold", default))
            return val
        except Exception:
            return default
    return default


@_cache_resource
def load_catboost_model(
    cbm_path: Optional[str] = DEFAULT_CBM,
    pkl_path: Optional[str] = DEFAULT_PKL,
) -> Optional[CatBoostClassifier]:
    """
    Load CatBoost model (prefer .cbm, fallback to .pkl).
    Returns None if neither exists.
    """
    # Prefer .cbm (native)
    if cbm_path and os.path.exists(cbm_path):
        model = CatBoostClassifier()
        model.load_model(cbm_path)
        return model

    # Fallback .pkl (pickle)
    if pkl_path and os.path.exists(pkl_path):
        with open(pkl_path, "rb") as f:
            model = pickle.load(f)
        return model

    return None


# ---------------------------------------------------------------------
# Encoding helpers
# ---------------------------------------------------------------------
def _coerce_types(row: Dict[str, Any]) -> Dict[str, Any]:
    """Cast known numeric features to numbers if they arrive as strings."""
    fixed: Dict[str, Any] = {}
    for k, v in row.items():
        if k in NUMERIC_FEATURES and v is not None and v != "":
            try:
                # int(...) is fine; if your model saw floats, use float(v)
                fixed[k] = int(v)
            except Exception:
                try:
                    fixed[k] = float(v)
                except Exception:
                    fixed[k] = v  # leave as-is if coercion fails
        else:
            fixed[k] = v
    return fixed

_NUMERIC_PASSTHRU = [
    "Age",
    "Years_of_Experience",
    "Hours_Worked_Per_Week",
    "Number_of_Virtual_Meetings",
    "Social_Isolation_Rating",
]

def encode_user_input(raw_input: Dict[str, Any],
                      feature_order: Optional[list[str]] = None) -> pd.DataFrame:
    """
    Keep categoricals as strings (CatBoost can handle them); ensure numerics are numeric.
    When aligning to feature_order, fill missing numeric cols with 0 and missing
    categoricals with 'Unknown' to avoid <NA> reaching CatBoost.
    """
    row: Dict[str, Any] = {}

    # 1) Build row: keep strings for categoricals, cast numerics where possible
    for k, v in raw_input.items():
        if k in _NUMERIC_PASSTHRU:
            try:
                row[k] = float(v)
            except Exception:
                row[k] = v  # we'll coerce below and fillna
        else:
            row[k] = v

    df = pd.DataFrame([row])

    # 2) If a feature_order is supplied, ensure all expected columns exist
    if feature_order:
        for col in feature_order:
            if col not in df.columns:
                if col in _NUMERIC_PASSTHRU:
                    df[col] = 0.0         # safe numeric default
                else:
                    df[col] = "Unknown"   # safe categorical default
        # keep only expected order
        df = df[[c for c in feature_order]]

    # 3) Final coercion for numeric columns + fillna
    for col in _NUMERIC_PASSTHRU:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df



# ---------------------------------------------------------------------
# Predict helpers
# ---------------------------------------------------------------------
def predict_proba_positive(model: CatBoostClassifier, input_df: pd.DataFrame) -> float:
    """Return probability of the positive class (index 1)."""
    proba = model.predict_proba(input_df)[0][1]
    return float(proba)


def predict_label(proba_positive: float, threshold: float = 0.5) -> int:
    """Convert probability to 0/1 by threshold."""
    return int(proba_positive >= threshold)


def run_pipeline(
    model: CatBoostClassifier,
    raw_input: Dict[str, Any],
    feature_order: Optional[List[str]] = None,
    threshold: Optional[float] = None,
    default_threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Convenience: encode -> proba -> label.
    If `threshold` is None, tries to load from THRESH_JSON; otherwise uses default_threshold.
    """
    if threshold is None:
        threshold = load_best_threshold(default=default_threshold)

    input_df = encode_user_input(raw_input, feature_order=feature_order)
    proba = predict_proba_positive(model, input_df)
    label = predict_label(proba, threshold)

    return {
        "input_df": input_df,
        "proba": proba,
        "label": label,
        "threshold": float(threshold),
    }
