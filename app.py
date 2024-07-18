from flask import Flask, Response, make_response, request, jsonify
import joblib
import numpy as np
import pandas as pd
from flask_cors import CORS
from model import calculate_path_danger, calculate_point_danger, decode_polyline, get_directions
import requests


app = Flask(__name__)
CORS(app)

# Load the saved kNN model
joblib_file = "knn_model.pkl"
knn_model = joblib.load(joblib_file)

# Load your data that contains 'accident_score'
data = pd.read_csv('Data_Rapid_2019.csv')
data['accident_score'] = (data['Death'] * 2) + (data['Grievous'] * 1.5) + (data['Minor'] * 0.5)

# We will work on improving this calculation and taking more features into consideration
data = data[data['accident_score'] != 0]
x_di = data['accident_score'].values

@app.route('/test')
def test():
    return Response('{ "message":"Application is up and running"}', status=201, mimetype='application/json')

@app.route('/predict', methods=['POST'])
def predict():
    try :
        # Get data from POST request
        data = request.get_json(force=True)
        
        # Parse the data for prediction
        longitude = data['Longitude']
        latitude = data['Latitude']
        
        # Create an array for prediction
        prediction_data = np.array([[longitude, latitude]])
        
        # Get the nearest neighbors using the kNN model
        distances, indices = knn_model.kneighbors(prediction_data)
        
        # Calculate the danger score
        danger_score = calculate_point_danger(longitude, latitude, distances, indices,x_di,data)
        
        # Return the danger score as JSON
        # return jsonify({'danger_score': danger_score})
        response = jsonify({'danger_score': danger_score})
        return make_response(response, 200) 
    except Exception as e:
        return Response('{ "message":"Please try later"}', status=500, mimetype='application/json')




@app.route('/api/v1/test2', methods =['POST'])
def test2():
    data = request.get_json(force=True)
    print(data)
    return Response('{"message": "Deepanshu garg"}',200)


@app.route('/api/v1/direction', methods = ['POST'])
def getdirection():
    try:
        data = request.get_json(force=True)
        origin_lat = str(data['origin_lat'])
        origin_long = str(data['origin_long'])

        dest_lat = str(data['dest_lat'])
        dest_long = str(data['dest_long'])

        directions = get_directions(origin_lat, origin_long, dest_lat, dest_long)

        direction_polylines = []
        if directions['status'] == 'OK':
            for route in directions['routes']:
                polyline = route['overview_polyline']['points']
                distance = route['legs'][0]['distance']['text']
                duration = route['legs'][0]['duration']['text']
                direction_polylines.append({"polyline": polyline, "distance": distance, "duration": duration})
        else:
             print("Error: ", directions['status'])
             response  = jsonify({'message':  directions['status']})
             return make_response(response, 500)
        
        result = []
             
        for r in direction_polylines:
            lat_long_arr = decode_polyline(r['polyline'])
            # danger = calculate_path_danger(lat_long_arr,knn_model,x_di)
            sz = len(lat_long_arr)
            danger =0
            for a in lat_long_arr:
                to_send = []
                to_send.append(a)
                dist,ind = knn_model.kneighbors(to_send)
                temp = calculate_point_danger(a[0],a[1],dist,ind,x_di)
                danger+=temp
            danger = danger/sz
            result.append({"polyline": r['polyline'], "danger_score": danger, "duration": r['duration'], "distance": r['distance']})
            print(result)
            response = jsonify(result)
        return make_response(response, 200)
    except Exception as e:
        response = jsonify({"message": e})
        return make_response(response,500)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port = 5000,debug=True)





#     import requests

# API_KEY = 'AIzaSyBy45iq2jviV0N6f1HXK_FzyUag9apSsD4'
# origin = '40.712776,-74.005974'  # New York City
# destination = '42.360082,-71.058880'  # Boston
# url = f'https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&alternatives=true&key={API_KEY}'




