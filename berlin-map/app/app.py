import streamlit as st
import streamlit.components.v1 as components
import os
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap
from pathlib import Path
import json
from pyproj import Transformer
import pandas as pd
import get_crime

st.title("Berlin Safety Map")

# Expandable "About" section at the top of the page
with st.expander("About this Project", expanded=False):
    st.write("""
    ## About
    Berlin Safety Map provides various features and data visualizations for the map of Berlin, including:
    
    - **Crime Heat Map**: Visualizes crime data for different crime types and years across Berlin.
    - **Crime Data**: Shows crime statistics of different crimes in Berlin's districts.
    - **Traffic Data**: Shows traffic patterns on specific streets at different time of the day.
    - **Police Precincts**: Displays police precinct locations and information.
    - **Streetlights**: Locates all streetlights in Berlin to differentiate between illuminated and dark streets at night.
    
    The key idea of the project is to provide user with clearly visualized data from official open-source data available for the city of Berlin.
    The data should help analyze the safety level of Berlin from different perspectives and dimensions by looking at the city and its districts as a whole.
    The map feature and the ability of the user to integrate with it to display and view different types of data should help
    researchers, governmental institutions and Berlin's citizens who wish to know how safe they are in this large city.
    
    For more technical details, visit our GitHub repository(https://github.com/Kamilla-23/Map).
    """)

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

# Load district boundaries
districts_file = Path(__file__).parent / 'bezirksgrenzen.geojson'
districts = load_districts(districts_file)

# Load streetlight GeoJSON
streetlights_file = Path(__file__).parent / 'pruned_streetlight.geojson'
streetlights = load_streetlights(streetlights_file)

# Load traffic data GeoJSON
traffic_file = Path(__file__).parent / 'converted_telraam_segments.geojson'
traffic_coordinates = load_traffic_geojson(traffic_file)

# Load segment traffic data
segment_file = Path(__file__).parent / 'fetched_segments_data.json'
segment_data = load_traffic_data(segment_file)

# Load police precincts GeoJSON
police_precincts_file = Path(__file__).parent / 'converted_police_precincts.geojson'
police_precincts = load_police_precincts(police_precincts_file)

crime_data = get_crime.load_and_process_crime_data()

# Streamlit sidebar options
st.sidebar.title("Map Options")
selected_district = st.sidebar.selectbox("Choose a District", districts['Gemeinde_name'].unique())
selected_layer = st.sidebar.selectbox("Select Layer", ["Crime Heat Map", "Crime Data", "Traffic Data", "Streetlights", "Police Precincts"])

# Add descriptions for each layer
layer_descriptions = {
    "Streetlights": "This layer shows the locations of streetlights within the selected district.",
    "Traffic Data": "This layer displays traffic data, including average counts of cars, bikes, and pedestrians per hour for different segments.",
    "Police Precincts": "This layer highlights the locations and contact information of police precincts in the district.",
    "Crime Data": "This layer presents detailed crime data for the selected year and crime type.",
    "Crime Heat Map": "This layer shows a heat map of crime incidents across all districts based on selected crime type and year."
}

st.sidebar.write(layer_descriptions[selected_layer])

district = districts[districts['Gemeinde_name'] == selected_district]

if selected_layer == "Traffic Data":
    selected_hour = st.sidebar.slider("Choose an Hour", min_value=0, max_value=23)

