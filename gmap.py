import os
import requests
from dotenv import load_dotenv

load_dotenv()
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

        poly.append([lng/1e5, lat/1e5])

    return poly


def get_directions(origin_lat, origin_long, dest_lat, dest_long, travel_mode):
    origin = origin_lat + ', ' + origin_long
    destination = dest_lat + ', ' + dest_long

    API_KEY = os.getenv("API_KEY")
    url = f'https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&mode={travel_mode}&alternatives=true&key={API_KEY}'

    response = requests.get(url)
    directions = response.json()
    return directions
