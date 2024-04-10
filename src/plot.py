"""
This module contains functions for plotting data on a Plotly figure.
"""
from src.constants import *
import plotly.graph_objs as go
import geopandas as gpd
from typing import List, Union
from shapely.geometry import Point


def plotly_layer_from_shapefile(fig, shapefile_df,
                                landcolor='#FAF3E0', watercolor='#a1b8b7',
                                waterbody_points=None,
                                linecolor='gray', linewidth=0.0,
                                name=None, showlegend=False):
    """
    Add a shapefile layer to a Plotly figure.
    :param fig: Plotly figure
    :param shapefile_df: Shapefile dataframe
    :param landcolor: Color for land areas
    :param watercolor: Color for water areas
    :param waterbody_points: List of points that are in water bodies
    :param linecolor: Color for the lines
    :param linewidth: Width of the lines
    :param name: Name of the layer
    :param showlegend: Whether to show the legend
    :return: Plotly figure
    """
    if waterbody_points is None:
        waterbody_points = []

    for _, row in shapefile_df.iterrows():
        geom = row.geometry
        if geom.geom_type == 'Polygon' or geom.geom_type == 'MultiPolygon':
            if geom.geom_type == 'Polygon':
                polygons = [geom]
            else:
                polygons = geom.geoms

            for polygon in polygons:
                x, y = polygon.exterior.coords.xy
                x = list(x)
                y = list(y)
                if any(polygon.contains(Point(point)) for point in waterbody_points):
                    fillcolor = watercolor
                else:
                    fillcolor = landcolor

                if fillcolor is None:
                    # Create a trace for the Polygon
                    trace = go.Scattergeo(lon=x, lat=y, mode='lines', fill='none',
                                          line=dict(width=linewidth, color=linecolor),
                                          name=None, showlegend=False)
                else:
                    # Create a trace for the Polygon
                    trace = go.Scattergeo(lon=x, lat=y, mode='lines', fill='toself', fillcolor=fillcolor,
                                          name=None, showlegend=showlegend,
                                          line=dict(width=linewidth, color=linecolor))
                # Add the trace to the figure
                fig.add_trace(trace)

    return fig


def plot_primary_land_layer(fig, shapefile_df):
    """
    Plot the primary land layer. All land areas are colored in a light yellow color.
    :param fig: Plotly figure
    :param shapefile_df: Shapefile for the primary land layer. All polygons/multipolygons in the shapefile are plotted as land areas.
    :return: Plotly figure
    """
    fig = plotly_layer_from_shapefile(fig, shapefile_df, landcolor='#FAF3E0', watercolor='#a1b8b7',
                                      linecolor='white', linewidth=0.5)
    return fig


def plot_secondary_land_layer(fig, shapefile_df, waterbody_points=None):
    """
    Plot the secondary land layer. All land areas are colored in off white color.
    :param fig: Plotly figure
    :param shapefile_df: Shapefile for the secondary land layer. All polygons/multipolygons in the shapefile are plotted as land areas.
    :return: Plotly figure
    """
    fig = plotly_layer_from_shapefile(fig, shapefile_df, landcolor='#fbfcf9', watercolor='#a1b8b7',
                                      waterbody_points=waterbody_points,
                                      linecolor='gray', linewidth=0.5,
                                      name=None, showlegend=False)

    return fig


def plot_boundaries(fig, shapefile_df):
    """
    Plot the boundaries of the shapefile.
    :param fig: Plotly figure
    :param shapefile_df: Shapefile dataframe
    :return: Plotly figure
    """
    fig = plotly_layer_from_shapefile(fig, shapefile_df, landcolor=None, watercolor=None,
                                      linecolor='gray', linewidth=0.5,
                                      name=None, showlegend=False)

    return fig


