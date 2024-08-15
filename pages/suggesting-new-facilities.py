from ast import literal_eval
from datetime import datetime
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.constants import DEFAULT_POVERTY_THRESHOLD, DEFAULT_RURAL_DISTANCE_THRESHOLD, DEFAULT_URBAN_DISTANCE_THRESHOLD
from src.usa.constants import state_names, interesting_states
from src.usa.states import USAState
from src.usa.facilities import (UrgentCare, Hospitals, NursingHomes,
    ChildCare, PrivateSchools, FDICInsuredBanks, PharmaciesTop3)
from src.usa.utils import racial_labels, compute_medical_deserts, get_demographic_data, get_page_url
from src.usa.plot_utils import plot_state, plot_stacked_bar, plot_existing_facilities, plot_blockgroups, plot_new_facilities


@st.cache_data
def read_new_facilities(facility_name):
    new_facilities_path = os.path.join('data', 'usa', 'new_facilities', facility_name, 'new_facilities_combined.csv')
    new_facilities = pd.read_csv(new_facilities_path, index_col=0)
    return new_facilities['100'].apply(literal_eval)


st.set_page_config(layout='wide', initial_sidebar_state='expanded', page_title='suggesting-new-facilities')


def get_facility_from_facility_name(facilities, facility_name):
    for facility in facilities:
        if facility.display_name == facility_name:
            return facility


def state_of_the_day(state_names):
    day_of_year = datetime.now().timetuple().tm_yday
    state_of_the_day = state_names[day_of_year % len(state_names)]
    return state_of_the_day


st.sidebar.caption('This tool suggests new facilities to reduce the number of facility deserts, based on '
                   'the optimization models in our [paper](https://arxiv.org/abs/2211.14873) on '
                   'fairness in facility location.')


facilities = [PharmaciesTop3, UrgentCare, Hospitals, NursingHomes, PrivateSchools, FDICInsuredBanks, ChildCare]
facility_display_names = [facility.display_name for facility in facilities]


with st.sidebar:
    # Facility selection
    def update_facility_display_name():
        st.session_state['facility_display_name'] = st.session_state['facility_display_name_new']

    if 'facility_display_name' in st.session_state:
        facility_display_name = st.session_state['facility_display_name']
        index = facility_display_names.index(facility_display_name)
    else:
        index = 0
    facility_display_name = st.selectbox(
        label='Choose a facility',
        options=facility_display_names,
        index=index,
        key='facility_display_name_new',
        help='Select the type of facility to analyze',
        on_change=update_facility_display_name
    )
    facility = get_facility_from_facility_name(facilities, facility_display_name)

    # State selection
    def update_state_name():
        st.session_state['state_name'] = st.session_state['state_name_new']

    state_of_the_day = state_of_the_day(interesting_states)
    if 'state_name' in st.session_state:
        state_of_the_day = st.session_state['state_name']
    state_name = st.selectbox(
        label='Choose a US state',
        options=state_names,
        index=state_names.index(state_of_the_day),
        key='state_name_new',
        on_change=update_state_name
    )

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


url = get_page_url('')
st.markdown('''
    This tool suggests locations of new facilities to reduce the number of [''' + facility.type + ''' deserts](''' + url + '''). 
    To aid planning, the tool allows you to choose the number of new facilities to suggest, with the potential to expand later.
    As before, you can also choose the poverty and distance thresholds that define a ''' + facility.type + ''' desert in the sidebar.
    ''', unsafe_allow_html=True
)

with st.sidebar:
    def update_poverty_threshold():
        st.session_state['poverty_threshold'] = st.session_state['poverty_threshold_new']

    with st.container(border=True):
        poverty_threshold = DEFAULT_POVERTY_THRESHOLD
        if 'poverty_threshold' in st.session_state:
            poverty_threshold = st.session_state['poverty_threshold']
        poverty_threshold = st.slider(r'Choose poverty threshold $p$%', min_value=0, max_value=100, step=5, key='poverty_threshold_new',
                                      value=poverty_threshold, help='Only blockgroups with over $p$% of the population below the poverty line are considered ' + facility.type + ' deserts.',
                                      on_change=update_poverty_threshold)

    def update_urban_distance_threshold():
        st.session_state['urban_distance_threshold'] = st.session_state['urban_distance_threshold_new']

    def update_rural_distance_threshold():
        st.session_state['rural_distance_threshold'] = st.session_state['rural_distance_threshold_new']

    with st.container(border=True):
        st.write('Choose distance threshold $n$ miles')
        col_side1, col_side2 = st.columns(2)

        urban_distance_threshold = DEFAULT_URBAN_DISTANCE_THRESHOLD
        if 'urban_distance_threshold' in st.session_state:
            urban_distance_threshold = st.session_state['urban_distance_threshold']
        urban_distance_threshold = col_side1.slider(
            label=r'For urban areas',
            min_value=0.0, max_value=15.0, step=0.5, value=urban_distance_threshold,
            format='%.1f',
            key='urban_distance_threshold_new',
            help='Distance threshold for urban areas; only blockgroups further than this distance from the nearest facility are considered ' + facility.type + ' deserts.',
            on_change=update_urban_distance_threshold
        )

        rural_distance_threshold = DEFAULT_RURAL_DISTANCE_THRESHOLD
        if 'rural_distance_threshold' in st.session_state:
            rural_distance_threshold = st.session_state['rural_distance_threshold']
        rural_distance_threshold = col_side2.slider(
            label=r'For rural areas',
            min_value=0.0, max_value=30.0, step=1.0, value=rural_distance_threshold,
            format='%.1f',
            key='rural_distance_threshold_new',
            help='Distance threshold for rural areas; only blockgroups further than this distance from the nearest facility are considered ' + facility.type + ' deserts.',
            on_change=update_rural_distance_threshold
        )


