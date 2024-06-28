from datetime import datetime
import geopandas as gpd
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit_antd_components as sac
from streamlit_extras.switch_page_button import switch_page
from st_pages import Page, add_page_title, show_pages

from src.usa.constants import state_names, racial_label_dict, populous_states
from src.usa.states import USAState
from src.usa.facilities import (
    Pharmacies, CVS, Walgreens, Walmart, UrgentCare, Hospitals, NursingHomes,
    ChildCare, PrivateSchools, FDICInsuredBanks, DHL, UPS, FedEx, PharmaciesTop3)
from src.usa.utils import racial_labels, colors, compute_medical_deserts
from src.usa.plot_utils import plot_state, plot_stacked_bar, plot_existing_facilities, plot_medical_deserts, plot_blockgroups, plot_voronoi_cells


def get_base_url(page):
    if st.secrets.get("IS_DEPLOYED", False):
        # If deployed, use the Streamlit Cloud URL
        if page == 'suggesting-new-facilities':
            return "https://usa-medical-deserts.streamlit.app/suggesting-new-facilities"
        elif page == 'visualizing-medical-deserts':
            return "https://usa-medical-deserts.streamlit.app/"
        elif page == "explainer":
            return "https://usa-medical-deserts.streamlit.app/Explainer"
    else:
        # If local, use localhost
        if page == "suggesting-new-facilities":
            return "https://usa-medical-deserts.streamlit.app/suggesting-new-facilities"
        elif page == "visualizing-medical-deserts":
            return "http://localhost:8501/"
        elif page == "explainer":
            return "http://localhost:8501/explainer"


st.set_page_config(layout='wide', initial_sidebar_state='expanded')

show_pages(
    [
        Page("medical-facility-deserts.py", "Visualizing facility deserts", None),
        Page("pages/suggesting-new-facilities.py", "Suggesting new facilities", None),
        Page("pages/explainer.py", "Explainer", None),
    ]
)

st.sidebar.caption('This tool aims to identify facility deserts in the US – poorer areas with low '
                   'access to various critical facilities such as pharmacies, hospitals, and schools.'
                   )


def get_facility_from_facility_name(facilities, facility_name):
    for facility in facilities:
        if facility.display_name == facility_name:
            return facility


def state_of_the_day(state_names):
    day_of_year = datetime.now().timetuple().tm_yday
    state_of_the_day = state_names[day_of_year % len(state_names)]
    return state_of_the_day


facilities = [PharmaciesTop3, UrgentCare, Hospitals, NursingHomes, PrivateSchools, FDICInsuredBanks, ChildCare]
facility_display_names = [facility.display_name for facility in facilities]


with st.sidebar:
    facility_display_name = st.selectbox('Choose a facility', facility_display_names)
    facility = get_facility_from_facility_name(facilities, facility_display_name)
    state_of_the_day = state_of_the_day(populous_states)
    state_name = st.selectbox('Choose a US state', options=state_names, index=state_names.index(state_of_the_day))

State = USAState(state_name)
state_fips = State.fips
state_abbr = State.abbreviation

st.markdown("""
    <h1 style="font-size: 40px; text-align: center; margin-bottom: 0em; margin-top: 0em; line-height: 1.0;">
        """ + facility.type.capitalize() + """ deserts in
        <span style="color: #c41636">
            """ + state_name + """
        </span>
    </h1>
    <h3 style="font-size: 18px; text-align: center; margin-top: 0em;">
        Based on distances to <span style="color: #c41636">""" + facility.display_name + """</span>
    </h3>
    <br>
    """, unsafe_allow_html=True)

st.markdown(facility.get_message(), unsafe_allow_html=True)

with st.sidebar:
    with st.container(border=True):
        poverty_threshold = st.slider(r'Choose poverty threshold $p$%', min_value=0, max_value=100, value=20, step=5, key='poverty_threshold')

    with st.container(border=True):
        st.write('Choose distance threshold $n$ miles')
        col_side1, col_side2 = st.columns(2)
        urban_distance_threshold = col_side1.slider(r'For urban areas', min_value=0.0, max_value=15.0, value=2.0, step=0.5, format='%.1f')
        rural_distance_threshold = col_side2.slider(r'For rural areas', min_value=0.0, max_value=30.0, value=8.0, step=1.0, format='%.1f')

col1, col2 = st.columns([3, 2], gap='medium')

with col2:
    with st.expander('Figure options'):
        show_deserts = st.checkbox('Show ' + facility.type + ' deserts', value=True)
        show_facility_locations = st.checkbox('Show ' + facility.display_name.lower(), value=False)
        show_voronoi_cells = st.checkbox('''Show [voronoi](https://en.wikipedia.org/wiki/Voronoi_diagram) cells''', value=False)


