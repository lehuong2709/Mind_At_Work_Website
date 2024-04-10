from src.constants import *
from src.usa.constants import *
import contextily as ctx
# from src.usa.facilities_data_handler import read_abridged_facilities
from functools import partial
import geopandas as gpd
import geoplot.crs as gcrs
import logging
import mapclassify as mc
import matplotlib.cm as cm
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import os
import pandas as pd
import pyproj
from src.regions import Province
import requests
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, box
from shapely.ops import transform
import topojson as tp
from src.projections import closest_distance
from src.plot import *


class USAState(Province):
    """
    Represents a state in the USA.
    """

    def __init__(self, name):
        """
        Initializes a new USAState object.
        :param name: The name of the state.
        :param fips: The FIPS code of the state.
        """
        super().__init__(name, USA)
        self._name = name
        self._fips = territories_dictionary[name]['fips']
        self._abbreviation = territories_dictionary[name]['abbreviation']

    def get_state_info(self):
        """
        Get information about the state.
        :return: Information about the state.
        """
        info = 'US State: ' + self.name + ', '
        info += 'FIPS code: ' + self.fips + ', '
        info += 'Abbreviation: ' + self.abbreviation
        return info

    @property
    def name(self):
        """
        Gets the name of the state.
        :return: The name of the state.
        """
        return self._name

    @property
    def fips(self):
        """
        Gets the FIPS code of the state.
        :return: The FIPS code of the state.
        """
        return self._fips

    @property
    def abbreviation(self):
        """
        Gets the abbreviation of the state.
        :return: The abbreviation of the state.
        """
        return self._abbreviation

    @staticmethod
    def _simplify_census_tract_data(census_data):
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

        for j, row in census_data.iterrows():
            if row['white_only'] >= 50:
                census_data.at[j, 'racial_majority'] = 1
            elif row['black_only'] >= 50:
                census_data.at[j, 'racial_majority'] = 2
            elif row['aian_alone'] >= 50:
                census_data.at[j, 'racial_majority'] = 3
            elif row['asian_only'] >= 50:
                census_data.at[j, 'racial_majority'] = 4
            elif row['nhopi_alone'] >= 50:
                census_data.at[j, 'racial_majority'] = 5
            elif row['hispanic'] >= 50:
                census_data.at[j, 'racial_majority'] = 6
            else:
                census_data.at[j, 'racial_majority'] = 7

        return census_data

    def _get_census_data_from_api(self, level='blockgroup', variables=None, census_key=None):
        """
        Get data for US Census data for the state from census API.
        :param level: one of 'blockgroup', 'tract', or 'county'
        :param variables: list of variables (other than default variables) to get from the census API, optional
        :param census_key: Census API key, optional
        """
        if variables is None:
            variables = []

        if level == 'blockgroup':
            variables = variables + (total_population_variable +
                                     race_ethnicity_variables +
                                     economic_variables +
                                     healthcare_variables +
                                     geography_variables)

            url_header = census_base_url + 'blockgroup?get='
            url_variables = ','.join(variables)
            url_footer = '&for=block%20group:*&in=state:' + self.fips + '&in=county:*&in=tract:*&key='
            url_blockgroup = url_header + url_variables + url_footer + census_key

            response = requests.get(url_blockgroup)
            if response.status_code == 200:         # Check if the request was successful (status code 200)
                data = response.text
            else:
                raise ValueError('Failed to retrieve US census data. Status code:', response.status_code)

            # Convert the data to a pandas DataFrame
            census_data = pd.read_json(data)
            census_data.columns = census_data.iloc[0]
            census_data = census_data[1:]
            census_data['GEOID'] = (
                    census_data['state'] + census_data['county'] + census_data['tract'] + census_data['block group'])
            if len(census_data) == 0:
                raise ValueError("No data found for the specified state.")

            census_data = self._simplify_census_tract_data(census_data)
            census_data = self._get_locations_for_census_data(census_data, level='blockgroup')
        elif level == 'tract':
            variables = variables + (total_population_variable +
                                     race_ethnicity_variables +
                                     economic_variables +
                                     healthcare_variables
                                     )

            # Get data for US Census tracts:
            url_header = census_base_url + 'tract?get='
            url_variables = ','.join(variables)
            url_footer = '&for=tract:*&in=state:' + self.fips + '&in=county:*&key='
            url_tract = url_header + url_variables + url_footer + census_key

            response = requests.get(url_tract)
            if response.status_code == 200:             # Check if the request was successful (status code 200)
                data = response.text
            else:
                raise ValueError('Failed to retrieve US census data. Status code:', response.status_code)

            # Convert the data to a pandas DataFrame
            census_data = pd.read_json(data)
            census_data.columns = census_data.iloc[0]
            census_data = census_data[1:]
            census_data['GEOID'] = (census_data['state'] + census_data['county'] + census_data['tract'])

            if len(census_data) == 0:
                print("No data found for the specified state.")
            census_data = self._simplify_census_tract_data(census_data)
            census_data = self._get_locations_for_census_data(census_data, level='tract')
        elif level == 'county':
            variables = variables + (total_population_variable +
                                     race_ethnicity_variables +
                                     economic_variables +
                                     healthcare_variables
                                     )

            # Get data for US Census counties:
            url_header = census_base_url + 'county?get='
            url_variables = ','.join(variables)
            url_footer = '&for=county:*&in=state:' + self.fips + '&key='
            url_county = url_header + url_variables + url_footer + census_key

            response = requests.get(url_county)
            if response.status_code == 200:             # Check if the request was successful (status code 200)
                data = response.text
            else:
                raise ValueError('Failed to retrieve US census data. Status code:', response.status_code)

            # Convert the data to a pandas DataFrame
            census_data = pd.read_json(data)
            census_data.columns = census_data.iloc[0]
            census_data = census_data[1:]
            census_data['GEOID'] = (census_data['state'] + census_data['county'])

            if len(census_data) == 0:
                raise ValueError("No data found for the specified state.")
            census_data = self._simplify_census_tract_data(census_data)
            census_data = self._get_locations_for_census_data(census_data, level='county')
        else:
            raise ValueError("level must be one of 'blockgroup', 'tract', or 'county'.")

        return census_data

    def _get_census_data_from_cache(self, level='blockgroup'):
        """
        Get data for US Census data for the state if it exists in the local cache.
        :param level: one of 'blockgroup', 'tract', or 'county'
        :return: The census data if it exists in the local cache.
        """
        if level == 'blockgroup':
            savefile_path = os.path.join(CENSUS_DATA_PATH, self.fips + '_census_blockgroup_data.csv')
        elif level == 'tract':
            savefile_path = os.path.join(CENSUS_DATA_PATH, self.fips + '_census_tract_data.csv')
        elif level == 'county':
            savefile_path = os.path.join(CENSUS_DATA_PATH, self.fips + '_census_county_data.csv')
        else:
            raise ValueError("level must be one of 'blockgroup', 'tract', or 'county'.")

        if os.path.exists(savefile_path):
            census_data = pd.read_csv(savefile_path)
            if 'Unnamed: 0' in census_data.columns:
                census_data.drop(columns=['Unnamed: 0'], inplace=True)
        else:
            raise ValueError("No data found for the specified state and level.")

        return census_data

    def get_census_data(self, level='blockgroup', override_cache=False, save_to_file=False, census_key=None):
        """
        Get data for US Census data for the state from the local cache or the internet. If the data is retrieved from the
        internet, it can be saved to the local cache.
        :param level: one of 'blockgroup', 'tract', or 'county'
        :param override_cache: whether to ignore the local cache and get the data from the internet
        :param save_to_file: whether to save the data to the local cache when retrieved from the internet
        :param census_key: census API key to use when getting data from the internet
        :return:
        """
        if override_cache is False:
            try:
                census_data = self._get_census_data_from_cache(level=level)
            except ValueError:
                census_data = self._get_census_data_from_api(level=level, census_key=census_key)
        else:
            census_data = self._get_census_data_from_api(level=level, census_key=census_key)

        if save_to_file:
            if level == 'blockgroup':
                savefile_path = os.path.join(CENSUS_DATA_PATH, self.fips + '_census_blockgroup_data.csv')
            elif level == 'tract':
                savefile_path = os.path.join(CENSUS_DATA_PATH, self.fips + '_census_tract_data.csv')
            elif level == 'county':
                savefile_path = os.path.join(CENSUS_DATA_PATH, self.fips + '_census_county_data.csv')
            else:
                raise ValueError("level must be one of 'blockgroup', 'tract', or 'county'.")
            census_data.to_csv(savefile_path, index=False)

        return census_data

    @staticmethod
    def _add_geographical_centroid(dataframe):
        dataframe_geometry = dataframe.geometry
        original_crs = 4326  # Save the original CRS
        target_crs = 3035  # equal planar area projection
        dataframe_geometry = dataframe_geometry.to_crs(target_crs)  # Reproject GeoDataFrame to the target CRS
        dataframe_geometry['centroid'] = dataframe.geometry.centroid  # Compute the centroid of the geometries
        dataframe_geometry.crs = original_crs  # Set the original CRS
        dataframe['centroid'] = dataframe_geometry['centroid']  # Add the centroid to the GeoDataFrame

        return dataframe

    def get_shapefiles(self, level='tract', savefile=False, override_cache=False, CENSUS_DATA_PATH=CENSUS_DATA_PATH,
                       variables=None, census_key=None, savefile_path=None):
        """
        Get shapefiles for the specified state and level.
        :param level: one of 'blockgroup', 'tract', 'county', or 'state'
        :param state_fips: FIPS code for the state, see, e.g., https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt
        :param savefile: if true, saves file to SHAPEFILE_PATH
        :param override_cache: if true, ignores local cache and gets data from the internet
        :return: shapefile dataframe
        """
        if level not in ['blockgroup', 'tract', 'county', 'state']:
            raise ValueError("level must be one of 'blockgroup', 'tract', 'county', or 'state'.")

        if savefile_path is None:
            savefile_path = os.path.join(SHAPEFILE_PATH, self.fips + '_' + level + '_shapefile.shp')

        if os.path.exists(savefile_path) and override_cache is False:
            shapefile_df = gpd.read_file(savefile_path, geometry='geometry')
            return shapefile_df

        logging.info(f'Local data not found. Getting shapefile data for {self.name}...')

        if census_key is None:
            census_key = census_key

        if level == 'blockgroup':
            shapefile_url = shapefiles_base_url + 'BG/tl_' + SHAPEFILES_YEAR + '_' + self.fips + '_bg.zip'
        elif level == 'tract':
            shapefile_url = shapefiles_base_url + 'TRACT/tl_' + SHAPEFILES_YEAR + '_' + self.fips + '_tract.zip'
        elif level == 'county':
            shapefile_url = shapefiles_base_url + 'COUNTY/tl_' + SHAPEFILES_YEAR + '_us_county.zip'
        else:
            shapefile_url = shapefiles_base_url + 'STATE/tl_' + SHAPEFILES_YEAR + '_us_state.zip'

        shapefile_df = gpd.read_file(shapefile_url, geometry='geometry')

        shapefile_df = shapefile_df[shapefile_df['STATEFP'] == self.fips]
        shapefile_df = self._add_geographical_centroid(shapefile_df)
        shapefile_df['Longitude'] = shapefile_df.centroid.x
        shapefile_df['Latitude'] = shapefile_df.centroid.y
        shapefile_df = shapefile_df.drop('centroid', axis=1)
        shapefile_df['GEOID'] = pd.to_numeric(shapefile_df['GEOID'])

        topo = tp.Topology(shapefile_df, prequantize=False)
        shapefile_df = topo.toposimplify(0.01).to_gdf()

        if savefile:
            shapefile_df.to_file(savefile_path)

        return shapefile_df

    def _get_locations_for_census_data(self, census_data, level='tract', census_key=None):
        """
        Get the locations for the census data.
        :param census_data: Census data
        :param level: The level of the data (tract, blockgroup, etc.)
        :return: The locations for the census data.
        """
        shapefile_df = self.get_shapefiles(level=level, census_key=census_key)
        census_data = census_data.merge(shapefile_df[['Longitude', 'Latitude', 'GEOID']], left_on='GEOID', right_on='GEOID')

        return census_data

    def plot_state_boundary(self, fig):
        """
        Plot the boundary of the state.
        :param fig: Plotly figure
        :return: Plotly figure
        """

        shapefile_df = self.get_shapefiles(level='state').to_crs(projection_north_america)
        usa_shapefile_df = gpd.read_file('data/usa/shapefiles/north_america_political_boundaries/Political_Boundaries__Area_.shp')
        usa_shapefile_df.to_crs(projection_north_america, inplace=True)

        bounds = shapefile_df.total_bounds

        x_span = bounds[2] - bounds[0]
        y_span = bounds[3] - bounds[1]
        x_pad = x_span * 0.05
        y_pad = y_span * 0.05

        bounds[0], bounds[2] = bounds[0] - x_pad, bounds[2] + x_pad
        bounds[1], bounds[3] = bounds[1] - y_pad, bounds[3] + y_pad

        if self.name == 'Alaska':
            bounds[0] = -180
            bounds[2] = -130
            x_span = (bounds[2] - bounds[0])/2

        usa_shapefile_df = usa_shapefile_df.cx[bounds[0] - 0.2 * x_span: bounds[2] + 0.2 * x_span, bounds[1] - 0.2 * y_span: bounds[3] + 0.2 * y_span]
        shapefile_df = usa_shapefile_df[usa_shapefile_df['STATEABB'] == 'US-' + self.abbreviation]

        # Add the secondary land layer
        fig = plot_secondary_land_layer(fig, usa_shapefile_df, waterbody_points)

        # Add the primary land layer
        fig = plot_primary_land_layer(fig, shapefile_df)

        # Add the boundaries
        fig = plot_boundaries(fig, usa_shapefile_df)

        # Update the layout
        # fig = update_plotly_figure_layout(fig, bounds)

        return fig, bounds


