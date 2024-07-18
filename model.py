# Decode the polyline string and return array of lat long pair

import requests


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

# Calculate accident score for a give lat long point

def calculate_point_danger(longitude,latitude,dist,ind,x_di):
    # result = data[(data['Longitude'] == longitude) & (data['Latitude'] == latitude)]['accident_score']

    # if not result.empty:
    #     return result.iloc[0]


    ans = 0
    sz = len(dist[0])
    i = 0
    while i < sz:
      di = x_di[ind[0][i]]
      we = 1/(200*(dist[0][i] + 0.000000000001))
      if we > 2:  #Hyperparameter
        we = 2
      ans += di*we
      i+=1
    return ans/sz


def calculate_path_danger(lat_long_pair_arr,knn_model,x_di):

  sz = len(lat_long_pair_arr)
  total_di =0
  for a in lat_long_pair_arr:
    dist,ind = knn_model.kneighbors(a)
    temp = calculate_point_danger(a[0],a[1],dist,ind,x_di)
    total_di+=temp
  return (total_di/sz)


def get_directions(origin_lat,origin_long,dest_lat,dest_long):
    origin = origin_lat + ', ' + origin_long
    destination = dest_lat + ', ' + dest_long

    API_KEY = 'AIzaSyBy45iq2jviV0N6f1HXK_FzyUag9apSsD4'
    url = f'https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&alternatives=true&key={API_KEY}'

    response = requests.get(url)
    directions = response.json()
    return directions