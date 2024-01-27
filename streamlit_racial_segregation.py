import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import scripts.utils as utils
import scripts.plot_utils as plot_utils
import scripts.constants as constants
import geopandas as gpd
import requests
import shapely

st.set_page_config(layout="wide")


# ToDo: move to constant.py
state_data = {
    "Alabama": {"Postal Abbr.": "AL", "FIPS Code": "01"},
    "Alaska": {"Postal Abbr.": "AK", "FIPS Code": "02"},
    "Arizona": {"Postal Abbr.": "AZ", "FIPS Code": "04"},
    "Arkansas": {"Postal Abbr.": "AR", "FIPS Code": "05"},
    "California": {"Postal Abbr.": "CA", "FIPS Code": "06"},
    "Colorado": {"Postal Abbr.": "CO", "FIPS Code": "08"},
    "Connecticut": {"Postal Abbr.": "CT", "FIPS Code": "09"},
    "Delaware": {"Postal Abbr.": "DE", "FIPS Code": "10"},
    "District of Columbia": {"Postal Abbr.": "DC", "FIPS Code": "11"},
    "Florida": {"Postal Abbr.": "FL", "FIPS Code": "12"},
    "Georgia": {"Postal Abbr.": "GA", "FIPS Code": "13"},
    "Hawaii": {"Postal Abbr.": "HI", "FIPS Code": "15"},
    "Idaho": {"Postal Abbr.": "ID", "FIPS Code": "16"},
    "Illinois": {"Postal Abbr.": "IL", "FIPS Code": "17"},
    "Indiana": {"Postal Abbr.": "IN", "FIPS Code": "18"},
    "Iowa": {"Postal Abbr.": "IA", "FIPS Code": "19"},
    "Kansas": {"Postal Abbr.": "KS", "FIPS Code": "20"},
    "Kentucky": {"Postal Abbr.": "KY", "FIPS Code": "21"},
    "Louisiana": {"Postal Abbr.": "LA", "FIPS Code": "22"},
    "Maine": {"Postal Abbr.": "ME", "FIPS Code": "23"},
    "Maryland": {"Postal Abbr.": "MD", "FIPS Code": "24"},
    "Massachusetts": {"Postal Abbr.": "MA", "FIPS Code": "25"},
    "Michigan": {"Postal Abbr.": "MI", "FIPS Code": "26"},
    "Minnesota": {"Postal Abbr.": "MN", "FIPS Code": "27"},
    "Mississippi": {"Postal Abbr.": "MS", "FIPS Code": "28"},
    "Missouri": {"Postal Abbr.": "MO", "FIPS Code": "29"},
    "Montana": {"Postal Abbr.": "MT", "FIPS Code": "30"},
    "Nebraska": {"Postal Abbr.": "NE", "FIPS Code": "31"},
    "Nevada": {"Postal Abbr.": "NV", "FIPS Code": "32"},
    "New Hampshire": {"Postal Abbr.": "NH", "FIPS Code": "33"},
    "New Jersey": {"Postal Abbr.": "NJ", "FIPS Code": "34"},
    "New Mexico": {"Postal Abbr.": "NM", "FIPS Code": "35"},
    "New York": {"Postal Abbr.": "NY", "FIPS Code": "36"},
    "North Carolina": {"Postal Abbr.": "NC", "FIPS Code": "37"},
    "North Dakota": {"Postal Abbr.": "ND", "FIPS Code": "38"},
    "Ohio": {"Postal Abbr.": "OH", "FIPS Code": "39"},
    "Oklahoma": {"Postal Abbr.": "OK", "FIPS Code": "40"},
    "Oregon": {"Postal Abbr.": "OR", "FIPS Code": "41"},
    "Pennsylvania": {"Postal Abbr.": "PA", "FIPS Code": "42"},
    "Puerto Rico": {"Postal Abbr.": "PR", "FIPS Code": "72"},
    "Rhode Island": {"Postal Abbr.": "RI", "FIPS Code": "44"},
    "South Carolina": {"Postal Abbr.": "SC", "FIPS Code": "45"},
    "South Dakota": {"Postal Abbr.": "SD", "FIPS Code": "46"},
    "Tennessee": {"Postal Abbr.": "TN", "FIPS Code": "47"},
    "Texas": {"Postal Abbr.": "TX", "FIPS Code": "48"},
    "Utah": {"Postal Abbr.": "UT", "FIPS Code": "49"},
    "Vermont": {"Postal Abbr.": "VT", "FIPS Code": "50"},
    "Virginia": {"Postal Abbr.": "VA", "FIPS Code": "51"},
    "Virgin Islands": {"Postal Abbr.": "VI", "FIPS Code": "78"},
    "Washington": {"Postal Abbr.": "WA", "FIPS Code": "53"},
    "West Virginia": {"Postal Abbr.": "WV", "FIPS Code": "54"},
    "Wisconsin": {"Postal Abbr.": "WI", "FIPS Code": "55"},
    "Wyoming": {"Postal Abbr.": "WY", "FIPS Code": "56"}
}
races = ['White', 'Black', 'Hispanic', 'Asian', 'AIAN', 'NHPI', 'Other']

