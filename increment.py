import numpy as np
import pandas as pd
from datetime import datetime

accident_type_weightage = {
    'Fatal': 4,
    'Grevious Injury': 3,
    'Minor Injury': 2,
    'Non Injury': 1,
    np.nan: 0
}
crime_category_weightage = {
    'Violence and Assault': 8,
    'Traffic and Road Safety': 4,
    'Regulatory and Miscellaneous': 4,
    'Property Crimes': 5,
    'Missing Persons': 6,
    'Economic Activities': 4,
    'Uncategorized': 4,
    'Offences with Violence': 6,
    'House Theft': 6,
    np.nan: 0  # Assign a weightage for NaN if needed
}

def time_to_section(time_strs):
    time_str = str(time_strs)
    if isinstance(time_str, str):
        try:

            time_obj = datetime.strptime(
                time_str, '%Y-%m-%d %H:%M:%S.%f').time()
            print(time_obj)
            print(time_str)

            if time_obj >= datetime.strptime('07:00:00', '%H:%M:%S').time() and time_obj < datetime.strptime('19:00:00', '%H:%M:%S').time():
                return 'Morning'
            else:
                return 'Night'
        except ValueError:
            print(time_str)
            return None
    else:
        # print(time_str)
        return None


def calculate_age_weightage(date, interval_months=3):

    current_date = datetime.now()
    if pd.isna(date):
        return 0
    months_difference = (current_date.year - date.year) *12 + current_date.month - date.month

    weightage = 1 / ((months_difference // interval_months) + 1)
    return weightage


def preprocess_and_calculate_accident_scores(accident_data):

    accident_data['age_weightage'] = accident_data['Date accident'].apply(
        lambda x: calculate_age_weightage(x))

    accident_data['accident_type_weightage'] = accident_data['Accident type'].map(
        accident_type_weightage)

    accident_data['individual_score'] = (
        (accident_data['accident_type_weightage'] + (accident_data['Death'] * 5) +
         (accident_data['Grievous']*3) + (accident_data['Minor']*2)) * accident_data['age_weightage']
    )

    grouped = accident_data.groupby(['Latitude', 'Longitude'])

    accident_data['accident_score'] = grouped['individual_score'].transform(
        'mean')
    
    return accident_data

def preprocess_and_calculate_crime_scores(crime_data):
    # Calculate age weightage for each crime
    crime_data['age_weightage'] = crime_data['Date of Report'].apply(
        lambda x: calculate_age_weightage(x))

    # Map crime category to weightages
    crime_data['crime_category_weightage'] = crime_data['Category'].map(crime_category_weightage)

    # Calculate score based on crime category weightage and age weightage
    crime_data['crime_score'] = (
        crime_data['crime_category_weightage'] *
        crime_data['age_weightage']
    )

    # Group by latitude and longitude
    grouped = crime_data.groupby(['Latitude', 'Longitude'])

    # Calculate average score for each group
    crime_data['crime_score'] = grouped['crime_score'].transform(
        'mean')

    return crime_data



def update_accident_data(accident_data,new_data_values):

    new_data = pd.DataFrame(new_data_values, columns=accident_data.columns)

    new_data['Date accident'] = pd.to_datetime(
        new_data['Date accident'], errors='coerce')
    accident_data = pd.concat([accident_data, new_data], ignore_index=True)
    return preprocess_and_calculate_accident_scores(accident_data)

def update_crime_data(crime_data, new_crime_values):
    # Convert new data values to DataFrame
    new_data = pd.DataFrame(new_crime_values, columns=crime_data.columns)

    # Ensure 'Date' is a datetime object in the new data
    new_data['Date of Report'] = pd.to_datetime(new_data['Date of Report'], errors='coerce')

    # Append new data and recalculate scores
    crime_data = pd.concat([crime_data, new_data], ignore_index=True)
    return preprocess_and_calculate_crime_scores(crime_data)
    # crime_preprocessed_df = preprocess_and_calculate_crime_scores()
