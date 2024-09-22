import geopandas as gpd
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.usa.constants import state_names, interesting_states, mainland_states
from src.usa.states import USAState
from src.usa.facilities import CVS, Walgreens, Walmart, UrgentCare, Hospitals, NursingHomes, ChildCare, PrivateSchools, FDICInsuredBanks, PharmaciesTop3
from src.usa.utils import racial_labels, racial_labels_display_names, compute_medical_deserts, get_page_url, get_demographic_data, get_facility_from_facility_name, get_state_of_the_day
from src.usa.plot_utils import plot_state, plot_stacked_bar, plot_existing_facilities, plot_blockgroups, plot_voronoi_cells, plot_new_facilities, plot_demographic_analysis, plot_radar_chart, plot_distance_histogram
from src.tabs.utils import get_facility_from_user, get_poverty_threshold_from_user, get_distance_thresholds_from_user


# Function to convert a hex color to rgba format with opacity
def hex_to_rgba(hex_color, opacity):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"


# Define the custom container function with background opacity
def custom_container(content, bg_color='#dfdfdf', opacity=0.5):
    rgba_color = hex_to_rgba(bg_color, opacity)
    container_style = f"""
        <div style='
            background-color: {rgba_color};
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        '>
            {content}
        </div>
    """
    st.markdown(container_style, unsafe_allow_html=True)


@st.cache_data
def distances_by_state(facility, new=False, k=10):
    """
    Get the states where poor people travel farther to access the facility.
    """
    groups = ['no_health_ins', 'below_poverty'] + [label for label in racial_labels if label != 'other']
    columns = ['Mean Distance'] + ['Mean Distance ' + group for group in groups]
    urban_distance_df = pd.DataFrame(index=mainland_states, columns=columns)
    rural_distance_df = pd.DataFrame(index=mainland_states, columns=columns)

    if not new:
        distance_label = facility.distance_label
    else:
        distance_label = facility.distance_label + str('_combined_k_' + str(k))

    for state in mainland_states:
        State = USAState(state)
        census_df = State.get_census_data()
        census_df.dropna(inplace=True)

        urban_df = census_df[census_df['urban'] == 1]
        rural_df = census_df[census_df['urban'] == 0]

        urban_population = urban_df['population'].sum()
        urban_mean_distance = (urban_df[distance_label] @ urban_df['population']) / urban_population
        urban_distance_df.loc[state, 'Mean Distance'] = round(urban_mean_distance/1.602, 2)

        rural_population = rural_df['population'].sum()
        rural_mean_distance = (rural_df[distance_label] @ rural_df['population'])/ rural_population
        rural_distance_df.loc[state, 'Mean Distance'] = round(rural_mean_distance/1.602, 2)

        for group in groups:
            urban_group_populations = urban_df[group] * urban_df['population']
            urban_group_mean_distance = (urban_df[distance_label] @ urban_group_populations)/ urban_group_populations.sum()
            urban_distance_df.loc[state, 'Mean Distance ' + group] = round(urban_group_mean_distance/1.602, 2)

            rural_group_populations = rural_df[group] * rural_df['population']
            rural_group_mean_distance = (rural_df[distance_label] @ rural_group_populations)/ rural_group_populations.sum()
            rural_distance_df.loc[state, 'Mean Distance ' + group] = round(rural_group_mean_distance/1.602, 2)

    return urban_distance_df, rural_distance_df


def plot_disparity_bar_chart(fig, distance_df, column_1, column_2, disparity_threshold, color=px.colors.qualitative.Plotly[3]):
    """
    Plot the disparity bar chart.
    """
    states_with_disparity = distance_df[column_1] - distance_df[column_2] > disparity_threshold
    states_with_disparity = states_with_disparity[states_with_disparity == True].index

    disparities = distance_df.loc[states_with_disparity][column_1] - distance_df.loc[states_with_disparity][column_2]
    disparities.sort_values(ascending=True, inplace=True)

    fig.add_trace(go.Bar(
        x=disparities,
        y=disparities.index,
        orientation='h',
        hoverinfo='x',
        marker_color=color,
    ))

    fig.update_layout(
        margin=dict(t=5, b=10),
        height=20*len(states_with_disparity) + 30,
    )

    config = dict(
        displayModeBar=False,
        responsive=True,
    )

    return fig, config