col1, col2 = st.columns([3, 2], gap='medium')

with col2:
    with st.container(border=True):
        k = st.select_slider(label='Choose the number of new facilities', options=[0, 5, 10, 25, 50, 100], value=25)

    col21, col22, col23 = st.columns(3)

    with col21:
        show_deserts = st.checkbox(label=facility.type.capitalize() + ' deserts', value=False)
    with col22:
        show_existing_facilities = st.checkbox(label='Existing facilities', value=True)
    with col23:
        show_new_facilities = st.checkbox(label='Suggested facilities', value=True)


with col1:
    old_distance_label = facility.distance_label
    new_distance_label = facility.distance_label + '_combined_k_' + str(k)
    if k == 0:
        new_distance_label = old_distance_label

    original_desert_df = compute_medical_deserts(census_df, poverty_threshold, urban_distance_threshold, rural_distance_threshold, old_distance_label)
    new_desert_df = compute_medical_deserts(census_df, poverty_threshold, urban_distance_threshold, rural_distance_threshold, new_distance_label)

    fig = go.Figure()
    fig, bounds = plot_state(fig, State)
    if show_deserts:
        difference_df = original_desert_df[~original_desert_df.index.isin(new_desert_df.index)]
        fig = plot_blockgroups(fig, difference_df, color='lightgrey')
        fig = plot_blockgroups(fig, new_desert_df)
    if show_existing_facilities:
        fig = plot_existing_facilities(fig, facility, bounds)
    if show_new_facilities:
        fig = plot_new_facilities(fig, facility=facility, state_fips=State.fips, k=k, name='Suggested facilities',
                                  marker_color='cyan', marker_symbol='diamond', p='combined',
                                  marker_line_color='black', marker_line_width=2.0)

    st.plotly_chart(fig, use_container_width=True)

