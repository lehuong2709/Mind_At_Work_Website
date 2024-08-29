from src.constants import *
from src.usa.constants import *
import os
import pandas as pd
from src.regions import Province
import requests
import streamlit as st


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

    def __reduce__(self):
        return USAState, (self.name, self.fips, self.abbreviation)

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
        else:
            raise ValueError("level must be one of 'blockgroup', 'tract', or 'county'.")

        if os.path.exists(savefile_path):
            census_data = pd.read_csv(savefile_path)
            if 'Unnamed: 0' in census_data.columns:
                census_data.drop(columns=['Unnamed: 0'], inplace=True)
        else:
            raise ValueError("No data found for the specified state and level.")

        return census_data

    @st.cache_data
    def get_census_data(self, level='blockgroup', override_cache=False, census_key=None):
        """
        Get data for US Census data for the state from the local cache or the internet. If the data is retrieved from the
        internet, it can be saved to the local cache.
        :param level: one of 'blockgroup' or 'tract'
        :param override_cache: whether to ignore the local cache and get the data from the internet
        :param save_to_file: whether to save the data to the local cache when retrieved from the internet
        :param census_key: census API key to use when getting data from the internet
        :return:
        """
        if override_cache is False:
            census_data = self._get_census_data_from_cache(level=level)
        else:
            raise NotImplementedError('Getting census data from API is not implemented yet.')

        return census_data