def plot_reduction_in_disparity(fig, distance_df, distance_df_new, column_1, column_2, disparity_threshold, k, color=px.colors.qualitative.Plotly[3]):
    states_with_disparity = distance_df[column_1] - distance_df[column_2] > disparity_threshold
    states_with_disparity = states_with_disparity[states_with_disparity == True].index

    disparities = distance_df.loc[states_with_disparity][column_1] - distance_df.loc[states_with_disparity][column_2]
    disparities.sort_values(ascending=True, inplace=True)
    maximum_disparity = disparities.max()

    fig.add_trace(go.Scatter(
        y=disparities.index,
        x=disparities,
        mode='markers',
        name='Existing disparity',
        marker_color=color,
        hoverinfo='x',
    ))

    disparities_new = distance_df_new.loc[states_with_disparity][column_1] - distance_df_new.loc[states_with_disparity][column_2]
    for state in states_with_disparity:
        if disparities_new.loc[state] < 0:
            disparities_new.loc[state] = 0

    disparities_new = disparities_new.loc[disparities.index]

    fig.add_trace(go.Scatter(
        y=disparities.index,
        x=disparities_new,
        mode='markers',
        name='Disparity after opening ' + str(k) + ' proposed facilities',
        marker_color='forestgreen',
        hoverinfo='x',
    ))

    fig.update_layout(
        margin=dict(t=30, b=0, l=0, r=0),
        xaxis_range=(-0.1, maximum_disparity + 0.1),
        legend=dict(
            yanchor="bottom",
            y=1,
            xanchor="center",
            x=0.5,
            orientation='h',
        ),
        height=20*len(states_with_disparity) + 30,
    )

    config = dict(
        displayModeBar=False,
        responsive=True,
    )

    return fig, config


def plot_distance_against_poverty(facility, urban=1):
    state_data = pd.DataFrame(index=mainland_states, columns=['name', 'below_poverty', 'distance_to_nearest_' + facility.description[2:]])

    for state in mainland_states:
        State = USAState(state)
        census_df = State.get_census_data()
        census_df.dropna(inplace=True)

        census_df = census_df[census_df['urban'] == urban]

        state_data.loc[state, 'name'] = state

        mean_distance = census_df[facility.distance_label] @ census_df['population'] / census_df['population'].sum()
        state_data.loc[state, 'distance_to_nearest_' + facility.description[2:]] = mean_distance

        poverty_rate = census_df['below_poverty'] @ census_df['population'] / census_df['population'].sum()
        state_data.loc[state, 'below_poverty'] = poverty_rate

    fig = px.scatter(
        state_data,
        x='distance_to_nearest_' + facility.description[2:],
        y='below_poverty',
        hover_data=None,
        hover_name='name',
        labels={
            'distance_to_nearest_' + facility.description[2:]: 'Mean distance to nearest ' + facility.description[2:] + ' (miles)',
            'below_poverty': 'Population below poverty line (%)',
        },
        title='Distance to nearest ' + facility.description[2:] + ' vs. Population below poverty line',
    )

    fig.update_layout(
        showlegend=False,
    )

    return fig


