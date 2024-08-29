from haversine import haversine, Unit
import numpy as np
import pandas as pd
from typing import List, Tuple
import bisect


class Point:
    def __init__(self, longitude: float, latitude: float, precision: int = 3):
        """
        Creates a new instance of the Point class.

        Args:
            longitude (float): The longitude of the point.
            latitude (float): The latitude of the point.

        Returns:
            Point: A new instance of the Point class.
        """
        if longitude > 180 or longitude < -180:
            raise ValueError("Longitude must be between -180 and 180")
        self._longitude = round(longitude, precision)

        if latitude > 90 or latitude < -90:
            raise ValueError("Latitude must be between -90 and 90")
        self._latitude = round(latitude, precision)

    def __repr__(self):
        """
        Returns a string representation of the Point object.

        Returns:
            str: String representation of the Point object.
        """
        return f"Point ({self._longitude}, {self._latitude})"

    def longitude(self):
        return self._longitude

    def latitude(self):
        return self._latitude


def distance_between_two_points(point1: Point, point2: Point):
    """
    Calculates the distance between two points using the haversine formula

    Args:
        point1 (Point): The first point.
        point2 (Point): The second point.

    Returns:
        float: The distance between the two points in kilometers.
    """
    distance = haversine((point1.latitude(), point1.longitude()), (point2.latitude(), point2.longitude()), unit=Unit.KILOMETERS)
    return distance


class PointSet:
    def __init__(self, points: List[Point]):
        """
        Creates a new instance of the Points class.

        Args:
            points (list): The list of points.

        Returns:
            Points: A new instance of the Points class.
        """
        self.points = points
        self._df = pd.DataFrame([(point.longitude(), point.latitude()) for point in points], columns=['Longitude', 'Latitude'])

    def __repr__(self):
        """
        Returns a string representation of the Points object.

        Returns:
            str: String representation of the Points object.
        """
        return f"Points ({self.points})"


    def __len__(self):
        return len(self.points)

    def list_of_longitudes_and_latitudes(self, sort_latitudes: bool=False):
        longitudes = self.list_of_longitudes()
        latitudes = self.list_of_latitudes()
        if sort_latitudes:
            longitudes, latitudes = zip(*sorted(zip(longitudes, latitudes), key=lambda pair: pair[1]))

        return longitudes, latitudes

    def list_of_longitudes(self):
        return self._df['Longitude'].tolist()

    def list_of_latitudes(self):
        return self._df['Latitude'].tolist()


def distance_between_point_and_point_set(point: Point, points: PointSet, starting_point=None):
    """
    This function computes the closest geographical distance between
    - a point p = (point_latitude, point_longitude) given as a Point object
    - a list of points given as PointSet object
    The distance is computed using the haversine formula (https://github.com/mapado/haversine) in kilometers

    Args:
        point (Point): The point.
        points (PointSet): The set of points.
        starting_point (Point): The starting point, must be in the set of points or None.
    """

    # This is the maximum distance between two points that differ by 1 degree in latitude
    # For a perfect sphere, this is a constant, but varies slightly for the Earth
    absolute_one_latitude_distance = 1.0001 * haversine((0, 0), (1, 0), unit=Unit.KILOMETERS)

    # The algorithm searches over points to find the point
    # q^* = (latitude^*, longitude^*) = argmin_{q in points} distance(p, q)
    # A candidate q is maintained at all times, and the distance is updated if a closer point is found
    # The search is not linear over points

    # Check if S is empty:
    if len(points) == 0:
        return np.inf

    longitudes, latitudes = points.list_of_longitudes_and_latitudes(sort_latitudes=True)

    # Initialize q_star and minimum_distance
    if starting_point is not None:
        q_star = starting_point                         # Initialize q_star with the starting index
    else:
        q_star = points.points[0]                              # Initialize q_star to be an arbitrary point in points

    minimum_distance = distance_between_two_points(point, q_star)           # Initialize minimum distance to be infinity

    # The latitude difference between q^* and p is upper bounded by the minimum distance per latitude difference
    latitude_difference_upper_bound = minimum_distance/absolute_one_latitude_distance

    # Find the index of the first point in points that has a latitude >= latitude1 - latitude_difference_upper_bound
    i_low = bisect.bisect_left(latitudes, (point.latitude() - latitude_difference_upper_bound))
    # Find the index of the first point in points that has a latitude > latitude1 + latitude_difference_upper_bound
    i_high = bisect.bisect_right(latitudes, (point.latitude() + latitude_difference_upper_bound))

    # Start search over points[i_low:i_high]
    improvement = np.inf                # Initialize improvement to be infinity
    while improvement > 0:              # While improvement > 0
        improvement = 0                 # Set improvement to 0
        for i in range(i_low, i_high):  # For each point q in points[i_low:i_high]
            q = Point(longitudes[i], latitudes[i])               # Set q to be the current point

            distance = distance_between_two_points(point, q)                    # Compute the distance between p and q
            if distance < minimum_distance:
                q_star = q                                                      # Update q_star
                improvement = minimum_distance - distance                       # Compute the improvement
                minimum_distance = distance                                     # Update the minimum distance
                # Update the latitude difference between q^* and p
                latitude_difference_upper_bound = minimum_distance/absolute_one_latitude_distance

                # Find the index of the first point in points that has
                # latitude >= latitude1 - latitude_difference_upper_bound
                i_low = bisect.bisect_left(latitudes, (point.latitude() - latitude_difference_upper_bound))
                # Find the index of the first point in points that has
                # latitude > latitude1 + latitude_difference_upper_bound
                i_high = bisect.bisect_right(latitudes, (point.latitude() + latitude_difference_upper_bound))

                break                                                           # Break the for loop

    return minimum_distance, q_star


def distances_from_point_set_to_point_set(points1: PointSet, points2: PointSet):
    """
    This function computes the closest geographical distance between two sets of points.
    The distance is computed using the haversine formula (https://github.com/mapado/haversine) in kilometers
    :param points1: list of tuples of latitudes and longitudes.
    :param points2: list of tuples of latitudes and longitudes.
    :return: distances (in km) from each point in points1 to the closest point in points2, output as a dictionary
    """
    distances = {}
    for point in points1.points:
        distances[point], _ = distance_between_point_and_point_set(point, points2)
    return distances
