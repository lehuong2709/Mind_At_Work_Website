import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import scripts.utils as utils
import scripts.plot_utils as plot_utils
import scripts.constants as constants
import seaborn as sns
import importlib
import matplotlib as mpl
import pylatex

importlib.reload(utils)
importlib.reload(plot_utils)
importlib.reload(constants)

state_names = pd.read_csv(utils.state_abbreviations_path, index_col=0).index.to_list()

st.set_page_config(layout="wide", initial_sidebar_state="expanded")

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

        component_longitudes = []
        component_latitudes = []
        for i in range(len(coordinates)):
            component_longitudes.append(coordinates[i][0])
            component_latitudes.append(coordinates[i][1])
        boundary_longitudes.append(component_longitudes)
        boundary_latitudes.append(component_latitudes)
    else:
        for i in range(len(coordinates)):
            component_longitudes = []
            component_latitudes = []
            for j in range(len(coordinates[i][0])):
                component_longitudes.append(coordinates[i][0][j][0])
                component_latitudes.append(coordinates[i][0][j][1])
            boundary_longitudes.append(component_longitudes)
            boundary_latitudes.append(component_latitudes)

    return boundary_longitudes, boundary_latitudes


st.sidebar.write('A medical desert is defined as a US Census tract that is more than $n$ miles away from the '
                 'nearest CVS/Walgreens/Walmart pharmacy with $p$ percent of the population below the poverty level.')
county_name = None
state_name = st.sidebar.text_input('Enter US state name:', key='state_name', value='Georgia')
state_name = state_name.capitalize()
if state_name not in state_names:
    st.sidebar.subheader(":red[State name not found]")
    st.stop()

state_abbrv, state_fips = constants.get_state_abbreviation_and_fips_by_name(state_name)

@st.cache_data
def get_state_data(state_name):
    boundary_longitudes, boundary_latitudes = get_state_boundaries(state_name)
    df = utils.get_dataframe(state_name)
    return boundary_longitudes, boundary_latitudes, df


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

    df['Racial Majority'] = racial_majority
    return df


boundary_longitudes, boundary_latitudes, df = get_state_data(state_name)
tracts_by_racial_majority_title = 'Census tracts in ' + state_name + ', USA \n colored by racial majority'
tracts_by_poverty_level_title = 'Census tracts in ' + state_name + ', USA \n colored by poverty level'

st.title('Medical deserts in :orange[' + state_name + '], United States')

n_miles = st.sidebar.slider("Enter $n$, the number of miles", key="n_miles", min_value=1, max_value=10, value=5, step=1)
poverty_threshold = st.sidebar.slider('Enter $p$, the percentage threshold for population below poverty level', key="pov_threshold",
                  min_value=0, max_value=100, value=30, step=1)

st.sidebar.write(':orange[Currently unoptimized and may take a few seconds to load. '
                 'Preliminary and indicative results only.]')
st.sidebar.write('Data for pharmacies is from 2005-10 and taken from ' + r'https://data.world/dhs/pharmacies')
st.sidebar.write('Data for Census tracts is from 2020 and taken from https://data.census.gov/')

st.sidebar.write('''This model makes the following assumptions:
- Population in each Census tract is assumed to be at the center of the tract.
- Facility capacities are not accounted for.
- Pharmacies other than CVS, Walgreens, and Walmart are not accounted for.
- All distances are straight-line distances.
''')

st.sidebar.markdown('''
Based on _Which $L_p$ norm is the fairest? Approximations for fair facility location across all \"$p$\"_ by Swati Gupta, Jai Moondra, Mohit Singh.
Created by :blue[Jai Moondra], :blue[Swati Gupta], and :blue[Mohit Singh].
Part of the code was written by :blue[Michael Wang] and :blue[Hassan Mortagy].
''')

st.sidebar.markdown('''
This work is licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0).
''')

left_column, middle_column, right_column = st.columns(3)

