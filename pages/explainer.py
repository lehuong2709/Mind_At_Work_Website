from datetime import datetime
import geopandas as gpd
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit_antd_components as sac
from streamlit_pills import pills
from src.constants import DEFAULT_POVERTY_THRESHOLD, DEFAULT_RURAL_DISTANCE_THRESHOLD, DEFAULT_URBAN_DISTANCE_THRESHOLD
from src.usa.constants import state_names, interesting_states
from src.usa.states import USAState
from src.usa.facilities import CVS, Walgreens, Walmart, UrgentCare, Hospitals, NursingHomes, ChildCare, PrivateSchools, FDICInsuredBanks, PharmaciesTop3
from src.usa.utils import racial_labels, racial_labels_display_names, compute_medical_deserts, get_page_url, get_demographic_data, get_facility_from_facility_name, get_state_of_the_day
from src.usa.plot_utils import plot_state, plot_stacked_bar, plot_existing_facilities, plot_blockgroups, plot_voronoi_cells, plot_new_facilities, plot_demographic_analysis, plot_radar_chart, plot_distance_histogram
from src.tabs.analysis import run_analysis_tab


st.set_page_config(layout='wide', initial_sidebar_state='expanded', page_title='Facility Deserts in USA', page_icon='🏥')


def update_variable(variable_name):
    st.session_state[variable_name] = st.session_state['_' + variable_name]


def loop_list(list_like_object):
    l = list(list_like_object)
    l = l + [l[0]]
    return l


def get_facility_from_user():
    """
    Get the facility type from the user using a selectbox.
    """
    # Set the default facility type to 'Pharmacy chains'
    if 'facility_display_name' not in st.session_state:
        st.session_state.facility_display_name = 'Pharmacy chains'

    # Set current facility type to the default facility type
    facility_display_name = st.session_state['facility_display_name']
    index = facility_display_names.index(facility_display_name)

    # Get the facility type from the user
    facility_display_name = st.selectbox(
        label='Choose a facility',
        options=facility_display_names,
        index=index,
        key='_facility_display_name',
        on_change=lambda: update_variable('facility_display_name'),
        help='Select the type of facility to analyze',
    )
    # Update the facility type in the session state

    # Get the facility object from the facility type
    facility = get_facility_from_facility_name(facilities, st.session_state.facility_display_name)

    return facility


def get_state_from_user():
    """
    Get the US state from the user using a selectbox.
    """
    # Set the default state to the state of the day
    if 'state_name' not in st.session_state:
        st.session_state['state_name'] = get_state_of_the_day(interesting_states)

    # Get the state from the user
    state_of_the_day = st.session_state['state_name']
    st.selectbox(
        label='Choose a US state',
        options=state_names,
        index=state_names.index(state_of_the_day),
        key='_state_name',
        on_change=lambda: update_variable('state_name'),
    )

    # Get the state object from the state name
    State = USAState(st.session_state.state_name)
    return State


def get_poverty_threshold_from_user():
    """
    Get the poverty threshold from the user using a slider.
    """
    # Set the default poverty threshold to 20%
    if 'poverty_threshold' not in st.session_state:
        st.session_state['poverty_threshold'] = DEFAULT_POVERTY_THRESHOLD
    poverty_threshold = st.session_state['poverty_threshold']

    # Get the poverty threshold from the user
    st.slider(
        label=r'Choose poverty threshold $p$%',
        min_value=0, max_value=100, step=5, value=poverty_threshold,
        key='_poverty_threshold',
        on_change=lambda: update_variable('poverty_threshold'),
        help='Only blockgroups with over $p$% of the population below the poverty line are considered ' + facility.type + ' deserts.',
    )

    return


