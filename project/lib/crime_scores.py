import requests
import json
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors


def get_json(url):
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    route_info = json.loads(response.text)
    
    return route_info


def waypoints_and_distance(json_text):
    route_waypoints = []
    for i in range(len(json_text['routes'])):
        startpoints = []
        for point in json_text['routes'][i]['legs'][0]['steps']:
            
            start =  point['start_location']
            start_lat = start['lat']
            start_lng = start['lng']
    
            end = point['end_location']
            end_lat = end['lat']
            end_lng = end['lng']
    
            meters = point['distance']['value']
    
            startpoints.append((start_lat, start_lng, meters))
        startpoints.append((end_lat, end_lng, 0))
        route_waypoints.append(startpoints)
        
    return route_waypoints


def add_equal_spaced_points(route_list, k=1):
    all_routes_extra_points = []
    distance_list = []
    for x, route in enumerate(route_list):
        
        new_points = []
        total_distance = 0
        for i in range(len(route) - 1):
            j = i + 1
            start = route[i][:2]
            end = route[j][:2]
            meters = route[i][2]
            total_distance += meters/10
            new_lat = np.linspace(start[0], end[0], meters//k, endpoint=False)   # endpoint false so we dont double count
            new_lng = np.linspace(start[1], end[1], meters//k, endpoint=False)
            points = list(zip(new_lat, new_lng))
            new_points += points
        
        distance_list.append(total_distance)
        new_points.append(end)
        all_routes_extra_points.append(new_points)
    
    return all_routes_extra_points, distance_list


def knn_crime_score(points_list, crime_data, radius=0.000100):
    # fit knn to crime data
    lat_lng_data = crime_data[['Latitude', 'Longitude']].copy()
    neigh = NearestNeighbors(n_jobs=-1, radius=radius)
    neigh.fit(lat_lng_data)
    scores = []
    for route in points_list:
        dist, indexes = neigh.radius_neighbors(route)
        joined = np.concatenate(indexes)
        local_crime = crime_data.iloc[joined, :]
        local_crime = local_crime.drop_duplicates('Incident Number')
        crime_score = np.round(np.sum(local_crime['Crime Index']), 1)
        scores.append(crime_score)
    return scores


def calculate_crime_score(url):
    # read in crime data
    crime_data = pd.read_csv('../data/sfcrime_cleaned.csv')
    crime = crime_data[['Incident Number', 'Latitude', 'Longitude', 'Crime Index']]
    
    route_json = get_json(url)    # get json data
    route_points = waypoints_and_distance(route_json)
    all_routes, distances = add_equal_spaced_points(route_points)
    crime_scores = knn_crime_score(all_routes, crime)
    
    crime_scores = np.round(np.array(crime_scores)/np.array(distances), 3)
    
    return list(crime_scores)


def generate_url_and_scores(start=None, end=None):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start}&destination={end}&alternatives=true&mode=walking&key=AIzaSyCINW6uGcvCKu9J-8AkdKFt4YcBObovM94"
    score = calculate_crime_score(url)
    return score




