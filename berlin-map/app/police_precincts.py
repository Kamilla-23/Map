import json
from pyproj import Transformer
from pathlib import Path

# Define the transformer to convert coordinates from EPSG:25833 to EPSG:4326
transformer = Transformer.from_crs("EPSG:25833", "EPSG:4326", always_xy=True)

# Load the GeoJSON file
input_file = Path(__file__).parent / 'polizeiabschnitte.geojson'
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Function to transform coordinates
def transform_coordinates(coords):
    lon, lat = transformer.transform(coords[0], coords[1])
    return [lon, lat]

# Transform the coordinates in each feature
for feature in data['features']:
    if feature['geometry']['type'] == 'Point':
        feature['geometry']['coordinates'] = transform_coordinates(feature['geometry']['coordinates'])

# Save the transformed GeoJSON to a new file
output_file = Path(__file__).parent / 'converted_police_precincts.geojson'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Transformed GeoJSON saved to {output_file}")