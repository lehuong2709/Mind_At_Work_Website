from src.constants import *
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shapely.geometry import Point
import streamlit as st
from PIL import Image
import base64
from io import BytesIO
# import kaleido

st.set_page_config(layout="wide")

col1, col2 = st.columns([1, 1])

with col1:
    # st.write('\n', fontsize=10)
    fig2 = go.Figure()
    # Read your image
    image_path = 'notebooks/fig_modified.png'
    with Image.open(image_path) as img:
    # Convert the image to base64 for embedding
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        encoded_image = base64.b64encode(buffered.getvalue()).decode('utf-8')


    # Add the image using fig.add_image
    fig2.add_image(
        source='data:image/png;base64,' + encoded_image,
        opacity=1,
    )

    fig2.update_layout(
            margin=dict(l=0, r=0, b=0, t=0),
            xaxis=dict(visible=False, showgrid=False, showline=False),
            yaxis=dict(visible=False, showgrid=False, showline=False),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )

    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
        # st.image('fig_modified.png', use_column_width=True)


shapefile_df = gpd.read_file('../data/usa/shapefiles/12_county_shapefile.shp').set_crs(projection_north_america)
census_df = pd.read_csv('../data/usa/census/12_census_blockgroup_data.csv')

usa_shapefile_df = gpd.read_file(
    '../data/usa/shapefiles/north_america_political_boundaries/Political_Boundaries__Area_.shp')
usa_shapefile_df.to_crs(projection_wgs84, inplace=True)

bounds = shapefile_df.total_bounds

x_span = bounds[2] - bounds[0]
y_span = bounds[3] - bounds[1]
x_pad = x_span * 0.03
y_pad = y_span * 0.03

bounds[0], bounds[2] = bounds[0] - x_pad, bounds[2] + x_pad
bounds[1], bounds[3] = bounds[1] - y_pad, bounds[3] + y_pad

usa_shapefile_df = usa_shapefile_df.cx[bounds[0] - 2*x_pad: bounds[2] + 2*x_pad, bounds[1] - 2*y_pad: bounds[3] + 2*y_pad]

# Create Plotly figure
fig = go.Figure()

# Add shapefile to the figure
for _, row in usa_shapefile_df.iterrows():
    geom = row.geometry
    if geom.geom_type == 'Polygon' or geom.geom_type == 'MultiPolygon':
        if geom.geom_type == 'Polygon':
            polygons = [geom]
        else:  # Handle MultiPolygon
            polygons = geom.geoms

        for polygon in polygons:
            x, y = polygon.exterior.coords.xy
            x = list(x)
            y = list(y)
            if polygon.contains(Point(-130, 30)):
                # Create a trace for the Polygon
                trace = go.Scattergeo(lon=x, lat=y, mode='lines', fill='toself', fillcolor='#a1b8b7',
                                      line=dict(width=0.0, color='white'), name=None, showlegend=False)
                # Add the trace to the figure
                fig.add_trace(trace)
            else:
                # Create a trace for the Polygon
                trace = go.Scattergeo(lon=x, lat=y, mode='lines', fill='toself', fillcolor='#FBFCF9',
                                      line=dict(width=1.0, color='#ebe9ce'), name=None, showlegend=False)
                # Add the trace to the figure
                fig.add_trace(trace)

# Add shapefile to the figure
for _, row in shapefile_df.iterrows():
    geom = row.geometry
    if geom.geom_type == 'Polygon' or geom.geom_type == 'MultiPolygon':
        if geom.geom_type == 'Polygon':
            polygons = [geom]
        else:  # Handle MultiPolygon
            polygons = geom.geoms

        for polygon in polygons:
            x, y = polygon.exterior.coords.xy
            x = list(x)
            y = list(y)
            # Create a trace for the Polygon
            trace = go.Scattergeo(lon=x, lat=y, mode='lines', name=None, showlegend=False,
                                  line=dict(width=0.5, color='white'), hovertext=row['NAMELSAD'],
                                  fillcolor='#fdf6e6', fill='toself')
            # Add the trace to the figure
            fig.add_trace(trace)


# Create a slider in the Streamlit sidebar for the threshold
threshold = st.sidebar.slider('Threshold', min_value=0, max_value=100, value=10, step=5)

# census_df = census_df.head(threshold)

# Filter DataFrame based on a threshold (dynamic layer)
census_df = census_df[census_df['below_poverty'] > threshold]
#
# def find_empty_location(df, lat_col, lon_col):
#     """
#     This function finds the first empty location in the dataframe. The first empty location is the first row where the
#     latitude and longitude are empty.
#     :param df: The dataframe that contains the latitude and longitude columns
#     :param lat_col: The name of the column that contains the latitude
#     :param lon_col: The name of the column that contains the longitude
#     :return: The index of the first empty location
#     """
#     return df[(df[lat_col].isnull()) | (df[lon_col].isnull())].index[0]

census_df['racial_majority'] = census_df['racial_majority'].astype(str)

color_cycle_new = ['#ff823f', '#2e6a65', '#5d366f', '#010349', '#cb595b', '#5c98cc', '#fff08a']
# colors:          orange,   green,   purple,   navy,     red,      blue,     yellow

for i in range(1, 8):
    if len(census_df[census_df['racial_majority'] == str(i)]) > 0:
        census_df_i = census_df[census_df['racial_majority'] == str(i)]
        fig.add_trace(px.scatter_geo(census_df_i, lon='Longitude', lat='Latitude',
                                     color='racial_majority', color_discrete_map={str(i): color_cycle_new[i - 1]}, opacity=0.7,
                                     width=0,
                                     # size='below_poverty', size_max=10,
                                     projection='mercator', basemap_visible=False,
                                     ).data[0])

fig.update_geos(showland=False, showcoastlines=False, showframe=False)

# Add ranges for latitude and longitude
fig.update_geos(
    lonaxis_range=[bounds[0], bounds[2]],
    lataxis_range=[bounds[1], bounds[3]],
)

fig.update_layout(showlegend=True,
                  margin={"r": 0, "t": 0, "l": 0, "b": 0},
                  # paper_bgcolor='lightblue',
                  # plot_bgcolor='lightblue',
                  coloraxis_showscale=False,
                  xaxis=dict(visible=False, showgrid=False, showline=False, rangeslider=dict(visible=True)),
                  yaxis=dict(visible=False, showgrid=False, showline=False),
                  geo=dict(
                      showland=False,
                      showcountries=False,
                      showocean=False,
                      showcoastlines=False,
                      projection_type='mercator',
                      bgcolor='#a1b8b7',
                  ),
                  uirevision='noloss',
                  legend=dict(
                      title='Categories \n',
                      title_font=dict(  # Adjusting the legend title font size
                          size=12  # Specify your desired font size here
                      ),
                      itemsizing = 'constant',
                        x = 0.02,
                        y = 0.05,
                      # x=0.01,  # Adjust for horizontal position
                      # y=0.,  # Adjust for vertical position
                      orientation='v',
                      font=dict(
                          size=12,
                      ),
                      bgcolor='rgba(255,255,255,0.5)',  # Semi-transparent white background
                      bordercolor=None,
                      borderwidth=1,

                  )
                  )

color_cycle_new = ['#2e6a65', '#ff823f', '#5d366f', '#010349', '#cb595b', '#5c98cc', '#fff08a']
# colors:          green,   orange,   purple,   navy,     red,      blue,     yellow

voronoi_color = '#0b0a17'

with col2:
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})

#%%