def get_distance_thresholds_from_user():
    """
    Get the distance thresholds for urban and rural areas from the user using sliders.
    """
    st.write('Choose distance threshold $n$ miles')
    col_side1, col_side2 = st.columns(2)

    # Set the default distance thresholds to 2 miles for urban areas
    if 'urban_distance_threshold' not in st.session_state:
        st.session_state['urban_distance_threshold'] = DEFAULT_URBAN_DISTANCE_THRESHOLD
    urban_distance_threshold = st.session_state['urban_distance_threshold']

    # Get the distance threshold for urban areas from the user
    col_side1.slider(
        label=r'For urban areas',
        min_value=0.0, max_value=15.0, step=0.5, value=urban_distance_threshold,
        format='%.1f',
        key = '_urban_distance_threshold',
        on_change=lambda: update_variable('urban_distance_threshold'),
        help='Distance threshold for urban areas; only blockgroups further than this distance from the nearest facility are considered ' + facility.type + ' deserts.',
    )

    # Set the default distance thresholds to 10 miles for rural areas
    if 'rural_distance_threshold' not in st.session_state:
        st.session_state['rural_distance_threshold'] = DEFAULT_RURAL_DISTANCE_THRESHOLD
    rural_distance_threshold = st.session_state['rural_distance_threshold']

    # Get the distance threshold for rural areas from the user
    col_side2.slider(
        label=r'For rural areas',
        min_value=0.0, max_value=30.0, step=1.0, value=rural_distance_threshold,
        format='%.1f',
        key='_rural_distance_threshold',
        on_change=lambda: update_variable('rural_distance_threshold'),
        help='Distance threshold for rural areas; only blockgroups further than this distance from the nearest facility are considered ' + facility.type + ' deserts.',
    )

    return


# Remove extra padding from the top and bottom of the page
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 2rem;  /* Adjust this value as needed */
        padding-bottom: 2rem; /* Optionally reduce bottom padding too */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Create a tab to select the tool to use
tab = sac.tabs(
    items=['Facility Deserts', 'Opening New Facilities', 'Explanation', 'More Analysis'],
    index=2,
    align='center',
)

# Sidebar messages for the different tools
if tab == 'Facility Deserts':
    st.sidebar.caption('This tool aims to identify facility deserts in the US – poorer areas with low '
                       'access to various critical facilities such as pharmacies, hospitals, and schools.')

if tab == 'Opening New Facilities':
    st.sidebar.caption('This tool proposes new facilities to reduce the number of facility deserts, based on '
                       'the optimization models in our [paper](https://arxiv.org/abs/2211.14873) on '
                       'fairness in facility location.')

# Define the facilities to analyze
facilities = [PharmaciesTop3, UrgentCare, Hospitals, NursingHomes, PrivateSchools, FDICInsuredBanks, ChildCare]
facility_display_names = [facility.display_name for facility in facilities]

if tab == 'Facility Deserts' or tab == 'Opening New Facilities':
    # Get the facility type and state from the user
    with st.sidebar:
        facility = get_facility_from_user()

        State = get_state_from_user()
        state_fips = State.fips
        state_abbr = State.abbreviation
        census_df = State.get_census_data(level='blockgroup')

        with st.container(border=True):
            get_poverty_threshold_from_user()

        with st.container(border=True):
            get_distance_thresholds_from_user()


