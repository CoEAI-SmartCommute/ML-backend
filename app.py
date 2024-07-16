from flask import Flask, Response, request, jsonify
import joblib
import numpy as np
import pandas as pd

from model import calculate_point_danger

app = Flask(__name__)

# Load the saved kNN model
joblib_file = "knn_model.pkl"
knn_model = joblib.load(joblib_file)

# Load your data that contains 'accident_score'
data = pd.read_csv('Data_Rapid_2019.csv')
data['accident_score'] = (data['Death'] * 2) + (data['Grievous'] * 1.5) + (data['Minor'] * 0.5)

# We will work on improving this calculation and taking more features into consideration
data = data[data['accident_score'] != 0]
x_di = data['accident_score'].values

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
        return jsonify({'danger_score': danger_score})
    except Exception as e:
        return Response('{ "message":"Please try later"}', status=500, mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0',port = 5000)