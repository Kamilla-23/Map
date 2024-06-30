import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
import time
from pathlib import Path
import json
from pyproj import Transformer
import pandas as pd

st.set_page_config(layout="wide")

# Measure total runtime
start_total = time.time()

# Cache the function for loading district boundaries
@st.cache_data
def load_districts(file_path):
    return gpd.read_file(file_path)

# Cache the function for loading streetlight GeoJSON
@st.cache_data
def load_streetlights(file_path):
    return gpd.read_file(file_path)

# Cache the function for loading traffic data from GeoJSON file
@st.cache_data
def load_traffic_geojson(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Cache the function for loading traffic data
@st.cache_data
def load_traffic_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Cache the function for loading police precincts GeoJSON
@st.cache_data
def load_police_precincts(file_path):
    return gpd.read_file(file_path)

# Cache the function for loading and processing crime data
@st.cache_data
def load_and_process_crime_data():
    PATH = 'Fallzahlen&HZ 2014-2023.xlsx'
    GEO_PATH = 'bezirksgrenzen.geojson'

    BEZIRKE = ["Mitte", "Friedrichshain-Kreuzberg", "Pankow", "Charlottenburg-Wilmersdorf", "Spandau", "Steglitz-Zehlendorf", "Tempelhof-Schöneberg", "Neukölln", "Treptow-Köpenick", "Marzahn-Hellersdorf", "Lichtenberg", "Reinickendorf"]
    STRAFTATEN = ["Bezeichnung (Bezirksregion)", "Straftaten \n-insgesamt-", "Raub", "Straßenraub,\nHandtaschen-raub", "Körper-verletzungen \n-insgesamt-", "Gefährl. und schwere Körper-verletzung", "Freiheits-beraubung, Nötigung,\nBedrohung, Nachstellung", "Diebstahl \n-insgesamt-"]

    NEW_COLUMN_NAMES = {
        "Straftaten \n-insgesamt-": "Gesamt",
        "Raub": "Raub",
        "Straßenraub,\nHandtaschen-raub": "Straßenraub",
        "Körper-verletzungen \n-insgesamt-": "Körperverletzung",
        "Gefährl. und schwere Körper-verletzung": "schwere Körperverletzung",
        "Freiheits-beraubung, Nötigung,\nBedrohung, Nachstellung": "Freiheitsberaubung",
        "Diebstahl \n-insgesamt-": "Diebstahl"
    }

    COLUMNS_TO_SUBTRACT = ["Raub", "Körperverletzung", "schwere Körperverletzung", "Freiheitsberaubung", "Diebstahl"]

    def load_and_filter_data(year, path=PATH):
        """Loads data for a specific year, filters by relevant columns and districts."""
        sheet_name = f"Fallzahlen_{year}"
        df = pd.read_excel(path, sheet_name=sheet_name, skiprows=4)
        df_filtered = df[df["Bezeichnung (Bezirksregion)"].isin(BEZIRKE)][STRAFTATEN]
        df_filtered["Jahr"] = year
        return df_filtered.rename(columns=NEW_COLUMN_NAMES)

    def calculate_other_crimes(df):
        """Calculates the 'Other' crime category by subtracting known categories from the total."""
        df["Other"] = df["Gesamt"] - df[COLUMNS_TO_SUBTRACT].sum(axis=1)
        return df

    def merge_with_geo_data(df, geo_path=GEO_PATH):
        """Merges crime data with GeoJSON data, handles missing districts."""
        df_geo = gpd.read_file(geo_path)
        df = df.rename(columns={"Bezeichnung (Bezirksregion)": "Gemeinde_name"})
        merged_df = df.merge(df_geo, on="Gemeinde_name", how="inner")
        merged_df = merged_df.drop(columns=["gml_id", "Gemeinde_schluessel", "Land_name", "Land_schluessel", "Schluessel_gesamt"])
        return gpd.GeoDataFrame(merged_df, geometry='geometry')

    # Main execution
    all_data = [load_and_filter_data(year) for year in range(2014, 2024)]
    df_combined = pd.concat(all_data, ignore_index=True)
    df_combined = calculate_other_crimes(df_combined)
    return merge_with_geo_data(df_combined)

# Function to convert coordinates from EPSG:25833 to EPSG:4326
def convert_coordinates(coords):
    transformer = Transformer.from_crs("epsg:25833", "epsg:4326", always_xy=True)
    lon, lat = transformer.transform(coords[0], coords[1])
    return [lat, lon]

# Measure time for loading district boundaries
start_districts = time.time()
districts_file = Path(__file__).parent / 'bezirksgrenzen.geojson'
districts = load_districts(districts_file)
end_districts = time.time()

# Measure time for loading streetlight GeoJSON
start_streetlights = time.time()
streetlights_file = Path(__file__).parent / 'pruned_streetlight.geojson'
streetlights = load_streetlights(streetlights_file)
end_streetlights = time.time()

# Measure time for loading traffic data GeoJSON
start_traffic = time.time()
traffic_file = Path(__file__).parent / 'converted_telraam_segments.geojson'
traffic_coordinates = load_traffic_geojson(traffic_file)
end_traffic = time.time()

# Measure time for loading segment traffic data
start_segment_data = time.time()
segment_file = Path(__file__).parent / 'fetched_segments_data.json'
segment_data = load_traffic_data(segment_file)
end_segment_data = time.time()

# Measure time for loading police precincts GeoJSON
start_police_precincts = time.time()
police_precincts_file = Path(__file__).parent / 'polizeiabschnitte.geojson'
police_precincts = load_police_precincts(police_precincts_file)
end_police_precincts = time.time()

# Streamlit sidebar options
st.sidebar.title("Map Options")
selected_district = st.sidebar.selectbox("Choose a District", districts['Gemeinde_name'].unique())
selected_layer = st.sidebar.selectbox("Select Layer", ["Streetlights", "Traffic Data", "Police Precincts", "Crime Data", "Crime Heat Map"])
selected_hour = st.sidebar.selectbox("Choose an Hour", list(range(24)))

# Measure time for filtering the selected district
start_filter_district = time.time()
district = districts[districts['Gemeinde_name'] == selected_district]
end_filter_district = time.time()

# Measure time for creating the folium map 
start_map_creation = time.time()

if selected_layer == "Crime Heat Map":
    bounds = districts.total_bounds 
    m = folium.Map(
        location=[(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2],  # Center of the bounds (SUGGESTED BY CHATGPT)
        zoom_start=10  
    )
    # Add all district boundaries to the map
    folium.GeoJson(districts).add_to(m)
else:
    bounds = district.total_bounds  
    m = folium.Map(
        location=[(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2],  
        zoom_start=12
    )
    folium.GeoJson(district).add_to(m)

end_map_creation = time.time()

# Add the selected layer to the map
if selected_layer == "Streetlights":
    # Measure time for filtering streetlights within the selected district
    start_filter_streetlights = time.time()
    streetlights_in_district = streetlights[streetlights.geometry.within(district.geometry.squeeze())]
    end_filter_streetlights = time.time()

    # Measure time for adding streetlights to the map
    start_add_streetlights = time.time()
    for _, row in streetlights_in_district.iterrows():
        for point in row.geometry.geoms: 
            folium.CircleMarker(
                location=[point.y, point.x],
                radius=0.5,
                color='yellow',
                fill=True,
                fill_color='yellow'
            ).add_to(m)
    end_add_streetlights = time.time()

elif selected_layer == "Traffic Data":
    # Measure time for filtering traffic segments within the selected district
    start_filter_traffic = time.time()
    traffic_segments_in_district = [
        feature for feature in traffic_coordinates['features']
        if any([district.geometry.squeeze().contains(gpd.points_from_xy([coord[0]], [coord[1]])[0]) for coord in feature['geometry']['coordinates']])
    ]
    end_filter_traffic = time.time()

    # Measure time for adding traffic segments to the map
    start_add_traffic = time.time()
    for feature in traffic_segments_in_district:
        coordinates = feature['geometry']['coordinates']
        segment_id = str(feature['properties']['segment_id']) 

        # Get traffic data for the segment from segments_data
        if segment_id in segment_data:
            segment_data_hourly = segment_data[segment_id]['averages']

            # Check if selected hour data is available
            if str(selected_hour) in segment_data_hourly:
                data_hour = segment_data_hourly[str(selected_hour)]
                avg_car = round(data_hour.get('avg_car', 0))
                avg_bike = round(data_hour.get('avg_bike', 0))
                avg_pedestrian = round(data_hour.get('avg_pedestrian', 0))
            
                # Add LineString to the map with traffic data pop-up
                folium.PolyLine(
                    locations=[(coord[1], coord[0]) for coord in coordinates],
                    color='blue',
                    weight=5,
                    popup=folium.Popup(
                        f"Segment ID: {segment_id}<br>"
                        f"Hour: {selected_hour}<br>"
                        f"Cars: {avg_car}<br>"
                        f"Bikes: {avg_bike}<br>"
                        f"Pedestrians: {avg_pedestrian}<br>",
                        max_width=500
                    )
                ).add_to(m)
    end_add_traffic = time.time()

elif selected_layer == "Police Precincts":

    # Measure time for adding police precincts to the map
    start_add_police_precincts = time.time()
    for _, precinct in police_precincts.iterrows():
        coords = convert_coordinates(precinct.geometry.centroid.coords[0])
        popup_html = f"<b>Police Precinct</b><br>"
        popup_html += f"<b>Address:</b> {precinct['text']}, {precinct['locatorDesignator']}, {precinct['postCode']}<br>"
        popup_html += f"<b>Phone:</b> {precinct['telephoneVoice']}<br>"
        popup_html += f"<b>Website:</b> <a href='{precinct['website']}' target='_blank'>{precinct['website']}</a><br>"
        
        folium.Marker(
            location=coords,
            popup=folium.Popup(popup_html, max_width=500),
            icon=folium.Icon(color='red', icon='shield')
        ).add_to(m)
    end_add_police_precincts = time.time()

elif selected_layer == "Crime Data":
    # Measure time for adding crime data to the map
    start_add_crime_data = time.time()
    crime_data = load_and_process_crime_data()
    crime_data_in_district = crime_data[crime_data['Gemeinde_name'] == selected_district]
    
    # Add crime data to the map
    for _, row in crime_data_in_district.iterrows():
        coords = row['geometry'].centroid.coords[0][::-1]  
        popup_html = f"<b>Crime Data ({row['Jahr']})</b><br>"
        popup_html += f"<b>Total Crimes:</b> {row['Gesamt']}<br>"
        popup_html += f"<b>Robbery:</b> {row['Raub']}<br>"
        popup_html += f"<b>Street Robbery:</b> {row['Straßenraub']}<br>"
        popup_html += f"<b>Assault:</b> {row['Körperverletzung']}<br>"
        popup_html += f"<b>Serious Assault:</b> {row['schwere Körperverletzung']}<br>"
        popup_html += f"<b>Deprivation of Liberty:</b> {row['Freiheitsberaubung']}<br>"
        popup_html += f"<b>Theft:</b> {row['Diebstahl']}<br>"
        popup_html += f"<b>Other Crimes:</b> {row['Other']}<br>"
        
        folium.Marker(
            location=coords,
            popup=folium.Popup(popup_html, max_width=500),
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m)
    end_add_crime_data = time.time()

elif selected_layer == "Crime Heat Map":
    # Measure time for adding crime heat map to the map
    start_add_heat_map = time.time()
    crime_data = load_and_process_crime_data()
    
    # Prepare data for the heat map
    heat_data = [[row['geometry'].centroid.y, row['geometry'].centroid.x, row['Gesamt']] for idx, row in crime_data.iterrows()]
    
    # Add heat map to the map
    HeatMap(heat_data).add_to(m)
    end_add_heat_map = time.time()

# Display the map with Streamlit
st.title("Berlin Map")
st_folium(m, width=1400, height=1000)

# Measure total end time
end_total = time.time()

# Print results
st.text(f"Total runtime: {end_total - start_total:.2f} seconds")
st.text(f"Loading districts file: {end_districts - start_districts:.2f} seconds")
st.text(f"Loading streetlights file: {end_streetlights - start_streetlights:.2f} seconds")
st.text(f"Loading traffic data file: {end_traffic - start_traffic:.2f} seconds")
st.text(f"Loading segment data file: {end_segment_data - start_segment_data:.2f} seconds")
st.text(f"Loading police precincts file: {end_police_precincts - start_police_precincts:.2f} seconds")
st.text(f"Filtering district: {end_filter_district - start_filter_district:.2f} seconds")
st.text(f"Creating map: {end_map_creation - start_map_creation:.2f} seconds")

if selected_layer == "Streetlights":
    st.text(f"Filtering streetlights: {end_filter_streetlights - start_filter_streetlights:.2f} seconds")
    st.text(f"Adding streetlights to map: {end_add_streetlights - start_add_streetlights:.2f} seconds")
elif selected_layer == "Traffic Data":
    st.text(f"Filtering traffic data: {end_filter_traffic - start_filter_traffic:.2f} seconds")
    st.text(f"Adding traffic data to map: {end_add_traffic - start_add_traffic:.2f} seconds")
elif selected_layer == "Police Precincts":
    st.text(f"Filtering police precincts: {end_filter_police_precincts - start_filter_police_precincts:.2f} seconds")
    st.text(f"Adding police precincts to map: {end_add_police_precincts - start_add_police_precincts:.2f} seconds")
elif selected_layer == "Crime Data":
    st.text(f"Adding crime data to map: {end_add_crime_data - start_add_crime_data:.2f} seconds")
elif selected_layer == "Crime Heat Map":
    st.text(f"Adding crime heat map to map: {end_add_heat_map - start_add_heat_map:.2f} seconds")