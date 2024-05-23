from datetime import datetime
import geopandas as gpd
import plotly.graph_objects as go
import random
import pandas as pd
from src.constants import MILES_TO_KM
from src.usa.constants import state_names, racial_label_dict
from src.usa.states import USAState
from src.usa.facilities_data_handler import (
    CVS, Walgreens, Walmart, UrgentCare, Hospitals, DialysisCenters, NursingHomes,
    ChildCare, PrivateSchools, FDICInsuredBanks, DHL, UPS, FedEx, PharmaciesTop3)
import streamlit as st
import streamlit_antd_components as sac
from streamlit_extras.switch_page_button import switch_page
from src.usa.states import USAState
import numpy as np
from haversine import haversine
import csv
import ast


def plot_old_facilities(fig, facility_df):
    longitudes = facility_df.geometry.x
    latitudes = facility_df.geometry.y
    color='black'

    fig.add_trace(go.Scattergeo(
        lon=longitudes,
        lat=latitudes,
        mode='markers',
        marker=dict(
            size=5,
            color=color,
            opacity=0.8,
            symbol='x'
        ),
        name='Existing CVS/Walgreens/Walmart Pharmacies'
    ))

    return fig


def plot_new_facilities(fig, facilities, census_dataframe):
    longitudes = [census_dataframe.loc[i]['Longitude'] for i in facilities]
    latitudes = [census_dataframe.loc[i]['Latitude'] for i in facilities]
    color='red'

    fig.add_trace(go.Scattergeo(
        lon=longitudes,
        lat=latitudes,
        mode='markers',
        marker=dict(
            size=10,
            color=color,
            opacity=0.8,
            symbol='x'
        ),
        name='Suggested New Facilities'
    ))

    return fig


def plot_blockgroups(fig, blockgroup_df):
    longitudes = blockgroup_df.Longitude
    latitudes = blockgroup_df.Latitude
    fig.add_trace(go.Scattergeo(
        lon=longitudes,
        lat=latitudes,
        mode='markers',
        marker=dict(
            size=4,
            color='blue',
            opacity=0.5,
            symbol='circle'
        ),
    ))

    return fig


def get_bounds(blockgroup_df):
    latitudes = blockgroup_df.Latitude
    longitudes = blockgroup_df.Longitude
    lat_min, lat_max = latitudes.min(), latitudes.max()
    lat_diff = lat_max - lat_min
    lat_min = lat_min - 0.1 * lat_diff
    lat_max = lat_max + 0.1 * lat_diff

    lon_min, lon_max = longitudes.min(), longitudes.max()
    lon_diff = lon_max - lon_min
    lon_min = lon_min - 0.1 * lon_diff
    lon_max = lon_max + 0.1 * lon_diff

    return [(lat_min, lat_max), (lon_min, lon_max)]


def compute_distances_to_new_facilities(census_dataframe, new_facilities):
    n = len(census_dataframe)
    f = len(new_facilities)

    # facility_longitudes = [census_dataframe.iloc[i]['Longitude'] for i in new_facilities]
    # facility_latitudes = [census_dataframe.iloc[i]['Latitude'] for i in new_facilities]

    for j in census_dataframe.index:
        best_distance = np.inf

        lat_j = census_dataframe.loc[j]['Latitude']
        lon_j = census_dataframe.loc[j]['Longitude']
        for i in new_facilities:
            facility_lat = census_dataframe.loc[i]['Latitude']
            facility_lon = census_dataframe.loc[i]['Longitude']
            distance = haversine((lat_j, lon_j), (facility_lat, facility_lon))
            if distance < best_distance:
                best_distance = distance

        census_dataframe.at[j, 'Distance to new facility'] = best_distance

    return census_dataframe


