import streamlit as st
from src.usa.utils import get_facility_from_facility_name
from src.usa.facilities import PharmaciesTop3, UrgentCare, Hospitals, NursingHomes, PrivateSchools, FDICInsuredBanks, ChildCare
from src.constants import DEFAULT_POVERTY_THRESHOLD, DEFAULT_RURAL_DISTANCE_THRESHOLD, DEFAULT_URBAN_DISTANCE_THRESHOLD


facilities = [PharmaciesTop3, UrgentCare, Hospitals, NursingHomes, PrivateSchools, FDICInsuredBanks, ChildCare]
facility_display_names = [facility.display_name for facility in facilities]


def update_variable(variable_name):
    st.session_state[variable_name] = st.session_state['_' + variable_name]


def get_facility_from_user():
    """
    Get the facility type from the user using a selectbox.
    """
    # Set the default facility type to 'Pharmacy chains'
    if 'facility_display_name' not in st.session_state:
        st.session_state.facility_display_name = 'Pharmacy chains'

    # Set current facility type to the default facility type
    facility_display_name = st.session_state['facility_display_name']
    index = facility_display_names.index(facility_display_name)

    # Get the facility type from the user
    facility_display_name = st.selectbox(
        label='Choose a facility',
        options=facility_display_names,
        index=index,
        key='_facility_display_name',
        on_change=lambda: update_variable('facility_display_name'),
        help='Select the type of facility to analyze',
    )
    # Update the facility type in the session state

    # Get the facility object from the facility type
    facility = get_facility_from_facility_name(facilities, st.session_state.facility_display_name)

    return facility


def get_poverty_threshold_from_user(facility):
    """
    Get the poverty threshold from the user using a slider.
    """
    # Set the default poverty threshold to 20%
    if 'poverty_threshold' not in st.session_state:
        st.session_state['poverty_threshold'] = DEFAULT_POVERTY_THRESHOLD
    poverty_threshold = st.session_state['poverty_threshold']

    # Get the poverty threshold from the user
    st.slider(
        label=r'Choose poverty threshold $p$%',
        min_value=0, max_value=100, step=5, value=poverty_threshold,
        key='_poverty_threshold',
        on_change=lambda: update_variable('poverty_threshold'),
        help='Only blockgroups with over $p$% of the population below the poverty line are considered ' + facility.type + ' deserts.',
    )

    return


def get_distance_thresholds_from_user(facility):
    """
    Get the distance thresholds for urban and rural areas from the user using sliders.
    """
    st.write('Choose distance threshold $n$ miles')
    col_side1, col_side2 = st.columns(2)

    # Set the default distance thresholds to 2 miles for urban areas
    if 'urban_distance_threshold' not in st.session_state:
        st.session_state['urban_distance_threshold'] = DEFAULT_URBAN_DISTANCE_THRESHOLD
    urban_distance_threshold = st.session_state['urban_distance_threshold']

    # Get the distance threshold for urban areas from the user
    col_side1.slider(
        label=r'For urban areas',
        min_value=0.0, max_value=15.0, step=0.5, value=urban_distance_threshold,
        format='%.1f',
        key = '_urban_distance_threshold',
        on_change=lambda: update_variable('urban_distance_threshold'),
        help='Distance threshold for urban areas; only blockgroups further than this distance from the nearest facility are considered ' + facility.type + ' deserts.',
    )

    # Set the default distance thresholds to 10 miles for rural areas
    if 'rural_distance_threshold' not in st.session_state:
        st.session_state['rural_distance_threshold'] = DEFAULT_RURAL_DISTANCE_THRESHOLD
    rural_distance_threshold = st.session_state['rural_distance_threshold']

    # Get the distance threshold for rural areas from the user
    col_side2.slider(
        label=r'For rural areas',
        min_value=0.0, max_value=30.0, step=1.0, value=rural_distance_threshold,
        format='%.1f',
        key='_rural_distance_threshold',
        on_change=lambda: update_variable('rural_distance_threshold'),
        help='Distance threshold for rural areas; only blockgroups further than this distance from the nearest facility are considered ' + facility.type + ' deserts.',
    )

    return
