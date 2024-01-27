import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import scripts.utils as utils
import scripts.plot_utils as plot_utils
import scripts.constants as constants

state_names = pd.read_csv(utils.state_abbreviations_path, index_col=0).index.to_list()

st.set_page_config(layout="wide")

st.sidebar.write('A medical desert is defined as a census tract that is more than $n$ miles away from the '
                 'nearest CVS/Walgreens/Walmart pharmacy with $p$ percent of the population below the poverty level.')
st.sidebar.text_input('Enter the state name:', key='state_name', value='Georgia')
state_name = st.session_state['state_name']
if state_name not in state_names:
    st.sidebar.write(":red[State name not found]")
    st.stop()

st.title('Medical deserts in :orange[' + state_name + '], United States')

st.sidebar.slider("Enter $n$, the number of miles", key="n_miles", min_value=1, max_value=10, value=5, step=1)
st.sidebar.slider('Enter $p$, the percentage threshold for population below poverty level', key="pov_threshold", min_value=0, max_value=100, value=30, step=1)

st.sidebar.write(':orange[Currently unoptimized and may take a few seconds to load. '
                 'Preliminary results only.]')

st.sidebar.write('''This model makes the following assumptions:
- Population in each Census tract is assumed to be at the center of the tract.
- Facility capacities are not accounted for.
- Pharmacies other than CVS, Walgreens, and Walmart are not accounted for.
- All distances are straight-line distances.
''')


left_column, middle_column, right_column = st.columns(3)
fig, ax = plt.subplots()

with left_column:
    @st.cache_data
    def plot_top3_pharmacies(state_name):
        plot_utils.plot_state_map(state_name)
        plot_utils.plot_pharmacies(state_name, which='top3')
        plt.axis('off')
        plt.title('Pharmacy Locations in ' + state_name + ', USA \n')
        st.pyplot(fig, dpi=600, transparent=True, bbox_inches='tight', clear_figure=True)
        return

    plot_top3_pharmacies(state_name)


with middle_column:
    @st.cache_data
    def plot_census_tracts(state_name):
        df = utils.get_dataframe(state_name)
        races = ['White', 'Black', 'Hispanic', 'Asian', 'AIAN', 'NHPI', 'Other']
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

        plot_utils.plot_state_map(state_name)

        for race in races:
            if len(all_tracts[race]) > 0:
                longitudes_group = [df.iloc[j].Longitude for j in all_tracts[race]]
                latitudes_group = [df.iloc[j].Latitude for j in all_tracts[race]]
                plt.scatter(longitudes_group, latitudes_group, marker='o', s=5, label='Majority ' + race)

        plt.legend(loc='best')
        plt.axis('off')
        plt.title('Census tracts in ' + state_name + ', USA \n colored by racial majority')
        st.pyplot(fig, dpi=600, transparent=True, bbox_inches='tight', clear_figure=True)
        return n, all_tracts

    n, all_tracts = plot_census_tracts(state_name)


with right_column:
    def get_medical_deserts(state_name, n_miles, poverty_threshold=30):
        df = utils.get_dataframe(state_name)
        n = len(df)
        print(n)

        latitudes = df['Latitude'].values
        longitudes = df['Longitude'].values

        medical_deserts = []
        races = ['White', 'Black', 'Hispanic', 'Asian', 'AIAN', 'NHPI', 'Other']
        medical_deserts_by_race = {race: [] for race in races}

        k, cvs_pharmacies, walgreens_pharmacies, walmart_pharmacies = utils.get_pharmacy_coordinates(state_name,
                                                                                                     which='top3')
        pharmacy_coordinates = cvs_pharmacies + walgreens_pharmacies + walmart_pharmacies

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
                medical_deserts.append([longitudes[j], latitudes[j]])
                if df.iloc[j].pct_NH_Blk_alone_ACS_10_14 >= 50:
                    medical_deserts_by_race['Black'].append([longitudes[j], latitudes[j]])
                elif df.iloc[j].pct_NH_White_alone_ACS_10_14 >= 50:
                    medical_deserts_by_race['White'].append([longitudes[j], latitudes[j]])
                elif df.iloc[j].pct_Hispanic_ACS_10_14 >= 50:
                    medical_deserts_by_race['Hispanic'].append([longitudes[j], latitudes[j]])
                elif df.iloc[j].pct_NH_Asian_alone_ACS_10_14 >= 50:
                    medical_deserts_by_race['Asian'].append([longitudes[j], latitudes[j]])
                elif df.iloc[j].pct_NH_AIAN_alone_ACS_10_14 >= 50:
                    medical_deserts_by_race['AIAN'].append([longitudes[j], latitudes[j]])
                elif df.iloc[j].pct_NH_NHOPI_alone_ACS_10_14 >= 50:
                    medical_deserts_by_race['NHPI'].append([longitudes[j], latitudes[j]])
                else:
                    medical_deserts_by_race['Other'].append([longitudes[j], latitudes[j]])

        return medical_deserts, medical_deserts_by_race


    races = ['White', 'Black', 'Hispanic', 'Asian', 'AIAN', 'NHPI', 'Other']
    n_miles = st.session_state['n_miles']
    poverty_threshold = st.session_state['pov_threshold']
    medical_deserts, medical_deserts_by_race = get_medical_deserts(state_name, n_miles, poverty_threshold)
    for race in races:
        if len(medical_deserts_by_race[race]) > 0:
            plt.scatter([x[0] for x in medical_deserts_by_race[race]], [x[1] for x in medical_deserts_by_race[race]],
                    marker='o', s=5, label='Majority ' + race)

    plt.legend()
    plot_utils.plot_state_map(state_name)
    plt.axis('off')
    plt.title('Medical deserts in ' + state_name + ', USA \n colored by racial majority')

    st.pyplot(fig, dpi=600, transparent=True, bbox_inches='tight', clear_figure=True)


fractional_medical_desert_groups = {race: [] for race in races}
fractional_census_tracts = {race: [] for race in races}

deserts = sum([len(medical_deserts_by_race[race]) for race in races])
st.write('There are :red[' + str(deserts) + '] medical deserts in ' + state_name + ', USA.')
if deserts != 0:
    for race in races:
        fractional_medical_desert_groups[race] = len(medical_deserts_by_race[race])/deserts
        fractional_census_tracts[race] = len(all_tracts[race])/n
        percent_deserts = math.floor(100*fractional_medical_desert_groups[race])
        percent_census_tracts = math.floor(100*fractional_census_tracts[race])
        race = race[0].upper() + race[1:]
        if fractional_medical_desert_groups[race] - fractional_census_tracts[race] >= 0.10 and race != 'Other':
            st.write(race + ' population may be disproportionately affected by medical deserts in ' + state_name + ', USA. ' +
                     'About :red[' + str(percent_deserts) + '%] of medical deserts are majority ' + race + '. ' +
                     'Only about :blue[' + str(percent_census_tracts) + '%] of Census tracts are majority ' + race + '.')