def add_new_minimum_distances(census_dataframe, facilities,
                              old_distance_label='Closest_Distance_Pharmacies_Top3',
                              new_distance_label='New_Closest_Distance'):
    census_dataframe = compute_distances_to_new_facilities(census_dataframe, facilities)

    for j in census_dataframe.index:
        # census_dataframe.at[j, new_distance_label] = census_dataframe.at[j, 'Distance to new facility']
        census_dataframe.at[j, new_distance_label] = min(census_dataframe.at[j, old_distance_label],
                                                         census_dataframe.at[j, 'Distance to new facility'])

    return census_dataframe


def compute_medical_deserts(census_dataframe, poverty_threshold=20,
                            urban_distance_threshold=2, rural_distance_threshold=5,
                            distance_label='New_Closest_Distance'):
    medical_deserts = census_dataframe[census_dataframe['below_poverty'] >= poverty_threshold]
    medical_deserts = medical_deserts[
        (medical_deserts['urban'] &
         (medical_deserts['New_Closest_Distance'] >= urban_distance_threshold * MILES_TO_KM)) |
        (~medical_deserts['urban'] &
         (medical_deserts['New_Closest_Distance'] >= rural_distance_threshold * MILES_TO_KM))
        ]
    return medical_deserts


def get_racial_demographic_summary(census_dataframe):
    n = len(census_dataframe)
    summary_absolute = census_dataframe.racial_majority.value_counts()
    summary_fractions = census_dataframe.racial_majority.value_counts(normalize=True)

    racial_summary = {}
    for key in racial_label_dict.keys():
        name = racial_label_dict[key]
        racial_summary[name] = {
            'absolute': summary_absolute.get(key, 0),
            'fraction': summary_fractions.get(key, 0)
        }
    racial_summary['All'] = {
        'absolute': n,
        'fraction': 1
    }

    racial_summary = pd.DataFrame(racial_summary)

    return racial_summary


def plot_state_boundary(fig, state_abbreviation):
    data = pd.DataFrame({
        'state': ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'],
        'value': [1] * 50  # Default value for all states
    })
    # Set a different value for the state to highlight it
    data.loc[data['state'] == state_abbreviation, 'value'] = 2

    choropleth = go.Choropleth(
        locations=data['state'],  # Spatial coordinates
        z=data['value'].astype(float),  # Data to be color-coded
        locationmode='USA-states',  # Set of locations match entries in `locations`
        colorscale=["#fbfcf9", "#f9f3e1"],  # Color scale for the choropleth map
        showscale=False,
    )

    # Add the choropleth map to the figure
    fig.add_trace(choropleth)

    return fig


scatter_palette = [
    '#007fee',          # Blue
    '#21d565',          # Green
    '#ffe00a',          # Yellow
    '#ff7700',          # Orange
    '#8bff08',          # Lime
    '#9918fe',          # Purple
    '#ff0004',          # Red
    '#179c49',          # Dark Green
    '#00318f',          # Dark Blue
    '#ff1f70',          # Pink
    '#af7b00',          # Brown
    '#ff517c',          # Light Pink
    '#d36969',          # Light Red
    '#18fe90'           # Light Green
]

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

k = st.slider('Number of facilities', 0, 75, 5, 1)

with st.sidebar:
    show_deserts = st.checkbox('Show medical deserts', value=False)
    show_non_deserts = st.checkbox('Show non-medical deserts', value=False)
    poverty_threshold = st.slider('Poverty threshold (%)', 0, 100, 20, 1)
    urban_distance_threshold = st.slider('Urban distance threshold (miles)', 0, 10, 2, 1)
    rural_distance_threshold = st.slider('Rural distance threshold (miles)', 0, 20, 10, 1)
# Get the current day of the year

state_name = 'Mississippi'
State = USAState(state_name)
state_abbr = State.abbreviation
state_fips = State.fips

blockgroup_df = State.get_census_data(level='blockgroup')
blockgroup_df = blockgroup_df.dropna(axis=0, subset=['two_health_ins'])
blockgroup_df.index = range(len(blockgroup_df))
blockgroup_df['urban'] = blockgroup_df['urban'].fillna(False)

n = len(blockgroup_df)

