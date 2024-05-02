import streamlit as st
from src.usa.states import USAState
from src.usa.constants import racial_label_dict
import plotly.graph_objects as go
from src.usa.facilities_data_handler import Hospitals
import geopandas as gpd
from st_pages import Page, add_page_title, show_pages
from streamlit_extras.switch_page_button import switch_page
import streamlit_antd_components as sac
import pandas as pd

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


st.set_page_config(initial_sidebar_state='collapsed', layout='wide')


About = Page("medical-facility-deserts.py", "About", None)
Explore = Page("pages/explore-medical-facility-deserts.py", "Explore", None)

# show_pages(
#     [
#         Page("medical-facility-deserts.py", "About", None),
#         Page("pages/explore-medical-facility-deserts.py", "Explore", None),
#     ]
# )

st.markdown("""
    <h1 style="font-size: 40px; text-align: center; margin-bottom: 0em; line-height: 1.0;">
        Facility deserts in <span style="color: #c41636"> USA </span>
    </h1>
    <br>
    """, unsafe_allow_html=True)


mode = None
mode = sac.buttons(
    [sac.ButtonsItem(label='Start Exploring!', color='#c41636')],
    index=None,
    align='center',
    use_container_width=True,
    color='#c41636',
    key=None,
    variant='filled',
    size='sm',
)
if mode == 'Start Exploring!':
    switch_page("medical-facility-deserts")

with st.expander('What is this?', expanded=True):
    st.markdown("""
        Access to critical infrastructure is considered one of three dimensions of
        [multidimensional poverty](https://www.worldbank.org/en/topic/poverty/brief/multidimensional-poverty-measure) 
        by the World Bank. Inequitable access to important facilities such as hospitals, schools, and banks can exacerabte monetary
        poverty and other social disparities. The US department of agriculture has identified areas with limited
        access to grocery stores as [food deserts](https://www.ers.usda.gov/data-products/food-access-research-atlas/go-to-the-atlas/).
        \n 
        This tool helps visualize potential 'deserts' for other critical facilities.
        """
                )

col1, col2 = st.columns([1, 1])

