from datetime import datetime
import geopandas as gpd
import os
import numpy as np
import pandas as pd
import pydeck as pdk
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st
import streamlit_antd_components as sac
from streamlit_pills import pills

from src.dashboard_insight import render_stress_donut
from src.dashboard_insight import render_consequences_from_data
from src.dashboard_insight import render_context_panel, render_progress_tracker

from src.model_pipeline import (
    load_catboost_model, load_feature_order, load_best_threshold,
    encode_user_input, predict_proba, predict_label)



st.set_page_config(layout='wide', initial_sidebar_state='expanded', page_title='MIND@WORK', page_icon='🏥')


# Remove extra padding from the top and bottom of the page
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 0rem;  /* Adjust this value as needed */
        padding-bottom: 2rem; /* Optionally reduce bottom padding too */
    }
    </style>
    """,
    unsafe_allow_html=True
)


# Create a tab to select the tool to use
tab = sac.tabs(
    items=['About Project', 'Prediction', 'Explanation', 'More Analysis'],
    index=0,
    align='start',
)

# ---------------------------------------------------------------------
# ---------About Project tab content ------------------------------------
# ---------------------------------------------------------------------
if tab == 'About Project':
    st.sidebar.caption(
        "Mind@Work is a prototype dashboard linking work conditions with employee mental health condition.\n"
        "⚠️ This tool offers insights for awareness and decision support, not for diagnosis or clinical use."
    )

    #Display the name of the tool
    st.markdown("""
    <h1 style="font-size: 48px; text-align: center; margin-bottom: 0em; margin-top: 0em; line-height: 1.0;">
        Mind@<span style="color: #1f77b4;">Work</span>
    </h1>
    <h3 style="font-size: 18px; text-align: center; margin-top: 0em;">
        A prototype dashboard for workplace mental health
    </h3>""", unsafe_allow_html=True)


    # Add some vertical space before the map/dropdown section
    st.markdown("<br><br>", unsafe_allow_html=True)
    left, right = st.columns([1, 3], gap="large")

   

    ###### Creating map and partnership list ######
    partners_df = pd.read_csv("/Users/huongle/Documents/GitHub/Mind_At_Work_Website/data/mind@work/company_lists/partners_sweden.csv")

    # Cities sorted for the selector
    cities = sorted(partners_df["city"].unique().tolist())

    # --- Layout: left narrow for controls, right wide for map ---
    left, right = st.columns([1, 2], gap="large")

    with left:
        st.markdown(
        """
        <h2 style="color:#0a3d62; font-size: 32px; font-weight: 700; margin-top: 1em; margin-bottom: 0.5em;">
            Where we’ve cooperated
        </h2>
        """,
        unsafe_allow_html=True
        )

        # Dropdown directly under the caption
        city = st.selectbox("Choose a city", options=cities, index=0)

        # List of partners
        sel = partners_df[partners_df["city"] == city]
        st.markdown(f"**Partners in {city}:**")
        if sel.empty:
            st.caption("No partners listed yet.")
        else:
            st.markdown("\n".join([f"- {row.company}" for row in sel.itertuples()]))

    with right:
        # Map view centered on Sweden
        view_state = pdk.ViewState(latitude=62.0, longitude=15.0, zoom=4.5, pitch=0)

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=partners_df,
            get_position='[lon, lat]',
            get_fill_color=[31, 119, 180, 200],  # blue pins
            get_line_color=[0, 0, 0],
            line_width_min_pixels=1,
            pickable=True,
            radius_min_pixels=6,
        )

        tooltip = {"text": "{company}\n{city}"}
        deck = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip, map_style="light")

        # Bigger map
        st.pydeck_chart(deck, use_container_width=True, height=600)

        
        
    ######## Project description ########
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
    """
    <h2 style="color:#0a3d62; font-size: 32px; font-weight: 700; margin-top: 1em; margin-bottom: 0.5em;">
        Why workplace mental health matters
    </h2>
    """,
    unsafe_allow_html=True
    )

    st.markdown(
        """
        According to the World Health Organization, **depression and anxiety** cause an estimated
        **12 billion lost workdays each year**, costing the global economy nearly **$1 trillion USD annually** [1].

        Our data confirms that **around 1 in 3 employees**
        report stress-related symptoms linked to their work environment.
        """
    )
    

    ### Showingx analysis chart.
    st.markdown(
    "#### Stress prevalence in workplaces data",
    unsafe_allow_html=True)

    render_stress_donut()  # uses the default DATA_PATH

    st.markdown(
    "#### How outcomes differ when stress is high (vs. low)",
    unsafe_allow_html=True)

    render_consequences_from_data(
    data_path="data/mind@work/mental heath dataset/Cleaned_remote_work.csv",   # adjust path if different
    stress_col="Stress_Level",                  # your column with Low/Medium/High
    max_features=5)

    st.markdown("<br><br>", unsafe_allow_html=True)

    #####What Mind@Work adds####
    st.markdown(
    """
    <h2 style="color:#0a3d62; font-size: 32px; font-weight: 700; margin-top: 1em; margin-bottom: 0.5em;">
    What Mind@Work adds
    </h2>
    """,unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Work conditions + outcomes**  \nConnects workload, control, support, and culture with employee metal health condition.")
    with c2:
        st.markdown("**ML + XAI**  \nUses machine learning with explainable outputs so leaders can see *why* risks appear.")
    with c3:
        st.markdown("**Decision support**  \nHighlights at-risk groups and actionable levers.")

    st.caption("Mind@Work is a research prototype intended for awareness and planning, **not** clinical use.")

    st.markdown("<br><br>", unsafe_allow_html=True)

    #Call to action
    
    st.markdown(
    """
    <h2 style="color:#0a3d62; font-size: 32px; font-weight: 700; margin-top: 1em; margin-bottom: 0.5em;">
    Interested in piloting Mind@Work?
    </h2>
    """,unsafe_allow_html=True)

    cta_col1, cta_col2 = st.columns([1, 3])
    with cta_col1:
        # If you're on Streamlit >= 1.25 you can use link_button; otherwise keep the markdown link below.
        try:
            st.link_button("Get in touch", "mailto:team@mindatwork.example?subject=Mind@Work%20pilot")
        except Exception:
            st.markdown("[👉 Get in touch](mailto:team@mindatwork.example?subject=Mind@Work%20pilot)")

    with cta_col2:
        st.markdown(
            "We’re looking for organizations to co-develop metrics, validate insights, and shape ethical use guidelines."
        )


    st.markdown("<br><hr>", unsafe_allow_html=True)  # separator line

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("© 2025 Mind@Work Project. All rights reserved.")

    with col2:
        st.markdown(
            """
            <div style="text-align: right; font-size: 13px; color: gray;">
                Built by the Mind@Work project team <br>
                in collaboration with Karolinska Institutet & Stockholm University.
            </div>
            """,
            unsafe_allow_html=True
    )
    
     # --- Put context + progress tracker in sidebar ---
    with st.sidebar:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)  # small spacer
        render_context_panel()
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        render_progress_tracker("data/mind@work/company_lists/partners_sweden.csv", current_country="Sweden")

        st.divider()
        



# ---------------------------------------------------------------------
# ---------Prediction tab content (from model_pipeline.py) ------------
# ---------------------------------------------------------------------
if tab == 'Prediction':
    st.sidebar.caption(
        "This tool uses predictive models to forecast how different work conditions "
        "may affect employee overall mental well-being. "
        "⚠️ Results are for awareness and learning only, not for diagnosis or clinical use."
    )
  #Display the name of the tool
    st.markdown(
    """
    <h2 style="color:#0a3d62; font-size: 48px; font-weight: 700; margin-top: 1em; margin-bottom: 0.5em;">
        Metal health prediction tool
    </h2>
    """,
    unsafe_allow_html=True
    )

    st.markdown(
        "<p style='color:#666'>Fill the fields below. The model estimates the probability of <b>Metal health condition</b> "
        "based on your inputs.</p>",
        unsafe_allow_html=True,
    )
  

    # --- Prediction tab content ---
    model = load_catboost_model()
    if model is None:
        st.warning("⚠️ No model found in `models/catboost`. Please add `model.cbm` or `model.pkl`.")
    else:
        feature_order = load_feature_order()
        tuned_t = load_best_threshold(default=0.52)

        with st.form("predict_form"):
            left, right = st.columns(2, gap="large")

            # LEFT: 5 categorical / manual inputs
            with left:
                age = st.number_input("Age", min_value=18, max_value=80, value=30, step=1)
                stress = st.selectbox("Stress Level", ["Low", "Medium", "High"])
                productivity = st.selectbox("Productivity Change", ["Decrease", "No Change", "Increase"])
                activity = st.selectbox("Physical Activity", ["None", "Weekly", "Daily"])
                sleep = st.selectbox("Sleep Quality", ["Poor", "Average", "Good"])

            # RIGHT: 5 sliders (numeric)
            with right:
                exp = st.slider("Years of Experience", 0, 40, 5)
                hours = st.slider("Hours Worked Per Week", 10, 80, 40)
                meetings = st.slider("Virtual Meetings / week", 0, 50, 5)
                isolation = st.slider("Social Isolation Rating (1–5)", 1, 5, 3)
                support = st.slider("Company Support for Remote Work (1–5)", 1, 5, 3)

                submitted = st.form_submit_button("Predict", use_container_width=True)
            

        if submitted:
            raw = {
                "Age": age,
                "Years_of_Experience": exp,
                "Hours_Worked_Per_Week": hours,
                "Number_of_Virtual_Meetings": meetings,
                "Stress_Level": stress,                  # "Low"/"Medium"/"High"  -> mapped
                "Productivity_Change": productivity,     # -> mapped
                "Social_Isolation_Rating": isolation,    # numeric (1-5)
                "Company_Support_for_Remote_Work": support,  # numeric (1-5)
                "Physical_Activity": activity,           # -> mapped
                "Sleep_Quality": sleep,                  # -> mapped
            }

            model = load_catboost_model()
            if model is None:
                st.warning("No model found in models/catboost/. Add model.cbm or model.pkl.")
            else:
                feature_order = load_feature_order()
                threshold = load_best_threshold(0.52)

                input_df = encode_user_input(raw, feature_order=feature_order)
                proba = predict_proba(model, input_df)
                label = predict_label(proba, threshold)

                st.metric("Probability of condition", f"{proba:.2%}")
                st.metric("Prediction", "In risk of having mental health problem" if label else "Not in risk",
                        help=f"Threshold = {threshold:.2f}")
                # 👉 Add explanation
                st.markdown(
                f"""
                <div style="background-color:#f8f9fa; border-left: 4px solid #6c757d; padding: 12px; border-radius: 4px; margin-top: 12px;">
                    <b>ℹ️ How to interpret this:</b><br>
                    The probability <b>{proba:.2%}</b> means that, given the information you entered,
                    the model estimates this individual is in risk of experiencing a 
                    <b>mental health condition</b> (e.g., anxiety, burnout, or depression).<br><br>
                """,
                unsafe_allow_html=True
            )


#---------------------------------------------------------------------
# ---------Explanation tab content ------------------------------------
#---------------------------------------------------------------------
if tab == 'Explanation':
    st.sidebar.caption(
        "This section explains how the prediction models work, showing which factors "
        "influence outcomes and clarifying the tool’s data sources and limitations."
    )
    

#---------------------------------------------------------------------
# ---------More Analysis tab content ------------------------------------
#---------------------------------------------------------------------
if tab == 'More Analysis':
    st.sidebar.caption(
        "This section provides descriptive analysis with charts and summaries, "
        "highlighting patterns between work conditions and mental health."
    )

    from src.analysis import render_more_analysis
        
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = os.path.join(
    APP_DIR,
    "data",
    "mind@work",
    "mental heath dataset",  # <- your folder name, even with the space/typo
    "Cleaned_remote_work.csv")

    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH = os.path.join(
        APP_DIR,
        "data",
        "mind@work",
        "mental heath dataset",  # even with the space/typo
        "Cleaned_remote_work.csv"
    )

    render_more_analysis(data_path=DATA_PATH, target_col="Stress_Level")