# Facilities - already existing
facility_df = PharmaciesTop3.read_abridged_facilities()
# facility_df = facility_df[facility_df.index == state_abbr]

df = pd.read_csv('.local/suggesting-facilities-experiment-2/Mississippi_facilities.csv')
facilities_1 = df[(df['p'] == 1)].Facility.values
facilities_1 = list(ast.literal_eval(facilities_1[0])) \
               + list(ast.literal_eval(facilities_1[1])) \
               + list(ast.literal_eval(facilities_1[2])) \
               + list(ast.literal_eval(facilities_1[3]))

facilities_2 = df[(df['p'] == 2)].Facility.values
facilities_2 = list(ast.literal_eval(facilities_2[0])) \
               + list(ast.literal_eval(facilities_2[1])) \
               + list(ast.literal_eval(facilities_2[2])) \
               + list(ast.literal_eval(facilities_2[3]))

facilities_inf = df[(df['p'] == np.inf)].Facility.values
facilities_inf = list(ast.literal_eval(facilities_inf[0])) \
                 + list(ast.literal_eval(facilities_inf[1])) \
                 + list(ast.literal_eval(facilities_inf[2])) \
                 + list(ast.literal_eval(facilities_inf[3]))

col1, col2, col3 = st.columns(3)

randomly_shuffled_indices = list(range(1, 8))
random.shuffle(randomly_shuffled_indices)

with col1:
    fig = go.Figure()

    fig = plot_state_boundary(fig, state_abbr)
    bounds = get_bounds(blockgroup_df)
    fig = plot_old_facilities(fig, facility_df)
    fig = plot_new_facilities(fig, facilities_1[:k], blockgroup_df)

    blockgroup_df = State.get_census_data(level='blockgroup')
    blockgroup_df = blockgroup_df.dropna(axis=0, subset=['two_health_ins'])
    blockgroup_df.index = range(len(blockgroup_df))
    blockgroup_df['urban'] = blockgroup_df['urban'].fillna(False)

    blockgroup_df = add_new_minimum_distances(blockgroup_df, facilities_1[:k],
                                              old_distance_label='Closest_Distance_Pharmacies_Top3',
                                              new_distance_label='New_Closest_Distance')

    desert_df = compute_medical_deserts(blockgroup_df, poverty_threshold=poverty_threshold,
                                        urban_distance_threshold=urban_distance_threshold,
                                        rural_distance_threshold=rural_distance_threshold,
                                        distance_label='New_Closest_Distance')

    if show_deserts:
        for i in randomly_shuffled_indices:
            desert_df_i = desert_df[desert_df['racial_majority'] == i]
            if len(desert_df_i) > 0:
                fig.add_trace(
                    go.Scattergeo(
                        name=racial_label_dict[i],
                        lon=desert_df_i['Longitude'],
                        lat=desert_df_i['Latitude'],
                        marker=dict(
                            color=scatter_palette[i - 1],
                            opacity=0.6,
                            line=dict(
                                width=1.0,
                                color='rgba(0, 0, 0, 0.9)',
                            ))))

    if show_non_deserts:
        non_desert_df = blockgroup_df[~blockgroup_df.index.isin(desert_df.index)]
        non_desert_df = non_desert_df[non_desert_df['below_poverty'] >= poverty_threshold]
        for i in randomly_shuffled_indices:
            non_desert_df_i = non_desert_df[non_desert_df['racial_majority'] == i]
            if len(non_desert_df_i) > 0:
                fig.add_trace(
                    go.Scattergeo(
                        name=racial_label_dict[i],
                        lon=non_desert_df_i['Longitude'],
                        lat=non_desert_df_i['Latitude'],
                        marker=dict(
                            color=scatter_palette[i - 1],
                            opacity=0.6,
                            line=dict(
                                width=1.0,
                                color='rgba(0, 0, 0, 0.9)',
                            ))))

    config = {
            'modeBarButtonsToRemove': ['zoomOut', 'select2d'],
            'staticPlot': False,
            'scrollZoom': True,
            'toImageButtonOptions': {
                'format': 'png',
                'scale': 1.5,
                'filename': 'open_facilities_' + str(1) + '_' + str(k) + '.png',
            }
        }

    fig.update_geos(
        showland=True,
        showcoastlines=True,
        showframe=False,
        showocean=True,
        showcountries=True,
        showrivers=True,
        rivercolor='#a4b8b7',
        showlakes=True,
        lakecolor='#a4b8b7',
        oceancolor='#a4b8b7',
        landcolor='#fbfcf9',
        scope="north america",
        lonaxis_range=[bounds[1][0], bounds[1][1]],
        lataxis_range=[bounds[0][0], bounds[0][1]],
        projection_type='mercator',
        # bgcolor='#a1b8b7',
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        autosize=True,
        xaxis=dict(range=[bounds[1][0], bounds[1][1]], autorange=False),
        yaxis=dict(range=[bounds[0][0], bounds[0][1]], autorange=False),
        showlegend=True,
        legend=dict(
            itemsizing='constant',
            x=0.10,
            y=1.12,
            orientation='v',
            bgcolor='rgba(255,255,255,0.5)',
        )
    )

    st.plotly_chart(fig, use_container_width=True, config=config)

    st.write('Number of medical deserts:', len(desert_df))
    desert_df_summary = desert_df.racial_majority.value_counts(normalize=True)
    st.write(desert_df_summary)


