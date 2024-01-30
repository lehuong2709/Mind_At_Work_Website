import logging
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import seaborn as sns
import geopandas as gpd
import requests
import shapely
import os
import importlib
import pylatex

import scripts.utils as utils
import scripts.plot_utils as plot_utils
import scripts.constants as constants

logging.basicConfig(level=logging.WARNING)

importlib.reload(utils)
importlib.reload(plot_utils)
importlib.reload(constants)

st.set_page_config(layout="wide", initial_sidebar_state='expanded')


@st.cache_data
def get_county_states_and_dataframe(county_name):
    if not county_name.endswith(' County'):
        county_name += ' County'
    county_data_file = 'data/tl_2020_us_county.zip'
    counties_df = gpd.read_file(county_data_file)

    county_df = counties_df[(counties_df["NAMELSAD"] == county_name)]
    if len(county_df) == 0:
        st.subheader('Cannot find :red[' + county_name + '.]')
        st.stop()
    all_states_fips_with_county = county_df['STATEFP'].unique()
    all_states_with_county = [constants.get_state_name_and_abbreviation_by_fips(fips) for fips in all_states_fips_with_county]

    return all_states_with_county, county_df


@st.cache_data
def get_state_boundaries(state_name='Georgia'):
    df = pd.read_json(constants.boundary_data_path)

    for i in range(len(df.index)):
        if df.iloc[i]['features']['properties']['NAME'] == state_name:
            coordinates = df.iloc[i]['features']['geometry']['coordinates']

    boundary_longitudes = []
    boundary_latitudes = []
    if len(coordinates) == 1:
        coordinates = coordinates[0]

        for i in range(len(coordinates)):
            boundary_longitudes.append(coordinates[i][0])
            boundary_latitudes.append(coordinates[i][1])
    else:
        for i in range(len(coordinates)):
            for j in range(len(coordinates[i][0])):
                boundary_longitudes.append(coordinates[i][0][j][0])
                boundary_latitudes.append(coordinates[i][0][j][1])

    return boundary_longitudes, boundary_latitudes


@st.cache_data
def get_county_boundaries(county_df):
    boundary_longitudes = []
    boundary_latitudes = []
    if type(county_df.geometry.iloc[0]) == shapely.geometry.multipolygon.MultiPolygon:
        for polygon in county_df.geometry.iloc[0].geoms:
            boundary_longitudes = boundary_longitudes + list(polygon.exterior.coords.xy[0])
            boundary_latitudes = boundary_latitudes + list(polygon.exterior.coords.xy[1])
            # boundary_coordinates = boundary_coordinates + [polygon.exterior.coords.xy]
    else:
        boundary_longitudes = county_df.geometry.iloc[0].exterior.coords.xy[0]
        boundary_latitudes = county_df.geometry.iloc[0].exterior.coords.xy[1]
        # boundary_coordinates = county_df.geometry.iloc[0].exterior.coords.xy

    return boundary_longitudes, boundary_latitudes


st.sidebar.write('A Census tract is designated poor where more than $p$% of the population is below the poverty level.')

option = st.sidebar.selectbox(
    "Mapping options:",
    ('By State', 'By County')
)
if option == 'By State':
    county_name = None
    state_name = st.sidebar.text_input('Enter US state name:', key='state_name', value='Georgia')
    state_abbrv, state_fips = constants.get_state_abbreviation_and_fips_by_name(state_name)
    st.title('Racial Segregation in :orange[' + state_name + '], USA')


    @st.cache_data
    def get_state_data(state_name):
        boundary_longitudes, boundary_latitudes = get_state_boundaries(state_name)
        df = utils.get_dataframe(state_name)
        return boundary_longitudes, boundary_latitudes, df

    boundary_longitudes, boundary_latitudes, df = get_state_data(state_name)
    tracts_by_racial_majority_title = 'Census tracts in ' + state_name + ', USA \n colored by racial majority'
    tracts_by_poverty_level_title = 'Census tracts in ' + state_name + ', USA \n colored by poverty level'

