import random

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shapely.geometry import Point

import src.plot
from src.constants import *
from src.usa.constants import *
from src.usa.states import *
from src.usa.facilities_data_handler import *
import streamlit as st
from PIL import Image
import base64
from io import BytesIO


scatter_palette = [
    '#007fee',
    '#21d565',
    '#ffe00a',
    '#ff7700',
    '#8bff08',
    '#9918fe',
    '#ff0004',
    '#179c49',
    '#00318f',
    '#ff1f70',
    '#af7b00',
    '#ff517c',
    '#d36969',
    '#18fe90'
]

st.set_page_config(layout="wide", initial_sidebar_state='expanded')

st.sidebar.write(r'A medical desert is defined as a US census blockgroup that is more than $n$ miles away from a '
                 r'CVS/Walgreeens/Walmart pharmacy and with over $p$% of the population living below the poverty line.')

state_names.sort()
state_name = st.sidebar.selectbox(label='Select a state', options=state_names, index=2)
State = USAState(state_name)

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    fig = go.Figure()
    fig, bounds = State.plot_state_boundary(fig)

    # voronoi_df = gpd.read_file('data/usa/facilities/shapefiles/Pharmacies_voronoi.shp', index=False)
    # state_shapefile_df = State.get_shapefiles(level='state')
    # voronoi_df = gpd.overlay(voronoi_df, state_shapefile_df, how='intersection')
    # voronoi_df = voronoi_df[~voronoi_df.geometry.is_empty]
    #
    state_fips = State.fips
    voronoi_df = gpd.read_file('data/usa/facilities/pharmacies_top3/voronoi_state_shapefiles/' + state_fips + '_voronoi.shp', index=False)

    for geom in voronoi_df.geometry:
        if geom.geom_type == 'LineString':
            x, y = geom.xy
            x = list(x)
            y = list(y)
            fig.add_trace(go.Scattergeo(lon=x, lat=y, mode='lines', line=dict(width=0.2, color='chocolate'),
                                        name=None, showlegend=False))

    pharmacy_df = Pharmacies.read_abridged_facilities()
    pharmacy_df = pharmacy_df[pharmacy_df['STATE'] == State.abbreviation]
    pharmacy_df['Longitude'] = pharmacy_df.geometry.x
    pharmacy_df['Latitude'] = pharmacy_df.geometry.y

    cvs = pharmacy_df[pharmacy_df['NAME'].str.contains('cvs', case=False)]
    walgreens = pharmacy_df[pharmacy_df['NAME'].str.contains('walgreens', case=False)]
    walmart = pharmacy_df[pharmacy_df['NAME'].str.contains('walmart', case=False)]

    fig.add_trace(go.Scattergeo(lon=cvs['Longitude'], lat=cvs['Latitude'], mode='markers',
                                marker=dict(size=4, color='red', opacity=0.6, symbol='x'),
                                name='CVS', showlegend=True))

    fig.add_trace(go.Scattergeo(lon=walgreens['Longitude'], lat=walgreens['Latitude'], mode='markers',
                                marker=dict(size=4, color='green', opacity=0.6, symbol='x'),
                                name='Walgreens', showlegend=True))

    fig.add_trace(go.Scattergeo(lon=walmart['Longitude'], lat=walmart['Latitude'], mode='markers',
                                marker=dict(size=4, color='blue', opacity=0.6, symbol='x'),
                                name='Walmart', showlegend=True))

    fig.update_geos(
        showland=False,
        showcoastlines=False,
        showframe=False,
        showocean=False,
        showcountries=False,
        lonaxis_range=[bounds[0], bounds[2]],
        lataxis_range=[bounds[1], bounds[3]],
        projection_type='mercator',
        bgcolor='#a1b8b7',
    )

    # Add title to the figure
    fig.update_layout(
        title={
            'text': "Locations of 3 largest <br> pharmacy chains in " + state_name,
            'y':0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
    )
    fig.update_layout(
        showlegend=True,
        # margin={"r": 0, "l": 0, "b": 0},
        width=4000,
        height=4000,
        autosize=False,
        coloraxis_showscale=False,
        xaxis=dict(visible=False, showgrid=False, showline=False),
        yaxis=dict(visible=False, showgrid=False, showline=False),
        uirevision='noloss',
        legend=dict(
            # title='Categories \n',
            title_font=dict(size=12),
            itemsizing='constant',
            x=0.02,
            y=0.05,
            orientation='v',
            font=dict(size=12,),
            bgcolor='rgba(255,255,255,0.5)',  # Semi-transparent white background
            bordercolor=None,
            borderwidth=1,
        )
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})