# plt.rc('text', usetex=True)
# plt.rc('text.latex', preamble=r'\usepackage{amssymb}')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['cmss']


with left_column:
    fig, ax = plt.subplots()
    plt.axis('off')
    ax.set_aspect(constants.aspect_ratio)
    for i in range(len(boundary_longitudes)):
        plt.plot(boundary_longitudes[i], boundary_latitudes[i], linewidth=1, color='gray')
    ax.set_title('Pharmacy locations in ' + state_name + '\n', fontsize='medium')
    k, cvs_pharmacy_coordinates, walgreens_pharmacies_coordinates, walmart_pharmacies_coordinates = (
        utils.get_pharmacy_coordinates(state_name=state_name, which='top3', county_name=county_name))
    df_pharm = pd.DataFrame({'Longitude': [x[0] for x in
                                     cvs_pharmacy_coordinates + walgreens_pharmacies_coordinates + walmart_pharmacies_coordinates],
                       'Latitude': [x[1] for x in
                                    cvs_pharmacy_coordinates + walgreens_pharmacies_coordinates + walmart_pharmacies_coordinates],
                       'Pharmacy': ['CVS'] * len(cvs_pharmacy_coordinates) + ['Walgreens'] * len(
                           walgreens_pharmacies_coordinates) + ['Walmart'] * len(walmart_pharmacies_coordinates)})
    sns.scatterplot(data=df_pharm, x='Longitude', y='Latitude', hue='Pharmacy', palette=['orange', 'red', 'green'],
                    markers=['X', 'X', 'X'], s=15, alpha=0.9, style='Pharmacy')
    markers, labels = ax.get_legend_handles_labels()
    if 'Pharmacy' in labels:
        # Find index where 'Tot_Population_ACS_10_14' is located
        index = labels.index('Pharmacy')
        labels = labels[1:4]
        markers = markers[1:4]
    ax.legend(markers, labels, loc='best', fontsize='small')
    st.pyplot(fig, dpi=1000, transparent=True, bbox_inches='tight', clear_figure=True)


with middle_column:
    fig, ax = plt.subplots()
    ax.set_aspect(constants.aspect_ratio)
    for i in range(len(boundary_longitudes)):
        plt.plot(boundary_longitudes[i], boundary_latitudes[i], linewidth=1, color='gray')
    plt.axis('off')

    df = get_census_tracts_by_race(df)
    n = len(df)

    def get_sizes(df):
        n = len(df)
        max_size = max((1/math.sqrt(n))*1200, 20)
        max_size = min(max_size, 60)
        min_size = min(df['Tot_Population_ACS_10_14']) / max(df['Tot_Population_ACS_10_14']) * max_size
        min_size = max(min_size, max_size / 2)
        sizes = []
        max_population = max(df['Tot_Population_ACS_10_14'])
        min_population = min(df['Tot_Population_ACS_10_14'])
        for j in range(len(df)):
            sizes.append((df.iloc[j]['Tot_Population_ACS_10_14'] - min_population)/(max_population - min_population) * (max_size - min_size) + min_size)

        df['size'] = sizes
        return

    markers = [r'^', 'o', 's', 'D', 'X', '*', 'P']
    racial_groups = ['Majority White', 'Majority Black', 'Majority Hispanic', 'Majority Asian', 'Majority AIAN',
             'Majority NHPI', 'Other']
    get_sizes(df)

    for race in racial_groups:
        df_race = df[df['Racial Majority'] == race]
        color = constants.color_cycle[racial_groups.index(race)]
        marker = markers[racial_groups.index(race)]
        sizes = df_race['size'].values

        if len(df_race) > 0:
            plt.scatter(df_race['Longitude'], df_race['Latitude'], s=sizes, edgecolor=color, alpha=0.8, facecolors='none',
                linewidths=1, marker=marker, label=race)

    plt.legend(loc='best', fontsize='small')
    ax.set_title('Census tracts in ' + state_name + ', \n colored by racial majority', fontsize='medium')
    st.pyplot(fig, dpi=1000, transparent=True, bbox_inches='tight', clear_figure=True)

