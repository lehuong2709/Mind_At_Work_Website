import geopandas as gpd
import os.path
from typing import List, Set, Union


class Region:
    """
    Represents a region with its name, official names, and common names. Since we are largely interested in the geographical and administrative data of a region, also contains a variable for 'shapefile' relating to that country.
    """

    def __init__(self, name: str, shapefile: str = None, default_crs: str = None):
        """
        Creates a new instance of the Region class.

        Args:
            name (str): The name of the region.
            shapefile (str): The shapefile of the region.
            default_crs (str): The default coordinate reference system of the shapefile.

        Returns:
            Region: A new instance of the Region class.
        """

        self._name = name
        self.shapefile = shapefile
        self.default_crs = default_crs

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        raise AttributeError("Cannot modify 'name' attribute directly")

    def read_shapefile_to_geodataframe(self, crs=None):
        """
        Reads the shapefile of the region into a GeoDataFrame.

        Returns:
            GeoDataFrame: A GeoDataFrame of the region.
        """
        if self.shapefile is None:
            raise ValueError('Shapefile has not been added yet')

        if os.path.exists(self.shapefile) is False:
            raise FileNotFoundError('Shapefile does not exist')

        try:
            shapefile_df = gpd.read_file(filename=self.shapefile, crs=self.default_crs)
        except ValueError:
            raise ValueError('Invalid shapefile')

        if crs is not None:
            try:
                shapefile_df = shapefile_df.to_crs(crs)
            except ValueError:
                raise ValueError(f'Invalid CRS: {crs}')

        return shapefile_df


class Country(Region):
    """
    Represents a country with its name, official names, and common names.
    """

    def __init__(self, name: str, official_names: Union[List[str], Set[str]] = None,
                 common_names: Union[List[str], Set[str]] = None, shapefile: str = None, default_crs: str = None):
        """
        Creates a new instance of the Country class.

        Args:
            name (str): The name of the country.
            official_names (list or set, optional): List of official names of the country. Defaults to None.
            common_names (list or set, optional): List of common names of the country. Defaults to None.
            shapefile (str): The shapefile of the country. Defaults to None.
            default_crs (str): The default coordinate reference system of the shapefile. Defaults to None.

        Returns:
            Country: A new instance of the Country class.
        """
        super().__init__(name=name, shapefile=shapefile, default_crs=default_crs)

        if official_names is None:
            official_names = set()
        try:
            official_names = set(official_names)
        except TypeError:
            raise ValueError('official_names for a Country must be a list or set of strings')

        if common_names is None:
            common_names = set()
        try:
            common_names = set(common_names)
        except TypeError:
            raise ValueError('common_names for a Country must be a list or set of strings')

        if name not in common_names:
            common_names.add(name)

    def __repr__(self):
        """
        Returns a string representation of the Country object.

        Returns:
            str: String representation of the Country object.
        """
        return f"Country ({self._name})"

    def __str__(self):
        """
        Returns a string representation of the Country object.

        Returns:
            str: String representation of the Country object.
        """
        return self._name

    def __eq__(self, other):
        """
        Checks if two Country objects are equal.

        Args:
            other (Country): Another Country object to compare with.

        Returns:
            bool: True if the two objects are equal, False otherwise.
        """
        return False


USA = Country(name='USA',
              official_names=['United States of America', 'United States', 'America'],
              common_names=['USA', 'US'],
              shapefile=None,
              default_crs=None)
# country_names_to_objects_dictionary = {
#     'USA': USA
# }
country_names_to_objects_dictionary = [('USA', USA)]


class Province:
    """
    Represents a province with its name and the country it belongs to.
    """
    def __init__(self, name, country: str, shapefile=None, default_crs=None):

        """
        Initializes a new Province object.

        Args:
            name (str): The name of the province.
            country (Country): The country that the province belongs to.
        """
        self._name = name

        # if country not in [item[0] for item in country_names_to_objects_dictionary]:
        #     raise ValueError(
        #         f'Country {country} is not currently supported. Please add it to the country_names_to_objects_dictionary.'.format(country))
        self._country = country

    @property
    def name(self):
        """
        Gets the name of the province.

        Returns:
            str: The name of the province.
        """
        return self._name

    @property
    def country(self):
        """
        Gets the country that the province belongs to.

        Returns:
            Country: The country that the province belongs to.
        """
        return self._country

