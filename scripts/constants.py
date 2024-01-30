import bidict

# Constants
latitude_to_km = 111.32
longitude_to_km = 92.18
aspect_ratio = latitude_to_km/longitude_to_km
miles_to_km = 1.602

color_cycle = ["#0072B2", "#D53E00", "#249e24", "#924900", "#b66dff", "#999999", "#F0E442", "#920000", "#009292"]
# color:       blue,      red,      green,     brown,     purple,    gray,      yellow,    orange,    teal

boundary_data_path = './data/usa_state_boundaries.json'


state_data = {
    "Alabama": {"Postal Abbr.": "AL", "FIPS Code": "01"},
    "Alaska": {"Postal Abbr.": "AK", "FIPS Code": "02"},
    "Arizona": {"Postal Abbr.": "AZ", "FIPS Code": "04"},
    "Arkansas": {"Postal Abbr.": "AR", "FIPS Code": "05"},
    "California": {"Postal Abbr.": "CA", "FIPS Code": "06"},
    "Colorado": {"Postal Abbr.": "CO", "FIPS Code": "08"},
    "Connecticut": {"Postal Abbr.": "CT", "FIPS Code": "09"},
    "Delaware": {"Postal Abbr.": "DE", "FIPS Code": "10"},
    "District of Columbia": {"Postal Abbr.": "DC", "FIPS Code": "11"},
    "Florida": {"Postal Abbr.": "FL", "FIPS Code": "12"},
    "Georgia": {"Postal Abbr.": "GA", "FIPS Code": "13"},
    "Hawaii": {"Postal Abbr.": "HI", "FIPS Code": "15"},
    "Idaho": {"Postal Abbr.": "ID", "FIPS Code": "16"},
    "Illinois": {"Postal Abbr.": "IL", "FIPS Code": "17"},
    "Indiana": {"Postal Abbr.": "IN", "FIPS Code": "18"},
    "Iowa": {"Postal Abbr.": "IA", "FIPS Code": "19"},
    "Kansas": {"Postal Abbr.": "KS", "FIPS Code": "20"},
    "Kentucky": {"Postal Abbr.": "KY", "FIPS Code": "21"},
    "Louisiana": {"Postal Abbr.": "LA", "FIPS Code": "22"},
    "Maine": {"Postal Abbr.": "ME", "FIPS Code": "23"},
    "Maryland": {"Postal Abbr.": "MD", "FIPS Code": "24"},
    "Massachusetts": {"Postal Abbr.": "MA", "FIPS Code": "25"},
    "Michigan": {"Postal Abbr.": "MI", "FIPS Code": "26"},
    "Minnesota": {"Postal Abbr.": "MN", "FIPS Code": "27"},
    "Mississippi": {"Postal Abbr.": "MS", "FIPS Code": "28"},
    "Missouri": {"Postal Abbr.": "MO", "FIPS Code": "29"},
    "Montana": {"Postal Abbr.": "MT", "FIPS Code": "30"},
    "Nebraska": {"Postal Abbr.": "NE", "FIPS Code": "31"},
    "Nevada": {"Postal Abbr.": "NV", "FIPS Code": "32"},
    "New Hampshire": {"Postal Abbr.": "NH", "FIPS Code": "33"},
    "New Jersey": {"Postal Abbr.": "NJ", "FIPS Code": "34"},
    "New Mexico": {"Postal Abbr.": "NM", "FIPS Code": "35"},
    "New York": {"Postal Abbr.": "NY", "FIPS Code": "36"},
    "North Carolina": {"Postal Abbr.": "NC", "FIPS Code": "37"},
    "North Dakota": {"Postal Abbr.": "ND", "FIPS Code": "38"},
    "Ohio": {"Postal Abbr.": "OH", "FIPS Code": "39"},
    "Oklahoma": {"Postal Abbr.": "OK", "FIPS Code": "40"},
    "Oregon": {"Postal Abbr.": "OR", "FIPS Code": "41"},
    "Pennsylvania": {"Postal Abbr.": "PA", "FIPS Code": "42"},
    "Puerto Rico": {"Postal Abbr.": "PR", "FIPS Code": "72"},
    "Rhode Island": {"Postal Abbr.": "RI", "FIPS Code": "44"},
    "South Carolina": {"Postal Abbr.": "SC", "FIPS Code": "45"},
    "South Dakota": {"Postal Abbr.": "SD", "FIPS Code": "46"},
    "Tennessee": {"Postal Abbr.": "TN", "FIPS Code": "47"},
    "Texas": {"Postal Abbr.": "TX", "FIPS Code": "48"},
    "Utah": {"Postal Abbr.": "UT", "FIPS Code": "49"},
    "Vermont": {"Postal Abbr.": "VT", "FIPS Code": "50"},
    "Virginia": {"Postal Abbr.": "VA", "FIPS Code": "51"},
    "Virgin Islands": {"Postal Abbr.": "VI", "FIPS Code": "78"},
    "Washington": {"Postal Abbr.": "WA", "FIPS Code": "53"},
    "West Virginia": {"Postal Abbr.": "WV", "FIPS Code": "54"},
    "Wisconsin": {"Postal Abbr.": "WI", "FIPS Code": "55"},
    "Wyoming": {"Postal Abbr.": "WY", "FIPS Code": "56"}
}


def get_state_abbreviation_and_fips_by_name(state_name):
    """Get state abbreviation and FIPS code from state name."""
    if state_name in state_data:
        data = state_data[state_name]
        return data["Postal Abbr."], data["FIPS Code"]
    else:
        return None, None


def get_state_name_and_abbreviation_by_fips(fips_code):
    """Get state name and abbreviation from state FIPS code."""
    for state_name, data in state_data.items():
        if data["FIPS Code"] == fips_code:
            return state_name
    return None


races = ['White', 'Black', 'Hispanic', 'Asian', 'AIAN', 'NHPI', 'Other']


# paths
census_county_url = 'https://www2.census.gov/geo/tiger/TIGER2020/COUNTY/tl_2020_us_county.zip'

