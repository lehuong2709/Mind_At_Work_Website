
import numpy as np
import pandas as pd
import streamlit as st
import streamlit_antd_components as sac
from streamlit_pills import pills
from src.model_pipeline import load_catboost_model, run_pipeline


st.set_page_config(layout='wide', initial_sidebar_state='expanded', page_title='M@W Explaination', page_icon='🏥')


# Load model once
model = load_catboost_model(
    cbm_path="models/catboost_model.cbm",
    pkl_path="models/catboost_model.pkl"
)

st.title("Stress Prediction")

# Example form
with st.form("prediction_form"):
    age = st.number_input("Age", 18, 65, 30)
    hours = st.slider("Hours Worked Per Week", 20, 80, 40)
    sleep = st.selectbox("Sleep Quality", ["Poor", "Average", "Good"])
    activity = st.selectbox("Physical Activity", ["None", "Weekly", "Daily"])
    submit = st.form_submit_button("Predict")

if submit and model:
    raw_input = {
        "Age": age,
        "Hours_Worked_Per_Week": hours,
        "Sleep_Quality": sleep,
        "Physical_Activity": activity,
    }
    result = run_pipeline(model, raw_input, threshold=0.52)
    st.metric("Probability of High Stress", f"{result['proba_high']:.2%}")
    st.write("Predicted Label:", "High Stress" if result["label"] else "Not High")