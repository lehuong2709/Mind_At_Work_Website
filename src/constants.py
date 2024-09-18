"""
This module contains constants that are used throughout the package. This includes colors, units, and other
parameters that are used in the package.
This module also contains the definition of the coordinate reference systems (CRS) that are used to define the map
projection (see the `Projections' section below).
The module also contains definitions of the directories that are used in the package.
The module also contains the definition of the countries and regions that are used in the package; currently only USA
is defined.
"""
import os
from src.regions import Region, Country

# === Units ===
MILES_TO_KM = 1.60934


# === Colors ===
WATERBODY_COLOR = '#a4b8b7'                 # teal, for sea, ocean, lake, river, etc.
LAND_COLOR_PRIMARY = '#f9f3e1'              # beige, for land being plotted
LAND_COLOR_SECONDARY = '#fbfcf9'            # soft white, for other landmass
BOUNDARY_COLOR = '#818181'                  # gray, for boundaries

# A color cycle for color-blind friendly plots
scatter_palette = [
    '#007fee',          # Blue
    '#21d565',          # Green
    '#ffe00a',          # Yellow
    '#ff7700',          # Orange
    '#8bff08',          # Lime
    '#9918fe',          # Purple
    '#ff0004',          # Red
    '#179c49',          # Dark Green
    '#00318f',          # Dark Blue
    '#ff1f70',          # Pink
    '#af7b00',          # Brown
    '#ff517c',          # Light Pink
    '#d36969',          # Light Red
    '#18fe90'           # Light Green
]


# === Plotting ===

default_dpi = 400


# === Projections ===
# coordinate reference system (CRS) that is used to define the map projection and the geodetic datum, by the standard
# EPSG code. The EPSG code is a standardized code that is used to identify the type of map projection and the geodetic
# This integer number (alterantely represented as the decimal representation), which is assigned to a specific map
# projection on the plane, is called the EPSG code. It forms a coordinate
# reference system (CRS) that is used to define the map projection and the geodetic datum. The EPSG code is a
# standardized code that is used to identify the type of map projection and the geodetic datum used by a set of
# geographic data.

# The EPSG code for the Web Mercator projection is 3857, which is close to the Mercator projection and is dominant in
# web mapping.
projection_web_mercator = 'EPSG:3857'

# The EPSG code for the North American Datum 1983 (NAD83) is 4269, which is a standard datum for the United States and
# Canada. It is the reference frame for the Global Positioning System (GPS) and is used for mapping and geodetic
# control throughout North America.
projection_north_america = 'EPSG:4269'

# The EPSG code for the World Geodetic System 1984 (WGS84) is 4326, which is a standard datum for the Global Positioning
# System (GPS) and is used for mapping and geodetic control throughout the world.
projection_wgs84 = 'EPSG:4326'

# The EPSG code for the Universal Transverse Mercator (UTM) projection in North America zone is 9712, which
# approximately preserves distances within each zone.
projection_equidistant = 'EPSG:9712'


# === Directories ===
ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)


USA = Country(name='United States of America',
              common_names=['USA', 'US', 'United States', 'America'],
              shapefile=None,
              default_crs=projection_north_america)

country_names_to_objects_dictionary = {
    'USA': USA
}

# === Default thresholds for facility deserts ===
DEFAULT_POVERTY_THRESHOLD = 25
DEFAULT_URBAN_DISTANCE_THRESHOLD = 1.0
DEFAULT_RURAL_DISTANCE_THRESHOLD = 5.0
