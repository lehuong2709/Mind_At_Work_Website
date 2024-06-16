import plotly.graph_objects as go
import os
from src.usa.utils import colors, compute_medical_deserts, racial_labels
import pandas as pd
import random
import geopandas as gpd


def plot_stacked_bar(demographic_data):
    legend_labels = {
        'white_alone': 'Majority White',
        'black_alone': 'Majority Black',
        'aian_alone': 'Majority AIAN',
        'asian_alone': 'Majority Asian',
        'nhopi_alone': 'Majority NHOPI',
        'hispanic': 'Majority Hispanic',
        'other': 'Other',
        'no_desert': 'Previous medical deserts',
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
            # hovertemplate='<b>%{text}</b><br>Value: %{x}<extra></extra>',
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

    bounds = dict(pd.read_csv('data/usa/geographical_bounds.csv', index_col=0).loc[state_name])
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
            y=0.98,
            orientation='v',
            bgcolor='rgba(255,255,255,0.5)',
        )
    )

    return fig, bounds


def plot_existing_facilities(fig, Facility, bounds, size=4):
    facility_df = Facility.read_abridged_facilities()
    facility_df = gpd.clip(facility_df, mask=[bounds['min_x'], bounds['min_y'], bounds['max_x'], bounds['max_y']])
    fig.add_trace(go.Scattergeo(lon=facility_df.geometry.x, lat=facility_df.geometry.y, mode='markers',
                                marker=dict(size=size, color=Facility.color, opacity=0.8, symbol='x'),
                                name=Facility.display_name, showlegend=True))

    return fig


def plot_new_facilities(fig, facilities, census_df, color='dark red', size=6, name='Proposed new existing_facilities'):
    lon, lat = census_df.loc[facilities]['Longitude'], census_df.loc[facilities]['Latitude']
    fig.add_trace(go.Scattergeo(lon=lon, lat=lat, mode='markers',
                                marker=dict(size=size, color=color, opacity=0.8, symbol='diamond'),
                                name=name, showlegend=True,
                                line=dict(width=1.0, color='red'),
                                ))

    return fig


def plot_voronoi_cells(fig, facility, state_fips):
    voronoi_df = gpd.read_file(os.path.join(facility.voronoi_folder, state_fips + '_voronoi.shp'), index=False)
    for geom in voronoi_df.geometry:
        if geom.geom_type == 'LineString':
            x, y = geom.xy
            x = list(x)
            y = list(y)
            fig.add_trace(go.Scattergeo(lon=x, lat=y, mode='lines', line=dict(width=0.2, color='chocolate'),
                                        name=None, showlegend=False))

    return fig


def plot_blockgroups(fig, census_df, color=None):
    if color is None:
        racial_labels_copy = racial_labels.copy()
        random.shuffle(racial_labels_copy)
        for racial_label in racial_labels_copy:
            census_df_label = census_df[census_df['racial_majority'] == racial_label]
            if len(census_df_label) > 0:
                fig.add_trace(go.Scattergeo(
                    name=racial_label.split('_')[0].capitalize(),
                    lon=census_df_label['Longitude'], lat=census_df_label['Latitude'],
                    marker=dict(
                        color=colors[racial_label], opacity=0.6, line=dict(width=0.5, color='rgba(0, 0, 0, 0.9)'),
                    )
                ))

        fig.update_layout(
            legend=dict(
                itemsizing='constant',
                x=0.02,
                y=1.00,
                bgcolor='rgba(255,255,255,0.5)',
                title= dict(
                    text='Racial/ethnic majority',
                    font=dict(
                        size=12,
                        color='black'
                    )
                ),
            ),
        )
    else:
        fig.add_trace(go.Scattergeo(
            lon=census_df['Longitude'], lat=census_df['Latitude'],
            name='Previous medical deserts',
            marker=dict(
                color=color, opacity=0.6, line=dict(width=0, color='rgba(0, 0, 0, 0.9)'),
            )
        ))

    return fig


def plot_medical_deserts(fig, census_df, distance_label, old_distance_label, poverty_threshold, n_urban, n_rural):
    old_desert_df = compute_medical_deserts(census_df, poverty_threshold, n_urban, n_rural, old_distance_label)
    desert_df = compute_medical_deserts(census_df, poverty_threshold, n_urban, n_rural, distance_label)

    racial_labels_copy = racial_labels.copy()
    random.shuffle(racial_labels_copy)

    if len(old_desert_df) - len(desert_df) > 0:
        fig.add_trace(go.Scattergeo(
            name='Previous medical deserts',
            lon=old_desert_df['Longitude'], lat=old_desert_df['Latitude'],
            marker=dict(
                color='lightgrey', opacity=1.0, line=dict(width=0.0, color='rgba(0, 0, 0, 0.9)'),
                size=4,
            )
        ))

    for racial_label in racial_labels_copy:
        desert_df_label = desert_df[desert_df['racial_majority'] == racial_label]
        if len(desert_df_label) > 0:
            fig.add_trace(go.Scattergeo(
                name=racial_label.split('_')[0].capitalize(),
                lon=desert_df_label['Longitude'], lat=desert_df_label['Latitude'],
                marker=dict(
                    color=colors[racial_label], opacity=0.6, line=dict(width=0.5, color='rgba(0, 0, 0, 0.9)'),
                )
            ))

    fig.update_layout(
        legend=dict(
            itemsizing='constant',
            x=0.02,
            y=1.00,
            bgcolor='rgba(255,255,255,0.5)',
            title=dict(
                text='Racial/ethnic majority',
                font=dict(
                    size=12,
                    color='black'
                ),
            ),
        ),
    )

    return fig, desert_df