def run_analysis_for_poverty(facility, col_left, col_right):
    with col_right:
        urban_distance_df, rural_distance_df = distances_by_state(facility)

        states_where_poor_people_travel_farther_urban = urban_distance_df['Mean Distance below_poverty'] - urban_distance_df['Mean Distance'] > 0.5
        states_where_poor_people_travel_farther_urban = states_where_poor_people_travel_farther_urban[states_where_poor_people_travel_farther_urban].index
        states_where_poor_people_travel_farther_rural = rural_distance_df['Mean Distance below_poverty'] - rural_distance_df['Mean Distance'] > 1
        states_where_poor_people_travel_farther_rural = states_where_poor_people_travel_farther_rural[states_where_poor_people_travel_farther_rural].index

        if len(states_where_poor_people_travel_farther_urban) > 4 or len(states_where_poor_people_travel_farther_rural) > 4:
            with st.container(border=True):
                st.markdown('''<center><h2>Where do poor people travel farther to access facilities?</h2></center>''', unsafe_allow_html=True)

                if len(states_where_poor_people_travel_farther_rural) > 4:
                    col1, col2 = st.columns(2)
                    with col1:
                        message = (f"In some states, poor people may travel farther than the general population to access "
                                   f"the nearest {facility.description[2:]}. This plot shows states where people below the poverty line "
                                   f"in rural areas travel a mile or more than the general population, on average. "
                                   f"This disparity can be doubly harmful, as poor people may have fewer resources to travel "
                                   f"longer distances.")
                        custom_container(message, '#dfdfdf')

                        with st.expander('How is this computed?'):
                            st.markdown('''
                                For each state, we compute the average distance traveled by the general population and by people below the poverty line to access the nearest ''' + facility.description[2:] + '''.
                                We then calculate the difference between these two distances. If the difference is greater than a threshold, we consider the state to have a disparity.
                            ''')
                            st.markdown('''
                                It is helpful to keep in mind the limitations of this analysis. In particular, we assume that people are located at the center of their respective blockgroups, and our distance computations are straight-line.
                            ''')

                    with col2:
                        color = 'salmon'
                        st.markdown(
                            '''<center><b>Average extra distance (in miles) traveled by poor people compared to general 
                            population in <span style="color:''' + color + ''';">rural areas</span></b></center>''',
                            unsafe_allow_html=True
                        )

                        fig = go.Figure()
                        fig, config = plot_disparity_bar_chart(
                            fig,
                            rural_distance_df,
                            'Mean Distance below_poverty',
                            'Mean Distance',
                            1.0,
                            color='salmon'
                        )
                        st.plotly_chart(fig, use_container_width=True, config=config)

                if len(states_where_poor_people_travel_farther_urban) > 2:
                    col1, col2 = st.columns(2)
                    with col1:
                        message = f"This plot shows states where people living below the poverty line in urban areas travel half mile or more than the general population, on average."
                        custom_container(message, '#dfdfdf')

                    with col2:
                        color = px.colors.qualitative.Plotly[3]
                        st.markdown(
                            '''<center><b>Average extra distance (in miles) traveled by poor people compared to general 
                            population in <span style="color:''' + color + ''';">urban areas</span></b></center>''',
                            unsafe_allow_html=True
                        )

                        fig = go.Figure()
                        fig, config = plot_disparity_bar_chart(
                            fig,
                            urban_distance_df,
                            'Mean Distance below_poverty',
                            'Mean Distance',
                            0.5
                        )

                        st.plotly_chart(fig, use_container_width=True, config=config)


    col_left, col_right = st.columns([1, 3])

    with col_left:
        with st.container(border=True):
            k = st.select_slider(options=[5, 10, 25, 50, 100], label='Choose number of proposed new facilities',
                                 value=25, key='_n_facilities', help='Select how many new facilities to open using our model')

        urban_distance_df_new, rural_distance_df_new = distances_by_state(facility, new=True, k=k)

    with col_right:
        if len(states_where_poor_people_travel_farther_urban) > 4 or len(states_where_poor_people_travel_farther_rural) > 4:
            with st.container(border=True):
                st.markdown('''<center><h2>How do our proposed facilities help?</h2></center>''', unsafe_allow_html=True)

                if len(states_where_poor_people_travel_farther_rural) > 4:
                    col1, col2 = st.columns(2)
                    with col1:
                        message = (f"Our model proposes opening new facilities to reduce distances to the nearest {facility.description[2:]} for both the average population and poor people. "
                                   f"Adding even a few of the 100 new facilities we propose in each state significantly reduces the disparity between poor people and the general population. "
                                   f"The plot on right shows existing disparities in urban areas and the disparities after opening {k} proposed facilities.")
                        custom_container(message, '#dfdfdf')

                        with st.expander('How is this computed?'):
                            st.markdown('''
                                For each state, we now add locations of our proposed facilities and compute the new disparity: the difference in average distance traveled poor people and the general population to access the nearest facility.
                                If this distance is negative, we consider the disparity to be zero. This is plotted in <span style="color:green;">green</span>. Existing disparities without our proposed facilities are also plotted.
                            ''', unsafe_allow_html=True)
                            st.markdown('''
                                Once again, our analysis has its limitations. However, our techniques themselves are independent of these limitations and are designed to reduce these disparities for protected groups on any dataset, while simultaneously reducing everyone's distances to nearest facilities.
                            ''')

                    with col2:
                        st.markdown('''<center><b>Opening our proposed facilities reduces the disparity (in miles) between poor people and the rest (rural areas)</b></center>''', unsafe_allow_html=True)

                        categories = list(states_where_poor_people_travel_farther_rural)
                        data_before = rural_distance_df.loc[states_where_poor_people_travel_farther_rural]['Mean Distance below_poverty'] - rural_distance_df.loc[states_where_poor_people_travel_farther_rural]['Mean Distance']
                        data_after = rural_distance_df_new.loc[states_where_poor_people_travel_farther_rural]['Mean Distance below_poverty'] - rural_distance_df_new.loc[states_where_poor_people_travel_farther_rural]['Mean Distance']

                        fig = go.Figure()

                        fig, config = plot_reduction_in_disparity(
                            fig,
                            rural_distance_df,
                            rural_distance_df_new,
                            'Mean Distance below_poverty',
                            'Mean Distance',
                            1.0,
                            k,
                            color='salmon'
                        )

                        st.plotly_chart(fig, use_container_width=True, config=config)

                if len(states_where_poor_people_travel_farther_urban) > 2:
                    col1, col2 = st.columns(2)
                    with col1:
                        message = (f"This plot shows existing disparities in urban areas and the disparities after opening {k} proposed facilities.")
                        custom_container(message, '#dfdfdf')

                    with col2:
                        st.markdown('''<center><b>Opening our proposed facilities reduces the disparity (in miles) between poor people and the rest (urban areas)</b></center>''', unsafe_allow_html=True)

                        fig = go.Figure()

                        fig, config = plot_reduction_in_disparity(
                            fig,
                            urban_distance_df,
                            urban_distance_df_new,
                            'Mean Distance below_poverty',
                            'Mean Distance',
                            0.5,
                            k
                        )

                        st.plotly_chart(fig, use_container_width=True, config=config)