racial_fractions_overall = {'1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0, '7': 0.0}
racial_fractions_deserts = {'1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0, '7': 0.0}


with col2:
    census_df = State.get_census_data(level='blockgroup')
    census_df['racial_majority'] = census_df['racial_majority'].astype(str)

    fig = go.Figure()
    fig, bounds = State.plot_state_boundary(fig)

    for i in range(1, 8):
        if len(census_df[census_df['racial_majority'] == str(i)]) > 0:
            racial_fractions_overall[str(i)] = len(census_df[census_df['racial_majority'] == str(i)]) / len(census_df)

            census_df_i = census_df[census_df['racial_majority'] == str(i)]
            fig.add_trace(go.Scattergeo(name=racial_label_dict[i],
                                        lon=census_df_i['Longitude'],
                                        lat=census_df_i['Latitude'],
                                        marker=dict(
                                            size=4,
                                            color=scatter_palette[i - 1],
                                            opacity=0.6,
                                            line=dict(width=1.0,
                                                      color='rgba(0, 0, 0, 0.9)',
                                                      ))))
        else:
            racial_fractions_overall[str(i)] = 0.0

    # Add title to the figure
    fig.update_layout(
        title={
            'text': "Census blockgroups by <br> racial majority in " + state_name,
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
    )

    fig.update_geos(
        showland=False,
        showcoastlines=False,
        showframe=False,
        showocean=False,
        showcountries=False,
        lonaxis_range=[bounds[0], bounds[2]],
        lataxis_range=[bounds[1], bounds[3]],
        projection_type='mercator',
        bgcolor='#a1b8b7',
    )

    fig.update_layout(
        showlegend=True,
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        width=4000,
        autosize=True,
        coloraxis_showscale=False,
        xaxis=dict(visible=False, showgrid=False, showline=False),
        yaxis=dict(visible=False, showgrid=False, showline=False),
        uirevision='noloss',
        legend=dict(
            title='Racial majority',
            title_font=dict(size=12),
            itemsizing='constant',
            x=0.02,
            y=0.05,
            orientation='v',
            font=dict(size=12,),
            bgcolor='rgba(255,255,255,0.5)',  # Semi-transparent white background
            bordercolor=None,
            borderwidth=1,
        )
    )
    # voronoi_color = '#0b0a17'

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

poverty_threshold = st.sidebar.slider(r'Choose poverty threshold $p$%', min_value=0, max_value=100, value=30, step=5)
distance_threshold = st.sidebar.slider(r'Choose distance threshold $n$ miles', min_value=0.0, max_value=30.0, value=5.0, step=0.5, format='%.1f')

with col3:
    census_df = State.get_census_data(level='blockgroup')
    census_df['racial_majority'] = census_df['racial_majority'].astype(str)

    fig = go.Figure()
    fig, bounds = State.plot_state_boundary(fig)

    desert_df = census_df[census_df['below_poverty'] >= poverty_threshold]
    # desert_df = desert_df[desert_df['Closest_Distance_Pharmacies'] >= distance_threshold]
    desert_df = desert_df[desert_df['Closest_Distance_Urgent_Care_Centers'] >= distance_threshold]
    # desert_df['racial_majority'] = desert_df['racial_majority'].astype(str)

    for i in range(1, 8):
        if len(desert_df[desert_df['racial_majority'] == str(i)]) > 0:
            racial_fractions_deserts[str(i)] = len(desert_df[desert_df['racial_majority'] == str(i)]) / len(desert_df)

            desert_df_i = desert_df[census_df['racial_majority'] == str(i)]
            fig.add_trace(go.Scattergeo(name=racial_label_dict[i],
                                        lon=desert_df_i['Longitude'],
                                        lat=desert_df_i['Latitude'],
                                        marker=dict(
                                            # size=8,
                                            color=scatter_palette[i - 1],
                                            opacity=0.6,
                                            line=dict(width=1.0,
                                                      color='rgba(0, 0, 0, 0.9)',
                                        ))))
        else:
            racial_fractions_deserts[str(i)] = 0.0

    # Add title to the figure
    fig.update_layout(
        title={
            'text': "Blockgroups classified as <br> medical deserts in " + state_name,
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
    )

    fig.update_geos(
        showland=False,
        showcoastlines=False,
        showframe=False,
        showocean=False,
        showcountries=False,
        lonaxis_range=[bounds[0], bounds[2]],
        lataxis_range=[bounds[1], bounds[3]],
        projection_type='mercator',
        bgcolor='#a1b8b7',
    )

    fig.update_layout(
        showlegend=True,
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        width=4000,
        autosize=True,
        coloraxis_showscale=False,
        xaxis=dict(visible=False, showgrid=False, showline=False),
        yaxis=dict(visible=False, showgrid=False, showline=False),
        uirevision='noloss',
        legend=dict(
            title='Racial majority \n',
            title_font=dict(size=12),
            itemsizing='constant',
            x=0.02,
            y=0.05,
            orientation='v',
            font=dict(size=12,),
            bgcolor='rgba(255,255,255,0.5)',  # Semi-transparent white background
            bordercolor=None,
            borderwidth=1,
        )
    )
    # voronoi_color = '#0b0a17'

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})


def get_perecentage_string(fraction):
    return f'{fraction * 100:.2f}%'


for i in range(1, 7):
    more_than_10_percent = (racial_fractions_deserts[str(i)] - racial_fractions_overall[str(i)]) > 0.10
    more_than_3_times = racial_fractions_deserts[str(i)] > 3 * racial_fractions_overall[str(i)]
    more_than_1_20_times = racial_fractions_deserts[str(i)] > 1.2 * racial_fractions_overall[str(i)]

    if (more_than_10_percent and more_than_1_20_times) or more_than_3_times:
        overall_percent = get_perecentage_string(racial_fractions_overall[str(i)])
        desert_percent = get_perecentage_string(racial_fractions_deserts[str(i)])
        racial_label = racial_label_dict[i]
        st.write(racial_label + ' population may be disproportionately affected by pharmacy deserts in ' + state_name
                 + ' compared to the overall population. ' + desert_percent + ' of pharmacy deserts are majority '
                 + racial_label + ' while only ' + overall_percent + ' of all blockgroups are majority ' + racial_label + '.')


st.sidebar.write('Data for pharmacies is from the HIFLD Open Data database from 2005-10. '
         'Data for census blockgroups is from the US Census Bureau, 2022.')

# fig = src.plot.update_plotly_figure_layout(fig, bounds)

# shapefile_df = State.get_shapefiles(level='county').to_crs(projection_north_america)
# usa_shapefile_df = gpd.read_file('data/usa/shapefiles/north_america_political_boundaries/Political_Boundaries__Area_.shp')
# usa_shapefile_df.to_crs(projection_north_america, inplace=True)
#
# bounds = shapefile_df.total_bounds
#
# x_span = bounds[2] - bounds[0]
# y_span = bounds[3] - bounds[1]
# x_pad = x_span * 0.03
# y_pad = y_span * 0.03
#
# bounds[0], bounds[2] = bounds[0] - x_pad, bounds[2] + x_pad
# bounds[1], bounds[3] = bounds[1] - y_pad, bounds[3] + y_pad
#
# if state_name == 'Alaska':
#     bounds[0] = -180
#     bounds[2] = -130
#
# usa_shapefile_df = usa_shapefile_df.cx[bounds[0] - 2*x_pad: bounds[2] + 2*x_pad, bounds[1] - 2*y_pad: bounds[3] + 2*y_pad]
#
# # Create Plotly figure
# fig = go.Figure()
#
# # color='#ebe9ce'
#
# # Add shapefile to the figure
# for _, row in usa_shapefile_df.iterrows():
#     geom = row.geometry
#     if geom.geom_type == 'Polygon' or geom.geom_type == 'MultiPolygon':
#         if geom.geom_type == 'Polygon':
#             polygons = [geom]
#         else:  # Handle MultiPolygon
#             polygons = geom.geoms
#
#         for polygon in polygons:
#             x, y = polygon.exterior.coords.xy
#             x = list(x)
#             y = list(y)
#             if polygon.contains(Point(-130, 30)):
#                 # Create a trace for the Polygon
#                 trace = go.Scattergeo(lon=x, lat=y, mode='lines', fill='toself', fillcolor='#a1b8b7',
#                                       name=None, showlegend=False, line=dict(width=0.0, color='white'))
#                 # Add the trace to the figure
#                 fig.add_trace(trace)
#             else:
#                 # Create a trace for the Polygon
#                 trace = go.Scattergeo(lon=x, lat=y, mode='lines', fill='toself', fillcolor='#FBFCF9',
#                                       name=None, showlegend=False, line=dict(width=0.0, color='#ebe9ce'))
#                 # Add the trace to the figure
#                 fig.add_trace(trace)
#
#
# # Add shapefile to the figure
# for _, row in shapefile_df.iterrows():
#     geom = row.geometry
#     if geom.geom_type == 'Polygon' or geom.geom_type == 'MultiPolygon':
#         if geom.geom_type == 'Polygon':
#             polygons = [geom]
#         else:  # Handle MultiPolygon
#             polygons = geom.geoms
#
#         for polygon in polygons:
#             x, y = polygon.exterior.coords.xy
#             x = list(x)
#             y = list(y)
#             # Create a trace for the Polygon
#             trace = go.Scattergeo(lon=x, lat=y, mode='lines', name=None, showlegend=False,
#                                   line=dict(width=0.5, color='white'), hovertext=row['NAMELSAD'],
#                                   fillcolor='#FAF3E0', fill='toself')
#                                   # fillcolor='#fdf6e6', fill='toself')
#             # Add the trace to the figure
#             fig.add_trace(trace)
#
#
# # Add shapefile to the figure
# for _, row in usa_shapefile_df.iterrows():
#     geom = row.geometry
#     if geom.geom_type == 'Polygon' or geom.geom_type == 'MultiPolygon':
#         if geom.geom_type == 'Polygon':
#             polygons = [geom]
#         else:  # Handle MultiPolygon
#             polygons = geom.geoms
#
#         for polygon in polygons:
#             x, y = polygon.exterior.coords.xy
#             x = list(x)
#             y = list(y)
#             if polygon.contains(Point(-130, 30)):
#                 # Create a trace for the Polygon
#                 trace = go.Scattergeo(lon=x, lat=y, mode='lines', fill='none',
#                                       line=dict(width=0.0, color='white'), name=None, showlegend=False)
#                 # Add the trace to the figure
#                 fig.add_trace(trace)
#             else:
#                 # Create a trace for the Polygon
#                 trace = go.Scattergeo(lon=x, lat=y, mode='lines', fill='none',
#                                       line=dict(width=1.0, color='gray'), name=None, showlegend=False)
#                 # Add the trace to the figure
#                 fig.add_trace(trace)
