import geopandas as gpd
import plotly.graph_objects as go
import os
import pandas as pd
import random
from src.usa.utils import colors, racial_labels, racial_labels_display_names
from src.constants import WATERBODY_COLOR, LAND_COLOR_PRIMARY, LAND_COLOR_SECONDARY, BOUNDARY_COLOR
import streamlit as st
from src.usa.constants import state_names
from src.usa.states import USAState
from src.usa.utils import compute_medical_deserts
import numpy as np


@st.cache_data
def get_us_cities(State):
    df_cities = pd.read_csv('data/usa/cities/uscities.csv')
    state_abbr = State.abbreviation
    df_cities = df_cities[df_cities['state_id'] == state_abbr]
    df_cities.sort_values(by='population', ascending=False, inplace=True)
    if state_abbr in ['CA', 'TX', 'FL', 'NY']:
        n_cities = 10
    else:
        n_cities = 5
    df_cities = df_cities.head(n_cities)

    return df_cities


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
        colorscale=[LAND_COLOR_SECONDARY, LAND_COLOR_PRIMARY],  # Color scale for the choropleth map
        showscale=False,
        hoverinfo='location'
    )

    # Add the choropleth map to the figure
    fig.add_trace(choropleth)

    bounds = dict(pd.read_csv('data/usa/geographical_bounds.csv', index_col=0).loc[state_name])
    fig.update_geos(
        showland=True,
        showcoastlines=True,
        showframe=False,
        showocean=True,
        showcountries=True,
        showlakes=True,
        lakecolor=WATERBODY_COLOR,
        oceancolor=WATERBODY_COLOR,
        landcolor=LAND_COLOR_SECONDARY,
        scope="north america",
        lonaxis_range=[bounds['min_x'], bounds['max_x']],
        lataxis_range=[bounds['min_y'], bounds['max_y']],
        projection_type='mercator',
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0, pad=0),
        autosize=False,
        xaxis=dict(range=[bounds['min_x'], bounds['max_x']], autorange=False),
        yaxis=dict(range=[bounds['min_y'], bounds['max_y']], autorange=False),
        showlegend=True,
        legend=dict(
            itemsizing='constant',
            x=0.02,
            orientation='v',
            bgcolor='rgba(255,255,255,0.5)',
        )
    )

    # fig.update_yaxes(automargin=True)

    return fig, bounds


def plot_cities(fig, State):
    df_cities = get_us_cities(State)
    fig.add_trace(
        go.Scattergeo(
            lon=df_cities['lng'],
            lat=df_cities['lat'],
            text=df_cities['city'],
            textposition='top center',
            mode='markers+text',
            hoverinfo='text',
            marker=dict(
                symbol='pentagon',
                size=10,
                opacity=0.8,
                color='black',
            ),
            showlegend=False,
        ),
    )

    return fig


def plot_points(fig, df, bounds=None, name='Points', showlegend=True,
                marker_symbol='x', marker_size=6, marker_color='black', marker_opacity=0.8,
                marker_line_width=0.0, marker_line_color='black',
                ):
    """
    Plots 2d points provided through columns 'Longitude' and 'Latitude' of a pandas dataframe df on a plotly figure fig
    Args:
        fig: plotly fig
        df: pandas or geopandas dataframe
        bounds: only points within this bound will be plotted. Must be a dictionary with keys 'min_x, 'max_x', 'min_y', and 'max_y'
        name: name in legend
        showlegend: whether to show legend
        marker_symbol: marker symbol
        marker_size: marker size
        marker_color: marker color
        marker_line_width: marker line width
        marker_line_color: marker line color
    Returns:
        fig: plotly figure
    """
    if 'Longitude' not in df.columns or 'Latitude' not in df.columns:
        raise ValueError('Dataframe must contain columns Longitude and Latitude to plot points')

    if bounds is not None:
        df_bounded = df[
            (df['Longitude'] >= bounds['min_x']) & (df['Longitude'] <= bounds['max_x']) &
            (df['Latitude'] >= bounds['min_y']) & (df['Latitude'] <= bounds['max_y'])
        ]
    else:
        df_bounded = df

    fig.add_trace(
        go.Scattergeo(
            lon=df_bounded['Longitude'],
            lat=df_bounded['Latitude'],
            mode='markers',
            name=name,
            showlegend=showlegend,
            marker=dict(
                symbol=marker_symbol,
                size=marker_size,
                color=marker_color,
                opacity=marker_opacity,
                line=dict(
                    width=marker_line_width,
                    color=marker_line_color,
                ),
            )
        )
    )
    return fig