with col1:
    census_df = State.get_census_data(level='blockgroup')

    fig = go.Figure()
    fig, bounds = plot_state(fig, State)

    distance_label = facility.distance_label
    desert_df = compute_medical_deserts(census_df, poverty_threshold, urban_distance_threshold, rural_distance_threshold, distance_label)
    if show_deserts:
        fig = plot_blockgroups(fig, desert_df)

    if show_facility_locations:
        if facility.name == 'top_3_pharmacy_chains':
            for pharmacy_chain in [CVS, Walgreens, Walmart]:
                fig = plot_existing_facilities(fig, pharmacy_chain, bounds)
        else:
            fig = plot_existing_facilities(fig, facility, bounds)

    if show_voronoi_cells:
        fig = plot_voronoi_cells(fig, facility, state_fips)

    config = {
        'modeBarButtonsToRemove': ['zoomOut', 'select2d'],
        'staticPlot': False,
        'scrollZoom': True,
        'toImageButtonOptions': {
            'format': 'png',
            'scale': 1.5,
            'filename': facility.type + '_deserts_' + state_abbr + '_' + facility.name + '.png',
        }
    }

    st.plotly_chart(fig, use_container_width=True, config=config)


with col2:
    st.caption(f'**Figure**: Census blockgroups classified as ' + facility.type + ' deserts in ' + state_name
               + '. Colored by racial/ethnic majority.')

    legend_labels = {
        'white_alone': 'Majority White',
        'black_alone': 'Majority Black',
        'aian_alone': 'Majority AIAN',
        'asian_alone': 'Majority Asian',
        'nhopi_alone': 'Majority NHOPI',
        'hispanic': 'Majority Hispanic',
        'other': 'Other',
    }

    demographics_all = {racial_label: census_df[census_df['racial_majority'] == racial_label].shape[0] for racial_label in racial_labels}
    demographics_all = {k: demographics_all[k] for k in demographics_all.keys() if demographics_all[k] > 0}
    n_blockgroups = len(census_df)

    demographics_deserts = {racial_label: desert_df[desert_df['racial_majority'] == racial_label].shape[0] for racial_label in racial_labels}
    demographics_deserts = {k: demographics_deserts[k] for k in demographics_deserts.keys() if demographics_deserts[k] > 0}

    fig1, fig2 = plot_stacked_bar(demographics_all), plot_stacked_bar(demographics_deserts)

    st.markdown('''<center>''' + state_name + ''' has <b>''' + str(len(census_df)) + '''</b> blockgroups</center>''', unsafe_allow_html=True)
    st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
    st.markdown('''<center><b>''' + str(len(desert_df)) + '''</b> are ''' + facility.type + ''' deserts</center>''', unsafe_allow_html=True)
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

    if len(desert_df) > 0:
        for racial_label in racial_labels:
            if racial_label in demographics_all and racial_label in demographics_deserts and racial_label != 'other':
                fraction_of_all_blockgroups = demographics_all[racial_label]/n_blockgroups
                fraction_of_medical_deserts = demographics_deserts[racial_label]/len(desert_df)

                four_times_deserts = fraction_of_medical_deserts> 4 * fraction_of_all_blockgroups
                over_ten_percent_difference = fraction_of_medical_deserts - fraction_of_all_blockgroups > 0.1
                over_five_deserts = fraction_of_medical_deserts * len(desert_df) >= 5

                if over_five_deserts and (four_times_deserts or over_ten_percent_difference):
                    overall_percent_str = str(round(fraction_of_all_blockgroups * 100, 2))
                    desert_percent_str = str(round(fraction_of_medical_deserts * 100, 2))
                    st.write(legend_labels[racial_label] + ' blockgroups may be disproportionately affected by '
                             + facility.type + ' deserts in ' + state_name + ': they make up :red[' + desert_percent_str +
                             '%] of ' + facility.type + ' deserts in ' + state_name + ' while being only :blue[' +
                             overall_percent_str + '%] of all blockgroups.')

    url = get_base_url('suggesting-new-facilities')
    st.markdown(
        '''
        We also created a [tool](''' + url + ''') that suggests locations for new facilities to 
        reduce the impact of ''' + facility.type + ''' deserts.'''.format(facility.type), unsafe_allow_html=True
    )

with st.sidebar:
    move_to_explanation = st.button('Explanation', use_container_width=True)
    if move_to_explanation:
        switch_page("explainer")

    move_to_suggesting_facilities = st.button('Suggesting new facilities', use_container_width=True)
    if move_to_suggesting_facilities:
        switch_page("suggesting-new-facilities")


st.sidebar.caption('Created by Swati Gupta, [Jai Moondra](https://jaimoondra.github.io/), Mohit Singh.\n'
                   'Based on our [paper](https://arxiv.org/abs/2211.14873) on fairness in facility location.\n'
                   'Submit any feedback to [jmoondra3@gatech.edu](mailto:jmoondra3@gatech.edu).\n')
