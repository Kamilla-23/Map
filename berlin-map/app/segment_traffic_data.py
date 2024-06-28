import os
import json
from datetime import datetime, timezone
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

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
def fetch_and_process_all_segments(data_folder):
    all_segments_data = {}
    
    # Iterate through JSON files in the specified folder
    for filename in os.listdir(data_folder):
        if filename.endswith(".json"):
            segment_id = filename.split('.')[0]  # Assuming the segment ID is the file name without extension
            file_path = os.path.join(data_folder, filename)
            
            with open(file_path, 'r') as file:
                data = json.load(file)
                
            if data:
                averages = process_traffic_data(data)
                all_segments_data[segment_id] = {
                    "averages": averages,
                }

    return all_segments_data

if __name__ == '__main__':
    data_folder = "segment_traffic_data"  # Path to the folder containing the JSON files
    logging.debug("Starting to fetch and process all segments")
    segments_data = fetch_and_process_all_segments(data_folder)
    logging.debug(f"All segments data fetched and processed: {segments_data}")
    
    # Save the processed data to a new JSON file
    output_file = 'fetched_segments_data.json'
    with open(output_file, 'w') as file:
        json.dump(segments_data, file, indent=4)
    logging.debug(f"Data written to {output_file}")
