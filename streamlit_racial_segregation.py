import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import seaborn as sns
import scripts.utils as utils
import scripts.plot_utils as plot_utils
import scripts.constants as constants
import geopandas as gpd
import requests
import shapely
import os
import importlib

importlib.reload(utils)


st.set_page_config(layout="wide", initial_sidebar_state='expanded')


@st.cache_data
def get_county_data(county_name='Fulton', state_name='Georgia'):
    county_write_file = 'us_counties_2020.zip'
    if not os.path.exists(county_write_file):
        url = constants.census_county_url  # Latest county boundaries dataset
        r = requests.get(url)
        with open(county_write_file, "wb") as f:
            f.write(r.content)

    counties = gpd.read_file(county_write_file)

    if not county_name.endswith(' County'):
        county_name += ' County'
    if not state_name in constants.state_data:
        st.write(':red[' + state_name + ' not found.]')
        st.stop()
    state_fp = constants.state_data[state_name]["FIPS Code"]

    # 3. Filter the county using name and optionally state
    county = counties[(counties["NAMELSAD"] == county_name) & (counties["STATEFP"] == state_fp)]
    if len(county) == 0:
        st.write('Cannot find :red[' + county_name + ', ' + state_name + '.]')
        st.stop()

    boundary_coordinates = []
    if type(county.geometry.iloc[0]) == shapely.geometry.multipolygon.MultiPolygon:
        length = len(county.geometry.iloc[0].geoms)
        for polygon in county.geometry.iloc[0].geoms:
            boundary_coordinates = boundary_coordinates + [polygon.exterior.coords.xy]
    else:
        length = 1
        boundary_coordinates = county.geometry.iloc[0].exterior.coords.xy
    # 4. Access the boundary coordinates
    return length, boundary_coordinates


st.sidebar.write(
    r'A Census tract is designated poor where more than $p$% of the population is below the poverty level.')

st.sidebar.text_input('Enter US state name:', key='state_name', value='Georgia')
state_name = st.session_state['state_name'].capitalize()
state_abbrv = constants.state_data[state_name]["Postal Abbr."]

with_county = st.sidebar.checkbox('Map a specific County', value=False)
if with_county:
    county_name = st.sidebar.text_input('Enter US county name:', key='county_name', value='Fulton').capitalize()
    if not county_name.endswith(' County'):
        county_name += ' County'
    st.title('Racial Segregation in :orange[' + county_name + '], ' + state_abbrv + ', USA')
else:
    county_name = None
    st.title('Racial Segregation in :orange[' + state_name + '], USA')
st.write('Each Census tract is plotted at its center. Census tracts with larger populations are plotted larger.')


st.sidebar.slider('Choose poverty threshold $p$%', key='poverty_threshold', min_value=0, max_value=100, value=25)
poverty_threshold = st.session_state['poverty_threshold']

# st.sidebar.write(
#     ':orange[Currently unoptimized and may take a few seconds to load. Preliminary results only. No legal claims.]')

if county_name is not None:
    length, boundary_coordinates = get_county_data(county_name, state_name)
    df = utils.get_dataframe(state_name, county_name)
    if df is None:
        st.sidebar.write(':red[' + county_name + ' not found.]')
        st.stop()
else:
    df = utils.get_dataframe(state_name)

avg_population_size = np.mean(df['Tot_Population_ACS_10_14'])


@st.cache_data
def get_census_tracts_by_race(df):
    racial_majority = []
    n = len(df)
    for j in range(n):
        if df.iloc[j].pct_NH_Blk_alone_ACS_10_14 >= 50:
            racial_majority.append('Majority Black')
        elif df.iloc[j].pct_NH_White_alone_ACS_10_14 >= 50:
            racial_majority.append('Majority White')
        elif df.iloc[j].pct_Hispanic_ACS_10_14 >= 50:
            racial_majority.append('Majority Hispanic')
        elif df.iloc[j].pct_NH_Asian_alone_ACS_10_14 >= 50:
            racial_majority.append('Majority Asian')
        elif df.iloc[j].pct_NH_AIAN_alone_ACS_10_14 >= 50:
            racial_majority.append('Majority AIAN')
        elif df.iloc[j].pct_NH_NHOPI_alone_ACS_10_14 >= 50:
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

with left_column:
    fig, ax = plt.subplots()
    ax.set_aspect(constants.aspect_ratio)
    if county_name is not None:
        if length == 1:
            plt.plot(boundary_coordinates[0], boundary_coordinates[1], linewidth=1, color='gray')
        else:
            for i in range(length):
                plt.plot(boundary_coordinates[i][0], boundary_coordinates[i][1], linewidth=1, color='gray')
    else:
        plot_utils.plot_state_map(state_name)

    df = get_census_tracts_by_race(df)
    n = len(df)
    max_size = max(1 / math.sqrt(n) * 800, 20)
    min_size = min(df['Tot_Population_ACS_10_14']) / max(df['Tot_Population_ACS_10_14']) * max_size
    ax = sns.scatterplot(df, x='Longitude', y='Latitude',
                         hue='Racial Majority', palette=constants.color_cycle,
                         size='Tot_Population_ACS_10_14', sizes=(min_size, max_size),
                         style='Racial Majority', markers=['H', 's', 'X', 'v', '^', 'P', 'd'], alpha=0.9,
                         edgecolor=None)
    if county_name is not None:
        ax.set_title('Census tracts in ' + county_name + ', ' + state_abbrv + ', USA \n colored by racial majority')
    else:
        ax.set_title('Census tracts in ' + state_name + ', USA \n colored by racial majority')
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
    st.pyplot(fig, dpi=600, transparent=True, bbox_inches='tight', clear_figure=True)

with middle_column:
    fig, ax = plt.subplots()
    ax.set_aspect(constants.aspect_ratio)
    if county_name is not None:
        if length == 1:
            plt.plot(boundary_coordinates[0], boundary_coordinates[1], linewidth=1, color='gray')
        else:
            for i in range(length):
                plt.plot(boundary_coordinates[i][0], boundary_coordinates[i][1], linewidth=1, color='gray')
    else:
        plot_utils.plot_state_map(state_name)

    df = get_census_tracts_by_poverty_levels(df, poverty_threshold)
    n = len(df)

    max_size = max(1 / math.sqrt(n) * 800, 20)
    if county_name is not None:
        title = 'Census tracts in ' + county_name + ', ' + state_abbrv + ', USA \n by poverty level'
    else:
        title = 'Census tracts in ' + state_name + ', USA \n by poverty level'
    ax = sns.scatterplot(df, x='Longitude', y='Latitude',
                         hue='Below Poverty Threshold', palette=constants.color_cycle[-2:],
                         size='Tot_Population_ACS_10_14', sizes=(min_size, max_size),
                         style='Below Poverty Threshold', markers=['o', 'D'], alpha=0.9, edgecolor=None)
    ax.set_title(title)

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

n = len(df)
n_poor = len(df[df['Below Poverty Threshold'] == True])
racial_majorities = df['Racial Majority'].unique()
if n_poor > 0:
    for race in racial_majorities:
        n_race = len(df[df['Racial Majority'] == race])
        fraction_race = n_race / n
        n_race_poor = len(df[(df['Racial Majority'] == race) & (df['Below Poverty Threshold'] == True)])
        fraction_race_poor = n_race_poor / n_poor
        percentage_race = int(100 * (fraction_race))
        percentage_race_poor = int(100 * (fraction_race_poor))
        if fraction_race_poor - fraction_race >= 0.10 and race != 'Other':
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
