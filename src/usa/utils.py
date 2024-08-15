from src.constants import scatter_palette, MILES_TO_KM
import streamlit as st
from datetime import datetime


racial_labels = ['white_alone', 'black_alone', 'aian_alone',
                 'asian_alone', 'nhopi_alone', 'hispanic', 'other']
racial_labels_display_names = {
    'white_alone': 'White',
    'black_alone': 'Black',
    'aian_alone': 'AIAN',
    'asian_alone': 'Asian',
    'nhopi_alone': 'NHOPI',
    'hispanic': 'Hispanic',
    'other': 'Other'
}
colors = {racial_labels[i]: scatter_palette[i] for i in range(len(racial_labels))}


def get_page_url(page_name):
    is_experimental = st.secrets.get('IS_EXPERIMENTAL')
    if is_experimental:
        return 'http://localhost:8501/' + page_name
    else:
        return 'https://usa-medical-deserts.streamlit.app/' + page_name


def get_demographic_data(census_df, racial_labels):
    # data = {}
    # for racial_label in racial_labels:
    #     if racial_label in census_df['racial_majority'].unique():
    #         data[racial_label] = len(census_df[census_df['racial_majority'] == racial_label])

    return dict(census_df['racial_majority'].value_counts())

    # return data


@st.cache_data
def compute_medical_deserts(state_df, poverty_threshold=20, n_urban=2, n_rural=10, distance_label='Closest_Distance_Pharmacies_Top3'):
    desert_df = state_df[state_df['below_poverty'] >= poverty_threshold]
    desert_df = desert_df[((desert_df['urban'] == 1) & (desert_df[distance_label] > MILES_TO_KM * n_urban)) | ((desert_df['urban'] == 0) & (desert_df[distance_label] > MILES_TO_KM * n_rural))]

    return desert_df[['Latitude', 'Longitude', 'below_poverty', 'racial_majority', 'urban', distance_label]]


def get_facility_from_facility_name(facilities, facility_name):
    for facility in facilities:
        if facility.display_name == facility_name:
            return facility


def get_state_of_the_day(state_names):
    day_of_year = datetime.now().timetuple().tm_yday
    state_of_the_day = state_names[day_of_year % len(state_names)]
    return state_of_the_day

