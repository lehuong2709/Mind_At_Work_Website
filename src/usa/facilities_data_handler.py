"""
Title: Facilities Data Handler
Author: Jai Moondra, @jaimoondra, jaimoondra.github.io
Date: 2024-02-15
Description: This file contains functions to handle facilities data for the USA.
"""

import csv
import geopandas as gpd
import geoplot as gplt
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


facility_types = ['medical', 'educational', 'food_related', 'financial', 'logistics', 'child_care', 'other']

facilities_files = [
    'Child_Care_Centers.csv',
    'DHL_Facilities.csv',
    'Dialysis_Centers.csv',
    'FDIC_Insured_Banks.csv',
    'FedEx_Facilities.csv',
    'Hospitals.csv',
    'Nursing_Homes.csv',
    'Pharmacies.csv',
    'Private_Schools.csv',
    'Public_Refrigerated_Warehouses.csv',
    'UPS_Facilities.csv',
    'Urgent_Care_Facilities.csv'
]


class FacilitiesDataHandler:
    def __init__(self, name, full_data_file_path=None, abridged_data_file_path=None, type=None):
        self.name = name
        self.full_data_file_path = full_data_file_path
        self.abridged_data_file_path = abridged_data_file_path
        self.total_number = None
        self.voronoi_SHAPEFILE_PATH = None
        self.type = type

    def convert_to_abridged_facilities(self, full_data_file_path=None, state_column_name='STATE',
                                       state_name_type='abbreviation', columns_to_retain=None,
                                       longitudes_column_name='X', latitudes_column_name='Y',
                                       topk=False, k=3, topk_list=None):
        """
        This function converts the full facilities data to abridged facilities data. The abridged facilities data
        contains only the geometric data (latitude and longitude) and the state abbreviation.
        :param full_data_file_path: path to the full facilities data file
        :param state_column_name: the name of the column in full data that contains the state name
        :param state_name_type: how the state name is represented in the full data. Can be 'abbreviation' (e.g., 'GA'),
        or 'name' (e.g. 'Georgia') or 'fips' (e.g. '13')
        :return: abridged facilities data, stored in file self.abridged_data_file_path
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
        This function reads the facilities data from the file and returns a GeoDataFrame.
        :param full_data_file_path: name for the facilities file, one of the facilities_files
        :param state_column_name: name of the column in the file that contains the state name
        :param longitudes_column_name: name of the column in the file that contains the longitudes
        :param latitudes_column_name: name of the column in the file that contains the latitudes
        :return: facilities dataframe
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


Pharmacies = FacilitiesDataHandler(name='Pharmacies', type='medical',
             abridged_data_file_path=os.path.join(FACILITIES_PATH, 'abridged_Pharmacies_all.csv'))
CVS = FacilitiesDataHandler(name='Pharmacies_cvs', type='medical',
             abridged_data_file_path=os.path.join(FACILITIES_PATH, 'abridged_Pharmacies_cvs.csv'))
Walgreens = FacilitiesDataHandler(name='Pharmacies_walgreens', type='medical',
             abridged_data_file_path=os.path.join(FACILITIES_PATH, 'abridged_Pharmacies_walgreens.csv'))
Walmart = FacilitiesDataHandler(name='Pharmacies_walmart', type='medical',
             abridged_data_file_path=os.path.join(FACILITIES_PATH, 'abridged_Pharmacies_walmart.csv'))
PharmaciesTop3 = FacilitiesDataHandler(name='Top3Pharmacies', type='medical',
             abridged_data_file_path=os.path.join(FACILITIES_PATH, 'abridged_Pharmacies_top3.csv'))

UrgentCare = FacilitiesDataHandler(name='UrgentCare', type='medical',
             abridged_data_file_path=os.path.join(FACILITIES_PATH, 'abridged_Urgent_Care_Facilities.csv'))

Hospitals = FacilitiesDataHandler(name='Hospitals', type='medical',
             abridged_data_file_path=os.path.join(FACILITIES_PATH, 'abridged_Hospitals.csv'))

DialysisCenters = FacilitiesDataHandler(name='DialysisCenters', type='medical',
             abridged_data_file_path=os.path.join(FACILITIES_PATH, 'abridged_Dialysis_Centers.csv'))

NursingHomes = FacilitiesDataHandler(name='NursingHomes', type='medical',
                abridged_data_file_path=os.path.join(FACILITIES_PATH, 'abridged_Nursing_Homes.csv'))
