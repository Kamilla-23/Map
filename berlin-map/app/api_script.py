import pyproj
import requests
import json
from datetime import datetime, timedelta, timezone
import geopandas as gpd
import our_secrets

# Define the projection for the conversion
geod = pyproj.Geod(ellps='WGS84')  # WGS84 ellipsoid, commonly used for GPS

# Function to convert [lon, lat] to [x, y]
def convert_coordinates(lon, lat):
    x, y, z = geod.fwd(lon, lat)
    return x, y

# Function to fetch data for a single segment
def fetch_segment_data(segment_id, start_time, end_time):
    url = "https://telraam-api.net/v1/reports/traffic"
    body = {
        "level": "segments",
        "format": "per-hour",
        "id": segment_id,
        "time_start": start_time,
        "time_end": end_time
    }
    headers = {
        'X-Api-Key': our_secrets.telraamApiKey
    }
    response = requests.post(url, headers=headers, json=body)
    return response.json() if response.status_code == 200 else None

# Function to fetch segment coordinates from the GeoJSON file
def fetch_segment_coordinates(geojson_url):
    try:
        # Load GeoJSON file
        segments = gpd.read_file(geojson_url)
        
        # Extract segment IDs and coordinates
        segment_coords = {}
        for idx, segment in segments.iterrows():
            segment_id = segment['segment_id']
            lon, lat = segment.geometry.centroid.x, segment.geometry.centroid.y
            x, y = convert_coordinates(lon, lat)
            segment_coords[segment_id] = [x, y]
        
        return segment_coords

    except Exception as e:
        print(f"Error fetching segment coordinates: {str(e)}")
        return None

# Function to process the fetched data
def process_traffic_data(data):
    hourly_traffic = {hour: {"car": [], "bike": [], "pedestrian": []} for hour in range(24)}

    for report in data.get('report', []):
        dt = datetime.fromisoformat(report['date'].replace("Z", "+00:00"))
        hour = dt.hour
        hourly_traffic[hour]["car"].append(report['car'])
        hourly_traffic[hour]["bike"].append(report['bike'])
        hourly_traffic[hour]["pedestrian"].append(report['pedestrian'])

    averages = {hour: {
        "avg_car": sum(values["car"]) / len(values["car"]) if values["car"] else 0,
        "avg_bike": sum(values["bike"]) / len(values["bike"]) if values["bike"] else 0,
        "avg_pedestrian": sum(values["pedestrian"]) / len(values["pedestrian"]) if values["pedestrian"] else 0
    } for hour, values in hourly_traffic.items()}

    return averages

# Function to fetch and process data for all segments
def fetch_and_process_all_segments():
    end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    start_time = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Fetch segment IDs and coordinates from Telraam API
    url = "https://telraam-api.net/v1/segments/all"
    headers = {
        'X-Api-Key': our_secrets.telraamApiKey
    }
    response = requests.get(url, headers=headers)
    segments_data = response.json() if response.status_code == 200 else None

    if not segments_data:
        return {}

    all_segments_data = {}
    for segment in segments_data['features']:
        segment_id = segment['properties']['oidn']
        lon, lat = segment['geometry']['coordinates']
        x, y = convert_coordinates(lon, lat)
        data = fetch_segment_data(segment_id, start_time, end_time)
        if data:
            averages = process_traffic_data(data)
            all_segments_data[segment_id] = {
                "averages": averages,
                "coordinates": [x, y]  # Store as [x, y] instead of [lon, lat]
            }
    
    return all_segments_data

if __name__ == '__main__':
    fetch_and_process_all_segments()