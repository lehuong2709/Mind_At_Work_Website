from datetime import datetime
import geopandas as gpd
import os
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
from src.usa.plot_utils import plot_state, plot_stacked_bar, plot_existing_facilities, plot_blockgroups, plot_voronoi_cells, plot_new_facilities


st.set_page_config(layout='wide', initial_sidebar_state='expanded')


def update_variable(variable_name):
    st.session_state[variable_name] = st.session_state['_' + variable_name]


def get_facility_from_user():
    if 'facility_display_name' not in st.session_state:
        st.session_state.facility_display_name = 'Pharmacy chains'
    facility_display_name = st.session_state['facility_display_name']
    index = facility_display_names.index(facility_display_name)
    facility_display_name = st.selectbox(
        label='Choose a facility',
        options=facility_display_names,
        index=index,
        key='_facility_display_name',
        on_change=lambda: update_variable('facility_display_name'),
        help='Select the type of facility to analyze',
    )
    st.session_state.facility_display_name = facility_display_name
    facility = get_facility_from_facility_name(facilities, st.session_state.facility_display_name)

    return facility


def get_state_from_user():
    if 'state_name' not in st.session_state:
        st.session_state['state_name'] = get_state_of_the_day(interesting_states)
    state_of_the_day = st.session_state['state_name']
    st.selectbox(
        label='Choose a US state',
        options=state_names,
        index=state_names.index(state_of_the_day),
        key='_state_name',
        on_change=lambda: update_variable('state_name'),
    )

    State = USAState(st.session_state.state_name)
    return State


def get_poverty_threshold_from_user():
    if 'poverty_threshold' not in st.session_state:
        st.session_state['poverty_threshold'] = DEFAULT_POVERTY_THRESHOLD
    poverty_threshold = st.session_state['poverty_threshold']
    st.slider(
        label=r'Choose poverty threshold $p$%',
        min_value=0, max_value=100, step=5, value=poverty_threshold,
        key='_poverty_threshold',
        on_change=lambda: update_variable('poverty_threshold'),
        help='Only blockgroups with over $p$% of the population below the poverty line are considered ' + facility.type + ' deserts.',
    )

    return


def get_distance_thresholds_from_user():
    st.write('Choose distance threshold $n$ miles')
    col_side1, col_side2 = st.columns(2)

    if 'urban_distance_threshold' not in st.session_state:
        st.session_state['urban_distance_threshold'] = DEFAULT_URBAN_DISTANCE_THRESHOLD
    urban_distance_threshold = st.session_state['urban_distance_threshold']
    col_side1.slider(
        label=r'For urban areas',
        min_value=0.0, max_value=15.0, step=0.5, value=urban_distance_threshold,
        format='%.1f',
        key = '_urban_distance_threshold',
        on_change=lambda: update_variable('urban_distance_threshold'),
        help='Distance threshold for urban areas; only blockgroups further than this distance from the nearest facility are considered ' + facility.type + ' deserts.',
    )

    if 'rural_distance_threshold' not in st.session_state:
        st.session_state['rural_distance_threshold'] = DEFAULT_RURAL_DISTANCE_THRESHOLD
    rural_distance_threshold = st.session_state['rural_distance_threshold']
    col_side2.slider(
        label=r'For rural areas',
        min_value=0.0, max_value=30.0, step=1.0, value=rural_distance_threshold,
        format='%.1f',
        key='_rural_distance_threshold',
        on_change=lambda: update_variable('rural_distance_threshold'),
        help='Distance threshold for rural areas; only blockgroups further than this distance from the nearest facility are considered ' + facility.type + ' deserts.',
    )

    return


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

tab = sac.tabs(
    items=['Visualize Facility Deserts', 'Suggest New Facilities', 'Explanation'],
    index=1,
    align='center',
)

if tab == 'Visualize Facility Deserts':
    st.sidebar.caption('This tool aims to identify facility deserts in the US – poorer areas with low '
                       'access to various critical facilities such as pharmacies, hospitals, and schools.')

if tab == 'Suggest New Facilities':
    st.sidebar.caption('This tool suggests new facilities to reduce the number of facility deserts, based on '
                       'the optimization models in our [paper](https://arxiv.org/abs/2211.14873) on '
                       'fairness in facility location.')

facilities = [PharmaciesTop3, UrgentCare, Hospitals, NursingHomes, PrivateSchools, FDICInsuredBanks, ChildCare]
facility_display_names = [facility.display_name for facility in facilities]

if tab != 'Explanation':
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


