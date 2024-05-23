from datetime import datetime
import geopandas as gpd
import plotly.graph_objects as go
import random
from src.constants import MILES_TO_KM, scatter_palette, facility_palette
from src.usa.constants import state_names, populous_states
from src.usa.states import USAState
from src.usa.facilities_data_handler import (
    CVS, Walgreens, Walmart, UrgentCare, Hospitals, DialysisCenters, NursingHomes,
    ChildCare, PrivateSchools, FDICInsuredBanks, DHL, UPS, FedEx)
import streamlit as st
import streamlit_antd_components as sac
from streamlit_extras.switch_page_button import switch_page
import pandas as pd
from utils import desert_types, get_message, distance_labels, show_location_labels, show_voronoi_labels, voronoi_file_names


racial_labels = ['white_alone', 'black_alone', 'aian_alone',
                 'asian_alone', 'nhopi_alone', 'hispanic', 'other']
colors = {racial_labels[i]: scatter_palette[i] for i in range(len(racial_labels))}

# Set the page configuration
st.set_page_config(layout='centered', initial_sidebar_state='expanded')

st.sidebar.caption('This tool aims to identify potentially vulnerable areas in the US with low access to '
                   'various critical facilities. We define these areas by high poverty rates and large distances '
                   'to facilities. You can choose the distance threshold and poverty rate to identify these areas.')


def get_state_of_the_day(list_of_states):
    day_of_year = datetime.now().timetuple().tm_yday
    state_of_the_day = populous_states[day_of_year % len(list_of_states)]
    index = state_names.index(state_of_the_day)
    return index


facilities = ['Pharmacy chains', 'Urgent care centers', 'Hospitals', 'Nursing homes', 'Private schools',
              'Banks', 'Child care centers', 'Logistics chains']

with st.sidebar:
    facility = st.selectbox('Choose a facility', facilities)
    index = get_state_of_the_day(populous_states)
    state_name = st.selectbox('Choose a US state', options=state_names, index=index)

desert_type = desert_types[facility]

State = USAState(state_name)
state_fips = State.fips
state_abbr = State.abbreviation

st.markdown("""
    <h1 style="font-size: 40px; text-align: center; margin-bottom: 0em; line-height: 1.0;">
        """ + desert_type + """ deserts in
        <span style="color: #c41636">
            """ + state_name + """
        </span>
    </h1>
    <h3 style="font-size: 18px; text-align: center; margin-top: 0em;">
        Based on distances to <span style="color: #c41636">""" + str(facility.lower()) + """</span>
    </h3>
    <br>
    """, unsafe_allow_html=True)

st.markdown(
    get_message(facility),
    unsafe_allow_html=True
)

with st.sidebar:
    with st.container(border=True):
        poverty_threshold = st.slider(r'Choose poverty threshold $p$%', min_value=0, max_value=100, value=20, step=5, key='poverty_threshold')

    with st.container(border=True):
        urban_rural = st.checkbox('Use separate urban/rural distances', value=True)
        if urban_rural:
            col_side1, col_side2 = st.columns(2)
            urban_distance_threshold = col_side1.slider(r'Choose urban distance threshold $n$ miles', min_value=0.0, max_value=15.0, value=2.0, step=0.5, key='urban_distance_threshold')
            urban_distance_threshold = MILES_TO_KM * urban_distance_threshold
            rural_distance_threshold = col_side2.slider(r'Choose rural distance threshold $n$ miles', min_value=0.0, max_value=30.0, value=8.0, step=1.0, key='rural_distance_threshold')
            rural_distance_threshold = MILES_TO_KM * rural_distance_threshold
        else:
            distance_threshold = st.slider(r'Choose distance threshold $n$ miles', min_value=0.0, max_value=25.0, value=3.0, step=0.5, key='distance_threshold')
            distance_threshold = MILES_TO_KM * distance_threshold

col1, col2 = st.columns([3, 2], gap='medium')

with col2:
    with st.expander('Figure options'):
        show_deserts = st.checkbox('Show ' + desert_type.lower() + ' deserts', value=True)
        show_facility_locations = st.checkbox(show_location_labels[facility], value=False)
        if show_voronoi_labels[facility] is not None:
            show_voronoi_cells = st.checkbox(show_voronoi_labels[facility], value=False)


def plot_state_boundary(fig, state_abbreviation):
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

    return fig


def get_bounds(state_name, blockgroup_df):
    min_x = blockgroup_df['Longitude'].min()
    max_x = blockgroup_df['Longitude'].max()
    min_y = blockgroup_df['Latitude'].min()
    max_y = blockgroup_df['Latitude'].max()

    x_span = max_x - min_x
    y_span = max_y - min_y
    x_pad = x_span * 0.05
    y_pad = y_span * 0.05

    bounds = [min_x, min_y, max_x, max_y]

    bounds[0], bounds[2] = bounds[0] - x_pad, bounds[2] + x_pad
    bounds[1], bounds[3] = bounds[1] - y_pad, bounds[3] + y_pad

    if state_name == 'Alaska':
        bounds[0] = -180
        bounds[2] = -125
        bounds[3] = bounds[3] + y_pad

    if state_name == 'Hawaii':
        bounds[0] = -162
        bounds[3] = 23

    return bounds