def update_plotly_figure_layout(fig, bounds):
    """
    Update the layout of the Plotly figure.
    :param fig: Plotly figure
    :return: Plotly figure
    """
    fig.update_geos(
        lonaxis_range=[bounds[0], bounds[2]],
        lataxis_range=[bounds[1], bounds[3]],
    )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},
                      autosize=True,
                      # width=4000,
                      plot_bgcolor='#a1b8b7',
                      paper_bgcolor='#a1b8b7',
                      coloraxis_showscale=False,
                      xaxis=dict(visible=False, showgrid=False, showline=False),
                      yaxis=dict(visible=False, showgrid=False, showline=False),
                      geo=dict(
                          showland=False,
                          showcoastlines=False,
                          showframe=False,
                          lonaxis_range=[bounds[0], bounds[2]],
                          lataxis_range=[bounds[1], bounds[3]],
                          bgcolor='#a1b8b7',
                      ),
                      uirevision='noloss',
                      showlegend=False,
                      legend=dict(
                          title='Categories \n',
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

    return fig



# def plot_shapefile(fig: go.Figure,
#                    shapefile_df: gpd.GeoDataFrame,
#                    bounds: List[float]=None, x_pad: float=None, y_pad: float=None,
#                    draw_boundary: bool=False,
#                    color_water: bool=False,
#                    waterbody_points: List[Point]=None,
#                    color_land: bool=False,
#                    is_primary: bool=False):
#     """Plot a shapefile on a Plotly figure
#
#     Args:
#         fig (plotly.graph_objs._figure.Figure): Plotly figure
#         shapefile_df (geopandas.geodataframe.GeoDataFrame): Shapefile dataframe
#         bounds (list): Bounds of the shapefile
#         x_pad (float): Padding in the x-direction
#         y_pad (float): Padding in the y-direction
#         draw_boundary (bool): Whether to draw the boundary
#         color_water (bool): Whether to color the water
#         waterbody_points (list): List of waterbody points
#         color_land (bool): Whether to color the land
#         primary_states (list): List of states to color as primary
#     Returns:
#         None
#     """
#     if plot_boundary:
#         linewidth = 1.0
#     else:
#         linewidth = 0.0
#
#     if waterbody_points is None:
#         waterbody_points = []
#
#     # If bounds are not provided, use the bounds of the shapefile
#     if bounds is None:
#         bounds = shapefile_df.total_bounds
#     if x_pad is None:
#         x_span = bounds[2] - bounds[0]
#         x_pad = x_span * 0.05
#     if y_pad is None:
#         y_span = bounds[3] - bounds[1]
#         y_pad = y_span * 0.05
#
#     shapefile_df = shapefile_df.cx[bounds[0] - x_pad: bounds[2] + x_pad, bounds[1] - y_pad: bounds[3] + y_pad]
#
#     # Add shapefile to the figure
#     for _, row in shapefile_df.iterrows():
#         geom = row.geometry
#         if geom.geom_type == 'Polygon' or geom.geom_type == 'MultiPolygon':
#             if geom.geom_type == 'Polygon':
#                 polygons = [geom]
#             else:  # Handle MultiPolygon
#                 polygons = geom.geoms
#
#             for polygon in polygons:
#                 x, y = polygon.exterior.coords.xy
#                 x = list(x)
#                 y = list(y)
#                 if plot_fill is False:
#                     trace = go.Scattergeo(lon=x, lat=y, mode='lines',
#                                           name=None, showlegend=False,
#                                           line=dict(width=linewidth, color=BOUNDARY_COLOR))
#                 else:
#                     if is_primary:
#                         color = LAND_COLOR_PRIMARY
#                     else:
#                         color = LAND_COLOR_SECONDARY
#                     for point in waterbody_points:
#                         if polygon.contains(point):
#                             color = WATERBODY_COLOR
#                             break
#
#                     trace = go.Scattergeo(lon=x, lat=y, mode='lines',
#                                           fill='toself', fillcolor=color,
#                                           name=None, showlegend=False,
#                                           line=dict(width=linewidth, color=BOUNDARY_COLOR))
#
#                 # Add the trace to the figure
#                 fig.add_trace(trace)
#
#     return
#
