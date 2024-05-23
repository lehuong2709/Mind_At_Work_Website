from datetime import datetime
import geopandas as gpd
import plotly.graph_objects as go
import random
from src.usa.constants import state_names, racial_label_dict
from src.usa.states import USAState
from src.usa.facilities_data_handler import UrgentCare
import streamlit as st


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
                   'Utah', 'California', 'Wisconsin', 'Texas', 'Missouri', 'Virginia',
                   'Mississippi', 'New York', 'Kentucky', 'Michigan', 'Illinois', 'Georgia',
                   'Ohio', 'Tennessee', 'Minnesota', 'Oregon', 'New Jersey', 'Washington']

st.set_page_config(initial_sidebar_state='expanded', layout='centered')

st.sidebar.write(r'Let\'s define a **medical desert** as a US census blockgroup that is more than $n$ miles away from '
                 r'an urgent care center and with over $p$% of the population living below the poverty line.')

state_names.sort()

# Get the current day of the year
day_of_year = datetime.now().timetuple().tm_yday
state_of_the_day = populous_states[day_of_year % len(populous_states)]
index = state_names.index(state_of_the_day)

# User selection via selectbox
state_name = st.sidebar.selectbox('Select a state', options=state_names, index=index)

State = USAState(state_name)
state_fips = State.fips
state_abbr = State.abbreviation

st.markdown("""
    <h1 style="font-size: 40px; text-align: center; margin-bottom: 0em; line-height: 0.2;">
        Medical deserts in
        <span style="color: #c41636">
            """ + state_name + """
        </span>
    </h1>
    <h3 style="font-size: 18px; text-align: center; margin-top: 0em;">
        Based on <span style="color: #c41636">urgent care centers</span>
    </h3>
    <br>
    """, unsafe_allow_html=True)

poverty_threshold = st.sidebar.slider(r'Choose poverty threshold p%', min_value=0, max_value=100, value=25, step=5, key='poverty_threshold')
distance_threshold = st.sidebar.slider(r'Distance threshold $n$ miles', min_value=0.0, max_value=40.0, value=5.0, step=0.5, key='distance_threshold')

show_pharmacies = st.sidebar.checkbox('Show urgent care locations', value=False)
# show_voronoi_cells = st.sidebar.checkbox('Show urgent care Voronoi cells', value=False)

col1, col2 = st.columns([2, 1], gap='small')

with col1:
    fig = go.Figure()
    fig, bounds = State.plot_state_boundary(fig)

    if show_pharmacies:
        urgent_care_centers = UrgentCare.read_abridged_facilities()
        urgent_care_centers = gpd.clip(urgent_care_centers, mask=bounds)
        fig.add_trace(go.Scattergeo(lon=urgent_care_centers.geometry.x, lat=urgent_care_centers.geometry.y, mode='markers',
                                    marker=dict(size=4, color='black', opacity=0.8, symbol='x'),
                                    name='Urgent care center', showlegend=True))

    # if show_voronoi_cells:
    #     voronoi_df = gpd.read_file('data/usa/facilities/pharmacies_top3/voronoi_state_shapefiles/' + state_fips + '_voronoi.shp', index=False)
    #     for geom in voronoi_df.geometry:
    #         if geom.geom_type == 'LineString':
    #             x, y = geom.xy
    #             x = list(x)
    #             y = list(y)
    #             fig.add_trace(go.Scattergeo(lon=x, lat=y, mode='lines', line=dict(width=0.2, color='chocolate'),
    #                                         name=None, showlegend=False))

    racial_fractions_overall = {'1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0, '7': 0.0}
    racial_fractions_deserts = {'1': 0.0, '2': 0.0, '3': 0.0, '4': 0.0, '5': 0.0, '6': 0.0, '7': 0.0}

    census_df = State.get_census_data(level='blockgroup')
    census_df['racial_majority'] = census_df['racial_majority'].astype(str)

    desert_df = census_df[census_df['below_poverty'] >= poverty_threshold]
    desert_df = desert_df[desert_df['Closest_Distance_Urgent_Care_Centers'] >= distance_threshold]

    randomly_shuffled_indices = list(range(1, 8))
    random.shuffle(randomly_shuffled_indices)
    for i in randomly_shuffled_indices:
        census_df_i = census_df[census_df['racial_majority'] == str(i)]
        racial_fractions_overall[str(i)] = len(census_df_i)/len(census_df)

        desert_df_i = desert_df[census_df['racial_majority'] == str(i)]
        if len(desert_df_i) > 0:
            racial_fractions_deserts[str(i)] = len(desert_df_i)/len(desert_df)
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

    # Define the configuration dictionary to customize the toolbar
    config = {
        'modeBarButtonsToRemove': ['zoomOut', 'reset'],
        'staticPlot': False,
        'scrollZoom': True,
    }

    st.plotly_chart(fig, use_container_width=True, config=config, margin=dict(l=0, r=0, t=0, b=0))

with col2:
    st.caption(f'**Figure**: Census blockgroups classified as medical deserts in ' + state_name + '. '
                                                                                                f'Colored by racial majority.')

    st.write('**' + str(len(desert_df)) + '** of the **' + str(len(census_df)) + '** blockgroups in ' + state_name + ''
                                                                                                                     ' are medical deserts.')

    for i in range(1, 7):
        four_times_deserts = racial_fractions_deserts[str(i)] > 4 * racial_fractions_overall[str(i)]
        over_ten_percent_difference = racial_fractions_deserts[str(i)] - racial_fractions_overall[str(i)] > 0.1
        over_five_deserts = racial_fractions_deserts[str(i)] * len(desert_df) >= 5
        if over_five_deserts and (four_times_deserts or over_ten_percent_difference):
            overall_percent_str = str(round(racial_fractions_overall[str(i)] * 100, 2))
            desert_percent_str = str(round(racial_fractions_deserts[str(i)] * 100, 2))

            st.write('Medical deserts in ' + state_name + ' may disproportionately affect the ' + str(racial_label_dict[i]) + ' population, '
                                                                                                                              'with :red[' + desert_percent_str + '%] of these deserts being majority ' + str(racial_label_dict[i]) + ' compared to just '
                                                                                                                                                                                                                                      ':blue[' + overall_percent_str + '%] of all blockgroups.')

st.sidebar.write('\n')
st.sidebar.caption('Created by Swati Gupta, Jai Moondra, Mohit Singh. Creative Commons BY-NC license.')
st.sidebar.caption('Data for pharmacies is from the HIFLD Open Data database from 2005-10. '
                   'Data for census blockgroups is from the US Census Bureau, 2022.')
st.sidebar.caption('Distances are approximate and based on straight-line computations. '
                   'Many other factors affect access to facilities. '
                   'The results are indicative only and meant for educational purposes.')