with col1:
    census_df = State.get_census_data(level='blockgroup')

    fig = go.Figure()
    fig = plot_state_boundary(fig, state_abbr)
    bounds = get_bounds(state_name, census_df)

    racial_fractions_overall = {racial_label: 0.0 for racial_label in racial_labels}
    racial_fractions_deserts = {racial_label: 0.0 for racial_label in racial_labels}

    distance_label = distance_labels[facility]

    if not urban_rural:
        desert_df = census_df[(census_df['below_poverty'] >= poverty_threshold) & (census_df[distance_label] >= distance_threshold)]
    else:
        desert_df = census_df[((census_df['below_poverty'] >= poverty_threshold) & (census_df['urban']) & (census_df[distance_label] >= urban_distance_threshold)) |
                              ((census_df['below_poverty'] >= poverty_threshold) & (~census_df['urban']) & (census_df[distance_label] >= rural_distance_threshold))]

    random.shuffle(racial_labels)

    for racial_label in racial_labels:
        census_df_label = census_df[census_df['racial_majority'] == racial_label]
        racial_fractions_overall[racial_label] = len(census_df_label)/len(census_df)

        desert_df_label = desert_df[desert_df['racial_majority'] == racial_label]
        if len(desert_df_label) > 0:
            racial_fractions_deserts[racial_label] = len(desert_df_label)/len(desert_df)
            if show_deserts:
                fig.add_trace(
                    go.Scattergeo(
                        name=racial_label.split('_')[0].capitalize(),
                        lon=desert_df_label['Longitude'], lat=desert_df_label['Latitude'],
                        marker=dict(
                            color=colors[racial_label], opacity=0.6, line=dict(width=1.0, color='rgba(0, 0, 0, 0.9)'),
                        )
                    ))

    if facility == 'Pharmacy chains':
        if show_facility_locations:
            cvs = CVS.read_abridged_facilities()
            cvs = gpd.clip(cvs, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=cvs.geometry.x, lat=cvs.geometry.y, mode='markers',
                                        marker=dict(size=4, color='#8b0000', opacity=0.8, symbol='x'),
                                        name='CVS', showlegend=True))

            walgreens = Walgreens.read_abridged_facilities()
            walgreens = gpd.clip(walgreens, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=walgreens.geometry.x, lat=walgreens.geometry.y, mode='markers',
                                        marker=dict(size=4, color='#006400', opacity=0.8, symbol='x'),
                                        name='Walgreens', showlegend=True))

            walmart = Walmart.read_abridged_facilities()
            walmart = gpd.clip(walmart, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=walmart.geometry.x, lat=walmart.geometry.y, mode='markers',
                                        marker=dict(size=4, color='#00008b', opacity=0.8, symbol='x'),
                                        name='Walmart', showlegend=True))
    elif facility == 'Urgent care centers':
        if show_facility_locations:
            urgent_care_centers = UrgentCare.read_abridged_facilities()
            urgent_care_centers = gpd.clip(urgent_care_centers, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=urgent_care_centers.geometry.x, lat=urgent_care_centers.geometry.y, mode='markers',
                                        marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                                        name='Urgent care center', showlegend=True))
    elif facility == 'Hospitals':
        if show_facility_locations:
            hospitals = Hospitals.read_abridged_facilities()
            hospitals = gpd.clip(hospitals, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=hospitals.geometry.x, lat=hospitals.geometry.y, mode='markers',
                                        marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                                        name='Hospital', showlegend=True))
    elif facility == 'Nursing homes':
        if show_facility_locations:
            nursing_homes = NursingHomes.read_abridged_facilities()
            nursing_homes = gpd.clip(nursing_homes, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=nursing_homes.geometry.x, lat=nursing_homes.geometry.y, mode='markers',
                                        marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                                        name='Nursing home', showlegend=True))
    elif facility == 'Private schools':
        if show_facility_locations:
            private_schools = PrivateSchools.read_abridged_facilities()
            private_schools = gpd.clip(private_schools, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=private_schools.geometry.x, lat=private_schools.geometry.y, mode='markers',
                                        marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                                        name='Private school', showlegend=True))
    elif facility == 'Banks':
        if show_facility_locations:
            banks = FDICInsuredBanks.read_abridged_facilities()
            banks = gpd.clip(banks, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=banks.geometry.x, lat=banks.geometry.y, mode='markers',
                                        marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                                        name='Bank', showlegend=True))
    elif facility == 'Child care centers':
        if show_facility_locations:
            child_care_centers = ChildCare.read_abridged_facilities()
            child_care_centers = gpd.clip(child_care_centers, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=child_care_centers.geometry.x, lat=child_care_centers.geometry.y, mode='markers',
                                        marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                                        name='Child care center', showlegend=True))
    elif facility == 'Logistics chains':
        dhl_color = '#8b1e2b'
        ups_color = '#521801'
        fedex_color = '#cc4700'
        if show_facility_locations:
            fedex = FedEx.read_abridged_facilities()
            fedex = gpd.clip(fedex, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=fedex.geometry.x, lat=fedex.geometry.y, mode='markers',
                                        marker=dict(size=4, color=fedex_color, opacity=0.8, symbol='x'),
                                        name='FedEx', showlegend=True))
            dhl = DHL.read_abridged_facilities()
            dhl = gpd.clip(dhl, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=dhl.geometry.x, lat=dhl.geometry.y, mode='markers',
                                        marker=dict(size=4, color=dhl_color, opacity=0.8, symbol='x'),
                                        name='DHL', showlegend=True))
            ups = UPS.read_abridged_facilities()
            ups = gpd.clip(ups, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=ups.geometry.x, lat=ups.geometry.y, mode='markers',
                                        marker=dict(size=4, color=ups_color, opacity=0.8, symbol='x'),
                                        name='UPS', showlegend=True))

    if show_voronoi_cells:
        voronoi_df = gpd.read_file(voronoi_file_names[facility] + state_fips + '_voronoi.shp', index=False)
        for geom in voronoi_df.geometry:
            if geom.geom_type == 'LineString':
                x, y = geom.xy
                x = list(x)
                y = list(y)
                fig.add_trace(go.Scattergeo(lon=x, lat=y, mode='lines', line=dict(width=0.2, color='chocolate'),
                                            name=None, showlegend=False))

    # Define the configuration dictionary to customize the toolbar
    facility_name_with_underscore = (facility.lower()).replace(' ', '_')
    config = {
        'modeBarButtonsToRemove': ['zoomOut', 'select2d'],
        'staticPlot': False,
        'scrollZoom': True,
        'toImageButtonOptions': {
            'format': 'png',
            'scale': 1.5,
            'filename': str(desert_type.lower()) + '_deserts_' + state_abbr + '_' + str(facility_name_with_underscore) + '.png',
        }
    }

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
        lonaxis_range=[bounds[0], bounds[2]],
        lataxis_range=[bounds[1], bounds[3]],
        projection_type='mercator',
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        autosize=True,
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