def plot_existing_facilities(fig, facility, bounds):
    facility_df = facility.get_existing_locations()
    fig = plot_points(
        fig=fig, df=facility_df, bounds=bounds, name=facility.display_name, showlegend=True,
        marker_symbol='x', marker_size=4, marker_color=facility.color, marker_opacity=0.8,
        marker_line_width=0.0, marker_line_color='black',
    )
    return fig


def plot_new_facilities(fig, facility, state_fips, p, k, name, marker_symbol, marker_color='black', marker_size=6,
                        marker_line_width=0.0, marker_line_color='black'):
    facility_df = facility.get_new_locations(state_fips=state_fips, p=p)
    facility_df = facility_df.head(k)
    fig = plot_points(
        fig=fig, df=facility_df, name=name, showlegend=True,
        marker_symbol=marker_symbol, marker_color=marker_color, marker_size=marker_size,
        marker_line_width=marker_line_width, marker_line_color=marker_line_color
    )
    return fig


def plot_voronoi_cells(fig, facility, state_fips):
    voronoi_df = facility.read_voronoi_cells(state_fips)
    for geom in voronoi_df.geometry:
        if geom.geom_type == 'LineString':
            x, y = geom.xy
            x = list(x)
            y = list(y)
            scattergeo = go.Scattergeo(lon=x, lat=y, mode='lines', line=dict(width=0.2, color='chocolate'), name=None, showlegend=False)
            fig.add_trace(scattergeo)

    return fig


def plot_blockgroups(fig, blockgroup_df, color=None):
    if color is not None:
        fig = plot_points(
            fig=fig, df=blockgroup_df, name='No longer a medical desert', showlegend=True,
            marker_symbol='circle', marker_size=5, marker_color=color, marker_opacity=0.6,
        )
    else:
        racial_labels_copy = racial_labels.copy()
        random.shuffle(racial_labels_copy)
        for racial_label in racial_labels_copy:
            name = racial_labels_display_names[racial_label]
            if racial_label in blockgroup_df['racial_majority'].unique():
                fig = plot_points(
                    fig=fig, df=blockgroup_df[blockgroup_df['racial_majority'] == racial_label], name=name, showlegend=True,
                    marker_color=colors[racial_label], marker_opacity=0.6, marker_symbol='circle', marker_size=6,
                    marker_line_width=0.5, marker_line_color='rgba(0, 0, 0, 0.9)'
                )
        fig.update_layout(
            legend=dict(
                itemsizing='constant',
                x=0.02,
                bgcolor='rgba(255,255,255,0.5)',
                title=dict(
                    text='Racial/ethnic majority',
                    font=dict(
                        size=12,
                        color='black'
                    )
                ),
            ),
        )

    return fig


def plot_stacked_bar(demographic_data):
    legend_labels = {
        'white_alone': 'Majority White',
        'black_alone': 'Majority Black',
        'aian_alone': 'Majority AIAN',
        'asian_alone': 'Majority Asian',
        'nhopi_alone': 'Majority NHOPI',
        'hispanic': 'Majority Hispanic',
        'other': 'Other',
        'no_desert': 'No longer a medical desert',
    }

    if sum(demographic_data.values()) == 0:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[1],
            y=[''],
            orientation='h',
            marker=dict(color='lightgrey'),
            showlegend=False,
            hoverinfo='none',
        ))
        fig.update_layout(
            barmode='stack',
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False
            ),
            height=30,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        return fig

    fig = go.Figure()
    for racial_label in demographic_data.keys():
        if racial_label == 'no_desert':
            color = 'lightgrey'
        else:
            color = colors[racial_label]

        if demographic_data[racial_label]/sum(demographic_data.values()) < 0.05:
            text=''
        else:
            text = str(demographic_data[racial_label])
        fig.add_trace(go.Bar(
            x=[demographic_data[racial_label]],
            y=[''],
            orientation='h',
            name=legend_labels[racial_label],
            marker=dict(color=color),
            showlegend=False,
            text=text,
            textposition='inside',
            insidetextanchor='middle',
            hoverinfo='name',
        ))

    fig.update_layout(
        barmode='stack',
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        height=30,
        margin=dict(l=0, r=0, t=0, b=0)
    )

    return fig