st.sidebar.write(r'A Census tract is designated poor where more than $p$% of the population is below the poverty level.')

st.sidebar.text_input('Enter US state name:', key='state_name', value='Georgia')
st.sidebar.text_input('Enter US county name:', key='county_name', value='Fulton')
state_name = st.session_state['state_name']
county_name = st.session_state['county_name']
state_abbrv = state_data[state_name]["Postal Abbr."]
if not county_name.endswith(' County'):
    county_name += ' County'
st.title('Racial Segregation in :orange[' + county_name + '], ' + state_abbrv + ', USA')


st.sidebar.slider('Choose poverty threshold $p$%', key='poverty_threshold', min_value=0, max_value=100, value=30)
# st.sidebar.slider('No insurance threshold (%)', key='no_insurance_threshold', min_value=0, max_value=100, value=25)
# st.sidebar.slider('Two or more insurance threshold (%)', key='two_or_more_insurance_threshold', min_value=0, max_value=100, value=25)
poverty_threshold = st.session_state['poverty_threshold']
# no_insurance_threshold = st.session_state['no_insurance_threshold']
# two_or_more_insurance_threshold = st.session_state['two_or_more_insurance_threshold']

st.sidebar.write(':orange[Currently unoptimized and may take a few seconds to load. Preliminary results only.]')


@st.cache_data
def get_county_data(county_name='Fulton', state_name='Georgia'):
    url = "https://www2.census.gov/geo/tiger/TIGER2020/COUNTY/tl_2020_us_county.zip"  # Latest county boundaries dataset
    r = requests.get(url)
    with open("tl_2020_us_county.zip", "wb") as f:
        f.write(r.content)
    counties = gpd.read_file("tl_2020_us_county.zip")

    if not county_name.endswith(' County'):
        county_name += ' County'
    if not state_name in state_data:
        st.write(':red[' + state_name + ' not found.]')
        st.stop()
    state_fp = state_data[state_name]["FIPS Code"]

    # 3. Filter the county using name and optionally state
    county = counties[(counties["NAMELSAD"] == county_name) & (counties["STATEFP"] == state_fp)]

    boundary_coordinates = []
    if type(county.geometry.iloc[0]) == shapely.geometry.multipolygon.MultiPolygon:
        length = len(county.geometry.iloc[0].geoms)
        for polygon in county.geometry.iloc[0].geoms:
            # st.write(type(polygon))
            boundary_coordinates = boundary_coordinates + [polygon.exterior.coords.xy]
            # st.write(polygon.centroid)
    else:
        length = 1
        boundary_coordinates = county.geometry.iloc[0].exterior.coords.xy
    # 4. Access the boundary coordinates
    return length, boundary_coordinates


length, boundary_coordinates = get_county_data(county_name, state_name)
df = utils.get_dataframe(state_name, county_name)
if df is None:
    st.sidebar.write(':red[' + county_name + ' not found.]')
    st.stop()


df = utils.get_dataframe(state_name, county_name)


def plot_census_tracts_by_race(state_name, county_name):
    all_tracts = {race: [] for race in races}
    n = len(df)
    for j in range(n):
        if df.iloc[j].pct_NH_Blk_alone_ACS_10_14 >= 50:
            all_tracts['Black'].append(j)
        elif df.iloc[j].pct_NH_White_alone_ACS_10_14 >= 50:
            all_tracts['White'].append(j)
        elif df.iloc[j].pct_Hispanic_ACS_10_14 >= 50:
            all_tracts['Hispanic'].append(j)
        elif df.iloc[j].pct_NH_Asian_alone_ACS_10_14 >= 50:
            all_tracts['Asian'].append(j)
        elif df.iloc[j].pct_NH_AIAN_alone_ACS_10_14 >= 50:
            all_tracts['AIAN'].append(j)
        elif df.iloc[j].pct_NH_NHOPI_alone_ACS_10_14 >= 50:
            all_tracts['NHPI'].append(j)
        else:
            all_tracts['Other'].append(j)

    for race in races:
        if len(all_tracts[race]) > 0:
            longitudes_group = [df.iloc[j].Longitude for j in all_tracts[race]]
            latitudes_group = [df.iloc[j].Latitude for j in all_tracts[race]]
            plt.scatter(longitudes_group, latitudes_group, marker='o', s=7, label='Majority ' + race)

    plt.legend(loc='best')
    plt.axis('off')
    plt.title('Census tracts in ' + county_name + ', ' + state_name + ', USA \n colored by racial majority')
    ax.set_aspect(constants.aspect_ratio)

    return n, all_tracts


