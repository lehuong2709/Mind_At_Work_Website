from datetime import datetime
import geopandas as gpd
import plotly.graph_objects as go
import random
from src.constants import MILES_TO_KM
from src.usa.constants import state_names, racial_label_dict
from src.usa.states import USAState
from src.usa.facilities_data_handler import (
    CVS, Walgreens, Walmart, UrgentCare, Hospitals, DialysisCenters, NursingHomes,
    ChildCare, PrivateSchools, FDICInsuredBanks, DHL, UPS, FedEx)
import streamlit as st
import streamlit_antd_components as sac
from streamlit_extras.switch_page_button import switch_page
import pandas as pd
import plotly.express as px


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
populous_states = ['Oklahoma', 'Pennsylvania', 'Massachusetts', 'Alabama', 'Louisiana', 'Indiana',
                   'Maryland', 'Colorado', 'North Carolina', 'South Carolina', 'Arizona', 'Florida',
                   'California', 'Wisconsin', 'Texas', 'Missouri', 'Virginia',
                   'Mississippi', 'New York', 'Kentucky', 'Michigan', 'Illinois', 'Georgia',
                   'Ohio', 'Tennessee', 'Minnesota', 'Oregon', 'New Jersey', 'Washington']

st.set_page_config(layout='centered', initial_sidebar_state='expanded')

st.sidebar.caption('This tool aims to identify potentially vulnerable areas in the US with low access to '
                   'various critical facilities. We define these areas by high poverty rates and large distances '
                   'to facilities. You can choose the distance threshold and poverty rate to identify these areas.')

# Get the current day of the year
day_of_year = datetime.now().timetuple().tm_yday
state_of_the_day = populous_states[day_of_year % len(populous_states)]
index = state_names.index(state_of_the_day)

facilities = ['Pharmacy chains', 'Urgent care centers', 'Hospitals', 'Nursing homes', 'Private schools',
              'Banks', 'Child care centers', 'Logistics chains']

with st.sidebar:
    facility = st.selectbox('Choose a facility', facilities)
    state_name = st.selectbox('Choose a US state', options=state_names, index=index)

if facility == 'Pharmacy chains' or facility == 'Urgent care centers' or facility == 'Hospitals' or \
        facility == 'Dialysis centers' or facility == 'Nursing homes':
    desert_type = 'Medical'
elif facility == 'Private schools':
    desert_type = 'Education'
elif facility == 'Banks':
    desert_type = 'Banking'
elif facility == 'Child care centers':
    desert_type = 'Facility'
elif facility == 'Logistics chains':
    desert_type = 'Logistics'

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

if facility == 'Pharmacy chains':
    st.markdown("""
        Let's define a **medical desert** as a US census [blockgroup](https://en.wikipedia.org/wiki/Census_block_group) 
        that is more than $n$ miles away from a CVS/Walgreeens/Walmart pharmacy and with over $p$% of the population living 
        below the poverty line. Choose these numbers from the sidebar.
    """, unsafe_allow_html=True)
elif facility == 'Urgent care centers':
    st.markdown("""
        Let's define a **medical desert** as a US census [blockgroup](https://en.wikipedia.org/wiki/Census_block_group) 
        that is more than $n$ miles away from an urgent care center and with over $p$% of the population living 
        below the poverty line. Choose these numbers from the sidebar.
    """, unsafe_allow_html=True)
elif facility == 'Hospitals':
    st.markdown("""
        Let's define a **medical desert** as a US census [blockgroup](https://en.wikipedia.org/wiki/Census_block_group) 
        that is more than $n$ miles away from a hospital and with over $p$% of the population living 
        below the poverty line. Choose these numbers from the sidebar.
    """, unsafe_allow_html=True)
elif facility == 'Nursing homes':
    st.markdown("""
        Let's define a **medical desert** as a US census [blockgroup](https://en.wikipedia.org/wiki/Census_block_group) 
        that is more than $n$ miles away from a nursing home and with over $p$% of the population living 
        below the poverty line. Choose these numbers from the sidebar.
    """, unsafe_allow_html=True)
