import pandas as pd
import math
import numpy as np
from ast import literal_eval
from bisect import bisect_left
from src.usa.plot_utils import plot_new_facilities, plot_state, plot_stacked_bar
from src.usa.utils import compute_medical_deserts, get_demographic_data, racial_labels
from src.facility_location.utils import compute_minimum_distances
from haversine import haversine
from src.usa.states import USAState
from src.usa.constants import state_names, racial_label_dict
import streamlit as st
import plotly.graph_objects as go


st.set_page_config(layout="wide", page_title="suggesting-new-facilities-combined")

state_name = st.sidebar.selectbox("Select a state", state_names)
State = USAState(state_name)
census_df = State.get_census_data(level='blockgroup')

k = st.sidebar.select_slider("Number of new facilities", options=[0, 5, 10, 25, 50, 100], value=10)

facility_name = st.sidebar.selectbox("Select a facility type", ["top_3_pharmacy_chains"])

df1 = pd.read_csv('data/usa/new_facilities/' + facility_name + '/new_facilities_1.csv', index_col=0)
df2 = pd.read_csv('data/usa/new_facilities/' + facility_name + '/new_facilities_2.csv', index_col=0)
df3 = pd.read_csv('data/usa/new_facilities/' + facility_name + '/new_facilities_inf.csv', index_col=0)

solutions = {
    1: literal_eval(df1.loc[state_name]['100']),
    2: literal_eval(df2.loc[state_name]['100']),
    3: literal_eval(df3.loc[state_name]['100'])
}

list_of_facilities = set(solutions[1] + solutions[2] + solutions[3])

poverty_threshold = st.sidebar.slider("Poverty threshold", 0, 100, 20, step=5)
n_urban = st.sidebar.slider("Urban distance threshold", 0.0, 15.0, 2.0, step=0.5)
n_rural = st.sidebar.slider("Rural distance threshold", 0.0, 30.0, 10.0, step=1.0)


def get_facility_weights(solutions):
    weights = dict()
    thresholds = [5, 10, 25, 50, 100, np.inf]

    for facility in set(solutions[1] + solutions[2] + solutions[3]):
        weights[facility] = 0
        for i in range(1, 4):
            if facility in solutions[i]:
                id = solutions[i].index(facility)
                threshold = bisect_left(a=thresholds, x=id)
                weights[facility] += math.pow(1/thresholds[threshold], 1)

    return weights


weights = get_facility_weights(solutions)


def compute_distances_to_facility(facility_longitude, facility_latitude, longitudes, latitudes):
    distances = []
    for i in range(len(longitudes)):
        distances.append(haversine(point1=(facility_latitude, facility_longitude), point2=(latitudes[i], longitudes[i])))

    return distances


def facility_gain(distances_to_existing_facilities, distances_to_facility, urban, weight):
    reduction = 0
    for i in range(len(distances_to_existing_facilities)):
        facility_gain = distances_to_existing_facilities[i] - distances_to_facility[i]
        facility_gain = max(facility_gain, 0)
        if urban[i]:
            facility_gain = facility_gain * 5
        reduction = reduction + facility_gain

    return reduction * weight


def find_facility_with_highest_score(scores):
    facility = -1
    score = 0
    for f in scores.keys():
        if scores[f] >= score:
            facility = f
            score = scores[f]

    return facility


def compute_new_minimum_distances(distances_to_existing_facilities, distances_to_facility):
    new_distances = []
    for i in range(len(distances_to_existing_facilities)):
        new_distances.append(min(distances_to_existing_facilities[i], distances_to_facility[i]))

    return new_distances


def greedy_algorithm(list_of_new_facilities, census_df, K=25):
    facilities_output_order = []
    existing_distances = list(census_df['closest_distance_' + facility_name])
    longitudes = list(census_df['Longitude'])
    latitudes = list(census_df['Latitude'])
    urban = list(census_df['urban'])

    distances_to_new_facilities = {
        facility: compute_distances_to_facility(census_df.loc[facility]['Longitude'], census_df.loc[facility]['Latitude'], longitudes, latitudes) for facility in list_of_new_facilities
    }
    weights = get_facility_weights(solutions)

    while len(facilities_output_order) < K:
        scores = dict()
        for facility in list_of_new_facilities:
            scores[facility] = facility_gain(existing_distances, distances_to_new_facilities[facility], urban, weights[facility])

        f = find_facility_with_highest_score(scores)
        facilities_output_order.append(f)
        list_of_new_facilities.remove(f)

        existing_distances = compute_new_minimum_distances(existing_distances, distances_to_new_facilities[f])

    return facilities_output_order, existing_distances


facilities_final_order, existing_distances = greedy_algorithm(list_of_facilities, census_df, K=k)
new_distance_label = 'closest_distance_' + facility_name + '_new'
census_df[new_distance_label] = existing_distances
all_facilities = {facility: 1 for facility in facilities_final_order}


def analyze_new_facilities(k, census_df, poverty_threshold=20, n_urban=2, n_rural=10):
    new_facilities = list(all_facilities.keys())[:k]
    census_df = compute_minimum_distances(census_df=census_df, facilities=new_facilities,
                                          existing_distances_label='closest_distance_' + facility_name,
                                          new_distances_label='temp_distance'
                                          )
    desert_df = compute_medical_deserts(state_df=census_df, poverty_threshold=poverty_threshold,
                                        n_urban=n_urban, n_rural=n_rural, distance_label='temp_distance')
    fig = go.Figure()
    fig, bounds = plot_state(fig, State)
    fig = plot_new_facilities(fig, list(all_facilities.keys())[:k], census_df)
    # fig = plot_blockgroups(fig, desert_df)

    return fig, len(desert_df)


col1, col2 = st.columns([3, 2])

with col2:
    with st.popover('Figure options', use_container_width=True):
        show_deserts = st.checkbox('Show ' + 'medical' + ' deserts', value=True)
        show_facility_locations = st.checkbox('Show ' + facility_name, value=False)
        show_voronoi_cells = st.checkbox('''Show [Voronoi](https://en.wikipedia.org/wiki/Voronoi_diagram) cells''', value=False)

with col1:
    fig, n_deserts = analyze_new_facilities(k=k, census_df=census_df, n_urban=2, n_rural=10)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    original_desert_df = compute_medical_deserts(census_df, poverty_threshold, n_urban, n_rural, 'closest_distance_' + facility_name)
    original_demographic_data = get_demographic_data(original_desert_df, racial_labels)
    original_medical_deserts = str(sum(original_demographic_data.values()))
    st.markdown('''<center>Original medical deserts (''' + original_medical_deserts + ''')</center>''', unsafe_allow_html=True)
    fig_original = plot_stacked_bar(original_demographic_data)
    st.plotly_chart(fig_original, use_container_width=True, config={'displayModeBar': False})

    new_desert_df = compute_medical_deserts(census_df, poverty_threshold, n_urban, n_rural, new_distance_label)
    new_demographic_data = get_demographic_data(new_desert_df, racial_labels)
    new_medical_deserts = str(sum(new_demographic_data.values()))
    st.markdown('''<center>Remaining medical deserts (''' + new_medical_deserts + ''')</center>''', unsafe_allow_html=True)
    new_demographic_data['no_desert'] = sum(original_demographic_data.values()) - sum(new_demographic_data.values())
    fig_new = plot_stacked_bar(new_demographic_data)
    st.plotly_chart(fig_new, use_container_width=True, config={'displayModeBar': False})
