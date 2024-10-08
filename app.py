from flask import Flask, Response, make_response, request, jsonify
import numpy as np
import pandas as pd
from flask_cors import CORS
import datetime
import vertexai
from vertexai.preview.generative_models import GenerativeModel, GenerationConfig
import json
from increment import time_to_section
from model import calculate_combined_score, data_update, data_update_crime, filter_data
from gmap import PROJECT_ID, decode_polyline, get_directions
import os
import time
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)


@app.route('/test')
def test():
    return Response('{ "message":"Application is up and running"}', status=201, mimetype='application/json')


@app.route('/safety_score', methods=['POST'])
def predict():
    try:
        data = request.get_json(force=True)
        longitude = data['Longitude']
        latitude = data['Latitude']
        timeZone = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(timeZone)
        time_section = time_to_section(current_time)
        # time_section = 'Night'

        filtered_accident_data, filtered_crime_data, accident_data, crime_data = filter_data(
            None, time_section)
        crime_score, acc_score = calculate_combined_score(
            latitude, longitude, filtered_accident_data, filtered_crime_data, 40)
        # print(filtered_accident_data)
        # print(filtered_crime_data)
        if acc_score > 0.0358:
            # print((max(accident_data['accident_score'].values)))
            # print(acc_score)
            acc_score = (1 - ((acc_score-0.035)/(max(accident_data['accident_score'].values)-0.035)))*10
        else:
            acc_score = 10
        # crime_score = (1-((crime_score-4)/(6.122-4)))*10
        crime_score = (max(crime_data['crime_score'].values) - crime_score)*10/max(crime_data['crime_score'].values)

        response = jsonify({'safety_score': (acc_score+crime_score)/2,
                           'crime_score': crime_score, "accident_score": acc_score})
        return make_response(response, 200)
    except Exception as e:
        # print(e)
        return Response('{ "message":"Please try later"}', status=500, mimetype='application/json')


@app.route('/routes', methods=['POST'])
def getdirection():
    try:
        data = request.get_json(force=True)
        origin_lat = str(data['origin_lat'])
        origin_long = str(data['origin_long'])

        dest_lat = str(data['dest_lat'])
        dest_long = str(data['dest_long'])
        gender = data['gender']
        travel_mode = data['travel_mode']

        # start  =time.time()
        directions = get_directions(
            origin_lat, origin_long, dest_lat, dest_long, travel_mode)
        
        # end  = time.time()

        # print(end-start)

        direction_polylines = []
        if directions['status'] == 'OK':
            for route in directions['routes']:
                polyline = route['overview_polyline']['points']
                distance = route['legs'][0]['distance']['text']
                duration = route['legs'][0]['duration']['text']
                direction_polylines.append(
                    {"polyline": polyline, "distance": distance, "duration": duration})
        else:
            response = jsonify({'message':  directions['status']})
            return make_response(response, 500)

        result = []
        # uid = 1
        timeZone = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(timeZone)
        time_section = time_to_section(current_time)
        # time_section='Night'
        filtered_accident_data, filtered_crime_data, accident_data, crime_data = filter_data(gender, time_section)
        for r in direction_polylines:
            lat_long_arr = decode_polyline(r['polyline'])
            sz = len(lat_long_arr)
            # print(sz)
            # danger = 0
            crime_score = 0
            acc_score = 0
            cnt=0
            # i=0
            for i in range(1,sz,10):
                cnt = cnt+1
                temp2, temp3 = calculate_combined_score(
                    lat_long_arr[i][1], lat_long_arr[i][0], filtered_accident_data, filtered_crime_data, 40)
                # danger += temp1
                if temp3 > 0.0358:
                    # print((max(accident_data['accident_score'].values)))
                    temp3 = (
                        1 - ((temp3-0.0357)/((max(accident_data['accident_score'].values))-0.0357)))*10
                else:
                    temp3 = 10
                temp2 = (max(crime_data['crime_score'].values) -temp2)*10/max(crime_data['crime_score'].values)
                crime_score += temp2
                acc_score += temp3
                # i += 10 if sz >= 100 else 5

            # danger = danger/sz
            crime_score = crime_score/cnt
            acc_score = acc_score/cnt
            combined_score=0
            if travel_mode=='walking':
                combined_score = 0.6*crime_score + 0.4*acc_score
            else:
                combined_score = 0.6*acc_score + 0.4*crime_score


            result.append({"polyline": r['polyline'], "safety_score": combined_score, "crime_score": crime_score,
                          "accident_score": acc_score, "duration": r['duration'], "distance": r['distance']})
            # uid += 1

        result_sorted = sorted(
            result, key=lambda x: x['safety_score'], reverse=True)
        uuid = 1
        for path in result_sorted:
            path['id'] = uuid
            uuid += 1
        response = jsonify(result_sorted)
        return make_response(response, 200)
    except Exception as e:
        response = jsonify({"message": e})
        return make_response(response, 500)