elif facility == 'Private schools':
    st.markdown("""
        Let's define an **education desert** as a US census [blockgroup](https://en.wikipedia.org/wiki/Census_block_group) 
        that is more than $n$ miles away from a private school and with over $p$% of the population living 
        below the poverty line. Choose these numbers from the sidebar.
    """, unsafe_allow_html=True)
elif facility == 'Banks':
    st.markdown("""
        Let's define a **banking desert** as a US census [blockgroup](https://en.wikipedia.org/wiki/Census_block_group) 
        that is more than $n$ miles away from an [FDIC insured bank](https://en.wikipedia.org/wiki/Federal_Deposit_Insurance_Corporation#:~:text=The%20Federal%20Deposit%20Insurance%20Corporation,in%20the%20American%20banking%20system.) and with over $p$% of the population living 
        below the poverty line. Choose these numbers from the sidebar.
    """, unsafe_allow_html=True)
elif facility == 'Child care centers':
    st.markdown("""
        Let's define a **facility desert** as a US census [blockgroup](https://en.wikipedia.org/wiki/Census_block_group) 
        that is more than $n$ miles away from a child care center and with over $p$% of the population living 
        below the poverty line. Choose these numbers from the sidebar.
    """, unsafe_allow_html=True)
elif facility == 'Logistics chains':
    st.markdown("""
        Let's define a **logistics desert** as a US census [blockgroup](https://en.wikipedia.org/wiki/Census_block_group) 
        that is more than $n$ miles away from a FedEx/UPS/DHL facility and with over $p$% of the population living 
        below the poverty line. Choose these numbers from the sidebar.
    """, unsafe_allow_html=True)

with st.sidebar:
    with st.container(border=True):
        poverty_threshold = st.slider(r'Choose poverty threshold $p$%', min_value=0, max_value=100, value=20, step=5, key='poverty_threshold')

    with st.container(border=True):
        urban_rural = st.checkbox('Use separate urban/rural distances', value=True)
        if urban_rural:
            col_side1, col_side2 = st.columns(2)
            urban_distance_threshold = col_side1.slider(r'Choose urban distance threshold $n$ miles', min_value=0.0, max_value=15.0, value=2.0, step=0.5, key='urban_distance_threshold')
            rural_distance_threshold = col_side2.slider(r'Choose rural distance threshold $n$ miles', min_value=0.0, max_value=30.0, value=8.0, step=1.0, key='rural_distance_threshold')
            urban_distance_threshold = MILES_TO_KM * urban_distance_threshold
            rural_distance_threshold = MILES_TO_KM * rural_distance_threshold
        else:
            distance_threshold = st.slider(r'Choose distance threshold $n$ miles', min_value=0.0, max_value=25.0, value=3.0, step=0.5, key='distance_threshold')
            distance_threshold = MILES_TO_KM * distance_threshold

col1, col2 = st.columns([3, 2], gap='medium')

