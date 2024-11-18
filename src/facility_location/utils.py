import pandas as pd
import numpy as np
from tqdm import tqdm
from haversine import haversine, Unit
import geopandas as gpd
from src.geodesy import Point, PointSet, distance_between_point_and_point_set


def generate_groups(census_dataframe, no_health_ins_threshold=25, two_health_ins_threshold=25, below_poverty_threshold=20):
    n = len(census_dataframe.index)
    group_indices = {(i, j, k): [] for i in range(3) for j in range(3) for k in range(2)}

    racial_majorities = census_dataframe['racial_majority'].value_counts()
    largest_racial_majority = None
    second_racial_majority = None

    for id in range(len(racial_majorities)):
        if racial_majorities.index[id] != 'other':
            largest_racial_majority = racial_majorities.index[id]
            break

    for id2 in range(id + 1, len(racial_majorities)):
        if racial_majorities.index[id2] != 'other':
            second_racial_majority = racial_majorities.index[id2]
            break

    for j in range(n):
        l = [0, 0, 0]
        racial_majority = census_dataframe.loc[j]['racial_majority']
        if racial_majority == largest_racial_majority:
            l[0] = 1
        elif racial_majority == second_racial_majority:
            l[0] = 2
        else:
            l[0] = 0

        if census_dataframe.iloc[j].no_health_ins >= no_health_ins_threshold:
            l[1] = 0
        elif census_dataframe.iloc[j].two_health_ins <= two_health_ins_threshold:
            l[1] = 1
        else:
            l[1] = 2

        if census_dataframe.iloc[j].below_poverty >= below_poverty_threshold:
            l[2] = 0
        else:
            l[2] = 1

        group_indices[tuple(l)].append(j)

    groups = []
    for l1 in [0, 1, 2]:
        for l2 in [0, 1, 2]:
            for l3 in [0, 1]:
                if len(group_indices[(l1, l2, l3)]) > 0:
                    groups.append(group_indices[(l1, l2, l3)])

    return groups


def generate_points_and_distances(state_df, existing_distances_label):
    points = list(state_df.index)
    urban_points = [point for point in points if state_df.loc[point, 'urban'] == 1]

    pairwise_distances = {j: {} for j in points}

    longitudes = {i: state_df.loc[i, 'Longitude'] for i in points}
    latitudes = {i: state_df.loc[i, 'Latitude'] for i in points}

    for j in tqdm(points):
        longitude_j = longitudes[j]
        latitude_j = latitudes[j]
        distance_to_existing_facility = state_df.loc[j, existing_distances_label]
        for i in points:
            longitude_i = longitudes[i]
            latitude_i = latitudes[i]
            if abs(longitude_i - longitude_j) < distance_to_existing_facility/50 and abs(latitude_i - latitude_j) < distance_to_existing_facility/50:
                distance = haversine((latitude_i, longitude_i), (latitude_j, longitude_j), unit=Unit.KILOMETERS)
                if distance < distance_to_existing_facility:
                    pairwise_distances[j][i] = distance

    existing_distances = {point: state_df.loc[point, existing_distances_label] for point in points}

    return points, urban_points, pairwise_distances, existing_distances


def compute_minimum_distances(census_df, facilities, existing_distances_label, new_distances_label, show_progress=True):
    # existing_distances = census_df[existing_distances_label]
    #
    # facility_longitudes = [census_df.loc[facility]['Longitude'] for facility in facilities]
    # facility_latitudes = [census_df.loc[facility]['Latitude'] for facility in facilities]
    #
    # distances = []
    # for i in range(len(facility_longitudes)):
    #     distances.append(census_df.apply(lambda x: haversine((x['Latitude'], x['Longitude']), (facility_latitudes[i], facility_longitudes[i]), unit=Unit.KILOMETERS), axis=1))
    # distances = np.array(distances)
    # distances = np.min(distances, axis=0)
    # distances = np.minimum(distances, existing_distances)
    # distances = np.round(distances, 3)
    #
    # census_df[new_distances_label] = distances
    # return census_df

    facility_longitudes = [census_df[census_df.GEOID == facility]['Longitude'].values[0] for facility in facilities]
    facility_latitudes = [census_df[census_df.GEOID == facility]['Latitude'].values[0] for facility in facilities]

    facility_points = []
    for i in range(len(facility_longitudes)):
        facility_points.append(Point(facility_longitudes[i], facility_latitudes[i], name=facilities[i]))

    for i in tqdm(range(len(census_df)), disable=not show_progress):
        point = Point(census_df.iloc[i]['Longitude'], census_df.iloc[i]['Latitude'], name=census_df.iloc[i]['GEOID'])
        min_distance, to_point = distance_between_point_and_point_set(point, PointSet(facility_points))
        if min_distance < census_df.loc[i, existing_distances_label]:
            census_df.loc[i, new_distances_label] = min_distance
            census_df.loc[i, new_distances_label + '_ID'] = str(to_point.name())
        else:
            census_df.loc[i, new_distances_label] = census_df.loc[i, existing_distances_label]
            census_df.loc[i, new_distances_label + '_ID'] = str(census_df.loc[i, existing_distances_label + '_ID'])

    return census_df


def compute_distances_to_new_facility(census_df, new_facility, existing_distances_label, new_distances_label, show_progress=True):
    new_facility = census_df[census_df.GEOID == new_facility].iloc[0]
    new_facility_longitude = new_facility['Longitude']
    new_facility_latitude = new_facility['Latitude']

    existing_distances = list(census_df[existing_distances_label])
    longitudes = list(census_df['Longitude'])
    latitudes = list(census_df['Latitude'])
    new_distances = []

    for i in tqdm(range(len(census_df)), disable= not show_progress):
        existing_distance = existing_distances[i]
        if abs(longitudes[i] - new_facility_longitude) < existing_distance/25 and abs(latitudes[i] - new_facility_latitude) < existing_distance/25:
            distance = haversine((census_df.loc[i, 'Latitude'], census_df.loc[i, 'Longitude']), (new_facility_latitude, new_facility_longitude), unit=Unit.KILOMETERS)
        else:
            distance = np.inf

        distance = min(distance, existing_distance)

        new_distances.append(distance)

    census_df[new_distances_label] = new_distances

    return census_df


def compute_medical_deserts(state_df, poverty_threshold=20, n_urban=2, n_rural=10, distance_label='Closest_Distance_Pharmacies_Top3'):
    desert_df = state_df[state_df['below_poverty'] >= poverty_threshold]
    desert_df = desert_df[((desert_df['urban'] == 1) & (desert_df[distance_label] > 1.60934 * n_urban)) | ((desert_df['urban'] == 0) & (desert_df[distance_label] > 1.60934 * n_rural))]

    return desert_df[['Latitude', 'Longitude', 'below_poverty', 'racial_majority', 'urban', distance_label]]


def get_demographics_of_medical_deserts(desert_df):
    white_only = desert_df[desert_df['racial_majority'] == 'white_alone'].shape[0]
    black_only = desert_df[desert_df['racial_majority'] == 'black_alone'].shape[0]
    hispanic = desert_df[desert_df['racial_majority'] == 'hispanic'].shape[0]
    other = len(desert_df) - (white_only + black_only + hispanic)

    return white_only, black_only, hispanic, other