# Display the selected tab
if tab == 'Facility Deserts':
    # Display the title of the tool
    st.markdown("""
        <h1 style="font-size: 40px; text-align: center; margin-bottom: 0em; margin-top: 0em; line-height: 1.0;">
            """ + facility.type.capitalize() + """ deserts in
            <span style="color: #c41636">
                """ + State.name + """
            </span>
        </h1>
        <h3 style="font-size: 18px; text-align: center; margin-top: 0em;">
            Based on distances to <span style="color: #c41636">""" + facility.display_name.lower() + """</span>
        </h3>
        """, unsafe_allow_html=True)

    # Display the description of the tool
    st.markdown('''This tool aims to identify poorer areas with low access to critical facilities.'''
                + facility.get_message(), unsafe_allow_html=True)

    # Left column contains the map and the right column contains the demographic data
    col1, col2 = st.columns([3, 2], gap='small')

    with col2:
        # Display the figure caption on top of column 2
        st.caption(f'**Figure**: Census blockgroups classified as ' + facility.type + ' deserts in ' + State.name
                   + '. Colored by racial/ethnic majority.')

    with col1:
        with st.container(border=True):             # Create a container with a border for the map
            items = sac.checkbox(                   # Create a checkbox to select the items to display on the map
                items=[facility.type.capitalize() + ' deserts', facility.display_name, 'Voronoi cells'],
                index=[0],
                size='xs',
                align='center',
            )

            show_deserts = True if facility.type.capitalize() + ' deserts' in items else False      # Show medical deserts
            show_facility_locations = True if facility.display_name in items else False             # Show locations of existing facilities
            show_voronoi_cells = True if 'Voronoi cells' in items else False                        # Show Voronoi cells

            # Create a new figure for the map
            fig = go.Figure()
            fig, bounds = plot_state(fig, State)

            # Compute the medical deserts based on the selected poverty and distance thresholds
            distance_label = facility.distance_label
            desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, distance_label)

            if show_deserts is True:
                # Plot the blockgroups classified as medical deserts on the map
                fig = plot_blockgroups(fig, desert_df)

            if show_facility_locations is True:
                # Plot the locations of existing facilities on the map
                if facility.name == 'top_3_pharmacy_chains':
                    for pharmacy_chain in [CVS, Walgreens, Walmart]:
                        fig = plot_existing_facilities(fig, pharmacy_chain, bounds)
                else:
                    fig = plot_existing_facilities(fig, facility, bounds)

            if show_voronoi_cells is True:
                # Plot the Voronoi cells of the existing facilities on the map
                fig = plot_voronoi_cells(fig, facility, state_fips)

            # Config for the plotly map
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

            # Display the map on the left column
            st.plotly_chart(fig, use_container_width=True, config=config)

    with col2:
        # Display the demographic data in the right column
        demographics_all = get_demographic_data(census_df)
        n_blockgroups = len(census_df)

        demographics_deserts = get_demographic_data(desert_df)

        # Display the number of blockgroups and medical deserts in the state by racial/ethnic majority
        fig1, fig2 = plot_stacked_bar(demographics_all), plot_stacked_bar(demographics_deserts)
        with st.container(border=True):
            st.markdown('''<center>''' + State.name + ''' has <b>''' + str(len(census_df)) + '''</b> blockgroups</center>''', unsafe_allow_html=True)
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

            st.markdown('''<center><b>''' + str(len(desert_df)) + '''</b> are ''' + facility.type + ''' deserts</center>''', unsafe_allow_html=True)
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

        # Message for racial/ethnic groups disproportionately affected by facility deserts
        for racial_label in racial_labels:
            if racial_label in demographics_deserts and racial_label != 'other':
                fraction_of_all_blockgroups = demographics_all[racial_label]/n_blockgroups
                fraction_of_medical_deserts = demographics_deserts[racial_label]/len(desert_df)

                four_times_deserts = fraction_of_medical_deserts> 4 * fraction_of_all_blockgroups
                over_ten_percent_difference = fraction_of_medical_deserts - fraction_of_all_blockgroups > 0.1
                over_five_deserts = fraction_of_medical_deserts * len(desert_df) >= 5

                if over_five_deserts and (four_times_deserts or over_ten_percent_difference):
                    overall_percent_str = str(round(fraction_of_all_blockgroups * 100, 2))
                    desert_percent_str = str(round(fraction_of_medical_deserts * 100, 2))
                    with st.container(border=True):
                        st.write('Majority ' + racial_labels_display_names[racial_label] + ' blockgroups may be disproportionately affected by '
                                 + facility.type + ' deserts in ' + State.name + ': they make up :red[' + desert_percent_str +
                                 '%] of ' + facility.type + ' deserts while being only :blue[' +
                                 overall_percent_str + '%] of all blockgroups.')

        url = get_page_url('suggesting-new-facilities')
        st.markdown(
            '''
            Also check out our [tool](''' + url + ''') to suggest locations for new facilities to 
            reduce the impact of ''' + facility.type + ''' deserts.'''.format(facility.type), unsafe_allow_html=True
        )

    st.sidebar.caption('Created by Swati Gupta, [Jai Moondra](https://jaimoondra.github.io/), Mohit Singh.\n'
                       'Based on our [paper](https://arxiv.org/abs/2211.14873) on fairness in facility location.\n'
                       'Submit any feedback to [jmoondra3@gatech.edu](mailto:jmoondra3@gatech.edu).\n')

    st.sidebar.caption('We assume straight-line distances, and the accuracy of our results depends on the accuracy of the underlying data. '
                       'Map boundaries are approximate.')

    with st.expander('More analysis'):
        st.markdown('''<center><b>Rural vs urban medical deserts</b></center>''', unsafe_allow_html=True)

        rural_df = census_df[census_df['urban'] == 0]
        urban_df = census_df[census_df['urban'] == 1]

        rural_desert_df = desert_df[desert_df['urban'] == 0]
        urban_desert_df = desert_df[desert_df['urban'] == 1]

        rural_overall_demographics = get_demographic_data(rural_df)
        urban_overall_demographics = get_demographic_data(urban_df)

        rural_desert_demographics = get_demographic_data(rural_desert_df)
        urban_desert_demographics = get_demographic_data(urban_desert_df)

        col_rural, col_urban = st.columns(2)

        with col_rural:
            st.markdown('''<center>''' + State.name + ''' has <b>''' + str(len(rural_df)) + '''</b> rural blockgroups</center>''', unsafe_allow_html=True)
            fig_rural_overall = plot_stacked_bar(rural_overall_demographics)
            st.plotly_chart(fig_rural_overall, use_container_width=True, config={'displayModeBar': False})

            st.markdown('''<center><b>''' + str(len(rural_desert_df)) + '''</b> are ''' + facility.type + ''' deserts</center>''', unsafe_allow_html=True)
            fig_rural_deserts = plot_stacked_bar(rural_desert_demographics)
            st.plotly_chart(fig_rural_deserts, use_container_width=True, config={'displayModeBar': False})

        with col_urban:
            st.markdown('''<center>''' + State.name + ''' has <b>''' + str(len(urban_df)) + '''</b> urban blockgroups</center>''', unsafe_allow_html=True)
            fig_urban_overall = plot_stacked_bar(urban_overall_demographics)
            st.plotly_chart(fig_urban_overall, use_container_width=True, config={'displayModeBar': False})

            st.markdown('''<center><b>''' + str(len(urban_desert_df)) + '''</b> are ''' + facility.type + ''' deserts</center>''', unsafe_allow_html=True)
            fig_urban_deserts = plot_stacked_bar(urban_desert_demographics)
            st.plotly_chart(fig_urban_deserts, use_container_width=True, config={'displayModeBar': False})


