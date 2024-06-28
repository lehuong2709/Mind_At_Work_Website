import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import streamlit as st
from st_pages import Page, add_page_title, show_pages
from streamlit_extras.switch_page_button import switch_page
import streamlit_antd_components as sac

from src.constants import scatter_palette
from src.usa.states import USAState
from src.usa.facilities import Hospitals
from src.usa.constants import racial_label_dict
from src.usa.utils import racial_labels, compute_medical_deserts
from src.usa.plot_utils import plot_state, plot_blockgroups, plot_voronoi_cells, plot_existing_facilities

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')


st.markdown("""
    <h1 style="font-size: 40px; text-align: center; margin-bottom: 0em; line-height: 1.0;">
        Facility deserts in <span style="color: #c41636"> USA </span>
    </h1>
    <br>
    """, unsafe_allow_html=True)


mode = None
# mode = sac.buttons(
#     [sac.ButtonsItem(label='Start Exploring!', color='#c41636')],
#     index=None,
#     align='center',
#     use_container_width=True,
#     color='#c41636',
#     key=None,
#     variant='filled',
#     size='sm',
# )
mode = st.button('Start Exploring!', use_container_width=True, type='primary')
if mode:
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
            7. Child care centers"""
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
            7. Other or no racial majority \n
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
            [HIFLD Open](https://hifld-geoplatform.hub.arcgis.com/pages/hifld-open) database. \n                    
            Data for [pharmacies](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::pharmacies-/about) is from 2010. \n
            Data for [urgent care centers](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::urgent-care-facilities/about) is from 2009. \n
            Data for [hospitals](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::hospitals/about) is from 2023. \n
            Data for [nursing homes](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::nursing-homes/about) is from 2017. \n
            Data for [private schools](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::private-schools/about) is from 2017. \n
            Data for [FDIC insured banks](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::fdic-insured-banks/about) is from 2019. \n
            Data for [Child care centers](https://hifld-geoplatform.hub.arcgis.com/datasets/geoplatform::child-care-centers/about) if from 2022. \n
            [Census](https://data.census.gov/) data is from 2022. \n"""
                    )

    with st.expander('Limitations', expanded=True):
        st.markdown("""
            The results are indicative only and meant for educational purposes. Distances are approximate and based on 
            straight-line computations, and all people in a census blockgroup are assumed to be at its geometric center.
             Many other factors affect access to facilities, for example, public transportation,
            road networks, rural-urban divide, and so on. Data for some facilities is older than census data.\n
        """
                    )

    with st.expander('License', expanded=True):
        st.write('Released under Creative Commons BY-NC license, 2024.')


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

        Facility = Hospitals
        desert_df = compute_medical_deserts(census_df, poverty_threshold, distance_threshold, distance_threshold,
                                            Hospitals.distance_label)

        fig = go.Figure()
        fig, bounds = plot_state(fig, State)
        fig = plot_blockgroups(fig, desert_df)
        fig = plot_existing_facilities(fig, Facility, bounds)

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
        fig, bounds = plot_state(fig, State)
        fig = plot_existing_facilities(fig, Hospitals, bounds)
        fig = plot_voronoi_cells(fig, Hospitals, state_fips)

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

        st.plotly_chart(fig, use_container_width=True, config=config)