with right_column:
    fig, ax = plt.subplots()
    def get_medical_deserts(df, n_miles, poverty_threshold=30):
        latitudes = df['Latitude'].values
        longitudes = df['Longitude'].values

        k, cvs_pharmacies, walgreens_pharmacies, walmart_pharmacies = utils.get_pharmacy_coordinates(state_name,
                                                                                                     which='top3')
        pharmacy_coordinates = cvs_pharmacies + walgreens_pharmacies + walmart_pharmacies

        is_medical_desert = []

        for j in range(n):
            # print(j) if j % 10 == 0 else None
            minimum_distance = np.inf
            for i in range(k):
                pharmacy_latitude = pharmacy_coordinates[i][1]
                pharmacy_longitude = pharmacy_coordinates[i][0]
                distance = utils.distance_from_coordinates_2(latitudes[j], longitudes[j], pharmacy_latitude,
                                                             pharmacy_longitude)
                if distance < minimum_distance:
                    minimum_distance = distance

            if minimum_distance > n_miles * constants.miles_to_km and df.iloc[
                j].pct_Prs_Blw_Pov_Lev_ACS_10_14 >= poverty_threshold:
                is_medical_desert.append(True)
            else:
                is_medical_desert.append(False)

        df['Is Medical Desert'] = is_medical_desert
        return df

    ax.set_aspect(constants.aspect_ratio)
    for i in range(len(boundary_longitudes)):
        plt.plot(boundary_longitudes[i], boundary_latitudes[i], linewidth=1, color='gray')
    plt.axis('off')

    df = get_medical_deserts(df, n_miles, poverty_threshold)

    markers = [r'^', 'o', 's', 'D', 'X', '*', 'P']
    racial_groups = ['Majority White', 'Majority Black', 'Majority Hispanic', 'Majority Asian', 'Majority AIAN',
             'Majority NHPI', 'Other']

    for race in racial_groups:
        df_race = df[(df['Racial Majority'] == race) & (df['Is Medical Desert'] == True)]
        color = constants.color_cycle[racial_groups.index(race)]
        marker = markers[racial_groups.index(race)]
        if len(df_race) > 0:
            sizes = df_race['size'].values
            plt.scatter(df_race['Longitude'], df_race['Latitude'], s=sizes, edgecolor=color, alpha=0.8, facecolors='none',
                linewidths=1, marker=marker, label=race)

    plt.legend(loc='best', fontsize='small')
    ax.set_title('Medical deserts in ' + state_name + ', \n colored by racial majority', fontsize='medium')
    st.pyplot(fig, dpi=1000, transparent=True, bbox_inches='tight', clear_figure=True)


deserts = len(df[df['Is Medical Desert'] == True])
st.write('There are :red[' + str(deserts) + '] medical deserts in ' + state_name + ', USA.')
if deserts != 0:
    n = len(df)
    n_poor = len(df[df['Is Medical Desert'] == True])
    racial_majorities = df['Racial Majority'].unique()
    if n_poor > 0:
        for race in racial_majorities:
            n_race = len(df[df['Racial Majority'] == race])
            fraction_race = n_race / n
            n_race_poor = len(df[(df['Racial Majority'] == race) & (df['Is Medical Desert'] == True)])
            fraction_race_poor = n_race_poor / n_poor
            percentage_race = int(100 * (fraction_race))
            percentage_race_poor = int(100 * (fraction_race_poor))
            if fraction_race_poor - fraction_race >= 0.10 and race != 'Other':
                 st.write(race.split()[1] + ' population may be disproportionately affected by medical deserts in ' + state_name + ', USA. ' +
                          'About :red[' + str(percentage_race_poor) + '%] of medical deserts are majority ' + race + '. ' +
                          'Only about :blue[' + str(percentage_race) + '%] of Census tracts are majority ' + race + '.')
