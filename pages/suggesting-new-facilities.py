from ast import literal_eval
from datetime import datetime
import geopandas as gpd
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.constants import DEFAULT_POVERTY_THRESHOLD, DEFAULT_RURAL_DISTANCE_THRESHOLD, DEFAULT_URBAN_DISTANCE_THRESHOLD
from src.usa.constants import state_names, racial_label_dict, populous_states, interesting_states
from src.usa.states import USAState
from src.usa.facilities import (UrgentCare, Hospitals, NursingHomes,
    ChildCare, PrivateSchools, FDICInsuredBanks, PharmaciesTop3)
from src.usa.utils import racial_labels, compute_medical_deserts, get_demographic_data
from src.usa.plot_utils import plot_state, plot_stacked_bar, plot_existing_facilities, plot_blockgroups, plot_new_facilities


def get_page_url(page_name):
    is_deployed = st.secrets.get('IS_DEPLOYED')
    if is_deployed:
        return 'https://usa-medical-deserts.streamlit.app/' + page_name
    else:
        return 'https://usa-medical-deserts.streamlit.app/' + page_name
        # return 'http://localhost:8501/' + page_name


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
    def update_facility_display_name():
        st.session_state['facility_display_name'] = st.session_state['facility_display_name_new']

    if 'facility_display_name' in st.session_state:
        facility_display_name = st.session_state['facility_display_name']
        index = facility_display_names.index(facility_display_name)
    else:
        index = 0
    facility_display_name = st.selectbox(label='Choose a facility', options=facility_display_names, index=index, key='facility_display_name_new',
                                         help='Select the type of facility to analyze', on_change=update_facility_display_name)
    facility = get_facility_from_facility_name(facilities, facility_display_name)

    def update_state_name():
        st.session_state['state_name'] = st.session_state['state_name_new']

    state_of_the_day = state_of_the_day(interesting_states)
    if 'state_name' in st.session_state:
        state_of_the_day = st.session_state['state_name']
    state_name = st.selectbox('Choose a US state', options=state_names, index=state_names.index(state_of_the_day), key='state_name_new', on_change=update_state_name)

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

# We present three solutions based on three different optimization models; each solution suggests up to 100 new facilities.


with st.sidebar:
    def update_poverty_threshold():
        st.session_state['poverty_threshold'] = st.session_state['poverty_threshold_new']

    with st.container(border=True):
        if 'poverty_threshold' in st.session_state:
            poverty_threshold = st.session_state['poverty_threshold']
        else:
            poverty_threshold = DEFAULT_POVERTY_THRESHOLD
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
        if 'urban_distance_threshold' in st.session_state:
            urban_distance_threshold = st.session_state['urban_distance_threshold']
        else:
            urban_distance_threshold = DEFAULT_URBAN_DISTANCE_THRESHOLD
        urban_distance_threshold = col_side1.slider(r'For urban areas', min_value=0.0, max_value=15.0, step=0.5,
                         value=urban_distance_threshold, format='%.1f', key='urban_distance_threshold_new',
                         help='Distance threshold for urban areas; only blockgroups further than this distance from the nearest facility are considered ' + facility.type + ' deserts.',
                                                    on_change=update_urban_distance_threshold)

        if 'rural_distance_threshold' in st.session_state:
            rural_distance_threshold = st.session_state['rural_distance_threshold']
        else:
            rural_distance_threshold = DEFAULT_RURAL_DISTANCE_THRESHOLD
        rural_distance_threshold = col_side2.slider(r'For rural areas', min_value=0.0, max_value=30.0, step=1.0,
                         value=rural_distance_threshold, format='%.1f', key='rural_distance_threshold_new',
                         help='Distance threshold for rural areas; only blockgroups further than this distance from the nearest facility are considered ' + facility.type + ' deserts.',
                                                    on_change=update_rural_distance_threshold)


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

    # with st.popover(label='Figure options', use_container_width=True):
    #     show_deserts = st.checkbox(label='Show medical deserts', value=False)
    #     show_existing_facilities = st.checkbox(label='Show existing facilities', value=True)
    #     show_new_facilities = st.checkbox(label='Show new facilities', value=True)


with col1:
    old_distance_label = facility.distance_label
    new_distance_label = facility.distance_label + '_combined_k_' + str(k)
    if k == 0:
        new_distance_label = old_distance_label

    new_facilities = pd.read_csv('data/usa/new_facilities/' + facility.name + '/new_facilities_combined.csv', index_col=0)['100'].apply(literal_eval)
    new_facilities = new_facilities[state_name][:k]

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
        fig = plot_new_facilities(fig, new_facilities[:k], census_df, name='Suggested facilities')

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


