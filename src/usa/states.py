from src.constants import *
from src.usa.constants import *
import os
import pandas as pd
from src.regions import Province
import requests


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
            savefile_path = os.path.join(CENSUS_DATA_PATH, self.fips, 'census_blockgroup_data.csv')
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


        return census_data
