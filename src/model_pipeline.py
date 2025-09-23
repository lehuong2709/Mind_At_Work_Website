# There are several components in this file: buiding blocks for prediction pages, from isha model pipeline
# Reusable mappings for categorical features
# An encoder to transform UI input into the model’s schema
# A cached CatBoost model loader (supports .cbm or .pkl)
# Convenience helpers to predict probability and label with a threshold
#A single pipeline function can call from prediction page


"""
Model pipeline: input encoding + model loading + prediction helpers.

Usage (from pages/prediction.py):
---------------------------------
from src.model_pipeline import (
    load_catboost_model, encode_user_input,
    predict_proba_high, predict_label, run_pipeline
)

model = load_catboost_model("models/catboost_model.cbm", "models/catboost_model.pkl")
input_df = encode_user_input(raw_input_dict)  # dict built from Streamlit form
proba = predict_proba_high(model, input_df)
label = predict_label(proba, threshold=0.52)
"""

from __future__ import annotations
import os
import pickle
from typing import Dict, Any, Optional
import pandas as pd

# Streamlit cache is handy to avoid reloading model on every rerun.
try:
    import streamlit as st
    _cache_resource = st.cache_resource
except Exception:
    # Fallback if not running inside Streamlit (e.g., unit tests)
    def _cache_resource(func):
        return func

# CatBoost is the model type used
from catboost import CatBoostClassifier  # type: ignore


# ------------------------------------------------------------------------------
# 1) FEATURE MAPPINGS — keep these consistent with what you used at training time
# ------------------------------------------------------------------------------

# Map categorical strings to numeric codes (or keep as strings if you trained that way)
_MAPPINGS: Dict[str, Dict[Any, Any]] = {
    "Sleep_Quality": {"Poor": 0, "Average": 1, "Good": 2},
    "Physical_Activity": {"None": 0, "Weekly": 1, "Daily": 2},
    "Productivity_Change": {"Decrease": -1, "No Change": 0, "Increase": 1},
    "Satisfaction_with_Remote_Work": {"Unsatisfied": 1, "Neutral": 2, "Satisfied": 3},
    "Work_Life_Balance_Rating": {"Poor": 1, "Average": 2, "Good": 3, "Excellent": 4},

    # If you trained with these, uncomment & keep consistent with training:
    # "Remote_Frequency": {"Never": 0, "Occasional": 1, "Hybrid": 2, "Fully remote": 3},
    # "Company_Size": {"Small": 0, "Medium": 1, "Large": 2},
}

# Numeric columns that pass through as-is
_NUMERIC_PASSTHRU = [
    "Age",
    "Years_of_Experience",
    "Hours_Worked_Per_Week",
    "Number_of_Virtual_Meetings",
    "Social_Isolation_Rating",
    # Add any other numeric features you trained on
]

# Optional: fix a final feature order if your model expects strict column ordering
# Leave empty to keep DataFrame natural order.
_FEATURE_ORDER: Optional[list[str]] = None


# ------------------------------------------------------------------------------
# 2) ENCODER — converts raw inputs to a one-row DataFrame that matches training
# ------------------------------------------------------------------------------

def encode_user_input(raw_input: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert raw UI inputs to a single-row DataFrame matching the training-time schema.
    - Applies categorical mappings in _MAPPINGS
    - Passes through numeric features listed in _NUMERIC_PASSTHRU
    - Leaves other values as-is (CatBoost can handle string categoricals)

    IMPORTANT: Do NOT include the target (e.g., 'Stress_Level') in raw_input.
    """
    row: Dict[str, Any] = {}

    for k, v in raw_input.items():
        if k in _MAPPINGS:
            row[k] = _MAPPINGS[k].get(v, None)
        elif k in _NUMERIC_PASSTHRU:
            row[k] = v
        else:
            # If you trained CatBoost with this as categorical, leaving it as str is fine.
            # If you one-hot encoded it during training outside CatBoost, mirror that here.
            row[k] = v

    df = pd.DataFrame([row])

    # Enforce a specific column order if defined
    if _FEATURE_ORDER is not None:
        # Add any missing columns as NaN, keep extra columns too (CatBoost ignores order if trained with same names)
        for col in _FEATURE_ORDER:
            if col not in df.columns:
                df[col] = pd.NA
        df = df[_FEATURE_ORDER]

    return df


# ------------------------------------------------------------------------------
# 3) MODEL LOADER — cached load from .cbm (preferred) or .pkl (fallback)
# ------------------------------------------------------------------------------

@_cache_resource
def load_catboost_model(cbm_path: Optional[str] = None,
                        pkl_path: Optional[str] = None) -> Optional[CatBoostClassifier]:
    """
    Load a CatBoost model (prefer .cbm; fallback .pkl). Returns None if files not found.

    Args:
        cbm_path: path to CatBoost .cbm file saved with model.save_model(...)
        pkl_path: path to pickle .pkl file

    Returns:
        CatBoostClassifier or None
    """
    model: Optional[CatBoostClassifier] = None

    if cbm_path and os.path.exists(cbm_path):
        model = CatBoostClassifier()
        model.load_model(cbm_path)
        return model

    if pkl_path and os.path.exists(pkl_path):
        with open(pkl_path, "rb") as f:
            model = pickle.load(f)
        return model

    return None


# ------------------------------------------------------------------------------
# 4) PREDICTION HELPERS — probability + label with threshold
# ------------------------------------------------------------------------------

def predict_proba_high(model: CatBoostClassifier, input_df: pd.DataFrame) -> float:
    """
    Returns the probability of the 'High' class (assumes positive class at index 1).
    """
    proba = model.predict_proba(input_df)[0][1]
    return float(proba)


def predict_label(proba_high: float, threshold: float = 0.5) -> int:
    """
    Convert probability to binary label given a threshold.
    1 = High stress, 0 = not High stress.
    """
    return int(proba_high >= threshold)


def run_pipeline(model: CatBoostClassifier,
                 raw_input: Dict[str, Any],
                 threshold: float = 0.5) -> Dict[str, Any]:
    """
    Convenience function: encode -> predict_proba -> label
    Returns a dict with 'input_df', 'proba_high', 'label'
    """
    input_df = encode_user_input(raw_input)
    proba = predict_proba_high(model, input_df)
    label = predict_label(proba, threshold)
    return {
        "input_df": input_df,
        "proba_high": proba,
        "label": label,
    }