def norm_column_1(norm, census_df, k):
    # solution = {'1': '1', '2': '2', 'inf': '3'}
    # st.markdown('''<h4 style='text-align: center; color: black;'>Solution ''' + solution[norm] + '''</h4>''', unsafe_allow_html=True)

    old_distance_label = facility.distance_label
    new_distance_label = facility.distance_label + '_p_' + norm + '_k_' + str(k)
    if k == 0:
        new_distance_label = old_distance_label

    new_facilities = pd.read_csv('data/usa/new_facilities/' + facility.name + '/new_facilities_' + norm + '.csv', index_col=0)['100'].apply(literal_eval)
    new_facilities = new_facilities[state_name][:k]

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
        fig = plot_new_facilities(fig, new_facilities[:k], census_df, name='Suggested Facilities')

    st.plotly_chart(fig, use_container_width=True)


def norm_column_2(norm, census_df, k):
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


with st.expander(label='How does this work?'):
    st.markdown('''
        Under the hood, our proposed solution above is a combination of three distinct solutions, each of which suggests 
         locations of up to 100 new facilities. These solutions optimize different aspects of fairness, and 
        are based on minimizing the $L_1$, $L_2$, and $L_\infty$ norms respectively of the distances of people in 
        various demographic groups from the nearest facility (see our [paper](https://arxiv.org/abs/2211.14873) for more details). You can compare the three solutions in the figure below.
    ''')

    col1, col2 = st.columns([3, 2], gap='medium')

    with col1:
        facilities_1 = pd.read_csv('data/usa/new_facilities/' + facility.name + '/new_facilities_1.csv', index_col=0)['100'].apply(literal_eval)
        facilities_1 = set(facilities_1[state_name][:k])
        facilities_2 = pd.read_csv('data/usa/new_facilities/' + facility.name + '/new_facilities_2.csv', index_col=0)['100'].apply(literal_eval)
        facilities_2 = set(facilities_2[state_name][:k])
        facilities_inf = pd.read_csv('data/usa/new_facilities/' + facility.name + '/new_facilities_inf.csv', index_col=0)['100'].apply(literal_eval)
        facilities_inf = set(facilities_inf[state_name][:k])
        facilities_combined = pd.read_csv('data/usa/new_facilities/' + facility.name + '/new_facilities_combined.csv', index_col=0)['100'].apply(literal_eval)
        facilities_combined = set(facilities_combined[state_name][:k])
        all_facilities = facilities_1.union(facilities_2).union(facilities_inf)

        fillcolors = {
            facility: 'aqua' if facility in facilities_combined else 'grey' for facility in all_facilities
        }
        colors = {
            facility: 'blue' if facility in facilities_combined else 'black' for facility in all_facilities
        }

        col11, col21, col31 = st.columns(3)
        with col11:
            show_solution1 = st.checkbox('Show solution 1', value=True)
        with col21:
            show_solution2 = st.checkbox('Show solution 2', value=True)
        with col31:
            show_solution3 = st.checkbox('Show solution 3', value=True)

        show_label1, show_label2, show_label3 = True, True, True

        fig = go.Figure()
        fig, bounds = plot_state(fig, State)
        if show_solution1:
            for f in facilities_1:
                fig.add_trace(
                    go.Scattergeo(
                        lon=[census_df.loc[f]['Longitude']], lat=[census_df.loc[f]['Latitude']],
                        mode='markers',
                        marker=dict(
                            size=8,
                            color=fillcolors[f],
                            opacity=0.8,
                            symbol='diamond'
                        ),
                        name='Facilities in solution 1',
                        showlegend=show_label1,
                    ))
                show_label1 = False
        if show_solution2:
            for f in facilities_2:
                fig.add_trace(
                    go.Scattergeo(
                        lon=[census_df.loc[f]['Longitude']], lat=[census_df.loc[f]['Latitude']],
                        mode='markers',
                        marker=dict(
                            size=8,
                            color='rgba(0, 0, 0, 0)',
                            symbol='diamond',
                            line=dict(
                                width=2.0,
                                color=colors[f],
                            )
                        ),
                        name='Facilities in solution 2',
                        showlegend=show_label2,
                    ))
                show_label2 = False
        if show_solution3:
            for f in facilities_inf:
                fig.add_trace(
                    go.Scattergeo(
                        lon=[census_df.loc[f]['Longitude']], lat=[census_df.loc[f]['Latitude']],
                        mode='markers',
                        marker=dict(
                            size=8,
                            opacity=0.8,
                            symbol='cross-thin',
                            color='rgba(0, 0, 0, 0)',
                            line=dict(
                                width=2.0,
                                color=colors[f]
                            )
                        ),
                        name='Facilities in solution 3',
                        showlegend=show_label3,
                    ))
                show_label3 = False

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


