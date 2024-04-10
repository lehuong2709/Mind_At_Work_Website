"""
ToDo: DEPRECATED. REMOVE.
Title: Census Data Handler
Author: Jai Moondra, @jaimoondra, jaimoondra.github.io
Date: 2024-02-15
Description: This file contains functions to handle the census data for the USA. Some other countries to be added soon.
"""

import geopandas as gpd
import logging
import matplotlib.pyplot as plt
import os
import pandas as pd
import requests
import topojson as tp
from src.usa.constants import *


CENSUS_DATA_PATH = os.path.join(os.getcwd(), 'data', 'usa', 'census')           # Path to the census data
SHAPEFILE_PATH = os.path.join(os.getcwd(), 'data', 'usa', 'shapefiles')         # Path to the shapefiles
PLOTS_PATH = os.path.join(os.getcwd(), 'data', 'usa', 'poverty_plots')          # Path to the plots


def simplify_census_tract_data(census_data):
    """
    Simplify the census data by renaming columns and converting data types.
    :param census_data: Census data
    :return:
    """

    census_data['population'] = pd.to_numeric(census_data['Tot_Population_ACS_16_20'])
    census_data.drop(columns=['Tot_Population_ACS_16_20'], inplace=True)
    census_data['white_only'] = pd.to_numeric(census_data['pct_NH_White_alone_ACS_16_20'])
    census_data.drop(columns=['pct_NH_White_alone_ACS_16_20'], inplace=True)
    census_data['black_only'] = pd.to_numeric(census_data['pct_NH_Blk_alone_ACS_16_20'])
    census_data.drop(columns=['pct_NH_Blk_alone_ACS_16_20'], inplace=True)
    census_data['aian_alone'] = pd.to_numeric(census_data['pct_NH_AIAN_alone_ACS_16_20'])
    census_data.drop(columns=['pct_NH_AIAN_alone_ACS_16_20'], inplace=True)
    census_data['asian_only'] = pd.to_numeric(census_data['pct_NH_Asian_alone_ACS_16_20'])
    census_data.drop(columns=['pct_NH_Asian_alone_ACS_16_20'], inplace=True)
    census_data['nhopi_alone'] = pd.to_numeric(census_data['pct_NH_NHOPI_alone_ACS_16_20'])
    census_data.drop(columns=['pct_NH_NHOPI_alone_ACS_16_20'], inplace=True)
    census_data['hispanic'] = pd.to_numeric(census_data['pct_Hispanic_ACS_16_20'])
    census_data.drop(columns=['pct_Hispanic_ACS_16_20'], inplace=True)
    census_data['below_poverty'] = pd.to_numeric(census_data['pct_Prs_Blw_Pov_Lev_ACS_16_20'])
    census_data.drop(columns=['pct_Prs_Blw_Pov_Lev_ACS_16_20'], inplace=True)
    census_data['no_health_ins'] = pd.to_numeric(census_data['pct_No_Health_Ins_ACS_16_20'])
    census_data.drop(columns=['pct_No_Health_Ins_ACS_16_20'], inplace=True)
    census_data['one_health_ins'] = pd.to_numeric(census_data['pct_One_Health_Ins_ACS_16_20'])
    census_data.drop(columns=['pct_One_Health_Ins_ACS_16_20'], inplace=True)
    census_data['two_health_ins'] = pd.to_numeric(census_data['pct_TwoPHealthIns_ACS_16_20'])
    census_data.drop(columns=['pct_TwoPHealthIns_ACS_16_20'], inplace=True)
    census_data['GEOID'] = pd.to_numeric(census_data['GEOID'])
    census_data['racial_majority'] = None

    for j in census_data.index:
        if census_data['white_only'][j] >= 50:
            census_data['racial_majority'][j] = 1
        elif census_data['black_only'][j] >= 50:
            census_data['racial_majority'][j] = 2
        elif census_data['aian_alone'][j] >= 50:
            census_data['racial_majority'][j] = 3
        elif census_data['asian_only'][j] >= 50:
            census_data['racial_majority'][j] = 4
        elif census_data['nhopi_alone'][j] >= 50:
            census_data['racial_majority'][j] = 5
        elif census_data['hispanic'][j] >= 50:
            census_data['racial_majority'][j] = 6
        else:
            census_data['racial_majority'][j] = 7

    return census_data


def get_census_blockgroup_data(state_fips, census_key, savefile=False, override_cache=False):
    """
    Get data for US Census blockgroups.
    :param state_fips: FIPS code for the state, see, e.g., https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt
    :param census_key: Census API key, see https://api.census.gov/data/key_signup.html
    :param savefile: if true, saves file to CENSUS_DATA_PATH
    :param override_cache: if true, ignores local cache and gets data from the internet
    :return: pandas DataFrame with census data
    """
    census_blockgroup_savefile = os.path.join(CENSUS_DATA_PATH, state_fips + '_census_blockgroup_data.csv')

    if os.path.exists(census_blockgroup_savefile) and (not override_cache):
        census_data = pd.read_csv(census_blockgroup_savefile)
    else:
        logging.info(f'Local data not found. Getting data for {state_fips}...')
        # Get data for US Census block groups:
        url_1_blockgroup = 'https://api.census.gov/data/2022/pdb/blockgroup?get='
        url_2_blockgroup = ','.join(
            total_population_variable + race_ethnicity_variables + economic_variables + healthcare_variables + geography_variables)
        url_3_blockgroup = '&for=block%20group:*&in=state:' + state_fips + '&in=county:*&in=tract:*&key='
        url_blockgroup = url_1_blockgroup + url_2_blockgroup + url_3_blockgroup + census_key

        response = requests.get(url_blockgroup)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Extract the data from the response
            data = response.text
            # print("Data retrieved successfully:")
        else:
            logging.error("Failed to retrieve data. Status code:", response.status_code)

        # Convert the data to a pandas DataFrame
        census_data = pd.read_json(data)
        census_data.columns = census_data.iloc[0]
        census_data = census_data[1:]
        census_data['GEOID'] = (
                census_data['state'] + census_data['county'] + census_data['tract'] + census_data['block group'])
        if len(census_data) == 0:
            print("No data found for the specified state.")

        census_data = simplify_census_tract_data(census_data)
        if savefile:
            census_data.to_csv(census_blockgroup_savefile)

    return census_data