else:
    county_name = st.sidebar.text_input('Enter US county name:', key='county_name', value='Queens').capitalize()
    if not county_name.endswith(' County'):
        county_name += ' County'

    county_states, county_df = get_county_states_and_dataframe(county_name)
    county_states.sort()

    state_name = st.sidebar.selectbox(
        "Choose state:",
        county_states
    )
    state_abbrv, state_fips = constants.get_state_abbreviation_and_fips_by_name(state_name)
    st.title('Racial Segregation in :orange[' + county_name + '], ' + state_abbrv + ', USA')

    county_df_with_state = county_df[(county_df["STATEFP"] == state_fips)]

    boundary_longitudes, boundary_latitudes = get_county_boundaries(county_df_with_state)
    df = utils.get_dataframe(state_name, county_name)

    if len(df) == 0:
        st.subheader('Sorry, data unavailable for ' + county_name + ', ' + state_name + ' .]')
        st.stop()

    tracts_by_racial_majority_title = ('Census tracts in ' + county_name + ', '
                                       + state_abbrv + ', USA \n colored by racial majority')
    tracts_by_poverty_level_title = ('Census tracts in ' + county_name + ', '
                                     + state_abbrv + ', USA \n colored by poverty level')


poverty_threshold = st.sidebar.slider('Choose poverty threshold $p$%', key='poverty_threshold', min_value=0,
                                          max_value=100, value=25)


st.sidebar.write(':orange[Currently unoptimized and may take a few seconds to load. No legal claims.]')
st.sidebar.write('Data for Census tracts is from 2020 and taken from https://data.census.gov/')

st.sidebar.markdown('''
Based on _Which $L_p$ norm is the fairest? Approximations for fair facility location across all \"$p$\"_ by Swati Gupta, Jai Moondra, Mohit Singh.
Created by :blue[Jai Moondra], :blue[Swati Gupta], and :blue[Mohit Singh].
Part of the code was written by :blue[Michael Wang] and :blue[Hassan Mortagy].
''')

st.sidebar.markdown('''
This work is licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0).
''')

st.write('Each Census tract is plotted at its center. Census tracts with larger populations are plotted larger.')


@st.cache_data
def get_census_tracts_by_race(df):
    racial_majority = []
    n = len(df)
    for j in range(n):
        if df.iloc[j].pct_NH_Blk_alone_ACS_10_14 > 50:
            racial_majority.append('Majority Black')
        elif df.iloc[j].pct_NH_White_alone_ACS_10_14 > 50:
            racial_majority.append('Majority White')
        elif df.iloc[j].pct_Hispanic_ACS_10_14 > 50:
            racial_majority.append('Majority Hispanic')
        elif df.iloc[j].pct_NH_Asian_alone_ACS_10_14 > 50:
            racial_majority.append('Majority Asian')
        elif df.iloc[j].pct_NH_AIAN_alone_ACS_10_14 > 50:
            racial_majority.append('Majority AIAN')
        elif df.iloc[j].pct_NH_NHOPI_alone_ACS_10_14 > 50:
            racial_majority.append('Majority NHPI')
        else:
            racial_majority.append('Other')

    df.insert(0, 'Racial Majority', racial_majority)
    return df


@st.cache_data
def get_census_tracts_by_poverty_levels(df, poverty_threshold):
    below_poverty_threshold = []
    n = len(df)
    for j in range(n):
        if df.iloc[j].pct_Prs_Blw_Pov_Lev_ACS_10_14 < poverty_threshold:
            below_poverty_threshold.append(False)
        else:
            below_poverty_threshold.append(True)

    df.insert(0, 'Below Poverty Threshold', below_poverty_threshold)
    return df


left_column, middle_column = st.columns(2)
plt.rc('text', usetex=True)
plt.rc('text.latex', preamble=r'\usepackage{amssymb}')

with left_column:
    fig, ax = plt.subplots()
    ax.set_aspect(constants.aspect_ratio)
    plt.plot(boundary_longitudes, boundary_latitudes, linewidth=1, color='gray')
    plt.axis('off')

    df = get_census_tracts_by_race(df)
    n = len(df)

    max_size = max(1/math.sqrt(n)*1200, 20)
    max_size = min(max_size, 60)
    min_size = min(df['Tot_Population_ACS_10_14']) / max(df['Tot_Population_ACS_10_14']) * max_size
    min_size = max(min_size, max_size / 2)
    markers = [r'$\triangle$', '$\circ$', '$\small\square$', '$\diamond$', r'$\times$', '$\star$', '$+$']
    # markers = ['H', 's', 'X', 'v', '^', 'P', 'd']
    sns.scatterplot(df, x='Longitude', y='Latitude',
                    hue='Racial Majority', palette=constants.color_cycle,
                    size='Tot_Population_ACS_10_14', sizes=(min_size, max_size),
                    style='Racial Majority', markers=markers, alpha=0.9,
                    edgecolor=None)
    ax.set_title(tracts_by_racial_majority_title)
    markers, labels = ax.get_legend_handles_labels()
    if 'Tot_Population_ACS_10_14' in labels:
        # Find index where 'Tot_Population_ACS_10_14' is located
        index = labels.index('Tot_Population_ACS_10_14')
        labels = labels[1:index]
        markers = markers[1:index]
    if 'Other' in labels:
        index = labels.index('Other')
        # Move 'Other' to the end of the list
        labels.append(labels.pop(index))
        markers.append(markers.pop(index))
    ax.legend(markers, labels, loc='best', fontsize='small')
    plt.axis('off')

    st.pyplot(fig, dpi=1000, transparent=True, bbox_inches='tight', clear_figure=True)