# class USAState(Province):
#     """
#     Represents a state in the USA.
#     """
#
#     def __init__(self, name):
#         """
#         Initializes a new USAState object.
#         :param name: The name of the state.
#         :param fips: The FIPS code of the state.
#         """
#         super().__init__(name, USA)
#         self._name = name
#         self._fips = territories_dictionary[name]['fips']
#         self._abbreviation = territories_dictionary[name]['abbreviation']
#
#     def get_state_info(self):
#         """
#         Get information about the state.
#         :return: Information about the state.
#         """
#         info = 'US State: ' + self.name + ', '
#         info += 'FIPS code: ' + self.fips + ', '
#         info += 'Abbreviation: ' + self.abbreviation
#         return info
#
#     @property
#     def name(self):
#         """
#         Gets the name of the state.
#         :return: The name of the state.
#         """
#         return self._name
#
#     @property
#     def fips(self):
#         """
#         Gets the FIPS code of the state.
#         :return: The FIPS code of the state.
#         """
#         return self._fips
#
#     @property
#     def abbreviation(self):
#         """
#         Gets the abbreviation of the state.
#         :return: The abbreviation of the state.
#         """
#         return self._abbreviation
#
#     @staticmethod
#     def _simplify_census_tract_data(census_data):
#         """
#         Simplify the census data by renaming columns and converting data types.
#         :param census_data: Census data
#         :return:
#         """
#         census_data['population'] = pd.to_numeric(census_data['Tot_Population_ACS_16_20'])
#         census_data.drop(columns=['Tot_Population_ACS_16_20'], inplace=True)
#         census_data['white_only'] = pd.to_numeric(census_data['pct_NH_White_alone_ACS_16_20'])
#         census_data.drop(columns=['pct_NH_White_alone_ACS_16_20'], inplace=True)
#         census_data['black_only'] = pd.to_numeric(census_data['pct_NH_Blk_alone_ACS_16_20'])
#         census_data.drop(columns=['pct_NH_Blk_alone_ACS_16_20'], inplace=True)
#         census_data['aian_alone'] = pd.to_numeric(census_data['pct_NH_AIAN_alone_ACS_16_20'])
#         census_data.drop(columns=['pct_NH_AIAN_alone_ACS_16_20'], inplace=True)
#         census_data['asian_only'] = pd.to_numeric(census_data['pct_NH_Asian_alone_ACS_16_20'])
#         census_data.drop(columns=['pct_NH_Asian_alone_ACS_16_20'], inplace=True)
#         census_data['nhopi_alone'] = pd.to_numeric(census_data['pct_NH_NHOPI_alone_ACS_16_20'])
#         census_data.drop(columns=['pct_NH_NHOPI_alone_ACS_16_20'], inplace=True)
#         census_data['hispanic'] = pd.to_numeric(census_data['pct_Hispanic_ACS_16_20'])
#         census_data.drop(columns=['pct_Hispanic_ACS_16_20'], inplace=True)
#         census_data['below_poverty'] = pd.to_numeric(census_data['pct_Prs_Blw_Pov_Lev_ACS_16_20'])
#         census_data.drop(columns=['pct_Prs_Blw_Pov_Lev_ACS_16_20'], inplace=True)
#         census_data['no_health_ins'] = pd.to_numeric(census_data['pct_No_Health_Ins_ACS_16_20'])
#         census_data.drop(columns=['pct_No_Health_Ins_ACS_16_20'], inplace=True)
#         census_data['one_health_ins'] = pd.to_numeric(census_data['pct_One_Health_Ins_ACS_16_20'])
#         census_data.drop(columns=['pct_One_Health_Ins_ACS_16_20'], inplace=True)
#         census_data['two_health_ins'] = pd.to_numeric(census_data['pct_TwoPHealthIns_ACS_16_20'])
#         census_data.drop(columns=['pct_TwoPHealthIns_ACS_16_20'], inplace=True)
#         census_data['GEOID'] = pd.to_numeric(census_data['GEOID'])
#         census_data['racial_majority'] = None
#
#         for j, row in census_data.iterrows():
#             if row['white_only'] >= 50:
#                 census_data.at[j, 'racial_majority'] = 1
#             elif row['black_only'] >= 50:
#                 census_data.at[j, 'racial_majority'] = 2
#             elif row['aian_alone'] >= 50:
#                 census_data.at[j, 'racial_majority'] = 3
#             elif row['asian_only'] >= 50:
#                 census_data.at[j, 'racial_majority'] = 4
#             elif row['nhopi_alone'] >= 50:
#                 census_data.at[j, 'racial_majority'] = 5
#             elif row['hispanic'] >= 50:
#                 census_data.at[j, 'racial_majority'] = 6
#             else:
#                 census_data.at[j, 'racial_majority'] = 7
#
#         return census_data
#
#     def get_census_blockgroup_data(self, savefile=False, override_cache=False,
#                                    variables=None, census_key=None, savefile_path=None):
#         """
#         Get data for US Census blockgroups for the state.
#         :param savefile: if true, saves file to CENSUS_DATA_PATH
#         :param override_cache: if true, ignores local cache and gets data from the internet
#         :param CENSUS_DATA_PATH: path to the census data
#         :param variables: list of variables to get from the census API
#         """
#         if savefile_path is None:
#             savefile_path = os.path.join(CENSUS_DATA_PATH, self.fips + '_census_blockgroup_data.csv')
#
#         if os.path.exists(savefile_path) and override_cache is False:
#             census_data = pd.read_csv(savefile_path)
#             return census_data
#
#         logging.info(f'Local data not found. Getting census data for {self.name}...')
#
#         if census_key is None:
#             census_key = census_key
#
#         if variables is None:
#             variables = (total_population_variable +
#                          race_ethnicity_variables +
#                          economic_variables +
#                          healthcare_variables +
#                          geography_variables)
#
#         # Get data for US Census block groups:
#         url_header = census_base_url + 'blockgroup?get='
#         url_variables = ','.join(variables)
#         url_footer = '&for=block%20group:*&in=state:' + self.fips + '&in=county:*&in=tract:*&key='
#         url_blockgroup = url_header + url_variables + url_footer + census_key
#
#         response = requests.get(url_blockgroup)
#         if response.status_code == 200:         # Check if the request was successful (status code 200)
#             data = response.text
#         else:
#             raise ValueError('Failed to retrieve US census data. Status code:', response.status_code)
#
#         # Convert the data to a pandas DataFrame
#         census_data = pd.read_json(data)
#         census_data.columns = census_data.iloc[0]
#         census_data = census_data[1:]
#         census_data['GEOID'] = (
#                 census_data['state'] + census_data['county'] + census_data['tract'] + census_data['block group'])
#         if len(census_data) == 0:
#             raise ValueError("No data found for the specified state.")
#
#         census_data = self._simplify_census_tract_data(census_data)
#         census_data = self._get_locations_for_census_data(census_data, level='blockgroup')
#
#         if savefile:
#             census_data.to_csv(savefile_path, index=False)
#
#         if 'Unnamed: 0' in census_data.columns:
#             census_data.drop(columns=['Unnamed: 0'], inplace=True)
#
#         return census_data
#
#     def get_census_tract_data(self, savefile=False, override_cache=False,
#                                    variables=None, census_key=None, savefile_path=None):
#         """
#         Get data for US Census tracts.
#         :param savefile: if true, saves file to CENSUS_DATA_PATH
#         :param override_cache: if true, ignores local cache and gets data from the internet
#         :param CENSUS_DATA_PATH: path to the census data
#         :param variables: list of variables to get from the census API
#         """
#         if savefile_path is None:
#             savefile_path = os.path.join(CENSUS_DATA_PATH, self.fips + '_census_tract_data.csv')
#
#         if os.path.exists(savefile_path) and override_cache is False:
#             census_data = pd.read_csv(savefile_path)
#             return census_data
#
#         logging.info(f'Local data not found. Getting census data for {self.name}...')
#
#         if census_key is None:
#             census_key = census_key
#
#         if variables is None:
#             variables = (total_population_variable +
#                          race_ethnicity_variables +
#                          economic_variables +
#                          healthcare_variables
#                         )
#
#
#         # Get data for US Census tracts:
#         url_header = census_base_url + 'tract?get='
#         url_variables = ','.join(variables)
#         url_footer = '&for=tract:*&in=state:' + self.fips + '&in=county:*&key='
#         url_tract = url_header + url_variables + url_footer + census_key
#
#         response = requests.get(url_tract)
#         if response.status_code == 200:             # Check if the request was successful (status code 200)
#             data = response.text
#         else:
#             raise ValueError('Failed to retrieve US census data. Status code:', response.status_code)
#
#         # Convert the data to a pandas DataFrame
#         census_data = pd.read_json(data)
#         census_data.columns = census_data.iloc[0]
#         census_data = census_data[1:]
#         census_data['GEOID'] = (census_data['state'] + census_data['county'] + census_data['tract'])
#
#         if len(census_data) == 0:
#             print("No data found for the specified state.")
#         census_data = self._simplify_census_tract_data(census_data)
#         census_data = self._get_locations_for_census_data(census_data, level='tract')
#
#         if savefile:
#             census_data.to_csv(savefile_path, index=False)
#
#         if 'Unnamed: 0' in census_data.columns:
#             census_data.drop(columns=['Unnamed: 0'], inplace=True)
#
#         return census_data
#
#     def get_census_county_data(self, savefile=False, override_cache=False,
#                               variables=None, census_key=None, savefile_path=None):
#         """
#         Get data for US Census counties.
#         :param savefile: if true, saves file to CENSUS_DATA_PATH
#         :param override_cache: if true, ignores local cache and gets data from the internet
#         :param CENSUS_DATA_PATH: path to the census data
#         :param variables: list of variables to get from the census API
#         """
#         if savefile_path is None:
#             savefile_path = os.path.join(CENSUS_DATA_PATH, self.fips + '_census_county_data.csv')
#
#         if os.path.exists(savefile_path) and override_cache is False:
#             census_data = pd.read_csv(savefile_path)
#             return census_data
#
#         logging.info(f'Local data not found. Getting census data for {self.name}...')
#
#         if census_key is None:
#             census_key = census_key
#
#         if variables is None:
#             variables = (total_population_variable +
#                          race_ethnicity_variables +
#                          economic_variables +
#                          healthcare_variables
#                         )
#
#         # Get data for US Census counties:
#         url_header = census_base_url + 'county?get='
#         url_variables = ','.join(variables)
#         url_footer = '&for=county:*&in=state:' + self.fips + '&key='
#         url_county = url_header + url_variables + url_footer + census_key
#
#         response = requests.get(url_county)
#         if response.status_code == 200:             # Check if the request was successful (status code 200)
#             data = response.text
#         else:
#             raise ValueError('Failed to retrieve US census data. Status code:', response.status_code)
#
#         # Convert the data to a pandas DataFrame
#         census_data = pd.read_json(data)
#         census_data.columns = census_data.iloc[0]
#         census_data = census_data[1:]
#         census_data['GEOID'] = (census_data['state'] + census_data['county'])
#
#         if len(census_data) == 0:
#             raise ValueError("No data found for the specified state.")
#         census_data = self._simplify_census_tract_data(census_data)
#         census_data = self._get_locations_for_census_data(census_data, level='county')
#
#         if savefile:
#             census_data.to_csv(savefile_path, index=False)
#
#         if 'Unnamed: 0' in census_data.columns:
#             census_data.drop(columns=['Unnamed: 0'], inplace=True)
#
#         return census_data
#
#     @staticmethod
#     def _add_geographical_centroid(dataframe):
#         dataframe_geometry = dataframe.geometry
#         original_crs = 4326  # Save the original CRS
#         target_crs = 3035  # equal planar area projection
#         dataframe_geometry = dataframe_geometry.to_crs(target_crs)  # Reproject GeoDataFrame to the target CRS
#         dataframe_geometry['centroid'] = dataframe.geometry.centroid  # Compute the centroid of the geometries
#         dataframe_geometry.crs = original_crs  # Set the original CRS
#         dataframe['centroid'] = dataframe_geometry['centroid']  # Add the centroid to the GeoDataFrame
#
#         return dataframe
#
#     def get_shapefiles(self, level='tract', savefile=False, override_cache=False, CENSUS_DATA_PATH=CENSUS_DATA_PATH,
#                               variables=None, census_key=None, savefile_path=None):
#         """
#         Get shapefiles for the specified state and level.
#         :param level: one of 'blockgroup', 'tract', 'county', or 'state'
#         :param state_fips: FIPS code for the state, see, e.g., https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt
#         :param savefile: if true, saves file to SHAPEFILE_PATH
#         :param override_cache: if true, ignores local cache and gets data from the internet
#         :return: shapefile dataframe
#         """
#         if level not in ['blockgroup', 'tract', 'county', 'state']:
#             raise ValueError("level must be one of 'blockgroup', 'tract', 'county', or 'state'.")
#
#         if savefile_path is None:
#             savefile_path = os.path.join(SHAPEFILE_PATH, self.fips + '_' + level + '_shapefile.shp')
#
#         if os.path.exists(savefile_path) and override_cache is False:
#             shapefile_df = gpd.read_file(savefile_path, geometry='geometry')
#             return shapefile_df
#
#         logging.info(f'Local data not found. Getting shapefile data for {self.name}...')
#
#         if census_key is None:
#             census_key = census_key
#
#         if level == 'blockgroup':
#             shapefile_url = shapefiles_base_url + 'BG/tl_' + SHAPEFILES_YEAR + '_' + self.fips + '_bg.zip'
#         elif level == 'tract':
#             shapefile_url = shapefiles_base_url + 'TRACT/tl_' + SHAPEFILES_YEAR + '_' + self.fips + '_tract.zip'
#         elif level == 'county':
#             shapefile_url = shapefiles_base_url + 'COUNTY/tl_' + SHAPEFILES_YEAR + '_us_county.zip'
#         else:
#             shapefile_url = shapefiles_base_url + 'STATE/tl_' + SHAPEFILES_YEAR + '_us_state.zip'
#
#         shapefile_df = gpd.read_file(shapefile_url, geometry='geometry')
#
#         shapefile_df = shapefile_df[shapefile_df['STATEFP'] == self.fips]
#         shapefile_df = self._add_geographical_centroid(shapefile_df)
#         shapefile_df['Longitude'] = shapefile_df.centroid.x
#         shapefile_df['Latitude'] = shapefile_df.centroid.y
#         shapefile_df = shapefile_df.drop('centroid', axis=1)
#         shapefile_df['GEOID'] = pd.to_numeric(shapefile_df['GEOID'])
#
#         topo = tp.Topology(shapefile_df, prequantize=False)
#         shapefile_df = topo.toposimplify(0.01).to_gdf()
#
#         if savefile:
#             shapefile_df.to_file(savefile_path)
#
#         return shapefile_df
#
#     def _get_locations_for_census_data(self, census_data, level='tract', census_key=None):
#         """
#         Get the locations for the census data.
#         :param census_data: Census data
#         :param level: The level of the data (tract, blockgroup, etc.)
#         :return: The locations for the census data.
#         """
#         shapefile_df = self.get_shapefiles(level=level, census_key=census_key)
#         census_data = census_data.merge(shapefile_df[['Longitude', 'Latitude', 'GEOID']], left_on='GEOID', right_on='GEOID')
#
#         return census_data
#
#     def plot_poverty_by_tract(self, savefile=False, savefile_path=None, override_cache=False, census_key=None,
#                               dpi=default_dpi):
#         """
#         Plot the poverty rate by census tract. The plot is saved to the PLOTS_PATH. The plot is not shown if the file
#         already exists and override_cache is False. The plot is shown if the file does not exist or override_cache is True.
#         :param savefile:
#         :param savefile_path:
#         :param override_cache:
#         :param census_key:
#         :param dpi:
#         :return:
#         """
#         fig, ax = plt.subplots(
#             subplot_kw={'projection': gcrs.WebMercator()})  # Create a subplot with the Web Mercator projection
#
#         if savefile_path is None:
#             savefile_path = os.path.join(PLOTS_PATH, 'poverty_rate', self.fips + '_poverty_tract.png')
#
#         if os.path.exists(savefile_path) and override_cache is False:
#             plt.imread(savefile_path)
#             return
#
#         shapefile_state_df = self.get_shapefiles(level='state', census_key=census_key)
#         shapefile_state_df = shapefile_state_df.to_crs(epsg=4326)
#
#         shapefile_tract_df = self.get_shapefiles(level='tract', census_key=census_key)
#         census_tract_df = self.get_census_tract_data(census_key=census_key)
#
#         # Merge the census tract data with the shapefile
#         census_tract_df_with_geometry = pd.merge(census_tract_df, shapefile_tract_df[['GEOID', 'geometry']], on='GEOID')
#         census_tract_df_with_geometry = gpd.GeoDataFrame(census_tract_df_with_geometry, geometry='geometry')
#
#         scheme = mc.UserDefined(census_tract_df_with_geometry['below_poverty'], bins=[0, 10, 20, 30, 50, 70, 100])
#
#         if self.name == 'Alaska':
#             bounds = shapefile_state_df.total_bounds
#             bounds[0] = - 180
#             bounds[1] = bounds[1] - 1
#             bounds[2] = - 127
#             bounds[3] = bounds[3] + 0.1
#
#             ax.set_xlim(-180, -127)
#             ax.set_ylim(bounds[1] - 1, bounds[3] + 0.1)
#
#             shapefile_state_df.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=0.6, zorder=2)
#             ctx.add_basemap(ax, crs='EPSG:4326', reset_extent=True, source=ctx.providers.CartoDB.Positron,
#                             attribution_size=5, attribution='CARTO', zoom=6)
#             census_tract_df_with_geometry.dropna(subset=['below_poverty'], inplace=True)
#             census_tract_df_with_geometry.plot(column='below_poverty', cmap='Reds', scheme='UserDefined', legend=True, ax=ax,
#                                                classification_kwds={'bins': [10, 20, 30, 50, 70, 100]}, zorder=1)
#         else:
#             shapefile_state_df.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=0.6, zorder=2)
#             ctx.add_basemap(ax, crs='EPSG:4326', reset_extent=True, source=ctx.providers.CartoDB.Positron,
#                             attribution_size=5, attribution='CARTO', zoom=9)
#             census_tract_df_with_geometry.dropna(subset=['below_poverty'], inplace=True)
#             census_tract_df_with_geometry.plot(column='below_poverty', cmap='Reds', scheme='UserDefined', legend=True, ax=ax,
#                                                classification_kwds={'bins': [10, 20, 30, 50, 70, 100]}, zorder=1)
#
#
#         bins = [0, 10, 20, 30, 50, 70, 100]
#         legend_labels = [f'{bins[i]}-{bins[i + 1]}' for i in range(len(bins) - 1)]
#         legend_labels[0] = f'{bins[0]}-{bins[1]}'
#
#         cmap = cm.get_cmap('Reds', len(bins) - 1)
#         legend_handles = [mpatches.Patch(facecolor=cmap(i), edgecolor='black', linewidth=0.2) for i in
#                           range(len(bins) - 1)]
#
#         ax.legend(legend_handles, legend_labels, title='Poverty rate (%)', fontsize='small', loc='best')
#         ax.axis('off')
#
#         plt.title('Poverty rate \n by census tract')
#         if savefile:
#             plt.savefig(savefile_path, bbox_inches='tight', dpi=dpi)
#
#         return
#
#     # def plot_facilities(self, facilities, ax, plot_webmap=True, plot_points=False, plot_voronoi=True):
#     #     """
#     #     Plot the facilities on a map. The plot is saved to the PLOTS_PATH. The plot is not shown if the file
#     #     already exists and override_cache is False. The plot is shown if the file does not exist or override_cache is True.
#     #     :param facilities:
#     #     :param savefile:
#     #     :param savefile_path:
#     #     :param override_cache:
#     #     :param dpi:
#     #     :return:
#     #     """
#     #
#     #     def filter_facilities(facilities, bounds):
#     #         padding = 1
#     #         return facilities[(facilities.geometry.y > bounds[1] - padding) &
#     #                           (facilities.geometry.y < bounds[3] + padding) &
#     #                           (facilities.geometry.x > bounds[0] - padding) &
#     #                           (facilities.geometry.x < bounds[2] + padding)]
#     #
#     #     if ax is None:
#     #         _, ax = plt.subplots(subplot_kw={'projection': gcrs.WebMercator()})
#     #
#     #     shapefile_state_df = self.get_shapefiles(level='state')
#     #     shapefile_state_df = shapefile_state_df.to_crs(epsg=4326)
#     #     bounds = shapefile_state_df.total_bounds
#     #     if self.name == 'Alaska':
#     #         bounds[2] = -128
#     #
#     #     shapefile_state_df.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=0.6, zorder=1)
#     #     zoom = 6 if self.name == 'Alaska' else 9
#     #     if plot_webmap:
#     #         # ctx.add_basemap(ax, crs='EPSG:4326', reset_extent=True, source=ctx.providers.CartoDB.Positron)
#     #         ctx.add_basemap(ax, crs='EPSG:4326', reset_extent=True, source=ctx.providers.CartoDB.Positron,
#     #                         attribution_size=5, attribution='CARTO', zoom=zoom)
#     #
#     #     if plot_voronoi:
#     #         facilities = filter_facilities(facilities, bounds)
#     #         facilities.set_crs(epsg=4326, inplace=True)
#     #
#     #
#     #         transformed_facilities = facilities.to_crs(epsg=9822)
#     #         transformed_facilities = [(point.x, point.y) for point in transformed_facilities.geometry]
#     #         # Compute Voronoi diagram
#     #         vor = Voronoi(transformed_facilities)
#     #
#     #         # Convert Voronoi vertices back to EPSG:4326
#     #         proj_to_4326 = partial(
#     #             pyproj.transform,
#     #             pyproj.Proj(init='EPSG:9822'),  # Albers Equal Area
#     #             pyproj.Proj(init='EPSG:4326'))  # Longitude/Latitude
#     #
#     #         voronoi_polygons = []
#     #         for region_index in vor.regions:
#     #             if -1 in region_index or len(region_index) == 0:
#     #                 continue
#     #             polygon_vertices = [vor.vertices[i] for i in region_index]
#     #             polygon = Polygon(polygon_vertices)
#     #             voronoi_polygons.append(transform(proj_to_4326, polygon))
#     #
#     #         # Create GeoDataFrame from Voronoi polygons in EPSG:4326
#     #         voronoi_polygons = gpd.GeoDataFrame(geometry=voronoi_polygons, crs='EPSG:4326').buffer(0)
#     #         voronoi_polygons = gpd.clip(voronoi_polygons, shapefile_state_df)
#     #         voronoi_polygons.plot(ax=ax, linewidth=0.4, edgecolor='black', facecolor='none', zorder=2)
#     #
#     #     if plot_points:
#     #         facilities = filter_facilities(facilities, bounds)
#     #         facilities.plot(ax=ax, color='black', marker='x', markersize=2, zorder=3)
#     #
#     #     if self.name == 'Alaska':
#     #         ax.set_xlim(-180, -127)
#     #         ax.set_ylim(bounds[1] - 1, bounds[3] + 0.1)
#     #     ax.axis('off')
#     #
#     #     return ax
#
#     # def get_facility_deserts(self, facility_name='hospital', poverty_threshold=20, distance_threshold=10,
#     #                          savefile=False, savefile_path=None, census_key=None, override_cache=False):
#     #     """
#     #     Get the facility deserts for the state.
#     #     :param facility_name: The name of the facility.
#     #     :param savefile:
#     #     :param savefile_path:
#     #     :param override_cache:
#     #     :param census_key:
#     #     :param dpi:
#     #     :return:
#     #     """
#     #     if not facility_name.endswith('.csv'):
#     #         facility_name = facility_name + '.csv'
#     #     facilities = read_abridged_facilities(facility_name)
#     #
#     #     census_df = self.get_census_blockgroup_data(census_key=census_key)
#     #     column_name = 'Closest_Distance_' + facility_name
#     #
#     #     if column_name not in census_df.columns:
#     #         census_df = closest_distance(census_df, facilities, distance_label=column_name)
#     #         if savefile:
#     #             if savefile_path is None and override_cache is False:
#     #                 savefile_path = os.path.join(CENSUS_DATA_PATH, self.fips + '_census_blockgroup_data.csv')
#     #             census_df.to_csv(savefile_path, index=False)
#     #
#     #     desert_dataframe = census_df[(census_df[column_name] >= distance_threshold * MILES_TO_KM) &
#     #                                  (census_df['below_poverty'] >= poverty_threshold)]
#     #     desert_dataframe = desert_dataframe.dropna(subset=[column_name], axis=0)
#     #     desert_dataframe['geometry'] = gpd.points_from_xy(desert_dataframe['Longitude'], desert_dataframe['Latitude'])
#     #     desert_dataframe = gpd.GeoDataFrame(desert_dataframe, geometry='geometry')
#     #
#     #     return desert_dataframe
#
#     # def plot_facility_deserts(self, facility_name='hospital', poverty_threshold=20, distance_threshold=10,
#     #                           savefile=False, savefile_path=None, override_cache=False,
#     #                           census_key=None, plot_points=False, plot_voronoi=True, plot_webmap=True):
#     #     """
#     #     :param facility_name:
#     #     :param poverty_threshold:
#     #     :param distance_threshold:
#     #     :param savefile:
#     #     :param savefile_path:
#     #     :param override_cache:
#     #     :param census_key:
#     #     :param dpi:
#     #     :return:
#     #     """
#     #     desert_dataframe = self.get_facility_deserts(facility_name=facility_name, poverty_threshold=poverty_threshold,
#     #                                                  distance_threshold=distance_threshold, savefile=savefile,
#     #                                                  override_cache=False, savefile_path=savefile_path,
#     #                                                  census_key=census_key)
#     #     if not facility_name.endswith('.csv'):
#     #         facility_name = facility_name + '.csv'
#     #     facilities = read_abridged_facilities(facility_name)
#     #
#     #     fig, ax = plt.subplots(subplot_kw={'projection': gcrs.WebMercator()})
#     #     ax = self.plot_facilities(facilities, ax, plot_webmap=plot_webmap, plot_points=plot_points, plot_voronoi=plot_voronoi)
#     #
#     #     bounds = self.get_shapefiles(level='state').total_bounds
#     #     if self.name == 'Alaska':
#     #         bounds[2] = -128
#     #         ax.set_xlim(-180, -127)
#     #         ax.set_ylim(bounds[1] - 1, bounds[3] + 0.1)
#     #
#     #     counts = desert_dataframe['racial_majority'].value_counts()
#     #     category_colors = {i: scatter_palette[i - 1] for i in counts.index if counts[i] > 0}
#     #     legend_labels = {i: racial_label_dict[i] for i in counts.index if counts[i] > 0}
#     #
#     #     if len(desert_dataframe) > 0:
#     #         for category in counts.index:
#     #             category_points = desert_dataframe[desert_dataframe['racial_majority'] == category]
#     #             ax.scatter(category_points.geometry.x, category_points.geometry.y, label=legend_labels[category],
#     #                        c=category_colors[category], s=2, zorder=3)
#     #
#     #     ax.legend(title='Blockgroup \n racial majority', fontsize='small', loc='best')
#     #     plt.title('Blockgroups that are \n facility deserts')
#     #
#     #     return ax