@st.cache_data
def plot_demographic_analysis(poverty_threshold, urban_distance_threshold, rural_distance_threshold, distance_label):
    def get_demographic_proportions(census_df):
        return dict(census_df['racial_majority'].value_counts(normalize=True, dropna=False))

    proportion_of_overall_population = pd.DataFrame(index=racial_labels, columns=state_names, data=np.zeros((len(racial_labels), len(state_names))))
    proportion_of_medical_deserts = pd.DataFrame(index=racial_labels, columns=state_names, data=np.zeros((len(racial_labels), len(state_names))))

    poor_blockgroups_fraction_overall = pd.Series(index=state_names, data=np.zeros(len(state_names)))
    poor_blockgroups_fraction_far_away = pd.Series(index=state_names, data=np.zeros(len(state_names)))

    for state_name in state_names:
        State = USAState(state_name)
        census_df = State.get_census_data(level='blockgroup')
        overall_demographic_data = get_demographic_proportions(census_df)

        desert_df = compute_medical_deserts(census_df, poverty_threshold=poverty_threshold, n_urban=urban_distance_threshold * 1.602, n_rural=rural_distance_threshold * 1.602,
                                            distance_label=distance_label)
        desert_demographic_data = get_demographic_proportions(desert_df)

        far_away_df = compute_medical_deserts(census_df, poverty_threshold=0, n_urban=urban_distance_threshold * 1.602, n_rural=rural_distance_threshold * 1.602,
                                              distance_label=distance_label)

        poor_blockgroups_fraction_overall.loc[state_name] = len(census_df[census_df['below_poverty'] >= poverty_threshold])/len(census_df)
        poor_blockgroups_fraction_far_away.loc[state_name] = len(far_away_df[far_away_df['below_poverty'] >= poverty_threshold])/len(far_away_df)

        for racial_label in racial_labels:
            if racial_label in overall_demographic_data:
                proportion_of_overall_population.loc[racial_label, state_name] = overall_demographic_data[racial_label]
            if racial_label in desert_demographic_data:
                proportion_of_medical_deserts.loc[racial_label, state_name] = desert_demographic_data[racial_label]

    for racial_label in racial_labels:
        proportion_of_overall_population.rename(index={racial_label: racial_labels_display_names[racial_label]}, inplace=True)
        proportion_of_medical_deserts.rename(index={racial_label: racial_labels_display_names[racial_label]}, inplace=True)

    M = max(100*((proportion_of_medical_deserts - proportion_of_overall_population).values.flatten()))
    m = min(100*((proportion_of_medical_deserts - proportion_of_overall_population).values.flatten()))

    alpha = abs(m)/(M + abs(m))

    fig = go.Figure(
        data=go.Heatmap(
            z=100*(proportion_of_medical_deserts - proportion_of_overall_population),
            x=state_names,
            y=[racial_labels_display_names[racial_label] for racial_label in racial_labels],
            colorscale=[[0, 'violet'], [alpha, 'white'], [1, 'orange']],
            colorbar=dict(title='''Percentage<br> point<br> difference'''),
        )
    )

    return fig


@st.cache_data
def get_urban_and_rural_df(census_df):
    urban_df = census_df[census_df['urban'] == 1]
    rural_df = census_df[census_df['urban'] == 0]
    return urban_df, rural_df


@st.cache_data
def get_poor_df(census_df, poverty_threshold):
    poor_df = census_df[census_df['below_poverty'] >= poverty_threshold]
    return poor_df


@st.cache_data
def get_uninsured_df(census_df, uninsured_threshold):
    uninsured_df = census_df[census_df['no_health_ins'] >= uninsured_threshold]
    return uninsured_df


@st.cache_data
def get_minority_and_majority_df(census_df):
    minority_df = census_df[census_df['racial_majority'] != 'white_alone']
    majority_df = census_df[census_df['racial_majority'] == 'white_alone']
    return minority_df, majority_df