with col2:
    with st.expander('What are the facilities considered?', expanded=True):
        st.markdown("""
            1. Pharmacy chains CVS/Walgreens/Walmart
            2. Urgent care centers
            3. Hospitals
            4. Nursing homes
            5. Private schools
            6. Banks
            7. Child care centers
            8. Logistics chains FedEx/UPS/USPS. """
                    )

    with st.expander('Tell me about racial/ethnic categories', expanded=True):
        st.markdown("""
            The racial/ethnic majority in a blockgroup is one of the following seven categories:
            1. White alone
            2. Black or African American alone
            3. American Indian or Alaska Native (AIAN) alone
            4. Asian alone
            5. Native Hawaiian or Other Pacific Islander (NHOPI) alone
            6. Hispanic
            7. Other or no racial majority
            The quantifier 'alone' is omitted in the tool for brevity."""
                    )

    with st.expander('Created by', expanded=True):
        st.markdown("""Created by Swati Gupta, [Jai Moondra](https://jaimoondra.github.io/), and Mohit Singh. Based on 
        our [paper](https://arxiv.org/abs/2211.14873) on fair facility location. Please submit any feedback or 
        questions to [jmoondra3@gatech.edu](mailto:jmoondra3@gatech.edu)."""
                    )

    with st.expander('Data sources', expanded=True):
        st.markdown("""
            The data used in this project is from the [US Census Bureau](https://www.census.gov/programs-surveys/acs/) and
            [HIFLD Open](https://hifld-geoplatform.hub.arcgis.com/pages/hifld-open) database."""
                    )

    with st.expander('Limitations', expanded=True):
        st.markdown("""
            The results are indicative only and meant for educational purposes. Distances are approximate and based on 
            straight-line computations, and all people in a census blockgroup are assumed to be at its geometric center.
             Many other factors affect access to facilities, for example, public transportation,
            road networks, rural-urban divide, and so on. \n
        """
                    )

    with st.expander('License', expanded=True):
        st.write('Released under Creative Commons BY-NC license, 2024.')


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
    with st.expander('How are facility deserts defined?', expanded=True):
        st.markdown("""
            This tool allows you to define facility deserts.
            Our basic unit of analysis is the [US census blockgroup](https://en.wikipedia.org/wiki/Census_block_group)
            which is a small geographic area with typical population of 600 to 3,000 people. You can choose 
            the facility of interest, the distance within which you consider the facility accessible, and poverty rate 
            threshold for classifying blockgroups as 'facility deserts'. \n
            
            As an example, consider hospitals in Colorado:
            """
                    )
        col21, col22 = st.columns([1, 1])
        with col21:
            poverty_threshold = st.slider('Choose poverty threshold (%)', min_value=0, max_value=100, value=10, step=5)
        with col22:
            distance_threshold = st.slider('Choose distance threshold (miles)', min_value=0.0, max_value=25.0, value=8.0, step=0.5)

        state = 'Colorado'
        State = USAState(state)
        census_df = State.get_census_data(level='blockgroup')
        census_df['racial_majority'] = census_df['racial_majority'].astype(str)
        desert_df = census_df[census_df['below_poverty'] >= poverty_threshold]
        desert_df = desert_df[desert_df['Closest_Distance_Hospitals'] >= distance_threshold]

        fig = go.Figure()
        fig = plot_state_boundary(fig, State.abbreviation)
        bounds = get_bounds(state, census_df)

        for i in range(1, 8):
            census_df_i = census_df[census_df['racial_majority'] == str(i)]

            desert_df_i = desert_df[desert_df['racial_majority'] == str(i)]
            if len(desert_df_i) > 0:
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
        hospitals = Hospitals.read_abridged_facilities()
        hospitals = gpd.clip(hospitals, mask=bounds)
        fig.add_trace(go.Scattergeo(lon=hospitals.geometry.x, lat=hospitals.geometry.y, mode='markers',
                                    marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                                    name='Hospital', showlegend=True))

        config = {
            'modeBarButtonsToRemove': ['zoomOut', 'select2d'],
            'displayModeBar': False,
            'staticPlot': False,
            'scrollZoom': True,
            'toImageButtonOptions': {
                'format': 'png',
                'scale': 1.5,
            }
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
        st.markdown("""
            Circles represent blockgroups classified as facility deserts and are colored by their racial majority.
            You can click on the legend to toggle the display of different racial categories.
            """
                    )

    with st.expander('What are Voronoi cells?', expanded=True):
        st.markdown("""
            [Voronoi cells](https://en.wikipedia.org/wiki/Voronoi_diagram) are polygons that partition a plane into regions based on the distance to facilities. Each
            Voronoi cell contains points that are closer to a particular facility than any other. They provide a way to
            visualize the density of facilities in a region. \n
            
            As an example, consider the Voronoi cells for hospitals in Colorado:
            """
                    )
        state = 'Colorado'
        State = USAState(state)
        state_fips = State.fips

        census_df = State.get_census_data(level='blockgroup')
        census_df['racial_majority'] = census_df['racial_majority'].astype(str)

        fig = go.Figure()
        fig = plot_state_boundary(fig, State.abbreviation)
        bounds = get_bounds(state, census_df)

        hospitals = Hospitals.read_abridged_facilities()
        hospitals = gpd.clip(hospitals, mask=bounds)
        fig.add_trace(go.Scattergeo(lon=hospitals.geometry.x, lat=hospitals.geometry.y, mode='markers',
                                    marker=dict(size=2, color='black', opacity=0.8, symbol='x'),
                                    name='Hospital', showlegend=True))

        voronoi_df = gpd.read_file('data/usa/facilities/hospitals/voronoi_state_shapefiles/' + state_fips + '_voronoi.shp', index=False)
        for geom in voronoi_df.geometry:
            if geom.geom_type == 'LineString':
                x, y = geom.xy
                x = list(x)
                y = list(y)
                fig.add_trace(go.Scattergeo(lon=x, lat=y, mode='lines', line=dict(width=0.2, color='chocolate'),
                                            name=None, showlegend=False))

        config = {
            'modeBarButtonsToRemove': ['zoomOut', 'select2d'],
            'displayModeBar': False,
            'staticPlot': False,
            'scrollZoom': True,
            'toImageButtonOptions': {
                'format': 'png',
                'scale': 1.5,
            }
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
            xaxis=dict(range=[bounds[0], bounds[2]], autorange=False),
            yaxis=dict(range=[bounds[1], bounds[3]], autorange=False),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, config=config)
