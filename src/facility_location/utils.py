import pandas as pd
import numpy as np
from tqdm import tqdm
from haversine import haversine, Unit
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from src.usa.facilities import CVS, Walgreens, Walmart, PharmaciesTop3
import geopandas as gpd


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


def map_facilities(df, new_facilities, existing_facilities):
    fig, ax = plt.subplots()
    ax.set_aspect(11/9)

    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    ax.grid(False)
    ax.set_frame_on(False)

    longitudes_urabn_points = df[df['urban']]['Longitude']
    latitudes_urban_points = df[df['urban']]['Latitude']

    longitudes_rural_points = df[~df['urban']]['Longitude']
    latitudes_rural_points = df[~df['urban']]['Latitude']

    longitudes_new_facilities = df.loc[new_facilities, 'Longitude']
    latitudes_new_facilities = df.loc[new_facilities, 'Latitude']

    longitudes_existing_facilities = df.loc[existing_facilities, 'Longitude']
    latitudes_existing_facilities = df.loc[existing_facilities, 'Latitude']

    ax.scatter(longitudes_urabn_points, latitudes_urban_points, c='blue', label='Urban blockgroups', s=1)
    ax.scatter(longitudes_rural_points, latitudes_rural_points, c='orange', label='Rural blockgroups', s=1)

    ax.scatter(longitudes_new_facilities, latitudes_new_facilities, c='red', label='New Facilities', marker='x')
    ax.scatter(longitudes_existing_facilities, latitudes_existing_facilities, c='green', label='Existing Facilities', marker='x')

    ax.legend(fontsize='x-small')
    plt.show()


def compute_minimum_distances(census_df, facilities, existing_distances_label, new_distances_label):
    existing_distances = census_df[existing_distances_label]

    facility_longitudes = [census_df.loc[facility]['Longitude'] for facility in facilities]
    facility_latitudes = [census_df.loc[facility]['Latitude'] for facility in facilities]

    distances = []
    for i in range(len(facility_longitudes)):
        distances.append(census_df.apply(lambda x: haversine((x['Latitude'], x['Longitude']), (facility_latitudes[i], facility_longitudes[i]), unit=Unit.KILOMETERS), axis=1))
    distances = np.array(distances)
    distances = np.min(distances, axis=0)
    distances = np.minimum(distances, existing_distances)
    distances = np.round(distances, 3)

    census_df[new_distances_label] = distances
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


def plot_state(fig, State):
    state_name = State.name
    state_abbreviation = State.abbreviation

    data = pd.DataFrame({
        'state': ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'],
        'value': [1] * 50  # Default value for all states
    })
    # Set a different value for the state to highlight it
    data.loc[data['state'] == state_abbreviation, 'value'] = 2

    choropleth = go.Choropleth(
        locations=data['state'],  # Spatial coordinates
        z=data['value'].astype(float),  # Data to be color-coded
        locationmode='USA-states',  # Set of locations match entries in `locations`
        colorscale=["#fbfcf9", "#f9f3e1"],  # Color scale for the choropleth map
        showscale=False,
    )

    # Add the choropleth map to the figure
    fig.add_trace(choropleth)

    bounds = dict(pd.read_csv('data/usa/bounds.csv', index_col=0).loc[state_name])
    fig.update_geos(
        showland=True,
        showcoastlines=True,
        showframe=False,
        showocean=True,
        showcountries=True,
        showlakes=True,
        lakecolor='#a4b8b7',
        oceancolor='#a4b8b7',
        landcolor='#fbfcf9',
        scope="north america",
        lonaxis_range=[bounds['min_x'], bounds['max_x']],
        lataxis_range=[bounds['min_y'], bounds['max_y']],
        projection_type='mercator',
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        autosize=True,
        xaxis=dict(range=[bounds['min_x'], bounds['max_x']], autorange=False),
        yaxis=dict(range=[bounds['min_y'], bounds['max_y']], autorange=False),
        showlegend=True,
        legend=dict(
            itemsizing='constant',
            x=0.02,
            y=1.00,
            orientation='v',
            bgcolor='rgba(255,255,255,0.5)',
        )
    )

    return fig, bounds


def plot_facilities(fig, Facility, bounds):
    facility_df = Facility.get_abridged_facilities()
    facility_df = gpd.clip(facility_df, mask=bounds)
    fig.add_trace(go.Scattergeo(lon=facility_df.geometry.x, lat=facility_df.geometry.y, mode='markers',
                            marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                            name='Facility', showlegend=True))


# def plot_medical_deserts_in_grayscale(fig, census_df, distance_label, poverty_threshold=20,
#                                       n_urban=2, n_rural=10):
#     desert_df = compute_medical_deserts(census_df, poverty_threshold, n_urban, n_rural, distance_label)
#
#