with col2:
    st.caption(f'**Figure**: Census blockgroups classified as ' + str(desert_type.lower()) + ' deserts in ' + state_name
               + '. Colored by racial/ethnic majority.')

    st.write('**' + str(len(desert_df)) + '** of the **' + str(len(census_df)) + '** blockgroups in ' + state_name +
             ' are ' + str(desert_type.lower()) + ' deserts.')
    for racial_label in racial_labels:
        four_times_deserts = racial_fractions_deserts[racial_label] > 4 * racial_fractions_overall[racial_label]
        over_ten_percent_difference = racial_fractions_deserts[racial_label] - racial_fractions_overall[racial_label] > 0.1
        over_five_deserts = racial_fractions_deserts[racial_label] * len(desert_df) >= 5
        if over_five_deserts and (four_times_deserts or over_ten_percent_difference):
            overall_percent_str = str(round(racial_fractions_overall[racial_label] * 100, 2))
            desert_percent_str = str(round(racial_fractions_deserts[racial_label] * 100, 2))
            st.write('Majority ' + racial_label.split('_')[0].capitalize() + ' blockgroups may be disproportionately affected by '
                     + desert_type.lower() + ' deserts in ' + state_name + ': they make up :red[' + desert_percent_str +
                     '%] of ' + desert_type.lower() + ' deserts in ' + state_name + ' while being only :blue[' +
                     overall_percent_str + '%] of all blockgroups.')

with st.sidebar:
    mode = None
    mode = sac.buttons(
        [sac.ButtonsItem(label='Explainer', color='#c41636')],
        index=None,
        align='center',
        use_container_width=True,
        color='#c41636',
        key=None,
        variant='outline',
        size='sm',
    )
    if mode == 'Explainer':
        switch_page("explore-medical-facility-deserts")


st.sidebar.caption('Created by Swati Gupta, [Jai Moondra](https://jaimoondra.github.io/), Mohit Singh.\n'
                   'Based on our [paper](https://arxiv.org/abs/2211.14873) on fairness in facility location.\n'
                   'Submit any feedback to [jmoondra3@gatech.edu](mailto:jmoondra3@gatech.edu).\n')
