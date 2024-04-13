"""
This module contains geometric functions for geographical projections and distances.
"""
import bisect
from src.constants import *
import geopandas as gpd
from haversine import haversine, Unit
import numpy as np
from tqdm import tqdm
from typing import List, Tuple
import warnings


def long_lat_to_spherical(long, lat):
    """
    This function converts longitude and latitude to spherical coordinates (with radius 1)
    :param long: longitude, between -180 and 180
    :param lat: latitude, between -90 and 90
    :return: [x, y, z] coordinates of the point on the unit sphere as np array
    """
    long0 = (long/180)*np.pi
    lat0 = (lat/180)*np.pi

    x = np.cos(lat0) * np.cos(long0)
    y = np.cos(lat0) * np.sin(long0)
    z = np.sin(lat0)
    return np.array([x, y, z])


def spherical_to_long_lat(x, y, z):
    """
    This function converts spherical coordinates (with radius 1) to longitude and latitude,
    inverse of long_lat_to_spherical
    :param x: x coordinate on unit sphere
    :param y: y coordinate on unit sphere
    :param z: z coordinate on unit sphere
    :return: longitude, latitude
    """
    lat = (np.arcsin(z)*180)/np.pi
    long = (np.arctan2(y, x)*180)/np.pi
    return long, lat


def normalize(v):
    """
    This function normalizes a vector v to be of unit length, unless v = 0
    :param v: vector v
    :return: unit vector in the direction of v or 0 if v = 0
    """
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


def closest_geographical_distance(point_longitude: float, point_latitude: float, points: List[Tuple[float, float]],
                                  starting_point=None):
    """
    This function computes the closest geographical distance between a point p = (point_latitude, point_longitude) and a
    list of points given as (latitude, longitude) pairs.
    The distance is computed using the haversine formula (https://github.com/mapado/haversine) in kilometers
    :param point_latitude: latitude of the point
    :param point_longitude: longitude of the point
    :param points: list of tuples of latitudes and longitudes
    :return: distance in kilometers
    ToDo: make the algorithm more efficient
    """

    # This is the maximum distance between two points that differ by 1 degree in latitude
    # For a perfect sphere, this is a constant, but varies slightly for the Earth due to its oblateness
    absolute_one_latitude_distance = 1.0001 * haversine((0, 0), (1, 0), unit=Unit.KILOMETERS)

    # The algorithm searches over points to find the point
    # q^* = (latitude^*, longitude^*) = argmin_{q in points} distance(p, q)
    # A candidate q is maintained at all times, and the distance is updated if a closer point is found
    # The search is not linear over points

    # Check if S is empty:
    if len(points) == 0:
        return np.inf

    # The point p = (point_latitude, point_longitude)
    p = (point_latitude, point_longitude)

    # Sort points by latitude
    points = sorted(points, key=lambda x: x[0])

    # Initialize q_star and minimum_distance
    if starting_point is not None:
        q_star = starting_point                         # Initialize q_star with the starting index
    else:
        q_star = points[0]                              # Initialize q_star to be an arbitrary point in points

    minimum_distance = haversine(p, q_star, unit=Unit.KILOMETERS)           # Initialize minimum distance to be infinity

    # The latitude difference between q^* and p is upper bounded by the minimum distance per latitude difference
    latitude_difference_upper_bound = minimum_distance/absolute_one_latitude_distance

    # Find the index of the first point in points that has a latitude >= latitude1 - latitude_difference_upper_bound
    i_low = bisect.bisect_left(points, (point_latitude - latitude_difference_upper_bound), key=lambda pair: pair[0])
    # Find the index of the first point in points that has a latitude > latitude1 + latitude_difference_upper_bound
    i_high = bisect.bisect_right(points, (point_latitude + latitude_difference_upper_bound), key=lambda pair: pair[0])

    # Start search over points[i_low:i_high]
    improvement = np.inf                # Initialize improvement to be infinity
    while improvement > 0:              # While improvement > 0
        improvement = 0                 # Set improvement to 0
        for i in range(i_low, i_high):  # For each point q in points[i_low:i_high]
            q = points[i]               # Set q to be the current point

            distance = haversine(p, q, unit=Unit.KILOMETERS)                    # Compute the distance between p and q
            if distance < minimum_distance:
                q_star = q                                                      # Update q_star
                improvement = minimum_distance - distance                       # Compute the improvement
                minimum_distance = distance                                     # Update the minimum distance
                # Update the latitude difference between q^* and p
                latitude_difference_upper_bound = minimum_distance/absolute_one_latitude_distance

                # Find the index of the first point in points that has
                # latitude >= latitude1 - latitude_difference_upper_bound
                i_low = bisect.bisect_left(points, (point_latitude - latitude_difference_upper_bound), key=lambda pair: pair[0])
                # Find the index of the first point in points that has
                # latitude > latitude1 + latitude_difference_upper_bound
                i_high = bisect.bisect_right(points, (point_latitude + latitude_difference_upper_bound), key=lambda pair: pair[0])

                break                                                           # Break the for loop

    return minimum_distance, q_star