def get_census_tract_data(state_fips, census_key, savefile=False, override_cache=False):
    """
    Get data for US Census tracts.
    :param state_fips: FIPS code for the state, see, e.g., https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt
    :param census_key: Census API key, see https://api.census.gov/data/key_signup.html
    :param savefile: if true, saves file to CENSUS_DATA_PATH
    :param override_cache: if true, ignores local cache and gets data from the internet
    :return: pandas DataFrame with census data
    """
    census_tract_savefile = os.path.join(CENSUS_DATA_PATH, state_fips + '_census_tract_data.csv')
    if os.path.exists(census_tract_savefile) and (not override_cache):
        census_data = pd.read_csv(census_tract_savefile)
    else:
        logging.info(f'Local data not found. Getting data for {state_fips}...')
        # Get data for US Census tracts:
        url_1_tract = 'https://api.census.gov/data/2022/pdb/tract?get='
        url_2_tract = ','.join(
            total_population_variable + race_ethnicity_variables + healthcare_variables + economic_variables)
        url_3_tract = '&for=tract:*&in=state:' + state_fips + '&in=county:*&key='
        url_tract = url_1_tract + url_2_tract + url_3_tract + census_key

        response = requests.get(url_tract)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Extract the data from the response
            data = response.text
            print("Data retrieved successfully:")
        else:
            print("Failed to retrieve data. Status code:", response.status_code)

        # Convert the data to a pandas DataFrame
        census_data = pd.read_json(data)
        census_data.columns = census_data.iloc[0]
        census_data = census_data[1:]
        census_data['GEOID'] = (census_data['state'] + census_data['county'] + census_data['tract'])
        if len(census_data) == 0:
            print("No data found for the specified state.")
        census_data = simplify_census_tract_data(census_data)
        if savefile:
            census_data.to_csv(census_tract_savefile)

    return census_data


def get_shapefiles(level, state_fips, savefile=False, override_cache=False):
    """
    Get shapefiles for the specified state and level.
    :param level: one of 'blockgroup', 'tract', 'county', or 'state'
    :param state_fips: FIPS code for the state, see, e.g., https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt
    :param savefile: if true, saves file to SHAPEFILE_PATH
    :param override_cache: if true, ignores local cache and gets data from the internet
    :return: shapefile dataframe
    """
    shapefile_save_path = SHAPEFILE_PATH
    shapefile_name = state_fips + '_' + level + '_shapefile.shp'

    if os.path.exists(os.path.join(shapefile_save_path, shapefile_name)) and (not override_cache):
        shapefile_df = gpd.read_file(os.path.join(shapefile_save_path, shapefile_name), geometry='geometry')
    else:
        logging.info(f'Local data not found. Getting data for {state_fips}...')
        shapefile_url_state = shapefiles_base_url + 'STATE/tl_' + shapefiles_year + '_us_state.zip'
        shapefile_url_county = shapefiles_base_url + 'COUNTY/tl_' + shapefiles_year + '_us_county.zip'
        shapefile_url_tract = shapefiles_base_url + 'TRACT/tl_' + shapefiles_year + '_' + state_fips + '_tract.zip'
        shapefile_url_blockgroup = shapefiles_base_url + 'BG/tl_' + shapefiles_year + '_' + state_fips + '_bg.zip'

        if level == 'blockgroup':
            shapefile_df = gpd.read_file(shapefile_url_blockgroup, geometry='geometry')
        elif level == 'tract':
            shapefile_df = gpd.read_file(shapefile_url_tract, geometry='geometry')
        elif level == 'county':
            shapefile_df = gpd.read_file(shapefile_url_county, geometry='geometry')
        elif level == 'state':
            shapefile_df = gpd.read_file(shapefile_url_state, geometry='geometry')
        else:
            raise ValueError("Invalid level. Must be one of 'blockgroup', 'tract', 'county', or 'state'.")

        shapefile_df = shapefile_df[shapefile_df['STATEFP'] == state_fips]
        shapefile_df['centroid'] = shapefile_df.geometry.centroid
        shapefile_df['Longitude'] = shapefile_df.centroid.x
        shapefile_df['Latitude'] = shapefile_df.centroid.y
        shapefile_df = shapefile_df.drop('centroid', axis=1)
        shapefile_df['GEOID'] = pd.to_numeric(shapefile_df['GEOID'])

        topo = tp.Topology(shapefile_df, prequantize=False)
        shapefile_df = topo.toposimplify(0.01).to_gdf()

        if savefile:
            shapefile_df.to_file(shapefile_save_path + shapefile_name)

    return shapefile_df


def get_merged_dataframe(shapefile_df, census_data):
    """
    Merge shapefile and census data.
    :param shapefile_df:
    :param census_data:
    :return:
    """
    merged_dataframe = pd.merge(shapefile_df, census_data, left_on='GEOID', right_on='GEOID')
    merged_dataframe.dropna(inplace=True)
    if len(merged_dataframe) == 0:
        raise ValueError("No data found for the specified state.")
    return merged_dataframe

