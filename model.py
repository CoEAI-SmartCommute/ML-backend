import pandas as pd
import numpy as np
import pickle
from sklearn.neighbors import NearestNeighbors
# from data import accident_data
from increment import update_accident_data, update_crime_data

pickle_file_path = 'array.pkl'
pickle_file_path_crime = 'array2.pkl'

def import_data():
    with open(pickle_file_path, 'rb') as f:
        accident_data = pickle.load(f)
    return accident_data


def import_crime_data():
    with open(pickle_file_path_crime, 'rb') as f:
        crime_data = pickle.load(f)
    return crime_data


accident_data = import_data()
crime_data = import_crime_data()

def calculate_combined_score(lat, lon, filtered_accident_data, filtered_crime_data, k=1):
    accident_locations = filtered_accident_data[[
        'Latitude', 'Longitude']].drop_duplicates().values
    crime_locations = filtered_crime_data[[
        'Latitude', 'Longitude']].drop_duplicates().values
    
    # print(crime_locations.shape)

    accident_nbrs = NearestNeighbors(
        n_neighbors=k, algorithm='ball_tree', metric='haversine').fit(accident_locations)
    crime_nbrs = NearestNeighbors(n_neighbors=10, algorithm='ball_tree', metric='haversine').fit(crime_locations)
    accident_distances, accident_indices = accident_nbrs.kneighbors([[lat, lon]])

    crime_distances, crime_indices = crime_nbrs.kneighbors([[lat, lon]])

    acc_score = 0
    sz = 40
    # acc_score = np.mean(di)
    # ci = filtered_crime_data['crime_score'].values[crime_indices[0]]
    # crime_score = np.mean(ci)

    i = 0
    # accident_distances[0] = 
    # accident_distances[0][accident_distances[0] == 0] = 1.0/200

    # accident_distances[0] = accident_distances[0]*200
    # accident_distances[0] = 1/accident_distances[0]
    # accident_distances[0][accident_distances[0] > 2.0] = 2.0
    # ccc = filtered_accident_data['accident_score'].values[accident_indices[0]]*accident_distances[0]
    # acc_score = np.mean(ccc)
    while i < sz:  
        di = filtered_accident_data['accident_score'].values[accident_indices[0][i]]
        we = 1/(200)
        if accident_distances[0][i]==0:
            we=1
        else:
            we = we*(1/accident_distances[0][i])
            
        if we > 2.0:  
            we = 2
        acc_score = acc_score + di*we
        i = i+1

    i=0
    crime_score=0
    while i < 10:
        di = filtered_crime_data['crime_score'].values[crime_indices[0][i]]
        we = 1/(200)
        if crime_distances[0][i] == 0:
            we = 1
        else:
            we = we*(1/crime_distances[0][i])

        if we > 2.0:
            we = 2
        crime_score = crime_score + di*we
        i = i+1

    crime_score = crime_score/10
    acc_score = acc_score/sz

    # print(crime_score)
    # print(acc_score)
    return crime_score,acc_score

def filter_data(gender,time_section):
    filtered_accident_data = accident_data
    filtered_crime_data = crime_data

    if gender:
        filtered_accident_data = filtered_accident_data[filtered_accident_data['Gender'].str.lower(
        ) == gender.lower()]
        filtered_crime_data = filtered_crime_data[filtered_crime_data['Gender'].str.lower(
        ) == gender.lower()]

    if time_section:
        filtered_accident_data = filtered_accident_data[
            filtered_accident_data['time_section'] == time_section]
        filtered_crime_data = filtered_crime_data[filtered_crime_data['time_section'] == time_section]

    if filtered_accident_data.empty or filtered_crime_data.empty:
        # print("No data available for the specified gender or time section.")
        return np.nan
    
    return filtered_accident_data, filtered_crime_data, accident_data, crime_data



def data_update(new_data_value):
    global accident_data
    print(len(accident_data))
    accident_data = update_accident_data(accident_data,new_data_value)
    print(len(accident_data))



def data_update_crime(new_data_value):
    global crime_data
    crime_data = update_crime_data(crime_data,new_data_value)