with col2:
    fig = go.Figure()

    fig = plot_state_boundary(fig, state_abbr)
    bounds = get_bounds(blockgroup_df)
    fig = plot_old_facilities(fig, facility_df)
    fig = plot_new_facilities(fig, facilities_2[:k], blockgroup_df)

    blockgroup_df = State.get_census_data(level='blockgroup')
    blockgroup_df = blockgroup_df.dropna(axis=0, subset=['two_health_ins'])
    blockgroup_df.index = range(len(blockgroup_df))
    blockgroup_df['urban'] = blockgroup_df['urban'].fillna(False)


    blockgroup_df = add_new_minimum_distances(blockgroup_df, facilities_2[:k],
                                              old_distance_label='Closest_Distance_Pharmacies_Top3',
                                              new_distance_label='New_Closest_Distance')

    desert_df = compute_medical_deserts(blockgroup_df, poverty_threshold=poverty_threshold,
                                        urban_distance_threshold=urban_distance_threshold,
                                        rural_distance_threshold=rural_distance_threshold,
                                        distance_label='New_Closest_Distance')

    if show_deserts:
        for i in randomly_shuffled_indices:
            desert_df_i = desert_df[desert_df['racial_majority'] == i]
            if len(desert_df_i) > 0:
                fig.add_trace(
                    go.Scattergeo(
                        name=racial_label_dict[i],
                        lon=desert_df_i['Longitude'],
                        lat=desert_df_i['Latitude'],
                        marker=dict(
                            color=scatter_palette[i - 1],
                            opacity=0.6,
                            line=dict(
                                width=1.0,
                                color='rgba(0, 0, 0, 0.9)',
                            ))))

    if show_non_deserts:
        non_desert_df = blockgroup_df[~blockgroup_df.index.isin(desert_df.index)]
        non_desert_df = non_desert_df[non_desert_df['below_poverty'] >= poverty_threshold]
        for i in randomly_shuffled_indices:
            non_desert_df_i = non_desert_df[non_desert_df['racial_majority'] == i]
            if len(non_desert_df_i) > 0:
                fig.add_trace(
                    go.Scattergeo(
                        name=racial_label_dict[i],
                        lon=non_desert_df_i['Longitude'],
                        lat=non_desert_df_i['Latitude'],
                        marker=dict(
                            color=scatter_palette[i - 1],
                            opacity=0.6,
                            line=dict(
                                width=1.0,
                                color='rgba(0, 0, 0, 0.9)',
                            ))))

    config = {
        'modeBarButtonsToRemove': ['zoomOut', 'select2d'],
        'staticPlot': False,
        'scrollZoom': True,
        'toImageButtonOptions': {
            'format': 'png',
            'scale': 1.5,
            'filename': 'open_facilities_' + str(2) + '_' + str(k) + '.png',
        }
    }

    fig.update_geos(
        showland=True,
        showcoastlines=True,
        showframe=False,
        showocean=True,
        showcountries=True,
        showlakes=True,
        lakecolor='#a4b8b7',
        oceancolor='#a4b8b7',
        landcolor='#fbfcf9',
        scope="north america",
        lonaxis_range=[bounds[1][0], bounds[1][1]],
        lataxis_range=[bounds[0][0], bounds[0][1]],
        projection_type='mercator',
        # bgcolor='#a1b8b7',
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        autosize=True,
        xaxis=dict(range=[bounds[1][0], bounds[1][1]], autorange=False),
        yaxis=dict(range=[bounds[0][0], bounds[0][1]], autorange=False),
        showlegend=True,
        legend=dict(
            itemsizing='constant',
            x=0.10,
            y=1.12,
            orientation='v',
            bgcolor='rgba(255,255,255,0.5)',
        )
    )

    st.plotly_chart(fig, use_container_width=True, config=config)

    st.write('Number of medical deserts:', len(desert_df))
    desert_df_summary = desert_df.racial_majority.value_counts(normalize=True)
    st.write(desert_df_summary)