if tab == 'Visualize Facility Deserts':
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

    st.markdown('''This tool aims to identify poorer areas with low access to various critical facilities.'''
                + facility.get_message(), unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2], gap='medium')

    with col2:
        st.caption(f'**Figure**: Census blockgroups classified as ' + facility.type + ' deserts in ' + State.name
                   + '. Colored by racial/ethnic majority.')
        col21, col22, col23 = st.columns(3)
        with col21:
            show_deserts = st.checkbox(facility.type.capitalize() + ' deserts', value=True)
        with col22:
            show_facility_locations = st.checkbox(facility.display_name, value=False)
        with col23:
            show_voronoi_cells = st.checkbox('''[Voronoi](https://en.wikipedia.org/wiki/Voronoi_diagram) cells''', value=False)

    with col1:
        fig = go.Figure()
        fig, bounds = plot_state(fig, State)

        distance_label = facility.distance_label
        desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, distance_label)

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
        demographics_all = get_demographic_data(census_df, racial_labels)
        n_blockgroups = len(census_df)

        demographics_deserts = get_demographic_data(desert_df, racial_labels)

        fig1, fig2 = plot_stacked_bar(demographics_all), plot_stacked_bar(demographics_deserts)

        st.markdown('''<center>''' + State.name + ''' has <b>''' + str(len(census_df)) + '''</b> blockgroups</center>''', unsafe_allow_html=True)
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

        st.markdown('''<center><b>''' + str(len(desert_df)) + '''</b> are ''' + facility.type + ''' deserts</center>''', unsafe_allow_html=True)
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

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
            Also check out our tool to suggest locations for new facilities to 
            reduce the impact of ''' + facility.type + ''' deserts.'''.format(facility.type), unsafe_allow_html=True
        )

    st.sidebar.caption('Created by Swati Gupta, [Jai Moondra](https://jaimoondra.github.io/), Mohit Singh.\n'
                       'Based on our [paper](https://arxiv.org/abs/2211.14873) on fairness in facility location.\n'
                       'Submit any feedback to [jmoondra3@gatech.edu](mailto:jmoondra3@gatech.edu).\n')

    st.sidebar.caption('We assume straight-line distances, and the accuracy of our results depends on the accuracy of the underlying data. '
                       'Map boundaries are approximate.')


if tab == 'Suggest New Facilities':
    def facility_names(facility):
        if facility.name == 'top_3_pharmacy_chains':
            return 'pharmacies'
        else:
            return facility.display_name.lower()


    st.markdown("""
        <h1 style="font-size: 40px; text-align: center; margin-bottom: 0em; margin-top: 0em; line-height: 1.0;">
             Suggesting new """ + facility_names(facility) + """ in
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

        original_desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, old_distance_label)
        new_desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, new_distance_label)

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
            st.caption('Figure: Suggested new facilities in the three solutions based on different optimization models')

            original_desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, old_distance_label)
            original_demographic_data = get_demographic_data(original_desert_df, racial_labels)
            original_medical_deserts = str(sum(original_demographic_data.values()))
            st.markdown('''<center>Original ''' + facility.type + ''' deserts (''' + original_medical_deserts + ''')</center>''', unsafe_allow_html=True)
            fig_original = plot_stacked_bar(original_demographic_data)
            st.plotly_chart(fig_original, use_container_width=True, config={'displayModeBar': False})

            st.markdown('''<center>Remaining ''' + str(facility.type) + ''' deserts</center>''', unsafe_allow_html=True)

            combined_solution_label = facility.distance_label + '_combined_k_' + str(k)
            if k == 0:
                combined_solution_label = old_distance_label
            new_desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, combined_solution_label)
            new_demographic_data = get_demographic_data(new_desert_df, racial_labels)
            new_medical_deserts = str(sum(new_demographic_data.values()))
            st.markdown('''<center>Proposed solution (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
            new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
            fig_new = plot_stacked_bar(new_demographic_data)
            st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})

            solution_1_distance_label = facility.distance_label + '_p_1_k_' + str(k)
            if k == 0:
                solution_1_distance_label = old_distance_label
            new_desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, solution_1_distance_label)
            new_demographic_data = get_demographic_data(new_desert_df, racial_labels)
            new_medical_deserts = str(sum(new_demographic_data.values()))
            st.markdown('''<center>Solution 1 (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
            new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
            fig_new = plot_stacked_bar(new_demographic_data)
            st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})

            solution_2_distance_label = facility.distance_label + '_p_2_k_' + str(k)
            if k == 0:
                solution_2_distance_label = old_distance_label
            new_desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, solution_2_distance_label)
            new_demographic_data = get_demographic_data(new_desert_df, racial_labels)
            new_medical_deserts = str(sum(new_demographic_data.values()))
            st.markdown('''<center>Solution 2 (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
            new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
            fig_new = plot_stacked_bar(new_demographic_data)
            st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})

            solution_inf_distance_label = facility.distance_label + '_p_inf_k_' + str(k)
            if k == 0:
                solution_inf_distance_label = old_distance_label
            new_desert_df = compute_medical_deserts(census_df, st.session_state.poverty_threshold, st.session_state.urban_distance_threshold, st.session_state.rural_distance_threshold, solution_inf_distance_label)
            new_demographic_data = get_demographic_data(new_desert_df, racial_labels)
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