with middle_column:
    fig, ax = plt.subplots()
    ax.set_aspect(constants.aspect_ratio)
    plt.plot(boundary_longitudes, boundary_latitudes, linewidth=1, color='gray')
    plt.axis('off')

    df = get_census_tracts_by_poverty_levels(df, poverty_threshold)
    n = len(df)
    max_size = max(1/math.sqrt(n) * 1200, 20)
    max_size = min(max_size, 60)
    min_size = min(df['Tot_Population_ACS_10_14'])/max(df['Tot_Population_ACS_10_14']) * max_size
    min_size = max(min_size, max_size/2)
    sns.scatterplot(df, x='Longitude', y='Latitude',
                    hue='Below Poverty Threshold', palette=constants.color_cycle[-2:],
                    size='Tot_Population_ACS_10_14', sizes=(min_size, max_size),
                    style='Below Poverty Threshold', markers=['$\circ$', '$\diamond$'], alpha=0.9, ec="face")
    ax.set_title(tracts_by_poverty_level_title)

    # Get the handles and labels
    markers, labels = ax.get_legend_handles_labels()
    if labels[1] == 'True':
        labels[1] = 'Above ' + str(poverty_threshold) + '%'
        labels[2] = 'Below ' + str(poverty_threshold) + '%'
    else:
        labels[1] = 'Below ' + str(poverty_threshold) + '%'
        labels[2] = 'Above ' + str(poverty_threshold) + '%'

    # slice the appropriate section of markers and labels to include in the legend
    ax.legend(markers[1:3], labels[1:3], loc='best')

    plt.axis('off')
    st.pyplot(plt, dpi=600, transparent=True, bbox_inches='tight', clear_figure=True)


def write_disproportionate_poverty(race, percentage_race_poor, percentage_race, state_name, county_name=None):
    if county_name is not None:
        st.write(race.split()[
                     1] + ' population may be disproportionately affected by poverty in ' + county_name + ', ' + state_name + ', USA. '
                                                                                                                              ':red[' + str(
            percentage_race_poor) + '%] of poor Census tracts in ' + county_name + ' are ' + race + '. '
                                                                                                    'Only :blue[' + str(
            percentage_race) + '%] of all Census tracts in ' + county_name + ' are ' + race + '.'
                 )
    else:
        st.write(
            race.split()[
                1] + ' population may be disproportionately affected by poverty in ' + state_name + ', USA. '
                                                                                                    ':red[' + str(
                percentage_race_poor) + '%] of poor Census tracts in ' + state_name + ' are ' + race + '. '
                                                                                                       'Only :blue[' + str(
                percentage_race) + '%] of all Census tracts in ' + state_name + ' are ' + race + '.'
        )


n = len(df)
n_poor = len(df[df['Below Poverty Threshold'] == True])
racial_majorities = df['Racial Majority'].unique()
if n_poor > 0:
    for race in racial_majorities:
        n_race = len(df[df['Racial Majority'] == race])
        fraction_race = n_race/n
        n_race_poor = len(df[(df['Racial Majority'] == race) & (df['Below Poverty Threshold'] == True)])
        fraction_race_poor = n_race_poor / n_poor
        percentage_race = int(100 * (fraction_race))
        percentage_race_poor = int(100 * (fraction_race_poor))
        if fraction_race_poor - fraction_race >= 0.10 and race != 'Other':
            write_disproportionate_poverty(race, percentage_race_poor, percentage_race, state_name, county_name)


# Function to draw a circle
def draw_circle(color):
    fig, ax = plt.subplots()

    # Create a circle
    circle = plt.Circle((0.5, 0.5), 0.2, color=color, fill=True)

    # Add the circle to the plot
    ax.add_patch(circle)

    # Set axis properties
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal', 'box')

    # Remove x and y ticks
    ax.set_xticks([])
    ax.set_yticks([])

    # Show the plot
    st.pyplot(fig)

with st.sidebar.expander("Show color cycle"):
    for circle_color in constants.color_cycle:
        # Draw the circle with the specified color
        draw_circle(circle_color)

