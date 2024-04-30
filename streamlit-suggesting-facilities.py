from datetime import datetime
import geopandas as gpd
import plotly.graph_objects as go
import random
import pandas as pd
from src.constants import MILES_TO_KM
from src.usa.constants import state_names, racial_label_dict
from src.usa.states import USAState
from src.usa.facilities_data_handler import (
    CVS, Walgreens, Walmart, UrgentCare, Hospitals, DialysisCenters, NursingHomes,
    ChildCare, PrivateSchools, FDICInsuredBanks, DHL, UPS, FedEx)
import streamlit as st
import streamlit_antd_components as sac
from streamlit_extras.switch_page_button import switch_page


scatter_palette = [
    '#007fee',          # Blue
    '#21d565',          # Green
    '#ffe00a',          # Yellow
    '#ff7700',          # Orange
    '#8bff08',          # Lime
    '#9918fe',          # Purple
    '#ff0004',          # Red
    '#179c49',          # Dark Green
    '#00318f',          # Dark Blue
    '#ff1f70',          # Pink
    '#af7b00',          # Brown
    '#ff517c',          # Light Pink
    '#d36969',          # Light Red
    '#18fe90'           # Light Green
]

st.set_page_config(layout='centered', initial_sidebar_state='expanded')

st.sidebar.caption('This tool aims to identify potentially vulnerable areas in the US with low access to '
                   'various critical facilities. We define these areas by high poverty rates and large distances '
                   'to facilities. You can choose the distance threshold and poverty rate to identify these areas.')


k = st.slider('Number of facilities', 20, 400, 174, 1)

# Get the current day of the year

state_name = 'Mississippi'
State = USAState(state_name)
state_fips = State.fips
state_abbr = State.abbreviation

open_facilities = pd.read_csv('.local/suggesting-facilities-experiment/mississippi_facility_location_results.csv')
# st.write(open_facilities_list)

census_df = State.get_census_data(level='blockgroup')
census_df['racial_majority'] = census_df['racial_majority'].astype(str)
n = len(census_df)
f = len(open_facilities)

longitudes = []
latitudes = []

for i in list(open_facilities['0']):
    longitudes.append(census_df.iloc[i]['Longitude'])
    latitudes.append(census_df.iloc[i]['Latitude'])

# open_facilities = gpd.GeoDataFrame(open_facilities, geometry=gpd.points_from_xy(open_facilities['Longitude'], open_facilities['Latitude']))
# st.write(open_facilities)

# st.write(open_facilities.geometry.x)
# st.write(open_facilities.geometry.y)

fig = go.Figure()
fig, bounds = State.plot_state_boundary(fig)


fig.add_trace(go.Scattergeo(lon=longitudes[:k], lat=latitudes[:k], mode='markers',
                            marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                            name='Suggested facility', showlegend=True))


randomly_shuffled_indices = list(range(1, 8))
random.shuffle(randomly_shuffled_indices)

config = {
    'modeBarButtonsToRemove': ['zoomOut', 'select2d'],
    'staticPlot': False,
    'scrollZoom': True,
}

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
    margin=dict(l=0, r=0, t=0, b=0),
    autosize=True,
    # title=dict(text=f'{state_name} - Suggested ' + str(k) + ' Facilities', y = 0),
    xaxis=dict(range=[bounds[0], bounds[2]], autorange=False),
    yaxis=dict(range=[bounds[1], bounds[3]], autorange=False),
    showlegend=True,
    legend=dict(
        itemsizing='constant',
        x=0.02,
        y=1.00,
        orientation='v',
        bgcolor='rgba(255,255,255,0.5)',
    )
)

st.plotly_chart(fig, use_container_width=True, config=config)
