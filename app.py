from flask import Flask, Response, make_response, request, jsonify
import numpy as np
import pandas as pd
from flask_cors import CORS
from model import  PROJECT_ID, SYSTEM_INSTRUCT, calculate_personalized_score, decode_polyline, get_directions, time_to_section
import requests
import datetime
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Image
# import os
# from dotenv import load_dotenv


app = Flask(__name__)
CORS(app)


# load_dotenv()
@app.route('/test')
def test():
    return Response('{ "message":"Application is up and running"}', status=201, mimetype='application/json')


@app.route('/danger_score', methods=['POST'])
def predict():
    try :
        # print("hi1")
        data = request.get_json(force=True)
        # print("hi2")
        longitude = data['Longitude']
        latitude = data['Latitude']

        # print(longitude)

        current_time =  datetime.datetime.now()
        # print(current_time)
        time_section  = time_to_section(current_time)
        # print(time_section)
         
        danger_score = calculate_personalized_score(latitude, longitude,None, time_section)

        # danger_score= 7-danger_score
        # danger_score= np.minimum(10,danger_score*10/7)


        response = jsonify({'danger_score': danger_score})
        return make_response(response, 200) 
    except Exception as e:
        return Response('{ "message":"Please try later"}', status=500, mimetype='application/json')






@app.route('/routes', methods = ['POST'])
def getdirection():
    try:
        data = request.get_json(force=True)
        origin_lat = str(data['origin_lat'])
        origin_long = str(data['origin_long'])

        dest_lat = str(data['dest_lat'])
        dest_long = str(data['dest_long'])
        gender = data['gender']

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
        uid=1
        current_time = datetime.datetime.now()
        time_section = time_to_section(current_time)
        print(len(direction_polylines))
        for r in direction_polylines:
            lat_long_arr = decode_polyline(r['polyline'])
            # danger = calculate_path_danger(lat_long_arr,knn_model,x_di)
            sz = len(lat_long_arr)
            danger =0
            for a in lat_long_arr:
                # to_send = []
                # to_send.append(a)
                # dist,ind = knn_model.kneighbors(to_send)
                # temp = calculate_point_danger(to_send)
                temp = calculate_personalized_score(a[1], a[0], gender, time_section)
                danger+=temp
            danger = danger/sz
            danger = 7-danger
            danger = np.minimum(10, danger*10/7)
            print(danger)
            result.append({"id":uid, "polyline": r['polyline'], "danger_score": danger, "duration": r['duration'], "distance": r['distance']})
            # print(result)
            uid+=1  
            response = jsonify(result)
        return make_response(response, 200)
    except Exception as e:
        response = jsonify({"message": e})
        return make_response(response,500)
    

@app.route('/update_data', methods= ['POST'])

def update_data():  
        data = request.get_json(force=True)
        lat = str(data['latitude'])
        lng = str(data['longitude'])

        date = str(data['date'])
        time = str(data['time'])
        description = data['description']

        
        REGION = "us-central1"
        vertexai.init(project=PROJECT_ID, location=REGION)
        

        generative_model = GenerativeModel("gemini-1.5-pro-001")
        response = generative_model.generate_content(
            [SYSTEM_INSTRUCT, description])
        print(response)

        return "Deepu",200

        # new_data_values = [
        #     {'Date accident': '2024-08-01', 'Time accident': '15:30:00', 'Accident type': 'Minor Injury', 'Death': 0, 'Grievous': 0, 'Minor': 1,
        #         'Gender': 'Male', 'Safety Device': 'Seat Belt', 'Alcohol Drugs': 'no', 'Longitude': 75.819000, 'Latitude': 11.280500, 'time_section': 'Afternoon', 'age_weightage': 0, 'accident_type_weightage': 0, 'individual_score': 0, 'accident_score':0},
        # ]

        # new_data_values['Date accident'] = date
        # new_data_values['Time accident'] = time
        # new_data_values['Longitude'] = lng
        # new_data_values['Latitude']  = lat
        # time_section = time_to_section(time)
        # new_data_values['time_section'] = time_section



        # update_data(new_data_values)







if __name__ == '__main__':
    app.run(host='0.0.0.0',port = 5000,debug=True)





#     import requests

# API_KEY = 'AIzaSyBy45iq2jviV0N6f1HXK_FzyUag9apSsD4'
# origin = '40.712776,-74.005974'  # New York City
# destination = '42.360082,-71.058880'  # Boston
# url = f'https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&alternatives=true&key={API_KEY}'