@app.route('/update_data', methods=['POST'])
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
    response_schemas = {
        "type": "OBJECT",
        "properties": {
            "gender": {
                "type": "STRING",
                "description": "Gender of the person involved",
            },
            "incident_type": {
                "type": "STRING",
                "description": "Type of the incident, e.g., 'crime' or 'accident'."
            },
            "age": {
                "type": "INTEGER",
                "description": "Age of the person involved in the incident."
            },
            "death": {
                "type": "INTEGER",
                "description": "Number of people died in accident or crime."
            },
            "location": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"}
                },
                "description": "Location details of the incident."
            },
            "grievous": {
                "type": "INTEGER",
                "description": "Count of people who got serious injuries in accident."
            },
            "minor": {
                "type": "INTEGER",
                "description": "Count of people who got minor injuries in accident."
            },
            "accident_details": {
                "type": "object",
                "properties": {
                    "accident_type": {"type": "string", "description": "Severity of accident., e.g., Fatal or minor accident or grevious accident"},
                    "safety_device_used": {"type": "boolean", "description": "Whether a safety device was used."},
                    "alcohol_involvement": {"type": "boolean", "description": "True if alcohol or drugs were involved, false otherwise."},

                },
                "description": "Details about the accident if it applies."
            },
            "crime_details": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Category of crime."},
                    "type_of_crime": {"type": "string", "description": "Specific type of crime, e.g., 'assault', 'robbery', 'murder'."},
                },
                "description": "Details about the accident if it applies."
            },
        },
        "required": ["gender", "age", "death", "grievous", "minor", "accident_details", "crime_details"]

    }
    generation_configs = GenerationConfig(
        response_mime_type="application/json", response_schema=response_schemas)
    # generation_configs = GenerationConfig(temperature=0)

    try:

        # service_account_key_path = '../saarthi.json'
        # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_key_path
        response = generative_model.generate_content(
            description, generation_config=generation_configs)

        # Step 1: Remove the code block markers and unnecessary characters
        # response_cleaned = response.text.strip(
        #     '"')  # Remove surrounding quotes
        # response_cleaned = response_cleaned.replace('```json\n', '').replace(
        #     '\n```', '')  # Remove code block markers

        # # Step 2: Parse the cleaned string into a JSON object
        # json_data = json.loads(response_cleaned)

        # # Now, `json_data` is a dictionary object containing the parsed JSON data
        # print(json_data)
        desc_data = json.loads(response.text)
        # print(desc_data)


        if (desc_data['incident_type'] == 'accident'):
            # print("accident")
            new_data_values = [{'Date accident': '2024-08-01', 'Time accident': '15:30:00', 'Accident type': 'Fatal', 'Death': 1, 'Grievous': 0, 'Minor': 0,
                                'Gender': 'Male', 'Safety Device': 'Seat Belt', 'Alcohol Drugs': 'no', 'Longitude': 75.819000, 'Latitude': 11.280500, 'time_section': 'Night', 'age_weightage': 0, 'accident_type_weightage': 0, 'individual_score': 0, 'accident_score': 0},]

            new_data_values[0]['Date accident'] = date
            # print(time)
            # print(time.time())
            date_time_obj = datetime.strptime(
                time, "%Y-%m-%d %H:%M:%S.%f").strftime("%H:%M:%S")
            # print(date_time_obj)
            new_data_values[0]['Time accident'] = date_time_obj
            new_data_values[0]['Longitude'] = lng
            new_data_values[0]['Latitude'] = lat
            time_section = time_to_section(time)
            # print(time_section)
            new_data_values[0]['time_section'] = time_section
            new_data_values[0]['Death'] = new_data_values[0]['Death'] if desc_data['death'] < 0 else desc_data['death']
            new_data_values[0]['Grievous'] = new_data_values[0]['grievous'] if desc_data['grievous'] < 0 else desc_data['grievous']
            new_data_values[0]['Minor'] = new_data_values[0]['minor'] if desc_data['minor'] < 0 else desc_data['minor']
            new_data_values[0]['Gender'] = 'Female' if desc_data['gender'] == 'female' else 'Male'

            data_update(new_data_values)
        else:
            # print("crime")
            new_data_value = [
                {'Date of Report': '2024-08-01', 'Time of Report': '15:30:00', 'Gender': 'Male', 'Age': 18, 'Latitude': 11.280500, 'Longitude': 75.819000, 'Category': 'Uncategorized', 'time_section': 'Night', 'age_weightage': 0, 'crime_category_weightage': 0, 'crime_score': 0}]
            new_data_value[0]['Date of Report'] = date
            new_data_value[0]['Time of Report'] = time.time()
            time_section = time_to_section(time)
            new_data_value[0]['time_section'] = time_section
            new_data_value[0]['Latitude'] = lat
            new_data_value[0]['Longitude'] = lng
            new_data_value[0]['Gender'] = 'Female' if desc_data['gender'] == 'female' else 'Male'

    except Exception as e:
        return str(e), 404

    return "Success", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