def plot_census_tracts_by_poverty_levels(state_name, county_name, poverty_threshold):
    poverty_levels = ['Below ' + str(poverty_threshold) + '%', 'Above ' + str(poverty_threshold) + '%']
    all_tracts = {level: [] for level in poverty_levels}
    n = len(df)
    for j in range(n):
        if df.iloc[j].pct_Prs_Blw_Pov_Lev_ACS_10_14 < poverty_threshold:
            all_tracts['Below ' + str(poverty_threshold) + '%'].append(j)
        else:
            all_tracts['Above ' + str(poverty_threshold) + '%'].append(j)

    colors = ['olive', 'brown']
    shapes = ['s', 'P']

    for level in poverty_levels:
        if len(all_tracts[level]) > 0:
            longitudes_group = [df.iloc[j].Longitude for j in all_tracts[level]]
            latitudes_group = [df.iloc[j].Latitude for j in all_tracts[level]]
            plt.scatter(longitudes_group, latitudes_group, s=7, label=level, marker=shapes[poverty_levels.index(level)],
                        facecolors='none', color=colors[poverty_levels.index(level)], alpha=0.9)

                        # color=colors[poverty_levels.index(level)])


    plt.legend(loc='best')
    plt.axis('off')
    plt.title('Census tracts in ' + county_name + ', ' + state_name + ', USA \n by poverty level')
    ax.set_aspect(constants.aspect_ratio)

    return n, all_tracts


left_column, middle_column = st.columns(2)


with left_column:
    fig, ax = plt.subplots()
    ax.set_aspect(constants.aspect_ratio)
    if length == 1:
        plt.plot(boundary_coordinates[0], boundary_coordinates[1], linewidth=1, color='gray')
    else:
        for i in range(length):
            plt.plot(boundary_coordinates[i][0], boundary_coordinates[i][1], linewidth=1, color='gray')
    n, tracts_by_race = plot_census_tracts_by_race(state_name, county_name)
    plt.axis('off')
    st.pyplot(fig, dpi=600, transparent=True, bbox_inches='tight', clear_figure=True)

with middle_column:
    fig, ax = plt.subplots()
    ax.set_aspect(constants.aspect_ratio)
    if length == 1:
        plt.plot(boundary_coordinates[0], boundary_coordinates[1], linewidth=1, color='gray')
    else:
        for i in range(length):
            plt.plot(boundary_coordinates[i][0], boundary_coordinates[i][1], linewidth=1, color='gray')
    _, tracts_by_poverty = plot_census_tracts_by_poverty_levels(state_name, county_name, poverty_threshold)
    plt.axis('off')
    st.pyplot(fig, dpi=600, transparent=True, bbox_inches='tight', clear_figure=True)


racial_poverty_tracts = {race: [] for race in races}


if len(tracts_by_poverty['Above ' + str(poverty_threshold) + '%']) != 0:
    for race in races:
        for j in tracts_by_race[race]:
            if df.iloc[j].pct_Prs_Blw_Pov_Lev_ACS_10_14 >= poverty_threshold:
                racial_poverty_tracts[race].append([df.iloc[j].Longitude, df.iloc[j].Latitude])

        fraction_of_tracts = len(tracts_by_race[race])/n
        fraction_of_poor_tracts = len(racial_poverty_tracts[race])/len(tracts_by_poverty['Above ' + str(poverty_threshold) + '%'])
        percentage_of_tracts = int(fraction_of_tracts * 100)
        percentage_of_poor_tracts = int(fraction_of_poor_tracts * 100)

        if race != 'Other' and fraction_of_poor_tracts - fraction_of_tracts >= 0.10:
            st.write(race + ' population may be disproportionately affected by poverty in ' + county_name + ', ' + state_name + ', USA. '
                     ':red[' + str(percentage_of_poor_tracts) + '%] of poor Census tracts in ' + county_name + ' are Majority ' + race + '. '
                     'Only :blue[' + str(percentage_of_tracts) + '%] of all Census tracts in ' + county_name + ' are Majority ' + race + '.'
                     )

