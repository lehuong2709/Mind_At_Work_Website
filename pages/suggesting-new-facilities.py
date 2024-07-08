from ast import literal_eval
from datetime import datetime
import geopandas as gpd
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit_antd_components as sac
from streamlit_extras.switch_page_button import switch_page
from st_pages import Page, add_page_title, show_pages

from src.constants import DEFAULT_POVERTY_THRESHOLD, DEFAULT_RURAL_DISTANCE_THRESHOLD, DEFAULT_URBAN_DISTANCE_THRESHOLD
from src.usa.constants import state_names, racial_label_dict, populous_states
from src.usa.states import USAState
from src.usa.facilities import (
    CVS, Walgreens, Walmart, UrgentCare, Hospitals, NursingHomes,
    ChildCare, PrivateSchools, FDICInsuredBanks, DHL, UPS, FedEx, PharmaciesTop3)
from src.usa.utils import racial_labels, colors, compute_medical_deserts, get_demographic_data
from src.usa.plot_utils import plot_state, plot_stacked_bar, plot_existing_facilities, plot_medical_deserts, plot_blockgroups, plot_voronoi_cells, plot_new_facilities


def get_page_url(page_name):
    is_deployed = st.secrets.get('IS_DEPLOYED')
    if is_deployed:
        return 'https://usa-medical-deserts.streamlit.app/' + page_name
    else:
        return 'http://localhost:8501/' + page_name


st.set_page_config(layout='wide', initial_sidebar_state='expanded', page_title='suggesting-new-facilities')


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


def facility_names(facility):
    if facility.name == 'top_3_pharmacy_chains':
        return 'pharmacies'
    else:
        return facility.display_name.lower()

st.markdown("""
    <h1 style="font-size: 40px; text-align: center; margin-bottom: 0em; margin-top: 0em; line-height: 1.0;">
         Suggesting new """ + facility_names(facility) + """ in
        <span style="color: #c41636">
            """ + state_name + """
        </span>
    </h1>
    <br>
    """, unsafe_allow_html=True)

census_df = State.get_census_data(level='blockgroup')


col1, col2 = st.columns([2, 1])

with col1:
    url = get_page_url('')
    st.markdown('''
        This tool suggests locations of new facilities to reduce the number of [medical deserts](''' + url + '''). 
        We present three solutions based on three different optimization models; each solution suggests up to 100 new facilities.
        As before, you can also choose the poverty and distance thresholds that define a medical desert in the sidebar.
        ''', unsafe_allow_html=True
    )

with col2:
    with st.container(border=False):
        k = st.select_slider(label='Select the number of new facilities', options=[0, 5, 10, 25, 50, 100], value=25)


with st.sidebar:
    with st.container(border=True):
        poverty_threshold = st.slider(r'Choose poverty threshold $p$%', min_value=0, max_value=100, value=DEFAULT_POVERTY_THRESHOLD, step=5, key='poverty_threshold')

    with st.container(border=True):
        st.write('Choose distance threshold $n$ miles')
        col_side1, col_side2 = st.columns(2)
        urban_distance_threshold = col_side1.slider(r'For urban areas', min_value=0.0, max_value=15.0, value=DEFAULT_URBAN_DISTANCE_THRESHOLD, step=0.5, format='%.1f')
        rural_distance_threshold = col_side2.slider(r'For rural areas', min_value=0.0, max_value=30.0, value=DEFAULT_RURAL_DISTANCE_THRESHOLD, step=1.0, format='%.1f')

    with st.expander('Figure options', expanded=True):
        show_deserts = st.checkbox(label='Show medical deserts', value=False)
        show_existing_facilities = st.checkbox(label='Show existing facilities', value=True)
        show_new_facilities = st.checkbox(label='Show new facilities', value=True)

def norm_column(norm, census_df, k):
    solution = {'1': '1', '2': '2', 'inf': '3'}
    st.markdown('''<h4 style='text-align: center; color: black;'>Solution ''' + solution[norm] + '''</h4>''', unsafe_allow_html=True)

    old_distance_label = facility.distance_label
    new_distance_label = facility.distance_label + '_p_' + norm + '_k_' + str(k)
    if k == 0:
        new_distance_label = old_distance_label

    original_desert_df = compute_medical_deserts(census_df, poverty_threshold, urban_distance_threshold, rural_distance_threshold, old_distance_label)
    original_demographic_data = get_demographic_data(original_desert_df, racial_labels)
    original_medical_deserts = str(sum(original_demographic_data.values()))
    st.markdown('''<center>Original medical deserts (''' + original_medical_deserts + ''')</center>''', unsafe_allow_html=True)
    fig_original = plot_stacked_bar(original_demographic_data)
    st.plotly_chart(fig_original, use_container_width=True, config={'displayModeBar': False})

    new_desert_df = compute_medical_deserts(census_df, poverty_threshold, urban_distance_threshold, rural_distance_threshold, new_distance_label)
    new_demographic_data = get_demographic_data(new_desert_df, racial_labels)
    new_medical_deserts = str(sum(new_demographic_data.values()))
    st.markdown('''<center>Remaining medical deserts (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
    new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
    fig_new = plot_stacked_bar(new_demographic_data)
    st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})

    new_facilities = pd.read_csv('data/usa/new_facilities/' + facility.name + '/new_facilities_' + norm + '.csv', index_col=0)['100'].apply(literal_eval)
    new_facilities = new_facilities[state_name][:k]

    fig = go.Figure()
    fig, bounds = plot_state(fig, State)
    if show_deserts:
        difference_df = original_desert_df[~original_desert_df.index.isin(new_desert_df.index)]
        fig = plot_blockgroups(fig, difference_df, color='lightgrey')
        fig = plot_blockgroups(fig, new_desert_df)
        # fig = plot_medical_deserts(fig, census_df, new_distance_label, old_distance_label, poverty_threshold, urban_distance_threshold, rural_distance_threshold)
    if show_existing_facilities:
        fig = plot_existing_facilities(fig, facility, bounds)
    if show_new_facilities:
        fig = plot_new_facilities(fig, new_facilities[:k], census_df, name='Suggested Facilities')

    st.plotly_chart(fig, use_container_width=True)


col_1, col_2, col_inf = st.columns([1, 1, 1])


with col_1:
    norm_column('1', census_df, k=k)

with col_2:
    norm_column('2', census_df, k=k)

with col_inf:
    norm_column('inf', census_df, k=k)


with st.sidebar:
    move_to_explanation = st.button('Explanation', use_container_width=True)
    if move_to_explanation:
        st.switch_page("pages/explainer.py")

    move_to_medical_deserts = st.button('Visualizing facility deserts', use_container_width=True)
    if move_to_medical_deserts:
        st.switch_page("medical-facility-deserts.py")


st.sidebar.caption('Created by Swati Gupta, [Jai Moondra](https://jaimoondra.github.io/), Mohit Singh.\n'
                   'Based on our [paper](https://arxiv.org/abs/2211.14873) on fairness in facility location.\n'
                   'Submit any feedback to [jmoondra3@gatech.edu](mailto:jmoondra3@gatech.edu).\n')