if selected_layer == "Crime Data" or selected_layer == "Crime Heat Map":
    crime_data_in_district = crime_data[crime_data['Gemeinde_name'] == selected_district]
    if crime_data_in_district.empty:
        st.error(f"No crime data available for {selected_district}")
    else:
        #selected_year = st.sidebar.selectbox("Choose a Year", crime_data_in_district["Jahr"].unique())
        selected_year = st.sidebar.slider("Choose a Year", int(crime_data_in_district["Jahr"].min()), int(crime_data_in_district["Jahr"].max()), step=1)

        if selected_layer == "Crime Heat Map":
            # Create aliases
            crime_type_aliases = {
            'Raub': 'Robbery',
            'Straßenraub': 'Burglary',
            'Körperverletzung': 'Assault',
            'schwere Körperverletzung': 'Serious assult',
            'Diebstahl': 'Theft',
            'Freiheitsberaubung': 'Deprivation of Liberty',
            'Other': 'Other crimes',
            'Gesamt': 'All'
            }           

            # Reverse mapping
            alias_to_crime_type = {v: k for k, v in crime_type_aliases.items()}

            # Create a list of English aliases for the selectbox
            crime_types = [crime_type_aliases[col] for col in crime_data.columns.drop(['Gemeinde_name', 'Jahr', 'geometry'])]

            # Add selectbox to sidebar with English aliases
            selected_crime_type_alias = st.sidebar.selectbox("Choose a Crime Type", crime_types)

            # Get the corresponding German column name
            selected_crime_type = alias_to_crime_type[selected_crime_type_alias]

# Create a base map

if selected_layer == "Crime Heat Map":
    bounds = districts.total_bounds 
    m = folium.Map(
        location=[(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2],  # Center of the bounds
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


# Add the selected layer to the map
if selected_layer == "Crime Heat Map":
    
    # Prepare data for the heat map
    filtered_crime_data = crime_data[(crime_data["Jahr"] == selected_year) & (crime_data[selected_crime_type] > 0)]

    # Prepare data for the heat map with selected crime type
    heat_data = [[row['geometry'].centroid.y, row['geometry'].centroid.x, row[selected_crime_type]] for idx, row in filtered_crime_data.iterrows()]

    # Add heat map to the map
    HeatMap(heat_data).add_to(m)

elif selected_layer == "Crime Data":

    crime_data_in_district = crime_data[(crime_data['Gemeinde_name'] == selected_district) & (crime_data['Jahr'] == selected_year)]
    
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

elif selected_layer == "Traffic Data":

    traffic_segments_in_district = [
        feature for feature in traffic_coordinates['features']
        if any([district.geometry.squeeze().contains(gpd.points_from_xy([coord[0]], [coord[1]])[0]) for coord in feature['geometry']['coordinates']])
    ]

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

elif selected_layer == "Police Precincts":

    police_in_district = police_precincts[police_precincts.geometry.within(district.geometry.squeeze())]

    for _, precinct in police_in_district.iterrows():
        popup_html = f"<b>Police Precinct</b><br>"
        popup_html += f"<b>Address:</b> {precinct['text']}, {precinct['locatorDesignator']}, {precinct['postCode']}<br>"
        popup_html += f"<b>Phone:</b> {precinct['telephoneVoice']}<br>"
        popup_html += f"<b>Website:</b> <a href='{precinct['website']}' target='_blank'>{precinct['website']}</a><br>"

        # Extract coordinates from geometry
        coordinates = precinct.geometry.coords[0]
        lat, lon = coordinates[1], coordinates[0]

        # Add marker to the map
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=500),
            icon=folium.Icon(color='red', icon='shield')
        ).add_to(m)

elif selected_layer == "Streetlights":

    streetlights_in_district = streetlights[streetlights.geometry.within(district.geometry.squeeze())]

    for _, row in streetlights_in_district.iterrows():
        for point in row.geometry.geoms: 
            folium.CircleMarker(
                location=[point.y, point.x],
                radius=0.5,
                color='yellow',
                fill=True,
                fill_color='yellow'
            ).add_to(m)

# Create space after sidebar content using Markdown
st.sidebar.markdown("---")

# Display the image at the end of the sidebar
st.sidebar.image("./static/berlin.png", caption='Contributors: Enes, Jinlin, Kamilla', use_column_width=True)

# Display the map with Streamlit
st_folium(m, width=1400, height=1000)