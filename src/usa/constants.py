"""
USA Constants
"""
import os
from shapely.geometry import Point
from src.constants import ROOT_DIR


# === Directories ===
CENSUS_DATA_PATH = os.path.join(ROOT_DIR, 'data', 'usa', 'census')           # Path to the census data
SHAPEFILE_PATH = os.path.join(ROOT_DIR, 'data', 'usa', 'shapefiles')         # Path to the shapefiles
PLOTS_PATH = os.path.join(ROOT_DIR, 'plots', 'usa')                          # Path to the plots
FACILITIES_PATH = os.path.join(ROOT_DIR, 'data', 'usa', 'facilities')        # Path to the facilities data

# === Files ===
USA_SHAPEFILE_WITH_STATES = os.path.join(SHAPEFILE_PATH, 'north_america_political_boundaries', 'Political_Boundaries__Area_.shp')


# === Census ===
CENSUS_KEY = ''
CENSUS_YEAR = '2022'
census_base_url = 'https://api.census.gov/data/' + CENSUS_YEAR + '/pdb/'

total_population_variable = ['Tot_Population_ACS_16_20']
race_ethnicity_variables = ['pct_NH_White_alone_ACS_16_20',
                            'pct_NH_Blk_alone_ACS_16_20',
                            'pct_NH_AIAN_alone_ACS_16_20',
                            'pct_NH_Asian_alone_ACS_16_20',
                            'pct_NH_NHOPI_alone_ACS_16_20',
                            'pct_Hispanic_ACS_16_20']
economic_variables = ['pct_Prs_Blw_Pov_Lev_ACS_16_20']
healthcare_variables = ['pct_No_Health_Ins_ACS_16_20',
                        'pct_One_Health_Ins_ACS_16_20',
                        'pct_TwoPHealthIns_ACS_16_20']
geography_variables = ['State', 'County', 'Tract', 'Block_group']
racial_label_dict = {1: 'White only',
                     2: 'Black only',
                     3: 'AIAN only',
                     4: 'Asian only',
                     5: 'NHOPI only',
                     6: 'Hispanic',
                     7: 'Other'}


# === Shapefiles ===
SHAPEFILES_YEAR = '2022'
shapefiles_base_url = 'https://www2.census.gov/geo/tiger/TIGER' + SHAPEFILES_YEAR + '/'


# === States and Territories ===
territories_dictionary = {
    'Alabama': {'fips': '01', 'abbreviation': 'AL'},
    'Alaska': {'fips': '02', 'abbreviation': 'AK'},
    'Arizona': {'fips': '04', 'abbreviation': 'AZ'},
    'Arkansas': {'fips': '05', 'abbreviation': 'AR'},
    'California': {'fips': '06', 'abbreviation': 'CA'},
    'Colorado': {'fips': '08', 'abbreviation': 'CO'},
    'Connecticut': {'fips': '09', 'abbreviation': 'CT'},
    'Delaware': {'fips': '10', 'abbreviation': 'DE'},
    'Florida': {'fips': '12', 'abbreviation': 'FL'},
    'Georgia': {'fips': '13', 'abbreviation': 'GA'},
    'Hawaii': {'fips': '15', 'abbreviation': 'HI'},
    'Idaho': {'fips': '16', 'abbreviation': 'ID'},
    'Illinois': {'fips': '17', 'abbreviation': 'IL'},
    'Indiana': {'fips': '18', 'abbreviation': 'IN'},
    'Iowa': {'fips': '19', 'abbreviation': 'IA'},
    'Kansas': {'fips': '20', 'abbreviation': 'KS'},
    'Kentucky': {'fips': '21', 'abbreviation': 'KY'},
    'Louisiana': {'fips': '22', 'abbreviation': 'LA'},
    'Maine': {'fips': '23', 'abbreviation': 'ME'},
    'Maryland': {'fips': '24', 'abbreviation': 'MD'},
    'Massachusetts': {'fips': '25', 'abbreviation': 'MA'},
    'Michigan': {'fips': '26', 'abbreviation': 'MI'},
    'Minnesota': {'fips': '27', 'abbreviation': 'MN'},
    'Mississippi': {'fips': '28', 'abbreviation': 'MS'},
    'Missouri': {'fips': '29', 'abbreviation': 'MO'},
    'Montana': {'fips': '30', 'abbreviation': 'MT'},
    'Nebraska': {'fips': '31', 'abbreviation': 'NE'},
    'Nevada': {'fips': '32', 'abbreviation': 'NV'},
    'New Hampshire': {'fips': '33', 'abbreviation': 'NH'},
    'New Jersey': {'fips': '34', 'abbreviation': 'NJ'},
    'New Mexico': {'fips': '35', 'abbreviation': 'NM'},
    'New York': {'fips': '36', 'abbreviation': 'NY'},
    'North Carolina': {'fips': '37', 'abbreviation': 'NC'},
    'North Dakota': {'fips': '38', 'abbreviation': 'ND'},
    'Ohio': {'fips': '39', 'abbreviation': 'OH'},
    'Oklahoma': {'fips': '40', 'abbreviation': 'OK'},
    'Oregon': {'fips': '41', 'abbreviation': 'OR'},
    'Pennsylvania': {'fips': '42', 'abbreviation': 'PA'},
    'Rhode Island': {'fips': '44', 'abbreviation': 'RI'},
    'South Carolina': {'fips': '45', 'abbreviation': 'SC'},
    'South Dakota': {'fips': '46', 'abbreviation': 'SD'},
    'Tennessee': {'fips': '47', 'abbreviation': 'TN'},
    'Texas': {'fips': '48', 'abbreviation': 'TX'},
    'Utah': {'fips': '49', 'abbreviation': 'UT'},
    'Vermont': {'fips': '50', 'abbreviation': 'VT'},
    'Virginia': {'fips': '51', 'abbreviation': 'VA'},
    'Washington': {'fips': '53', 'abbreviation': 'WA'},
    'West Virginia': {'fips': '54', 'abbreviation': 'WV'},
    'Wisconsin': {'fips': '55', 'abbreviation': 'WI'},
    'Wyoming': {'fips': '56', 'abbreviation': 'WY'},
    'American Samoa': {'fips': '60', 'abbreviation': 'AS'},
    'Guam': {'fips': '66', 'abbreviation': 'GU'},
    'Northern Mariana Islands': {'fips': '69', 'abbreviation': 'MP'},
    'Puerto Rico': {'fips': '72', 'abbreviation': 'PR'},
    'Virgin Islands': {'fips': '78', 'abbreviation': 'VI'}
}
territories = list(territories_dictionary.keys())
state_names = list(set(territories_dictionary.keys()).difference({'American Samoa', 'Guam', 'Puerto Rico',
                                                                  'Northern Mariana Islands', 'Virgin Islands'}))
state_names.sort()


# === Geographic ===
waterbody_points = [Point(-130, 30),    # Pacific Ocean
                    Point(-175, 68),    # Bering Sea, around Russia
                    Point(-130, 80),    # Arctic Ocean, around Canada
                    Point(-81, 31),     # Atlantic Ocean
                    Point(-87, 43),     # Lake Michigan and Huron, USA side
                    Point(-81, 45),     # Lake Huron, Canada side
                    Point(-81, 42),     # Lake Erie, USA side
                    Point(-81, 42.5),   # Lake Erie, Canada side
                    Point(-78, 43.5),   # Lake Ontario, USA side
                    Point(-78, 43.7),   # Lake Ontario, Canada side
                    Point(-87, 47),     # Lake Superior, USA side
                    Point(-87, 48),     # Lake Superior, Canada side
                    ]