def run_analysis_tab():
    col_left, col_right = st.columns([1, 3])

    if 'facility_display_name' not in st.session_state or st.session_state.facility_display_name is None:
        st.session_state.facility_display_name = UrgentCare.display_name

    with col_left:
        with st.container(border=True):
            facility = get_facility_from_user()

    run_analysis_for_poverty(facility, col_left, col_right)

    col_left, col_right = st.columns([1, 3])

    with col_left:
        with st.container(border=True):
            get_poverty_threshold_from_user(facility)

        with st.container(border=True):
            get_distance_thresholds_from_user(facility)

    with col_right:
        with st.container(border=True):
            st.markdown('''<center><h2>Racial disparities among medical deserts</h2></center>''', unsafe_allow_html=True)

            fig, proportion_of_overall_population, proportion_of_medical_deserts = plot_demographic_analysis(
                poverty_threshold=st.session_state.poverty_threshold,
                urban_distance_threshold=st.session_state.urban_distance_threshold,
                rural_distance_threshold=st.session_state.rural_distance_threshold,
                distance_label=facility.distance_label,
            )

            n_states_disproportionate = dict()
            for racial_label in proportion_of_overall_population.index:
                n_states_disproportionate[racial_label] = (proportion_of_medical_deserts.loc[racial_label] > proportion_of_overall_population.loc[racial_label]).sum()

            if sum(n_states_disproportionate.values()) - n_states_disproportionate['White'] > 50:
                message = f"Racial and ethnic minorities may be disproportionately affected by medical deserts in the US. " + \
                f"The heatmap below shows the difference between the proportion of the population in medical deserts and the overall population.<br>" + \
                f"- <span style=\"color:orange;\">Orange</span> indicates that the proportion of the population in medical deserts is higher than the overall population.<br>" + \
                f"- <span style=\"color:violet;\">Pink</span> indicates that the proportion of the population in medical deserts is lower than the overall population."
                custom_container(message, '#dfdfdf')

            fig.update_layout(
                margin=dict(t=5),
            )

            st.plotly_chart(fig, use_container_width=True)

