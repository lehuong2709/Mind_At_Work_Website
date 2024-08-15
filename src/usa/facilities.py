import geopandas as gpd
import os
import pandas as pd
from shapely import wkt
from shapely.geometry import Point
from src.constants import projection_wgs84
import streamlit as st


facility_types = ['medical', 'educational', 'food_related', 'financial', 'logistics', 'child_care', 'other']


class Facilities:
    def __init__(self, name, display_name=None, type=None, description=None, color='black'):
        self.name = name
        self.type = type
        if display_name is None:
            self.display_name = name.replace('_', ' ').capitalize()
        else:
            self.display_name = display_name
        self.color = color
        self.description = description
        self.distance_label = 'closest_distance_' + self.name
        self.existing_facilities_filepath = os.path.join('data', 'usa', 'existing_facilities', self.name)
        self.new_facilities_filepath = os.path.join('data', 'usa', 'new_facilities', self.name)
        self.voronoi_folder = os.path.join('data', 'usa', 'existing_facilities', self.name, 'voronoi_state_shapefiles')

    def __reduce__(self):
        return Facilities, (self.name, self.type, self.display_name, self.color, self.description, self.distance_label,
                            self.existing_facilities_filepath, self.new_facilities_filepath, self.voronoi_folder)

    def get_message(self):
        message = ("""
            Let's define a **""" + self.type + """ desert** as a US census
            [blockgroup](https://en.wikipedia.org/wiki/Census_block_group) that is more than $n$ miles away from """ +
            self.description + """ and with over $p$% of the population living below the poverty line. Choose $n$ 
            and $p$ from the sidebar."""
        )

        return message

    @st.cache_data
    def get_existing_locations(self):
        filepath = os.path.join(self.existing_facilities_filepath, 'abridged_facilities.csv')
        try:
            facilities = pd.read_csv(filepath)
        except FileNotFoundError:
            raise FileNotFoundError('The file ' + filepath + ' does not exist.')

        facilities['geometry'] = facilities['geometry'].apply(wkt.loads)
        facilities = gpd.GeoDataFrame(facilities, geometry='geometry', crs=projection_wgs84)
        facilities.dropna(subset=['geometry'], inplace=True)
        facilities.drop_duplicates(inplace=True)
        facilities['Longitude'] = facilities['geometry'].x
        facilities['Latitude'] = facilities['geometry'].y

        return facilities

    @st.cache_data
    def get_new_locations(self, state_fips, p='combined'):
        filepath = os.path.join(self.new_facilities_filepath, state_fips, 'new_facilities_' + str(p) + '.csv')
        try:
            new_facilities = pd.read_csv(filepath, index_col=0)
        except FileNotFoundError:
            raise FileNotFoundError('The file ' + filepath + ' does not exist.')

        new_facilities['geometry'] = new_facilities.apply(lambda row: Point(row['Longitude'], row['Latitude']), axis=1)
        new_facilities = gpd.GeoDataFrame(new_facilities, geometry='geometry', crs=projection_wgs84)

        return new_facilities

    @st.cache_data
    def read_voronoi_cells(self, state_fips):
        voronoi_file_path = os.path.join(self.voronoi_folder, state_fips + '_voronoi.shp')
        try:
            voronoi_df = gpd.read_file(voronoi_file_path, index=False)
        except FileNotFoundError:
            raise FileNotFoundError('The file ' + voronoi_file_path + ' does not exist.')
        return voronoi_df


Pharmacies = Facilities(name='pharmacies', type='medical', display_name='Pharmacies', description='a pharmacy')
CVS = Facilities(name='cvs_pharmacies', type='medical', display_name='CVS pharmacies', color='#8b0000')
Walgreens = Facilities(name='walgreens_pharmacies', type='medical', color='#006400')
Walmart = Facilities(name='walmart_pharmacies', type='medical', color='#00008b')
PharmaciesTop3 = Facilities(name='top_3_pharmacy_chains', type='medical', display_name='Pharmacy chains',
                                       description='a CVS/Walgreeens/Walmart pharmacy')
UrgentCare = Facilities(name='urgentcare_centers', type='medical', description='an urgent care center')
Hospitals = Facilities(name='hospitals', type='medical', description='a hospital')
DialysisCenters = Facilities(name='dialysis_centers', type='medical')
NursingHomes = Facilities(name='nursing_homes', type='medical', description='a nursing home')
ChildCare = Facilities(name='childcare_centers', type='facility', description='a childcare center')
FedEx = Facilities(name='fedex_facilities', type='logistics', display_name='FedEx', color='#cc4700')
UPS = Facilities(name='ups_facilities', type='logistics', display_name='UPS', color='#521801')
DHL = Facilities(name='dhl_facilities', type='logistics', display_name='DHL', color='#8b1e2b')
PrivateSchools = Facilities(name='private_schools', type='education', description='a private school')
PublicRefrigeratedWarehouses = Facilities(name='public_refrigerated_warehouses', type='food')
FDICInsuredBanks = Facilities(name='fdic_insured_banks', type='banking', display_name='Banks',
                                         description="""an [FDIC insured bank](https://en.wikipedia.org/wiki/Federal_Deposit_Insurance_Corporation)""")
