"""
Title: Facilities Data Handler
Author: Jai Moondra, @jaimoondra, jaimoondra.github.io
Date: 2024-02-15
Description: This file contains functions to handle existing_facilities data for the USA.
"""

import csv
import geopandas as gpd
import logging
import math
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from shapely.geometry import Point
from shapely import wkt
from src.usa.constants import *
from src.constants import *
import streamlit as st


facility_types = ['medical', 'educational', 'food_related', 'financial', 'logistics', 'child_care', 'other']

# facilities_files = [
#     'Child_Care_Centers.csv',
#     'DHL_Facilities.csv',
#     'Dialysis_Centers.csv',
#     'FDIC_Insured_Banks.csv',
#     'FedEx_Facilities.csv',
#     'Hospitals.csv',
#     'Nursing_Homes.csv',
#     'Pharmacies.csv',
#     'Private_Schools.csv',
#     'Public_Refrigerated_Warehouses.csv',
#     'UPS_Facilities.csv',
#     'Urgent_Care_Facilities.csv'
# ]


class FacilitiesDataHandler:
    def __init__(self, name, full_data_file_path=None, abridged_data_file_path=None, type=None, display_name=None,
                 descrption=None, color=None):
        self.name = name
        self.full_data_file_path = full_data_file_path
        if abridged_data_file_path is None:
            self.abridged_data_file_path = self._get_abridged_data_file_path()
        else:
            self.abridged_data_file_path = abridged_data_file_path
        self.total_number = None
        self.type = type
        if display_name is None:
            self.display_name = self._get_display_name(name)
        else:
            self.display_name = display_name
        if color is None:
            self.color = 'black'
        else:
            self.color = color
        self.distance_label = 'closest_distance_' + self.name
        self.description = descrption
        self.voronoi_folder = os.path.join('data', 'usa', 'existing_facilities', self.name, 'voronoi_state_shapefiles')

    def get_message(self):
        message = (
                """Let's define a **""" + self.type + """ desert** as a US census
            [blockgroup](https://en.wikipedia.org/wiki/Census_block_group) that is more than $n$ miles away from """ +
                self.description + """ and with over $p$% of the population living
            below the poverty line. Choose $n$ and $p$ from the sidebar."""
        )

        return message

    @staticmethod
    def _get_display_name(name):
        display_name = name.replace('_', ' ').capitalize()
        return display_name

    def _get_abridged_data_file_path(self):
        return os.path.join('data', 'usa', 'existing_facilities', 'abridged_' + self.name + '.csv')

    def convert_to_abridged_facilities(self, full_data_file_path=None, state_column_name='STATE',
                                       state_name_type='abbreviation', columns_to_retain=None,
                                       longitudes_column_name='X', latitudes_column_name='Y',
                                       topk=False, k=3, topk_list=None):
        """
        This function converts the full existing_facilities data to abridged existing_facilities data. The abridged existing_facilities data
        contains only the geometric data (latitude and longitude) and the state abbreviation.
        :param full_data_file_path: path to the full existing_facilities data file
        :param state_column_name: the name of the column in full data that contains the state name
        :param state_name_type: how the state name is represented in the full data. Can be 'abbreviation' (e.g., 'GA'),
        or 'name' (e.g. 'Georgia') or 'fips' (e.g. '13')
        :return: abridged existing_facilities data, stored in file self.abridged_data_file_path
        """
        if full_data_file_path is None and self.full_data_file_path is None:
            raise ValueError('The full data file path is not provided.')

        if full_data_file_path is not None and self.full_data_file_path is not None:
            if full_data_file_path != self.full_data_file_path:
                raise ValueError('The full data file path has already been provided, and is: ' + self.full_data_file_path
                                 + 'If you want to override this, please change class attribute full_data_file_path')

        if full_data_file_path is not None:
            self.full_data_file_path = full_data_file_path

        facilities = self.read_full_data(state_column_name=state_column_name,
                                         longitudes_column_name=longitudes_column_name, latitudes_column_name=latitudes_column_name)

        if columns_to_retain is None:
            columns_to_retain = [state_column_name, 'Latitude', 'Longitude']
        else:
            columns_to_retain = columns_to_retain + [state_column_name, 'Latitude', 'Longitude']

        if topk:
            topk_list = [s.lower() for s in topk_list]

            # Function to identify the matching string(s) from L
            def find_matching_string(row):
                row_lower = row.astype(str).str.lower()
                matching_strings = [s for s in topk_list if row_lower.astype(str).str.contains(s).any()]
                return ', '.join(matching_strings) if matching_strings else None

            # Apply the function to each row and create the 'NAME' column
            facilities['NAME'] = facilities.apply(find_matching_string, axis=1)
            facilities = facilities[facilities['NAME'].notna()]

            columns_to_retain = columns_to_retain + ['NAME']
            facilities = facilities[columns_to_retain]
        else:
            facilities = facilities[columns_to_retain]

        facilities.rename(columns={state_column_name: 'STATE'}, inplace=True)
        facilities.dropna(subset=['Latitude', 'Longitude'], how='any', axis=0, inplace=True)
        facilities = gpd.GeoDataFrame(facilities, geometry=gpd.points_from_xy(facilities.Longitude, facilities.Latitude),
                                      crs=projection_wgs84)
        facilities.drop(columns=['Latitude', 'Longitude'], inplace=True)

        self.abridged_data_file_path = os.path.join(FACILITIES_PATH, 'abridged_' + self.name + '.csv')
        facilities.to_csv(self.abridged_data_file_path)

        return facilities

    def read_full_data(self, full_data_file_path=None, state_column_name='STATE', state_column_type='abbreviation',
                       longitudes_column_name='X', latitudes_column_name='Y'):
        """
        This function reads the existing_facilities data from the file and returns a GeoDataFrame.
        :param full_data_file_path: name for the existing_facilities file, one of the facilities_files
        :param state_column_name: name of the column in the file that contains the state name
        :param longitudes_column_name: name of the column in the file that contains the longitudes
        :param latitudes_column_name: name of the column in the file that contains the latitudes
        :return: existing_facilities dataframe
        """
        if full_data_file_path is None and self.full_data_file_path is None:
            raise ValueError('The full data file path is not provided.')

        if full_data_file_path is not None and self.full_data_file_path is not None:
            if full_data_file_path != self.full_data_file_path:
                raise ValueError('The full data file path has already been provided, and is: ' + self.full_data_file_path
                                 + 'If you want to override this, please change class attribute full_data_file_path')

        if full_data_file_path is not None:
            self.full_data_file_path = full_data_file_path

        try:
            facilities = pd.read_csv(self.full_data_file_path)
        except FileNotFoundError or ValueError:
            raise FileNotFoundError('The file ' + self.full_data_file_path + ' does not exist.')

        if not (longitudes_column_name in facilities.columns) or not (latitudes_column_name in facilities.columns):
            raise ValueError('The file does not contain columns named ' + longitudes_column_name + ' and ' +
                             latitudes_column_name)

        if full_data_file_path == 'FDIC_Insured_Banks.csv':
            longitudes_column_name = 'x'
            latitudes_column_name = 'y'

        facilities.rename(columns={longitudes_column_name: 'X', latitudes_column_name: 'Y'}, inplace=True)
        facilities.rename(columns={state_column_name: 'STATE'}, inplace=True)

        facilities.replace('', pd.NA, inplace=True)
        facilities.dropna(subset=[longitudes_column_name, latitudes_column_name], how='any', axis=0, inplace=True)

        facilities['Longitude'] = facilities[longitudes_column_name].astype(float)
        facilities['Latitude'] = facilities[latitudes_column_name].astype(float)

        facilities['geometry'] = [Point(long, lat) for long, lat in zip(facilities['Longitude'], facilities['Latitude'])]

        geometry = [Point(x, y) for x, y in zip(facilities['X'], facilities['Y'])]
        facilities = gpd.GeoDataFrame(facilities, geometry=geometry, crs=projection_wgs84)

        return facilities

    def read_abridged_facilities(self):
        """
        :return:
        """
        if self.abridged_data_file_path is None:
            raise ValueError('The abridged data file path does not exist. Try running convert_to_abridged_facilities')
        try:
            facilities = pd.read_csv(self.abridged_data_file_path, index_col=0)
        except FileNotFoundError:
            raise FileNotFoundError('The file ' + self.abridged_data_file_path + ' does not exist.')

        facilities['geometry'] = facilities['geometry'].apply(wkt.loads)
        facilities = gpd.GeoDataFrame(facilities, geometry='geometry', crs=projection_wgs84)
        facilities.dropna(subset=['geometry'], inplace=True)
        facilities.drop_duplicates(inplace=True)

        return facilities


