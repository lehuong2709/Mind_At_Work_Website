from src.constants import usa_constants
from random import randint
import streamlit as st
import matplotlib.pyplot as plt
from src import usa, constants

st.set_page_config(layout="wide", initial_sidebar_state='expanded', page_title='Facility Deserts')

states = usa_constants.state_names
states.sort()
r = randint(0, len(states))

state_name = st.sidebar.selectbox('Select a state', options=states, index=0)

st.title('Facility Deserts in :orange[' + state_name + ']')

col1, col2 = st.columns(2)
State = usa.USAState(state_name)

poverty_threshold = st.sidebar.slider('Poverty Threshold', 0, 100, 5)
distance_threshold = st.sidebar.slider('Distance Threshold (miles)', 0, 100, 5)

with col1:
    State.plot_poverty_by_tract(savefile=False, savefile_path='../plots/usa/poverty_rate/', census_key=constants.usa_constants.census_key, dpi=constants.default_dpi)
    st.pyplot(plt, dpi=constants.default_dpi, bbox_inches='tight')

with col2:
    State.plot_facility_deserts(facility_name='Dialysis_Centers', savefile=True, poverty_threshold=poverty_threshold, distance_threshold=distance_threshold)
    st.pyplot(plt, dpi=constants.default_dpi, bbox_inches='tight')
