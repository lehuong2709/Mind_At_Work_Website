from src.constants import scatter_palette, MILES_TO_KM


racial_labels = ['white_alone', 'black_alone', 'aian_alone',
                 'asian_alone', 'nhopi_alone', 'hispanic', 'other']
colors = {racial_labels[i]: scatter_palette[i] for i in range(len(racial_labels))}


def get_demographic_data(census_df, racial_labels):
    data = {}
    for racial_label in racial_labels:
        if racial_label in census_df['racial_majority'].unique():
            data[racial_label] = len(census_df[census_df['racial_majority'] == racial_label])

    return data


def compute_medical_deserts(state_df, poverty_threshold=20, n_urban=2, n_rural=10, distance_label='Closest_Distance_Pharmacies_Top3'):
    desert_df = state_df[state_df['below_poverty'] >= poverty_threshold]
    desert_df = desert_df[((desert_df['urban'] == 1) & (desert_df[distance_label] > MILES_TO_KM * n_urban)) | ((desert_df['urban'] == 0) & (desert_df[distance_label] > MILES_TO_KM * n_rural))]

    return desert_df[['Latitude', 'Longitude', 'below_poverty', 'racial_majority', 'urban', distance_label]]