with col2:
    original_demographic_data = get_demographic_data(original_desert_df, racial_labels)
    original_medical_deserts = str(sum(original_demographic_data.values()))
    st.markdown('''<center>Original ''' + facility.type + ''' deserts (''' + original_medical_deserts + ''')</center>''', unsafe_allow_html=True)
    fig_original = plot_stacked_bar(original_demographic_data)
    st.plotly_chart(fig_original, use_container_width=True, config={'displayModeBar': False})

    new_demographic_data = get_demographic_data(new_desert_df, racial_labels)
    new_medical_deserts = str(sum(new_demographic_data.values()))
    st.markdown('''<center>Remaining ''' + facility.type + ''' deserts (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
    new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
    fig_new = plot_stacked_bar(new_demographic_data)
    st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})


with st.expander(label='How does this work?'):
    st.markdown('''
        Under the hood, our proposed solution above is a combination of three distinct solutions, each of which suggests 
         locations of up to 100 new facilities. These solutions optimize different aspects of fairness, and 
        are based on minimizing the $L_1$, $L_2$, and $L_\infty$ norms respectively of the distances of people in 
        various demographic groups from the nearest facility (see our [paper](https://arxiv.org/abs/2211.14873) for more details). You can compare the three solutions in the figure below.
    ''')

    col1, col2 = st.columns([3, 2], gap='medium')

    with col1:
        col11, col21, col31 = st.columns(3)
        with col11:
            show_solution1 = st.checkbox('Solution 1', value=True)
        with col21:
            show_solution2 = st.checkbox('Solution 2', value=True)
        with col31:
            show_solution3 = st.checkbox('Solution 3', value=True)

        fig = go.Figure()
        fig, bounds = plot_state(fig, State)

        fig.update_layout(
            legend=dict(title='Facilities')
        )

        if show_new_facilities:
            fig = plot_new_facilities(fig, facility=facility, state_fips=State.fips, k=k, name='In combined solution',
                                  marker_color='cyan', marker_symbol='diamond', p='combined', marker_size=10,
                                  marker_line_color='black', marker_line_width=0.0)
        if show_solution1:
            fig = plot_new_facilities(
                fig=fig, facility=facility, state_fips=State.fips, p=1, k=k, name='In solution 1',
                marker_symbol='circle-open-dot', marker_size=9, marker_color='black', marker_line_color='black', marker_line_width=1.5,
            )
        if show_solution2:
            fig = plot_new_facilities(
                fig=fig, facility=facility, state_fips=State.fips, p=2, k=k, name='In solution 2',
                marker_symbol='triangle-up-open', marker_size=12, marker_color='black', marker_line_color='black', marker_line_width=1.5,
            )
        if show_solution3:
            fig = plot_new_facilities(
                fig=fig, facility=facility, state_fips=State.fips, p='inf', k=k, name='In solution 3',
                marker_symbol='triangle-down-open', marker_size=12, marker_color='black', marker_line_color='black', marker_line_width=1.5,
            )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.caption('Figure: Suggested new facilities in the three solutions based on different optimization models. '
                   'Facilities present in our proposed solution above are in blue, those not in the proposed solution are in grey.')

        original_desert_df = compute_medical_deserts(census_df, poverty_threshold, urban_distance_threshold, rural_distance_threshold, old_distance_label)
        original_demographic_data = get_demographic_data(original_desert_df, racial_labels)
        original_medical_deserts = str(sum(original_demographic_data.values()))
        st.markdown('''<center>Original ''' + facility.type + ''' deserts (''' + original_medical_deserts + ''')</center>''', unsafe_allow_html=True)
        fig_original = plot_stacked_bar(original_demographic_data)
        st.plotly_chart(fig_original, use_container_width=True, config={'displayModeBar': False})

        st.markdown('''<center>Remaining ''' + str(facility.type) + ''' deserts</center>''', unsafe_allow_html=True)

        combined_solution_label = facility.distance_label + '_combined_k_' + str(k)
        if k == 0:
            combined_solution_label = old_distance_label
        new_desert_df = compute_medical_deserts(census_df, poverty_threshold, urban_distance_threshold, rural_distance_threshold, combined_solution_label)
        new_demographic_data = get_demographic_data(new_desert_df, racial_labels)
        new_medical_deserts = str(sum(new_demographic_data.values()))
        st.markdown('''<center>Combined solution (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
        new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
        fig_new = plot_stacked_bar(new_demographic_data)
        st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})

        solution_1_distance_label = facility.distance_label + '_p_1_k_' + str(k)
        if k == 0:
            solution_1_distance_label = old_distance_label
        new_desert_df = compute_medical_deserts(census_df, poverty_threshold, urban_distance_threshold, rural_distance_threshold, solution_1_distance_label)
        new_demographic_data = get_demographic_data(new_desert_df, racial_labels)
        new_medical_deserts = str(sum(new_demographic_data.values()))
        st.markdown('''<center>Solution 1 (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
        new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
        fig_new = plot_stacked_bar(new_demographic_data)
        st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})

        solution_2_distance_label = facility.distance_label + '_p_2_k_' + str(k)
        if k == 0:
            solution_2_distance_label = old_distance_label
        new_desert_df = compute_medical_deserts(census_df, poverty_threshold, urban_distance_threshold, rural_distance_threshold, solution_2_distance_label)
        new_demographic_data = get_demographic_data(new_desert_df, racial_labels)
        new_medical_deserts = str(sum(new_demographic_data.values()))
        st.markdown('''<center>Solution 2 (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
        new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
        fig_new = plot_stacked_bar(new_demographic_data)
        st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})

        solution_inf_distance_label = facility.distance_label + '_p_inf_k_' + str(k)
        if k == 0:
            solution_inf_distance_label = old_distance_label
        new_desert_df = compute_medical_deserts(census_df, poverty_threshold, urban_distance_threshold, rural_distance_threshold, solution_inf_distance_label)
        new_demographic_data = get_demographic_data(new_desert_df, racial_labels)
        new_medical_deserts = str(sum(new_demographic_data.values()))
        st.markdown('''<center>Solution 3 (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
        new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
        fig_new = plot_stacked_bar(new_demographic_data)
        st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})


with st.sidebar:
    move_to_explanation = st.button('Explanation', use_container_width=True)
    if move_to_explanation:
        st.switch_page("pages/explainer.py")

    move_to_medical_deserts = st.button('Visualizing facility deserts', use_container_width=True)
    if move_to_medical_deserts:
        st.switch_page("medical-facility-deserts.py")


st.sidebar.caption('Created by Swati Gupta, [Jai Moondra](https://jaimoondra.github.io/), Mohit Singh.\n'
                   'Submit any feedback to [jmoondra3@gatech.edu](mailto:jmoondra3@gatech.edu).\n')

st.sidebar.caption('We assume straight-line distances, and the accuracy of our results depends on the accuracy of the underlying data. '
                   'The maps are approximate.')