with col3:
    fig = go.Figure()

    fig = plot_state_boundary(fig, state_abbr)
    bounds = get_bounds(blockgroup_df)
    fig = plot_old_facilities(fig, facility_df)
    fig = plot_new_facilities(fig, facilities_inf[:k], blockgroup_df)

    blockgroup_df = State.get_census_data(level='blockgroup')
    blockgroup_df = blockgroup_df.dropna(axis=0, subset=['two_health_ins'])
    blockgroup_df.index = range(len(blockgroup_df))
    blockgroup_df['urban'] = blockgroup_df['urban'].fillna(False)


    blockgroup_df = add_new_minimum_distances(blockgroup_df, facilities_inf[:k],
                                              old_distance_label='Closest_Distance_Pharmacies_Top3',
                                              new_distance_label='New_Closest_Distance')

    desert_df = compute_medical_deserts(blockgroup_df, poverty_threshold=poverty_threshold,
                                        urban_distance_threshold=urban_distance_threshold,
                                        rural_distance_threshold=rural_distance_threshold,
                                        distance_label='New_Closest_Distance')

    if show_deserts:
        for i in randomly_shuffled_indices:
            desert_df_i = desert_df[desert_df['racial_majority'] == i]
            if len(desert_df_i) > 0:
                fig.add_trace(
                    go.Scattergeo(
                        name=racial_label_dict[i],
                        lon=desert_df_i['Longitude'],
                        lat=desert_df_i['Latitude'],
                        marker=dict(
                            color=scatter_palette[i - 1],
                            opacity=0.6,
                            line=dict(
                                width=1.0,
                                color='rgba(0, 0, 0, 0.9)',
                            ))))

    if show_non_deserts:
        non_desert_df = blockgroup_df[~blockgroup_df.index.isin(desert_df.index)]
        non_desert_df = non_desert_df[non_desert_df['below_poverty'] >= poverty_threshold]
        for i in randomly_shuffled_indices:
            non_desert_df_i = non_desert_df[non_desert_df['racial_majority'] == i]
            if len(non_desert_df_i) > 0:
                fig.add_trace(
                    go.Scattergeo(
                        name=racial_label_dict[i],
                        lon=non_desert_df_i['Longitude'],
                        lat=non_desert_df_i['Latitude'],
                        marker=dict(
                            color=scatter_palette[i - 1],
                            opacity=0.6,
                            line=dict(
                                width=1.0,
                                color='rgba(0, 0, 0, 0.9)',
                            ))))

    config = {
        'modeBarButtonsToRemove': ['zoomOut', 'select2d'],
        'staticPlot': False,
        'scrollZoom': True,
        'toImageButtonOptions': {
            'format': 'png',
            'scale': 1.5,
            'filename': 'open_facilities_' + str('inf') + '_' + str(k) + '.png',
        }
    }

    fig.update_geos(
        showland=True,
        showcoastlines=True,
        showframe=False,
        showocean=True,
        showcountries=True,
        showlakes=True,
        lakecolor='#a4b8b7',
        oceancolor='#a4b8b7',
        landcolor='#fbfcf9',
        scope="north america",
        lonaxis_range=[bounds[1][0], bounds[1][1]],
        lataxis_range=[bounds[0][0], bounds[0][1]],
        projection_type='mercator',
        # bgcolor='#a1b8b7',
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=0),
        autosize=True,
        xaxis=dict(range=[bounds[1][0], bounds[1][1]], autorange=False),
        yaxis=dict(range=[bounds[0][0], bounds[0][1]], autorange=False),
        showlegend=True,
        legend=dict(
            itemsizing='constant',
            x=0.10,
            y=1.12,
            orientation='v',
            bgcolor='rgba(255,255,255,0.5)',
        )
    )

    st.plotly_chart(fig, use_container_width=True, config=config)

    st.write('Number of medical deserts:', len(desert_df))
    desert_df_summary = desert_df.racial_majority.value_counts(normalize=True)
    st.write(desert_df_summary)


