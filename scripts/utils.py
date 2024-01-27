# Imports
"""
Author: Michael Wang, mzywang
Author: Jai Moondra
"""
from geopy.geocoders import Nominatim
import numpy as np
import pandas as pd
# import warnings
import re
import math
import os
from pathlib import Path
from scripts.constants import *


state_abbreviations_path = './data/usa_state_abbreviations.csv'
pharmacies_data_path = './data/usa_pharmacies.csv'
census_data_path = './data/usa_census_data_by_state/'
geographic_data_path = './data/usa_geographic_data.csv'


def get_state_abbreviation(state_name='Georgia'):
    """
    Returns a dictionary of state abbreviations
    :return: dictionary of state abbreviations
    """
    state_abbreviations = pd.read_csv(state_abbreviations_path,  index_col=0)
    return state_abbreviations.loc[state_name, 'Abbreviation']


def distance_from_coordinates(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on Earth using the Haversine formula
    :param lat1: latitude of point 1
    :param lon1: longitude of point 1
    :param lat2: latitude of point 2
    :param lon2: longitude of point 2
    :return: distance between the two points in km
    """
    # Convert degrees to radians
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    distance = 6371 * c

    return distance


def distance_from_coordinates_2(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on Earth using the Pythagorean theorem
    :param lat1: latitude of point 1
    :param lon1: longitude of point 1
    :param lat2: latitude of point 2
    :param lon2: longitude of point 2
    :return: distance between the two points in km
    """
    # Convert to km
    x_diff = (lon2 - lon1) * longitude_to_km
    y_diff = (lat2 - lat1) * latitude_to_km
    if abs(x_diff) > 50 or abs(y_diff) > 50:
        return np.inf
    else:
        return math.sqrt(x_diff ** 2 + y_diff ** 2)



def generate_groups(census_dataframe, income_threshold=30, no_insurance_threshold=25, two_insurance_threshold=25):
    """
    Generate the groups for the census data
    :param census_dataframe: dataframe containing the census data
    :param income_threshold: threshold for the income group
    :param no_insurance_threshold: threshold for the no insurance group
    :param two_insurance_threshold: threshold for the two insurance group
    :return: dataframe containing the census data with the groups
    """
    races = ['White', 'Black', 'Hispanic', 'Asian', 'AIAN', 'NHPI', 'Other']
    race_dict = {'AIAN': 'pct_NH_AIAN_alone_ACS_10_14',
                 'NHPI': 'pct_NH_NHOPI_alone_ACS_10_14',
                 'Other': 'pct_NH_SOR_alone_ACS_10_14',
                 'White': 'pct_NH_White_alone_ACS_10_14',
                 'Black': 'pct_NH_Blk_alone_ACS_10_14',
                 'Asian': 'pct_NH_Asian_alone_ACS_10_14',
                 'Hispanic': 'pct_Hispanic_ACS_10_14',
                }
    groups = {
        race: {'No insurance': {'BP': [], 'AP': []},
               'One insurance': {'BP': [], 'AP': []},
               'Two insurance': {'BP': [], 'AP': []}} for race in races
    }

    n = len(census_dataframe)
    l = [0, 0, 0]
    for j in range(n):
        if census_dataframe.iloc[j].pct_NH_Blk_alone_ACS_10_14 >= 50:
            l[0] = 'Black'
        elif census_dataframe.iloc[j].pct_NH_White_alone_ACS_10_14 >= 50:
            l[0] = 'White'
        elif census_dataframe.iloc[j].pct_Hispanic_ACS_10_14 >= 50:
            l[0] = 'Hispanic'
        elif census_dataframe.iloc[j].pct_NH_Asian_alone_ACS_10_14 >= 50:
            l[0] = 'Asian'
        elif census_dataframe.iloc[j].pct_NH_AIAN_alone_ACS_10_14 >= 50:
            l[0] = 'AIAN'
        elif census_dataframe.iloc[j].pct_NH_NHOPI_alone_ACS_10_14 >= 50:
            l[0] = 'NHPI'
        else:
            l[0] = 'Other'

        if census_dataframe.iloc[j].pct_No_Health_Ins_ACS_10_14 >= no_insurance_threshold:
            l[1] = 'No insurance'
        elif census_dataframe.iloc[j].pct_TwoPHealthIns_ACS_10_14 <= two_insurance_threshold:
            l[1] = 'Two insurance'
        else:
            l[1] = 'One insurance'

        if census_dataframe.iloc[j].pct_Prs_Blw_Pov_Lev_ACS_10_14 >= income_threshold:
            l[2] = 'BP'
        else:
            l[2] = 'AP'

        groups[l[0]][l[1]][l[2]].append(j)

    return groups


def df_for_county(county_name, df):
    """
    Takes in county name and state name and returns dataframe entries corresponding to that county

    Args:
        county_name (str): Name of the desired county

    Returns:
        county_df (df): Dataframe of corresponding entries for the desired county combination

    """
    county_df = df.loc[df['County_name'] == county_name]
    if len(county_df) == 0:
        print("Warning! (County = {}) filtered to an empty dataframe".format(county_name))
    return county_df


def map_lat_long_geoid(geoid_min, geoid_max, df, gaz_tracts_df):
    """
    Modifies dataframe in place to append latitude and longitude columns

    Args:
        geoid_min (int): Minimum geo_id in the dataframe being modified
        geoid_max (int): Maximum geo_id in the dataframe being modified
        df (df): Dataframe to append latitude and longitude to

    Returns:
        None

    """
    lat_long_df = gaz_tracts_df[gaz_tracts_df['GEOID'] >= geoid_min]
    lat_long_df = lat_long_df[lat_long_df['GEOID'] < geoid_max]
    lat_long_df = lat_long_df[['GEOID', 'INTPTLAT', 'INTPTLONG']]
    num_tracts = len(lat_long_df) - 1
    gidtr_lat, gidtr_long = {}, {}
    for i in range(num_tracts):
        geoid, lat, long = lat_long_df.iloc[i][0], lat_long_df.iloc[i][1], lat_long_df.iloc[i][2]
        gidtr_lat[geoid], gidtr_long[geoid] = lat, long
    df['Latitude'] = df['GIDTR'].map(gidtr_lat)
    df['Longitude'] = df['GIDTR'].map(gidtr_long)


def recursive_reverse(latlong):
    """
    Wrapper function for geolocator.reverse in case of timeout

    Args:
        latlong (list): List containing two elements, latitude and longitude to be looked up

    Returns:
        dict: A dictionary of the address associated with the lat-long argument

    """

    geolocator = Nominatim(user_agent='h-mortagy@hotmail.com')

    try:
        return geolocator.reverse(latlong)
    except:
        return recursive_reverse(latlong)


def generate_county_state_str(county, state):
    """
    Generates a string that uniquely identifies a state and county

    Args:
        county (str): Desired county
        state (str): Desired state

    Returns:
        str: Filename-friendly string that uniquely identifies the desired state and county.
    """
    return "{}_{}".format(county, state).replace(' ', '_')


def load_zipcode_data(income_current_tr_df, county_state_string, load_cached):
    """
    Loads zipcode data associated with a county-state pair

    Args:
        county_state_string (str): String that uniquely identifies the state county pair (see generate_county_state_str)
        load_cached (bool): True if loading cached copy of zipcode_list and zipcode_map

    Returns:
        zipcode_map (dict): Dictionary that maps zipcode strings to the customer id's residing in the zipcode
        zipcode_list (list): List of zipcodes (str) that are contained in the county
    """

    zipcode_data_string = ("zipcode_data/{}.pkl".format(county_state_string))
    if not load_cached:
        print("Using geolocator to retrieve zipcodes (this may take a few minutes)... \n")
        zipcode_map = {}
        zipcode_list = []

        for index, row in income_current_tr_df.iterrows():
            lat = row['Latitude']
            long = row['Longitude']
            location = recursive_reverse([lat, long])
            zipcode = ''
            if 'address' in location.raw:
                if 'postcode' in location.raw['address']:
                    postcode = location.raw['address']['postcode']
                    if ':' in postcode:
                        codes = postcode.split(':')
                        zipcode = codes[0]
                    else:
                        zipcode = re.sub('[^0-9]','', postcode)
            # Cleans a specific data point for Fulton County
            if zipcode != '':
                if zipcode == '300009':
                    zipcode = '30009'
                zipcode_map[index] = zipcode
                zipcode_list.append(zipcode)
            else:
                zipcode_map[index] = None
                zipcode_list.append(None)

        print("Saving zipcode data to '{}'...\n".format(zipcode_data_string))

        with open(zipcode_data_string, 'wb') as f:  # Python 3: open(..., 'wb')
            pickle.dump([zipcode_map, zipcode_list], f)
    else:
        try:
            print("Using cached copy of zipcode data from '{}'... \n".format(zipcode_data_string))
            with open(zipcode_data_string, 'rb') as f:
                zipcode_map, zipcode_list = pickle.load(f)
        except:
            print("No such cached copy exists, recursively calling function with False flag... \n")
            zipcode_map, zipcode_list = load_zipcode_data(income_current_tr_df, county_state_string, False)
    return (zipcode_map, zipcode_list)


def get_dataframe(current_state=None, current_county=None):
    if current_county is not None:
        if not current_county.endswith('County'):
            current_county += ' County'

    default_encoding = "ISO-8859-1"

    # Load raw data
    dataframe = pd.read_csv(Path(census_data_path + current_state + '.csv'), encoding='cp1252')

    # Filter for specified County
    # current_county = current_county.upper()
    if current_county is not None:
        current_tr_df = df_for_county(current_county, dataframe)
    else:
        current_tr_df = dataframe

    # Load raw geographic data
    gaz_tracts_df = pd.read_csv(geographic_data_path, encoding=default_encoding)
    gaz_tracts_df = gaz_tracts_df.drop(columns="Column1") # drops an empty column from bad csv formatting

    # Append latitude and longitudes
    min_geo_id = min(current_tr_df['GIDTR'].tolist())
    max_geo_id = max(current_tr_df['GIDTR'].tolist())
    map_lat_long_geoid(min_geo_id, max_geo_id, current_tr_df, gaz_tracts_df)

    # Filter columns for relevant attributes
    income_current_tr_df = current_tr_df[['Latitude',
                                        'Longitude',
                                        'LAND_AREA',
                                        'Tot_Population_ACS_10_14',
                                        'Med_HHD_Inc_ACS_10_14',
                                        'pct_Prs_Blw_Pov_Lev_ACS_10_14',
                                        'pct_NH_AIAN_alone_ACS_10_14',
                                        'pct_NH_NHOPI_alone_ACS_10_14',
                                        'pct_NH_SOR_alone_ACS_10_14',
                                        'pct_NH_White_alone_ACS_10_14',
                                        'pct_NH_Blk_alone_ACS_10_14',
                                        'pct_NH_Asian_alone_ACS_10_14',
                                        'pct_Hispanic_ACS_10_14',
                                        'pct_No_Health_Ins_ACS_10_14',
                                        'pct_One_Health_Ins_ACS_10_14',
                                        'pct_TwoPHealthIns_ACS_10_14',
                                        'PUB_ASST_INC_ACS_10_14']]

    old_len = len(income_current_tr_df)
    for header in list(income_current_tr_df):
        income_current_tr_df = income_current_tr_df[pd.notnull(income_current_tr_df[header])]
    new_len = len(income_current_tr_df)

    # Convert income attribute from string to float
    remove_characters = str.maketrans("", "", "$,")
    income_list = list(income_current_tr_df['Med_HHD_Inc_ACS_10_14'])
    if len(income_list) != 0 and isinstance(income_list[0], str):
        income_list_float = [float(income.translate(remove_characters)) for income in income_list]
        income_current_tr_df['Med_HHD_Inc_ACS_10_14'] = income_list_float

    income_current_tr_df = income_current_tr_df.dropna(axis=0, subset=['Latitude', 'Longitude'])

    # Collect zipcodes: if false then retrieves all zipcodes,
    # # otherwise uses a previously saved file with the "True" option.
    # county_state_string = generate_county_state_str(current_county, current_state)
    # zipcode_map, zipcode_list = load_zipcode_data(income_current_tr_df, county_state_string, False)

    # Append zipcode
    # income_current_tr_df['Zipcode'] = pd.Series(zipcode_list, index = income_current_tr_df.index)

    # Remove rows with null zipcode
    # old_len = len(income_current_tr_df)
    # income_current_tr_df = income_current_tr_df[pd.notnull(income_current_tr_df['Zipcode'])]
    # new_len = len(income_current_tr_df)

    return income_current_tr_df


def get_pharmacy_coordinates(state_name='Georgia', which='all', county_name=None):
    """
    Gets the coordinates of the pharmacies in the given state or county
    :param state_name: name of the state
    :param which: if 'all', returns all pharmacies in the given state or county, if 'top3', returns CVS, Walgreens and
        Walmart pharmacies
    :param county_name: name of the county
    :return:
    """
    state_abbreviation = get_state_abbreviation(state_name)
    # Load data from saved file
    pharmacies_data = pd.read_csv(pharmacies_data_path, encoding='cp1252')
    # Filter for state nad county
    if county_name is not None:
        pharmacies_data = pharmacies_data[
            (pharmacies_data['State_Abbreviation'] == state_abbreviation) & (pharmacies_data['County'] == county_name)]
    else:
        pharmacies_data = pharmacies_data[pharmacies_data['State_Abbreviation'] == state_abbreviation]

    pharmacy_coordinates = []

    if which == 'all':
        for i in range(len(pharmacies_data.index)):
            pharmacy_coordinates.append((pharmacies_data.iloc[i]['Longitude'], pharmacies_data.iloc[i]['Latitude']))

        k = len(pharmacy_coordinates)
        return k, pharmacy_coordinates

    elif which == 'top3':
        cvs_pharmacies = pharmacies_data[pharmacies_data['Pharmacy_Name'].str.contains('CVS')]
        walgreens_pharmacies = pharmacies_data[pharmacies_data['Pharmacy_Name'].str.contains('WALGREENS')]
        walmart_pharmacies = pharmacies_data[pharmacies_data['Pharmacy_Name'].str.contains('WAL-MART')]

        cvs_pharmacy_coordinates = []
        walgreens_pharmacies_coordinates = []
        walmart_pharmacies_coordinates = []

        for i in range(len(cvs_pharmacies.index)):
            cvs_pharmacy_coordinates.append((cvs_pharmacies.iloc[i]['Longitude'], cvs_pharmacies.iloc[i]['Latitude']))
            pharmacy_coordinates.append((pharmacies_data.iloc[i]['Longitude'], pharmacies_data.iloc[i]['Latitude']))

        for i in range(len(walgreens_pharmacies.index)):
            walgreens_pharmacies_coordinates.append(
                (walgreens_pharmacies.iloc[i]['Longitude'], walgreens_pharmacies.iloc[i]['Latitude']))
            pharmacy_coordinates.append((pharmacies_data.iloc[i]['Longitude'], pharmacies_data.iloc[i]['Latitude']))

        for i in range(len(walmart_pharmacies.index)):
            walmart_pharmacies_coordinates.append(
                (walmart_pharmacies.iloc[i]['Longitude'], walmart_pharmacies.iloc[i]['Latitude']))
            pharmacy_coordinates.append((pharmacies_data.iloc[i]['Longitude'], pharmacies_data.iloc[i]['Latitude']))

        k = len(cvs_pharmacy_coordinates) + len(walgreens_pharmacies_coordinates) + len(walmart_pharmacies_coordinates)
        return k, cvs_pharmacy_coordinates, walgreens_pharmacies_coordinates, walmart_pharmacies_coordinates

