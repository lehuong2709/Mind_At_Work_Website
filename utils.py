desert_types = {
    'Pharmacy chains': 'Medical',
    'Urgent care centers': 'Medical',
    'Hospitals': 'Medical',
    'Dialysis centers': 'Medical',
    'Nursing homes': 'Medical',
    'Private schools': 'Education',
    'Banks': 'Banking',
    'Child care centers': 'Facility',
    'Logistics chains': 'Logistics'
}


def get_message(facility):
    facility_descriptor = {
        'Pharmacy chains': 'a CVS/Walgreeens/Walmart pharmacy',
        'Urgent care centers': 'an urgent care center',
        'Hospitals': 'a hospital',
        'Dialysis centers': 'a dialysis center',
        'Nursing homes': 'a nursing home',
        'Private schools': 'a private school',
        'Banks': """an [FDIC insured bank](https://en.wikipedia.org/wiki/Federal_Deposit_Insurance_Corporation)""",
        'Child care centers': 'a child care center',
        'Logistics chains': 'a FedEx/UPS/DHL facility'
    }

    message = (
        """Let's define a **""" + desert_types[facility].lower() + """ desert** as a US census
        [blockgroup](https://en.wikipedia.org/wiki/Census_block_group) that is more than $n$ miles away from """ +
        facility_descriptor[facility] + """ and with over $p$% of the population living
        below the poverty line. Choose $n$ and $p$ from the sidebar."""
    )

    return message


distance_labels = {
    'Pharmacy chains': 'Closest_Distance_Pharmacies_Top3',
    'Urgent care centers': 'Closest_Distance_Urgent_Care_Centers',
    'Hospitals': 'Closest_Distance_Hospitals',
    'Nursing homes': 'Closest_Distance_Nursing_Homes',
    'Private schools': 'Closest_Distance_Private_Schools',
    'Banks': 'Closest_Distance_Banks',
    'Child care centers': 'Closest_Distance_Childcare',
    'Logistics chains': 'Closest_Distance_Logistical_Top3'
}


show_location_labels = {
    'Pharmacy chains': 'Show CVS/Walgreens/Walmart locations',
    'Urgent care centers': 'Show urgent care locations',
    'Hospitals': 'Show hospital locations',
    'Nursing homes': 'Show nursing home locations',
    'Private schools': 'Show private school locations',
    'Banks': 'Show bank locations',
    'Child care centers': 'Show child care center locations',
    'Logistics chains': 'Show FedEx/UPS/DHL locations',
}

show_voronoi_labels = {
    'Pharmacy chains': 'Show pharmacy Voronoi cells',
    'Urgent care centers': 'Show urgent care Voronoi cells',
    'Hospitals': 'Show hospital Voronoi cells',
    'Nursing homes': 'Show nursing home Voronoi cells',
    'Private schools': 'Show private school Voronoi cells',
    'Banks': 'Show bank Voronoi cells',
    'Child care centers': 'Show child care center Voronoi cells',
    'Logistics chains': None,
}

voronoi_file_names = {
    'Pharmacy chains': 'data/usa/facilities/pharmacies_top3/voronoi_state_shapefiles/',
    'Urgent care centers': 'data/usa/facilities/urgentcare_centers/voronoi_state_shapefiles/',
    'Hospitals': 'data/usa/facilities/hospitals/voronoi_state_shapefiles/',
    'Nursing homes': 'data/usa/facilities/nursing_homes/voronoi_state_shapefiles/',
    'Private schools': 'data/usa/facilities/private_schools/voronoi_state_shapefiles/',
    'Banks': 'data/usa/facilities/banks/voronoi_state_shapefiles/',
    'Child care centers': 'data/usa/facilities/childcare/voronoi_state_shapefiles/',
    'Logistics chains': None,
}