if tab == 'Opening New Facilities':
    def facility_names(facility):
        if facility.name == 'top_3_pharmacy_chains':
            return 'pharmacies'
        else:
            return facility.display_name.lower()


    st.markdown("""
        <h1 style="font-size: 40px; text-align: center; margin-bottom: 0em; margin-top: 0em; line-height: 1.0;">
             Proposing new """ + facility_names(facility) + """ in
            <span style="color: #c41636">
                """ + State.name + """
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

    col1, col2 = st.columns([3, 2], gap='small')

    with col2:
        with st.container(border=True):
            k = st.select_slider(label='Choose the number of new facilities', options=[0, 5, 10, 25, 50, 100], value=25)

    with col1:
        with st.container(border=True):
            old_distance_label = facility.distance_label
            new_distance_label = facility.distance_label + '_combined_k_' + str(k)
            if k == 0:
                new_distance_label = old_distance_label

            original_desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, old_distance_label)
            new_desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, new_distance_label)

            items = sac.checkbox(
                items=[facility.type.capitalize() + ' deserts', 'Existing facilities', 'Proposed facilities'],
                index=[1, 2],
                size='xs',
                align='center',
            )

            show_deserts = True if facility.type.capitalize() + ' deserts' in items else False
            show_existing_facilities = True if 'Existing facilities' in items else False
            show_new_facilities = True if 'Proposed facilities' in items else False

            fig = go.Figure()
            fig, bounds = plot_state(fig, State)
            if show_deserts:
                difference_df = original_desert_df[~original_desert_df.index.isin(new_desert_df.index)]
                fig = plot_blockgroups(fig, difference_df, color='lightgrey')
                fig = plot_blockgroups(fig, new_desert_df)
            if show_existing_facilities:
                fig = plot_existing_facilities(fig, facility, bounds)
            if show_new_facilities:
                fig = plot_new_facilities(fig, facility=facility, state_fips=State.fips, k=k, name='Proposed facilities',
                                          marker_color='cyan', marker_symbol='diamond', p='combined',
                                          marker_line_color='black', marker_line_width=2.0)

            st.plotly_chart(fig, use_container_width=True)

    with col2:
        with st.container(border=True):
            original_demographic_data = get_demographic_data(original_desert_df)
            original_medical_deserts = str(sum(original_demographic_data.values()))
            st.markdown('''<center>Original ''' + facility.type + ''' deserts (''' + original_medical_deserts + ''')</center>''', unsafe_allow_html=True)
            fig_original = plot_stacked_bar(original_demographic_data)
            st.plotly_chart(fig_original, use_container_width=True, config={'displayModeBar': False})

            new_demographic_data = get_demographic_data(new_desert_df)
            new_medical_deserts = str(sum(new_demographic_data.values()))
            st.markdown('''<center>Remaining ''' + facility.type + ''' deserts (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
            new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
            fig_new = plot_stacked_bar(new_demographic_data)
            st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})

    with st.container(border=True):
        st.markdown('''<center><b>Distance (in miles) to closest ''' + facility.description[2:] + ''' in ''' + State.name + '''<br>At blockgroup level</b></center>''', unsafe_allow_html=True)

        col_urban, col_rural = st.columns([1, 1])

        fig_urban, fig_rural = plot_radar_chart(
            State=State,
            facility=facility,
            k=k,
            poverty_threshold=st.session_state.poverty_threshold,
        )

        with col_urban:
            st.plotly_chart(fig_urban, use_container_width=True, config={'displayModeBar': False})

        with col_rural:
            st.plotly_chart(fig_rural, use_container_width=True, config={'displayModeBar': False})

        st.caption('**Figure**: Distances of various kinds of blockgroups in urban and rural areas of ' + State.name + ' to the nearest ' + facility.description[2:] + '.'
                                                                                                                                                                       ' Low insurance blockgroups are those with less than 80% of the population having health insurance.'
                                                                                                                                                                       ' Low income blockgroups are those with more than ' + str(st.session_state.poverty_threshold) + '% of the population below the poverty line.')

    with st.expander(label='How does this work?'):
        st.markdown('''
            Under the hood, our proposed solution above is a combination of three distinct solutions, each of which suggests 
             locations of up to 100 new facilities. These solutions optimize different aspects of fairness, and 
            are based on minimizing the $L_1$, $L_2$, and $L_\infty$ norms respectively of the distances of people in 
            various demographic groups from the nearest facility (see our [paper](https://arxiv.org/abs/2211.14873) for more details). You can compare the three solutions in the figure below.
        ''')

        col1, col2 = st.columns([3, 2], gap='small')

        with col1:
            with st.container(border=True):
                st.caption(f'**Figure**: Proposed locations for new facilities in the three solutions based on different optimization models.')

                show_solutions = sac.checkbox(
                    items=['Solution 1', 'Solution 2', 'Solution 3'],
                    size='xs',
                    align='center',
                    index=[0, 1, 2]
                )
                show_solution1 = True if 'Solution 1' in show_solutions else False
                show_solution2 = True if 'Solution 2' in show_solutions else False
                show_solution3 = True if 'Solution 3' in show_solutions else False

                fig = go.Figure()
                fig, bounds = plot_state(fig, State)

                fig.update_layout(
                    legend=dict(title='Facilities')
                )

                if show_new_facilities:
                    fig = plot_new_facilities(fig, facility=facility, state_fips=State.fips, k=k, name='In proposed solution',
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
            original_desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, old_distance_label)
            original_demographic_data = get_demographic_data(original_desert_df)
            original_medical_deserts = str(sum(original_demographic_data.values()))
            st.markdown('''<center>Original ''' + facility.type + ''' deserts (''' + original_medical_deserts + ''')</center>''', unsafe_allow_html=True)
            fig_original = plot_stacked_bar(original_demographic_data)
            st.plotly_chart(fig_original, use_container_width=True, config={'displayModeBar': False})

            st.markdown('''<center>Remaining ''' + str(facility.type) + ''' deserts</center>''', unsafe_allow_html=True)

            combined_solution_label = facility.distance_label + '_combined_k_' + str(k)
            if k == 0:
                combined_solution_label = old_distance_label
            new_desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, combined_solution_label)
            new_demographic_data = get_demographic_data(new_desert_df)
            new_medical_deserts = str(sum(new_demographic_data.values()))
            st.markdown('''<center>Proposed solution (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
            new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
            fig_new = plot_stacked_bar(new_demographic_data)
            st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})

            solution_1_distance_label = facility.distance_label + '_p_1_k_' + str(k)
            if k == 0:
                solution_1_distance_label = old_distance_label
            new_desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, solution_1_distance_label)
            new_demographic_data = get_demographic_data(new_desert_df)
            new_medical_deserts = str(sum(new_demographic_data.values()))
            st.markdown('''<center>Solution 1 (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
            new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
            fig_new = plot_stacked_bar(new_demographic_data)
            st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})

            solution_2_distance_label = facility.distance_label + '_p_2_k_' + str(k)
            if k == 0:
                solution_2_distance_label = old_distance_label
            new_desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, solution_2_distance_label)
            new_demographic_data = get_demographic_data(new_desert_df)
            new_medical_deserts = str(sum(new_demographic_data.values()))
            st.markdown('''<center>Solution 2 (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
            new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
            fig_new = plot_stacked_bar(new_demographic_data)
            st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})

            solution_inf_distance_label = facility.distance_label + '_p_inf_k_' + str(k)
            if k == 0:
                solution_inf_distance_label = old_distance_label
            new_desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, solution_inf_distance_label)
            new_demographic_data = get_demographic_data(new_desert_df)
            new_medical_deserts = str(sum(new_demographic_data.values()))
            st.markdown('''<center>Solution 3 (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
            new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
            fig_new = plot_stacked_bar(new_demographic_data)
            st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})

    st.sidebar.caption('Created by Swati Gupta, [Jai Moondra](https://jaimoondra.github.io/), Mohit Singh.\n'
                       'Based on our [paper](https://arxiv.org/abs/2211.14873) on fairness in facility location.\n'
                       'Submit any feedback to [jmoondra3@gatech.edu](mailto:jmoondra3@gatech.edu).\n')

    st.sidebar.caption('We assume straight-line distances, and the accuracy of our results depends on the accuracy of the underlying data. '
                       'Map boundaries are approximate.')


if tab == 'Explanation':
    st.markdown("""
    <h1 style="font-size: 40px; text-align: center; margin-bottom: 0em; line-height: 1.0;">
        Facility deserts in <span style="color: #c41636"> USA </span>
    </h1>
    <br>
    """, unsafe_allow_html=True)

    with st.expander('What is this?', expanded=True):
        st.markdown("""
            Access to critical infrastructure is considered one of three dimensions of
            [multidimensional poverty](https://www.worldbank.org/en/topic/poverty/brief/multidimensional-poverty-measure) 
            by the World Bank. Inequitable access to important facilities such as hospitals, schools, and banks can exacerabte monetary
            poverty and other social disparities. The US department of agriculture has identified areas with limited
            access to grocery stores as [food deserts](https://www.ers.usda.gov/data-products/food-access-research-atlas/go-to-the-atlas/).
            \n 
            This tool helps visualize potential 'deserts' for other critical facilities.
            """
                    )

    col1, col2 = st.columns([1, 1])

    with col2:
        with st.expander('What facilities are considered?', expanded=True):
            facility_names = [
                'Pharmacy chains CVS/Walgreens/Walmart',
                'Urgent care centers',
                'Hospitals',
                'Nursing homes',
                'Private schools',
                'Banks',
                'Child care centers'
            ]
            facility_name = pills(label='', options=facility_names, label_visibility='collapsed', clearable=True, index=None)
            if facility_name == 'Pharmacy chains CVS/Walgreens/Walmart':
                st.markdown('CVS, Walgreens, and Walmart are the three largest pharmacy chains in the US. Each CVS/Walgreens/Walmart pharmacy is considered a separate facility.')
            elif facility_name == 'Urgent care centers':
                st.markdown('Urgent care centers are walk-in clinics that provide non-emergency medical care.')
            elif facility_name == 'Hospitals':
                st.markdown('Each hospital is considered a separate facility.')
            elif facility_name == 'Nursing homes':
                st.markdown('Nursing homes provide residential care for elderly or disabled individuals. Each nursing home is considered a separate facility.')
            elif facility_name == 'Private schools':
                st.markdown('Private schools are educational institutions that are not operated by the government. Each private school is considered a separate facility.')
            elif facility_name == 'Banks':
                st.markdown('Each FDIC insured bank is considered a separate facility.')
            elif facility_name == 'Child care centers':
                st.markdown('Child care centers provide care for children. Each child care center is considered a separate facility.')

        with st.expander('Tell me about racial/ethnic categories', expanded=True):
            st.markdown("""
                The US census bureau recognizes the following racial/ethnic groups:
                - White alone
                - Black or African American alone
                - American Indian or Alaska Native (AIAN) alone
                - Asian alone
                - Native Hawaiian or Other Pacific Islander (NHOPI) alone
                - Hispanic
                - Other or no racial majority \n
                The quantifier 'alone' is omitted in the tool for brevity. We categorize blockgroups based on their racial majority."""
                        )

        with st.expander('Created by', expanded=True):
            st.markdown("""Created by Swati Gupta, [Jai Moondra](https://jaimoondra.github.io/), and Mohit Singh. Based on 
            our [paper](https://arxiv.org/abs/2211.14873) on fair facility location. Please submit any feedback or 
            questions to [jmoondra3@gatech.edu](mailto:jmoondra3@gatech.edu)."""
                        )

        with st.expander('Data sources', expanded=True):
            st.markdown("""
                The data used in this project is from the [US Census Bureau](https://www.census.gov/programs-surveys/acs/) and
                [HIFLD Open](https://hifld-geoplatform.hub.arcgis.com/pages/hifld-open) database. \n                    
                Data for [pharmacies](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::pharmacies-/about) is from 2010. \n
                Data for [urgent care centers](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::urgent-care-facilities/about) is from 2009. \n
                Data for [hospitals](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::hospitals/about) is from 2023. \n
                Data for [nursing homes](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::nursing-homes/about) is from 2017. \n
                Data for [private schools](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::private-schools/about) is from 2017. \n
                Data for [FDIC insured banks](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::fdic-insured-banks/about) is from 2019. \n
                Data for [Child care centers](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::child-care-centers/about) if from 2022. \n
                [Census](https://data.census.gov/) data is from 2022. \n"""
                        )

        with st.expander('Limitations', expanded=True):
            st.markdown("""
                The results are indicative only and meant for educational purposes. Distances are approximate and based on 
                straight-line computations, and all people in a census blockgroup are assumed to be at its geometric center.
                 Many other factors affect access to facilities, for example, public transportation,
                road networks, rural-urban divide, and so on. Data for some facilities is older than census data.\n
            """
                        )

        with st.expander('License', expanded=True):
            st.write('Released under Creative Commons BY-NC license, 2024.')


    with col1:
        with st.expander('How are facility deserts defined?', expanded=True):
            st.markdown("""
                This tool allows you to define facility deserts.
                Our basic unit of analysis is the [US census blockgroup](https://en.wikipedia.org/wiki/Census_block_group)
                which is a small geographic area with typical population of 600 to 3,000 people. You can choose 
                the facility of interest, the distance within which you consider the facility accessible, and poverty rate 
                threshold for classifying blockgroups as 'facility deserts'. \n
                
                As an example, consider hospitals in Colorado:
                """
                        )
            col21, col22 = st.columns([1, 1])
            with col21:
                poverty_threshold = st.slider('Choose poverty threshold (%)', min_value=0, max_value=100, value=10, step=5)
            with col22:
                distance_threshold = st.slider('Choose distance threshold (miles)', min_value=0.0, max_value=25.0, value=8.0, step=0.5)

            state = 'Colorado'
            State = USAState(state)
            census_df = State.get_census_data(level='blockgroup')

            Facility = Hospitals
            desert_df = compute_medical_deserts(census_df, poverty_threshold, distance_threshold, distance_threshold,
                                                Hospitals.distance_label)

            fig = go.Figure()
            fig, bounds = plot_state(fig, State)
            fig = plot_blockgroups(fig, desert_df)
            fig = plot_existing_facilities(fig, Facility, bounds)

            config = {
                'modeBarButtonsToRemove': ['zoomOut', 'select2d'],
                'displayModeBar': False,
                'staticPlot': False,
                'scrollZoom': True,
                'toImageButtonOptions': {
                    'format': 'png',
                    'scale': 1.5,
                }
            }

            st.plotly_chart(fig, use_container_width=True, config=config)
            st.markdown("""
                Circles represent blockgroups classified as facility deserts and are colored by their racial majority.
                You can click on the legend to toggle the display of different racial categories.
                """
                        )

        with st.expander('What are Voronoi cells?', expanded=True):
            st.markdown("""
                [Voronoi cells](https://en.wikipedia.org/wiki/Voronoi_diagram) are polygons that partition a plane into regions based on the distance to facilities. Each
                Voronoi cell contains points that are closer to a particular facility than any other. They provide a way to
                visualize the density of facilities in a region. \n
                
                As an example, consider the Voronoi cells for hospitals in Colorado:
                """
                        )
            state = 'Colorado'
            State = USAState(state)
            state_fips = State.fips

            census_df = State.get_census_data(level='blockgroup')
            census_df['racial_majority'] = census_df['racial_majority'].astype(str)

            fig = go.Figure()
            fig, bounds = plot_state(fig, State)
            fig = plot_existing_facilities(fig, Hospitals, bounds)
            fig = plot_voronoi_cells(fig, Hospitals, state_fips)

            config = {
                'modeBarButtonsToRemove': ['zoomOut', 'select2d'],
                'displayModeBar': False,
                'staticPlot': False,
                'scrollZoom': True,
                'toImageButtonOptions': {
                    'format': 'png',
                    'scale': 1.5,
                }
            }

            st.plotly_chart(fig, use_container_width=True, config=config)


if tab == 'More Analysis':
    run_analysis_tab()