def closest_distance(df1, df2, distance_label='Closest_Distance'):
    """
    This function calculates the closest distance between each point in df1 and the points in df2 in kilometers
    The first dataframe df1 will have distances stored in a new column named distance_label
    The distance is computed using the haversine formula
    :param df1: pandas or GeoPandas dataframe
    :param df2: pandas or GeoPandas dataframe
    :param distance_label: name of the new column to store the distances
    :return: df1 with the new column
    """
    def get_longitudes_and_latitudes_list(dataframe):
        """
        This function gets pairs of (latitude, longitude) pairs from a dataframe.
        If the dataframe is a pandas dataframe, it must have columns named 'Longitude' and 'Latitude'
        If the dataframe is a GeoDataFrame, it will first convert the geometry data into longitudes and latitudes.
        :param dataframe: pandas or GeoPandas dataframe
        :return:
            points: list of tuples of latitudes and longitudes
        """
        if 'Longitude' not in dataframe.columns or 'Latitude' not in dataframe.columns:
            if isinstance(dataframe, gpd.GeoDataFrame):
                if dataframe.crs is None:
                    crs = projection_wgs84
                    warnings.warn('The dataframe does not have a coordinate reference system (CRS) defined.'
                                  'The default CRS WGS84/EPSG:4326 is used.', UserWarning)
                else:
                    crs = dataframe.crs

                dataframe.to_crs(projection_wgs84, inplace=True)
                longitudes = list(dataframe.geometry.x)
                latitudes = list(dataframe.geometry.y)
                dataframe.to_crs(crs, inplace=True)
            else:
                raise ValueError('The dataframe does not have columns named "Longitude" and "Latitude"'
                                 'or a geometry of points')
        else:
            longitudes = dataframe['Longitude'].values
            latitudes = dataframe['Latitude'].values

        points = list(zip(latitudes, longitudes))
        points = sorted(points, key=lambda pair: pair[0])

        return points

    points = get_longitudes_and_latitudes_list(df2)

    def closest_geographical_distance_to_df2(point_longitude, point_latitude, starting_point=None):
        """Compute the closest geographical distance between a point and the points in the second dataframe"""
        distance, _ = closest_geographical_distance(point_longitude, point_latitude, points, starting_point)
        return distance

    if distance_label in df1.columns:
        warnings.warn('The dataframe already has a column named "{}".'
                      'The column will be overwritten.'.format(distance_label), UserWarning)

    tqdm.pandas(desc='Computing distances')                             # Show a progress bar
    if 'Longitude' not in df1.columns or 'Latitude' not in df1.columns:
        if isinstance(df1, gpd.GeoDataFrame):
            if df1.crs is None:                                         # Check if the dataframe has a CRS
                crs = projection_wgs84
                warnings.warn('The dataframe does not have a coordinate reference system (CRS) defined.'
                              'The default CRS WGS84/EPSG:4326 is used.', UserWarning)
            else:
                crs = df1.crs

            _, starting_point = closest_geographical_distance(point_longitude=df1.geometry.x[0], point_latitude=df1.geometry.y[0], points=points,
                                                              starting_point=None)

            df1.to_crs(projection_wgs84, inplace=True)                  # Convert the geometry to longitudes, latitudes
            # Compute the closest distance to the second dataframe
            df1[distance_label] = df1.progress_apply(lambda row: closest_geographical_distance_to_df2(row.geometry.x, row.geometry.y, starting_point), axis=1)
            df1.to_crs(crs, inplace=True)                               # Convert the geometry back to the original CRS
    else:
        # Compute the closest distance to the second dataframe
        df1[distance_label] = df1.progress_apply(lambda row: closest_geographical_distance_to_df2(row['Longitude'], row['Latitude']), axis=1)

    return df1

