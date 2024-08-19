import streamlit as st
from src.usa.plot_utils import plot_state, plot_stacked_bar, plot_existing_facilities, plot_medical_deserts, plot_blockgroups, plot_voronoi_cells
from src.usa.states import USAState
from src.usa.constants import state_names
import plotly.graph_objects as go
import pandas as pd


def hex_to_rgba(hex_color, alpha):
    hex_color = hex_color.lstrip('#')
    return f'rgba({int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)}, {alpha})'


def plot_visited_states(fig, StatesList):
    data = pd.DataFrame({
        'state': ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'],
        'value': [0] * 50  # Default value for all states
    })
    # Set a different value for the state to highlight it

    # Pacific Time Zone
    pacific_timezone_states = ['CA', 'OR', 'WA', 'NV']

    # Mountain Time Zone
    mountain_timezone_states = ['AZ', 'CO', 'ID', 'MT', 'NM', 'UT', 'WY']

    # Central Time Zone
    central_timezone_states = ['AL', 'AR', 'IL', 'IA', 'KS', 'KY', 'LA', 'MN', 'MS', 'MO', 'NE', 'ND', 'OK', 'SD', 'TN', 'TX', 'WI']

    # Eastern Time Zone
    eastern_timezone_states = ['CT', 'DE', 'FL', 'GA', 'IN', 'KY', 'ME', 'MD', 'MA', 'MI', 'NH', 'NJ', 'NY', 'NC', 'OH', 'PA', 'RI', 'SC', 'VT', 'VA', 'WV']

    # Alaska Time Zone
    alaska_timezone_states = ['AK']

    # Hawaii-Aleutian Time Zone
    hawaii_aleutian_timezone_states = ['HI']

    for State in StatesList:
        state_name = State.name
        state_abbreviation = State.abbreviation

        if state_abbreviation in pacific_timezone_states:
            data.loc[data['state'] == state_abbreviation, 'value'] = 1
        elif state_abbreviation in mountain_timezone_states:
            data.loc[data['state'] == state_abbreviation, 'value'] = 2
        elif state_abbreviation in central_timezone_states:
            data.loc[data['state'] == state_abbreviation, 'value'] = 3
        elif state_abbreviation in eastern_timezone_states:
            data.loc[data['state'] == state_abbreviation, 'value'] = 4
        elif state_abbreviation in alaska_timezone_states:
            data.loc[data['state'] == state_abbreviation, 'value'] = 5
        else:
            data.loc[data['state'] == state_abbreviation, 'value'] = 6

    hard_colors_hex = ['#fbfcf9', '#21d565', '#ff0004', '#9918fe', '#007fee', '#696969', '#ffe00a']
    soft_colors_rgba = [hex_to_rgba(color, 0.5) for color in hard_colors_hex]

    choropleth = go.Choropleth(
        locations=data['state'],  # Spatial coordinates
        z=data['value'].astype(float),  # Data to be color-coded
        locationmode='USA-states',  # Set of locations match entries in `locations`
        # colorscale=[[0, '#fbfcf9'], [1, 'green'], [2, 'red']],  # Fixed color scale
        colorscale=soft_colors_rgba,
        zmin=0,
        zmax=6,
        # colorbar=dict(title="Value", tickvals=[0, 1], ticktext=['0', '1']),  # Colorbar settings
        # # colorscale=["red", "#f9f3e1"],  # Color scale for the choropleth map
        showscale=False,
        hoverinfo='location',
    )

    # Add the choropleth map to the figure
    fig.add_trace(choropleth)

    return fig


st.set_page_config(layout='wide')

st.markdown(
    """
    <style>
    .css-1d391kg {  # This class targets the main container
        padding-top: 0rem;
    }
    .css-18e3th9 {  # This class targets the header container
        padding-top: 0rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

visited_states = st.multiselect(label='Select the states you have visited', options=state_names)
st.markdown('''<br>''', unsafe_allow_html=True)

fig = go.Figure()

StatesList = []
for state in visited_states:
    State = USAState(name=state)
    StatesList.append(State)

fig = plot_visited_states(fig, StatesList)

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
    scope="usa",
    # projection_type='mercator',
)

fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    autosize=False,
    showlegend=False,
    # legend=dict(
    #     itemsizing='constant',
    #     x=0.02,
    #     y=0.98,
    #     orientation='v',
    #     bgcolor='rgba(255,255,255,0.5)',
    # )
)

st.plotly_chart(fig, use_container_width=True)
