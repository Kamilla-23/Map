import pandas as pd
import requests
import json
import our_secrets
import geopandas as gpd
from pathlib import Path

path_to_bezirksgrenzen = "bezirksgrenzen.geojson"
target_folder = "results"
retry_count = 5

def download_data(area, time):
    url = "https://telraam-api.net/v1/reports/traffic_snapshot"
    body = {
        "time": time,
        "contents": "minimal",
        "area": area
    }
    headers = {
        'X-Api-Key': our_secrets.telraamApiKey
    }
    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error retrieving data for area {area}')
        return None

def get_gemeinde_boundaries(file_path):
    file = gpd.read_file(file_path)
    for _, y in file.iterrows():
        yield y.Gemeinde_name, y.geometry.bounds

def get_normalized_boundary_string(a, b, c, d):
    w = max(a, c)
    x = max(b, d)
    y = min(a, c)
    z = min(b, d)
    return f"{w},{x},{y},{z}"

def download_data_for_district(name, boundary, time, retry_count=retry_count):
    print(f"{name} has boundaries {boundary}")
    a, b, c, d = boundary
    formatted_boundaries = get_normalized_boundary_string(a, b, c, d)
    data = download_data(formatted_boundaries, time)
    if data is not None:
        print(f"Found {len(data['features'])} features.")
        file_path = f"{target_folder}/{name}.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return data
    else:
        if retry_count > 1:
            print(f"Retrying... tries remaining: {retry_count - 1}")
            return download_data_for_district(name, boundary, time, retry_count - 1)
        return None

def ensure_results_path_exists():
    Path(target_folder).mkdir(parents=True, exist_ok=True)