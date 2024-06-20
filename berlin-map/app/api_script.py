import requests
import json
from datetime import datetime, timedelta, timezone
import our_secrets

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

# Function to process the fetched data
def process_traffic_data(data):
    hourly_traffic = {hour: {"car": [], "bike": [], "pedestrian": []} for hour in range(24)}

    for report in data.get('report', []):
        # see https://stackoverflow.com/questions/127803/how-do-i-parse-an-iso-8601-formatted-date-and-time#comment90930357_49784038
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
        coordinates = segment['geometry']['coordinates']
        data = fetch_segment_data(segment_id, start_time, end_time)
        if data:
            averages = process_traffic_data(data)
            all_segments_data[segment_id] = {
                "averages": averages,
                "coordinates": coordinates
            }
    
    # Debugging output
    print("All segments data:", json.dumps(all_segments_data, indent=2))
    
    return all_segments_data

if __name__ == '__main__':
    fetch_and_process_all_segments()