with col2:
    with st.expander('Figure options'):
        show_deserts = st.checkbox('Show ' + desert_type.lower() + ' deserts', value=True)
        if facility == 'Pharmacy chains':
            show_pharmacies = st.checkbox('Show CVS/Walgreens/Walmart locations', value=False)
            show_voronoi_cells = st.checkbox('Show pharmacy Voronoi cells', value=False)
        elif facility == 'Urgent care centers':
            show_urgent_care = st.checkbox('Show urgent care locations', value=False)
            show_voronoi_cells = st.checkbox('Show urgent care Voronoi cells', value=False)
        elif facility == 'Hospitals':
            show_hospitals = st.checkbox('Show hospital locations', value=False)
            show_voronoi_cells = st.checkbox('Show hospital Voronoi cells', value=False)
        elif facility == 'Nursing homes':
            show_nursing_homes = st.checkbox('Show nursing home locations', value=False)
            show_voronoi_cells = st.checkbox('Show nursing home Voronoi cells', value=False)
        elif facility == 'Private schools':
            show_private_schools = st.checkbox('Show private school locations', value=False)
            show_voronoi_cells = st.checkbox('Show private school Voronoi cells', value=False)
        elif facility == 'Banks':
            show_banks = st.checkbox('Show bank locations', value=False)
            show_voronoi_cells = st.checkbox('Show bank Voronoi cells', value=False)
        elif facility == 'Child care centers':
            show_child_care_centers = st.checkbox('Show child care center locations', value=False)
            show_voronoi_cells = st.checkbox('Show child care center Voronoi cells', value=False)
        elif facility == 'Logistics chains':
            show_logistics = st.checkbox('Show FedEx/UPS/DHL locations', value=False)
            show_voronoi_cells = False


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

    # Create the choropleth map
    # choropleth = px.choropleth(
    #     data_frame=data,
    #     locations='state',
    #     locationmode='USA-states',
    #     color='value',
    #     color_continuous_scale=["#fbfcf9", "#f9f3e1"],
    #     scope="north america",
    # )
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
    census_df['racial_majority'] = census_df['racial_majority'].astype(str)

    fig = go.Figure()
    # fig, bounds = State.plot_state_boundary(fig)
    fig = plot_state_boundary(fig, state_abbr)
    bounds = get_bounds(state_name, census_df)

    racial_fractions_overall = {'1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0, '7': 0.0}
    racial_fractions_deserts = {'1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0, '7': 0.0}

    if facility == 'Pharmacy chains':
        distance_label = 'Closest_Distance_Pharmacies_Top3'
    elif facility == 'Urgent care centers':
        distance_label = 'Closest_Distance_Urgent_Care_Centers'
    elif facility == 'Hospitals':
        distance_label = 'Closest_Distance_Hospitals'
    elif facility == 'Nursing homes':
        distance_label = 'Closest_Distance_Nursing_Homes'
    elif facility == 'Private schools':
        distance_label = 'Closest_Distance_Private_Schools'
    elif facility == 'Banks':
        distance_label = 'Closest_Distance_Banks'
    elif facility == 'Child care centers':
        distance_label = 'Closest_Distance_Childcare'
    elif facility == 'Logistics chains':
        distance_label = 'Closest_Distance_Logistical_Top3'

    if not urban_rural:
        desert_df = census_df[(census_df['below_poverty'] >= poverty_threshold) & (census_df[distance_label] >= distance_threshold)]
    else:
        desert_df = census_df[((census_df['below_poverty'] >= poverty_threshold) & (census_df['urban']) & (census_df[distance_label] >= urban_distance_threshold)) |
                              ((census_df['below_poverty'] >= poverty_threshold) & (~census_df['urban']) & (census_df[distance_label] >= rural_distance_threshold))]

    randomly_shuffled_indices = list(range(1, 8))
    random.shuffle(randomly_shuffled_indices)

    for i in randomly_shuffled_indices:
        census_df_i = census_df[census_df['racial_majority'] == str(i)]
        racial_fractions_overall[str(i)] = len(census_df_i)/len(census_df)

        desert_df_i = desert_df[desert_df['racial_majority'] == str(i)]
        if len(desert_df_i) > 0:
            racial_fractions_deserts[str(i)] = len(desert_df_i)/len(desert_df)
            if show_deserts:
                fig.add_trace(
                    go.Scattergeo(
                        name=racial_label_dict[i],
                        lon=desert_df_i['Longitude'],
                        lat=desert_df_i['Latitude'],
                        marker=dict(
                            color=scatter_palette[i - 1],
                            opacity=0.6,
                            line=dict(
                                width=1.0,
                                color='rgba(0, 0, 0, 0.9)',
                            ))))

    if facility == 'Pharmacy chains':
        if show_pharmacies:
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
        if show_voronoi_cells:
            voronoi_df = gpd.read_file('data/usa/facilities/pharmacies_top3/voronoi_state_shapefiles/' + state_fips + '_voronoi.shp', index=False)
            for geom in voronoi_df.geometry:
                if geom.geom_type == 'LineString':
                    x, y = geom.xy
                    x = list(x)
                    y = list(y)
                    fig.add_trace(go.Scattergeo(lon=x, lat=y, mode='lines', line=dict(width=0.2, color='chocolate'),
                                                name=None, showlegend=False))
    elif facility == 'Urgent care centers':
        if show_urgent_care:
            urgent_care_centers = UrgentCare.read_abridged_facilities()
            urgent_care_centers = gpd.clip(urgent_care_centers, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=urgent_care_centers.geometry.x, lat=urgent_care_centers.geometry.y, mode='markers',
                                        marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                                        name='Urgent care center', showlegend=True))
        if show_voronoi_cells:
            voronoi_df = gpd.read_file('data/usa/facilities/urgentcare_centers/voronoi_state_shapefiles/' + state_fips + '_voronoi.shp', index=False)
            for geom in voronoi_df.geometry:
                if geom.geom_type == 'LineString':
                    x, y = geom.xy
                    x = list(x)
                    y = list(y)
                    fig.add_trace(go.Scattergeo(lon=x, lat=y, mode='lines', line=dict(width=0.2, color='chocolate'),
                                                name=None, showlegend=False))
    elif facility == 'Hospitals':
        if show_hospitals:
            hospitals = Hospitals.read_abridged_facilities()
            hospitals = gpd.clip(hospitals, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=hospitals.geometry.x, lat=hospitals.geometry.y, mode='markers',
                                        marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                                        name='Hospital', showlegend=True))
        if show_voronoi_cells:
            voronoi_df = gpd.read_file('data/usa/facilities/hospitals/voronoi_state_shapefiles/' + state_fips + '_voronoi.shp', index=False)
            for geom in voronoi_df.geometry:
                if geom.geom_type == 'LineString':
                    x, y = geom.xy
                    x = list(x)
                    y = list(y)
                    fig.add_trace(go.Scattergeo(lon=x, lat=y, mode='lines', line=dict(width=0.2, color='chocolate'),
                                                name=None, showlegend=False))
    elif facility == 'Nursing homes':
        if show_nursing_homes:
            nursing_homes = NursingHomes.read_abridged_facilities()
            nursing_homes = gpd.clip(nursing_homes, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=nursing_homes.geometry.x, lat=nursing_homes.geometry.y, mode='markers',
                                        marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                                        name='Nursing home', showlegend=True))
        if show_voronoi_cells:
            voronoi_df = gpd.read_file('data/usa/facilities/nursing_homes/voronoi_state_shapefiles/' + state_fips + '_voronoi.shp', index=False)
            for geom in voronoi_df.geometry:
                if geom.geom_type == 'LineString':
                    x, y = geom.xy
                    x = list(x)
                    y = list(y)
                    fig.add_trace(go.Scattergeo(lon=x, lat=y, mode='lines', line=dict(width=0.2, color='chocolate'),
                                                name=None, showlegend=False))
    elif facility == 'Private schools':
        if show_private_schools:
            private_schools = PrivateSchools.read_abridged_facilities()
            private_schools = gpd.clip(private_schools, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=private_schools.geometry.x, lat=private_schools.geometry.y, mode='markers',
                                        marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                                        name='Private school', showlegend=True))
        if show_voronoi_cells:
            voronoi_df = gpd.read_file('data/usa/facilities/private_schools/voronoi_state_shapefiles/' + state_fips + '_voronoi.shp', index=False)
            for geom in voronoi_df.geometry:
                if geom.geom_type == 'LineString':
                    x, y = geom.xy
                    x = list(x)
                    y = list(y)
                    fig.add_trace(go.Scattergeo(lon=x, lat=y, mode='lines', line=dict(width=0.2, color='chocolate'),
                                                name=None, showlegend=False))
    elif facility == 'Banks':
        if show_banks:
            banks = FDICInsuredBanks.read_abridged_facilities()
            banks = gpd.clip(banks, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=banks.geometry.x, lat=banks.geometry.y, mode='markers',
                                        marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                                        name='Bank', showlegend=True))
        if show_voronoi_cells:
            voronoi_df = gpd.read_file('data/usa/facilities/banks/voronoi_state_shapefiles/' + state_fips + '_voronoi.shp', index=False)
            for geom in voronoi_df.geometry:
                if geom.geom_type == 'LineString':
                    x, y = geom.xy
                    x = list(x)
                    y = list(y)
                    fig.add_trace(go.Scattergeo(lon=x, lat=y, mode='lines', line=dict(width=0.2, color='chocolate'),
                                                name=None, showlegend=False))
    elif facility == 'Child care centers':
        if show_child_care_centers:
            child_care_centers = ChildCare.read_abridged_facilities()
            child_care_centers = gpd.clip(child_care_centers, mask=bounds)
            fig.add_trace(go.Scattergeo(lon=child_care_centers.geometry.x, lat=child_care_centers.geometry.y, mode='markers',
                                        marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                                        name='Child care center', showlegend=True))
        if show_voronoi_cells:
            voronoi_df = gpd.read_file('data/usa/facilities/childcare/voronoi_state_shapefiles/' + state_fips + '_voronoi.shp', index=False)
            for geom in voronoi_df.geometry:
                if geom.geom_type == 'LineString':
                    x, y = geom.xy
                    x = list(x)
                    y = list(y)
                    fig.add_trace(go.Scattergeo(lon=x, lat=y, mode='lines', line=dict(width=0.2, color='chocolate'),
                                                name=None, showlegend=False))
    elif facility == 'Logistics chains':
        dhl_color = '#8b1e2b'
        ups_color = '#521801'
        fedex_color = '#cc4700'
        if show_logistics:
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
        # bgcolor='#a1b8b7',
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
    for i in range(1, 7):
        four_times_deserts = racial_fractions_deserts[str(i)] > 4 * racial_fractions_overall[str(i)]
        over_ten_percent_difference = racial_fractions_deserts[str(i)] - racial_fractions_overall[str(i)] > 0.1
        over_five_deserts = racial_fractions_deserts[str(i)] * len(desert_df) >= 5
        if over_five_deserts and (four_times_deserts or over_ten_percent_difference):
            overall_percent_str = str(round(racial_fractions_overall[str(i)] * 100, 2))
            desert_percent_str = str(round(racial_fractions_deserts[str(i)] * 100, 2))
            st.write('Majority ' + str(racial_label_dict[i]) + ' blockgroups may be disproportionately affected by '
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

# with st.sidebar.expander('About this app', expanded=False):
#     st.markdown('Released under Creative Commons BY-NC license, 2024.')
#     st.markdown('Distances are approximate and based on straight-line computations. '
#                 'Many other factors affect access to facilities. '
#                 'The results are indicative only and meant for educational purposes.')
#     st.markdown(
#         """
#         All facility datasets are from [HIFLD Open](https://hifld-geoplatform.hub.arcgis.com/pages/hifld-open) database. \n
#         Data for [pharmacies](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::pharmacies-/about) is from 2010. \n
#         Data for [urgent care centers](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::urgent-care-facilities/about) is from 2009. \n
#         Data for [hospitals](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::hospitals/about) is from 2023. \n
#         Data for [nursing homes](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::nursing-homes/about) is from 2017. \n
#         Data for [private schools](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::private-schools/about) is from 2017. \n
#         Data for [FDIC insured banks](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::fdic-insured-banks/about) is from 2019. \n
#         Data for [Child care centers](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::child-care-centers/about) if from 2022. \n
#         [Census](https://data.census.gov/) data is from 2022. \n
#         """
#     )