fig = go.Figure()

fig = plot_state_boundary(fig, 'MS')

st.write(df.head())

weights = {}
for i in range(len(df)):
    open_facilities = df.iloc[i].Facility
    open_facilities = list(ast.literal_eval(open_facilities))
    k = df.iloc[i].k
    for facility in open_facilities:
        if facility in weights.keys():
            weights[facility] = weights[facility] + 1/k
        else:
            weights[facility] = 1/k


longitudes = [blockgroup_df.loc[i]['Longitude'] for i in weights.keys()]
latitudes = [blockgroup_df.loc[i]['Latitude'] for i in weights.keys()]
weights = [weights[i] for i in weights.keys()]

import math

for i in range(len(longitudes)):
    fig.add_trace(go.Scattergeo(
        lat=[latitudes[i]],
        lon=[longitudes[i]],
        mode='markers',
        marker=dict(
            size=50 * math.sqrt(weights[i] / max(weights)),
            color='red',
            opacity=0.75 * math.sqrt(weights[i]/max(weights)),
            colorscale='Reds',
            showscale=True,
        ),
        showlegend=False,
    ))


bounds = get_bounds(blockgroup_df)
fig.update_geos(
    showland=True,
    showcoastlines=True,
    showframe=False,
    showocean=True,
    showcountries=True,
    showrivers=True,
    rivercolor='#a4b8b7',
    showlakes=True,
    lakecolor='#a4b8b7',
    oceancolor='#a4b8b7',
    landcolor='#fbfcf9',
    scope="north america",
    lonaxis_range=[bounds[1][0], bounds[1][1]],
    lataxis_range=[bounds[0][0], bounds[0][1]],
    projection_type='mercator',
    # bgcolor='#a1b8b7',
)

fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    width=1000,
    height=1000,
    autosize=True,
    xaxis=dict(range=[bounds[1][0], bounds[1][1]], autorange=False),
    yaxis=dict(range=[bounds[0][0], bounds[0][1]], autorange=False),
    showlegend=True,
    legend=dict(
        itemsizing='constant',
        x=0.10,
        y=1.12,
        orientation='v',
        bgcolor='rgba(255,255,255,0.5)',
    )
)

config = {
    'modeBarButtonsToRemove': ['zoomOut', 'select2d'],
    'staticPlot': False,
    'scrollZoom': True,
    'toImageButtonOptions': {
        'format': 'png',
        'scale': 10,
        'filename': 'open_facilities_' + str('inf') + '_' + str(k) + '.png',
    }
}

st.plotly_chart(fig, use_container_width=True)