def plot_radar_chart(State, facility, k, poverty_threshold):
    """
    Plot a radar chart comparing two lists of scalar values, before and after opening k facilities
    """
    def loop_list(list_like_object):
        """
        Loop a list-like object to make it circular
        """
        l = list(list_like_object)
        l = l + [l[0]]
        return l

    census_df = State.get_census_data(level='blockgroup')
    urban_df, rural_df = get_urban_and_rural_df(census_df)

    urban_poor_df = get_poor_df(urban_df, poverty_threshold=poverty_threshold)
    rural_poor_df = get_poor_df(rural_df, poverty_threshold=poverty_threshold)

    urban_uninsured_df = get_uninsured_df(urban_df, uninsured_threshold=20)
    rural_uninsured_df = get_uninsured_df(rural_df, uninsured_threshold=20)

    urban_minority_df, urban_majority_df = get_minority_and_majority_df(urban_df)
    rural_minority_df, rural_majority_df = get_minority_and_majority_df(rural_df)

    distance_label_before = facility.distance_label
    distance_label_after = facility.distance_label + '_combined_k_' + str(k)

    labels = ['''All''', 'Poor', '''Low<br>insurance''', '''Racial<br>minorities''', 'White']
    urban_list_before = [
        urban_df[distance_label_before].mean(),
        urban_poor_df[distance_label_before].mean(),
        urban_uninsured_df[distance_label_before].mean(),
        urban_minority_df[distance_label_before].mean(),
        urban_majority_df[distance_label_before].mean(),
    ]
    rural_list_before = [
        rural_df[distance_label_before].mean(),
        rural_poor_df[distance_label_before].mean(),
        rural_uninsured_df[distance_label_before].mean(),
        rural_minority_df[distance_label_before].mean(),
        rural_majority_df[distance_label_before].mean(),
    ]
    urban_list_after = [
        urban_df[distance_label_after].mean(),
        urban_poor_df[distance_label_after].mean(),
        urban_uninsured_df[distance_label_after].mean(),
        urban_minority_df[distance_label_after].mean(),
        urban_majority_df[distance_label_after].mean(),
    ]
    rural_list_after = [
        rural_df[distance_label_after].mean(),
        rural_poor_df[distance_label_after].mean(),
        rural_uninsured_df[distance_label_after].mean(),
        rural_minority_df[distance_label_after].mean(),
        rural_majority_df[distance_label_after].mean(),
    ]

    fig_urban = go.Figure()

    fig_urban.add_trace(go.Scatterpolar(
        r=loop_list(urban_list_before),
        theta=loop_list(labels),
        name='Existing',
        marker=dict(
            size=10,
            # color='tomato',
            color='#b66dff',
        ),
        fill='toself',
        fillcolor='rgba(255, 0, 255, 0.1)'
    ))

    fig_urban.add_trace(go.Scatterpolar(
        r=loop_list(urban_list_after),
        theta=loop_list(labels),
        name='After opening ' + str(k) + ' proposed facilities',
        textfont=dict(
            size=40,
        ),
        marker=dict(
            size=10,
            # color='forestgreen',
            color='#21d565',
        ),
        fill='toself',
        fillcolor='rgba(25, 200, 25, 0.2)'
    ))

    fig_urban.update_layout(
        title=dict(
            text='Urban areas',
            y=0.9,
        ),
        legend=dict(
            orientation='h',
            x=0.5,
            xanchor='center',
        ),
        margin=dict(t=20, l=50),
    )

    fig_rural = go.Figure()

    fig_rural.add_trace(go.Scatterpolar(
        r=loop_list(rural_list_before),
        theta=loop_list(labels),
        name='Existing',
        marker=dict(
            size=10,
            # color='tomato',
            color='#b66dff',
        ),
        fill='toself',
        fillcolor='rgba(255, 0, 255, 0.1)'
    ))

    fig_rural.add_trace(go.Scatterpolar(
        r=loop_list(rural_list_after),
        theta=loop_list(labels),
        name='After opening ' + str(k) + ' proposed facilities',
        textfont=dict(
            size=40,
        ),
        marker=dict(
            size=10,
            # color='forestgreen',
            color='#21d565',
        ),
        fill='toself',
        fillcolor='rgba(25, 200, 25, 0.2)'
    ))

    fig_rural.update_layout(
        title=dict(
            text='Rural areas',
            y=0.9,
        ),
        legend=dict(
            orientation='h',
            x=0.5,
            xanchor='center',
        ),
        margin=dict(t=20, l=50),
    )

    return fig_urban, fig_rural


def plot_distance_histogram(State, facility, k):
    distance_label = facility.distance_label
    census_df = State.get_census_data(level='blockgroup')

    distances_before = census_df[distance_label]/1.602
    distances_after = census_df[distance_label + '_combined_k_' + str(k)]/1.602

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=distances_before - distances_after,
        opacity=0.50,
    ))

    fig.update_layout(
        xaxis_title='Distance (miles)',
        yaxis_title='Number of blockgroups',
        barmode='overlay',
        legend=dict(
            orientation='h',
            x=0.5,
            y=0.9,
            xanchor='center',
        ),
        # yaxis=dict(
        #     showgrid=False,
        #     scaleanchor='x',
        #     scaleratio=1.0,
        # ),
        height=200,
        margin=dict(t=0, l=0, r=0, b=0),
    )

    return fig
