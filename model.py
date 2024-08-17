# Decode the polyline string and return array of lat long pair

import os
from dotenv import load_dotenv
import requests
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor, NearestNeighbors
import pickle
import numpy as np
from datetime import datetime

pickle_file_path = 'array.pkl'

# with open(pickle_file_path, 'rb') as f:
#     data = pickle.load(f)

load_dotenv()      

def import_data():
    with open(pickle_file_path, 'rb') as f:
        data = pickle.load(f)
    return data


data = import_data()


PROJECT_ID = os.getenv("PROJECT_ID")

def decode_polyline(encoded):
    if not encoded:
        return []

    poly = []
    index = 0
    lat = 0
    lng = 0

    while index < len(encoded):
        b = shift = result = 0

        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break

        dlat = ~(result >> 1) if result & 1 else (result >> 1)
        lat += dlat

        shift = result = 0

        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break

        dlng = ~(result >> 1) if result & 1 else (result >> 1)
        lng += dlng


        poly.append([lng/1e5,lat/1e5])

    return poly


def calculate_danger_score(lat, lon, filtered_data=None, k=50):
    
    try:
        
      if filtered_data is None:
        filtered_data = data

      # print("deepu")
    
      locations = filtered_data[['Latitude', 'Longitude']].drop_duplicates().values
      nbrs = NearestNeighbors(
          n_neighbors=k, algorithm='ball_tree', metric='haversine').fit(locations)
      distances, indices = nbrs.kneighbors([[lat, lon]])

      
      # nearest_scores = filtered_data.iloc[indices[0]]['accident_score']
      # return distances,nearest_scores
      # print(distances)
      ans = 0
      sz = len(distances[0])
      # print(sz)
      i = 0
      while i < sz:
        # di = x_di[ind[0][i]]
        di  = filtered_data['accident_score'].values[indices[0][i]]
        # di = nearest_scores[0][i]
        # print("Timus")
        we = 1/(200*(distances[0][i] + 0.00000000000001))
        if we > 2:  #Hyperparameter
          we = 2
        ans = ans + di*we
        i = i+1
      
      # print("hi" + ans/sz)
      return ans/sz
    except Exception as e:
        print(str(e) + "deepu")
        return 0


def calculate_personalized_score(lat, lon, gender=None, time_section=None, k=10):
    # Filter data by gender and time section if specified
    filtered_data = data
    if gender:
        # print(gender)
        filtered_data = filtered_data[filtered_data['Gender'].str.lower() == gender.lower()]
    if time_section:
        # print(time_section)
        filtered_data = filtered_data[filtered_data['time_section'] == time_section]
    if filtered_data.empty:
        print("No data available for the specified gender or time section.")
        return np.nan
    # print(filtered_data)
    # Use filtered data to calculate danger score
    return calculate_danger_score(lat, lon, filtered_data, k)



def get_directions(origin_lat,origin_long,dest_lat,dest_long,travel_mode):
    origin = origin_lat + ', ' + origin_long
    destination = dest_lat + ', ' + dest_long

    API_KEY = os.getenv("API_KEY")
    url = f'https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&mode={travel_mode}&alternatives=true&key={API_KEY}'

    response = requests.get(url)
    directions = response.json()
    return directions

accident_type_weightage = {
    'Fatal': 4,
    'Grevious Injury': 3,
    'Minor Injury': 2,
    'Non Injury': 1,
    np.nan: 0  # Assign a weightage for NaN if needed
}
safety_device_weights = {
    'Without wearing seatbelt': 2,
    'Without wearing Helmet': 2,
    'Seat Belt': 0,
    'Wearing Helmet': 0
}

alcohol_drugs_weights = {
    'yes': 3,
    'no': 0,
    'UpdateLater': 0,
    'Yes': 3
}



def time_to_section(time_strs):
    time_str = str(time_strs)
    if isinstance(time_str, str):  # Ensure time_str is a string
        try:
            # Convert time to a datetime object
            # print(time_str)
            time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f').time()
            # Define time sections
            # print(time_obj)
            if time_obj >= datetime.strptime('07:00:00', '%H:%M:%S').time() and time_obj < datetime.strptime('19:00:00', '%H:%M:%S').time():
                return 'Morning'
            else:
                return 'Night'
        except ValueError:
            # print("wrong2")
            return None  
    else:
        # print("wrong")
        return None  

# accident_score_data['Date accident'] = pd.to_datetime(accident_score_data['Date accident'], errors='coerce')


def calculate_age_weightage(date, interval_months=3):
  # Ensure the date is valid
  current_date = datetime.now()
  if pd.isna(date):
      return 0  # Assign zero weightage for invalid dates
  # Calculate the difference in months between the accident date and the current date
  months_difference = (current_date.year - date.year) *12 + current_date.month - date.month
  # Calculate weightage: more recent dates have higher weightage
  weightage = 1 / ((months_difference // interval_months) + 1)
  return weightage

def preprocess_and_calculate_scores():
    # Ensure 'Date accident' is a datetime object
    # self.data['Date accident'] = pd.to_datetime(self.data['Date accident'], errors='coerce')

    # Calculate age weightage for each accident
    data['age_weightage'] = data['Date accident'].apply(lambda x: calculate_age_weightage(x))

    # Map accident type to weightages
    data['accident_type_weightage'] = data['Accident type'].map(accident_type_weightage)

    # Calculate score based on accident type weightage and age weightage
    data['individual_score'] = (
        (data['accident_type_weightage'] + (data['Death']* 5) + (data['Grievous']*3) + (data['Minor']*2))* data['age_weightage']
    )

    # Group by latitude and longitude
    grouped = data.groupby(['Latitude', 'Longitude'])

    # Calculate average score for each group
    data['accident_score'] = grouped['individual_score'].transform('mean')

    return data


def add_data(new_data_values):
    # Convert new data values to DataFrame
    global data
    print("hi")
    print(data)
    print("hi")
    print(new_data_values)
    new_data = pd.DataFrame(new_data_values, columns=data.columns)

    # Ensure 'Date accident' is a datetime object in the new data
    new_data['Date accident'] = pd.to_datetime(new_data['Date accident'], errors='coerce')

    # Append new data and recalculate scores
    data = pd.concat([data, new_data], ignore_index=True)
    preprocess_and_calculate_scores()