Pharmacies = FacilitiesDataHandler(name='pharmacies', type='medical', display_name='Pharmacies', descrption='a pharmacy')
CVS = FacilitiesDataHandler(name='cvs_pharmacies', type='medical', display_name='CVS pharmacies', color='#8b0000')
Walgreens = FacilitiesDataHandler(name='walgreens_pharmacies', type='medical', color='#006400')
Walmart = FacilitiesDataHandler(name='walmart_pharmacies', type='medical', color='#00008b')
PharmaciesTop3 = FacilitiesDataHandler(name='top_3_pharmacy_chains', type='medical', display_name='Pharmacy chains',
                                       descrption='a CVS/Walgreeens/Walmart pharmacy')
UrgentCare = FacilitiesDataHandler(name='urgentcare_centers', type='medical', descrption='an urgent care center')
Hospitals = FacilitiesDataHandler(name='hospitals', type='medical', descrption='a hospital')
DialysisCenters = FacilitiesDataHandler(name='dialysis_centers', type='medical')
NursingHomes = FacilitiesDataHandler(name='nursing_homes', type='medical', descrption='a nursing home')
ChildCare = FacilitiesDataHandler(name='childcare_centers', type='facility', descrption='a childcare center')
FedEx = FacilitiesDataHandler(name='fedex_facilities', type='logistics', display_name='FedEx', color='#cc4700')
UPS = FacilitiesDataHandler(name='ups_facilities', type='logistics', display_name='UPS', color='#521801')
DHL = FacilitiesDataHandler(name='dhl_facilities', type='logistics', display_name='DHL', color='#8b1e2b')
PrivateSchools = FacilitiesDataHandler(name='private_schools', type='education', descrption='a private school')
PublicRefrigeratedWarehouses = FacilitiesDataHandler(name='public_refrigerated_warehouses', type='food')
FDICInsuredBanks = FacilitiesDataHandler(name='fdic_insured_banks', type='banking', display_name='Banks',
                                         descrption="""an [FDIC insured bank](https://en.wikipedia.org/wiki/Federal_Deposit_Insurance_Corporation)""")
