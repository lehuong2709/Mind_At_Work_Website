import random
import streamlit as st
from src.usa.constants import state_names, interesting_states
from src.usa.utils import get_state_of_the_day, compute_medical_deserts
from src.usa.plot_utils import plot_state, plot_blockgroups, plot_existing_facilities, plot_new_facilities
from src.usa.facilities import PharmaciesTop3
from src.usa.states import USAState
import plotly.graph_objects as go


# containers = {
#     "Home": [st.Page(page="medical-facility-desert-test.py", title="Home page")],
#     "": [
#         st.Page("medical-facility-deserts.py", title="Create your account"),
#         st.Page("containers/suggesting-new-facilities.py", title="Manage your account"),
#     ],
# }

st.set_page_config(page_title='medical-deserts-in-usa', initial_sidebar_state='collapsed', layout='wide')

st.markdown("""
    <h1 style="font-size: 40px; text-align: center; margin-bottom: 0em; margin-top: 0em; line-height: 1.0;">
        Facility deserts in
        <span style="color: #c41636">
            USA
        </span>
    </h1>
    """, unsafe_allow_html=True)

st.markdown('''This tool identifies facility deserts in the US – poorer areas with low access to various critical 
            facilities such as pharmacies, hospitals, and schools – and suggest locations of new facilities to reduce 
            the number of facility deserts.''')

# with st.sidebar:
#     st.navigation(containers)

state_of_the_day = get_state_of_the_day(interesting_states)
State = USAState(state_of_the_day)
blockgroup_df = State.get_census_data(level='blockgroup')

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        to_medical_deserts = st.button('Visualize facility deserts', type='primary', use_container_width=True)
        if to_medical_deserts:
            st.switch_page('medical-facility-deserts.py')

        desert_df = compute_medical_deserts(state_df=blockgroup_df)

        fig = go.Figure()
        fig, _ = plot_state(fig=fig, State=State)
        fig = plot_blockgroups(fig=fig, blockgroup_df=desert_df)

        st.plotly_chart(fig, use_container_width=True)


with col2:
    with st.container(border=True):
        to_suggesting_facilities = st.button('Suggest new facilities', type='primary', use_container_width=True)
        if to_suggesting_facilities:
            st.switch_page('containers/suggesting-new-facilities.py')

        facility = PharmaciesTop3

        fig = go.Figure()
        fig, bounds = plot_state(fig=fig, State=State)

        fig = plot_existing_facilities(fig=fig, facility=facility, bounds=bounds)
        fig = plot_new_facilities(fig=fig, state_fips=State.fips, p='combined', k=25, name='Suggested facilities',
                                  facility=facility, marker_symbol='diamond', marker_color='cyan', marker_line_width=2)

        st.plotly_chart(fig)
