import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from api_script import fetch_and_process_all_segments, fetch_segment_data, process_traffic_data
import our_secrets
import time

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

# Cache the function for loading traffic data
@st.cache_data
def load_traffic_data():
    return fetch_and_process_all_segments()

# Measure time for loading district boundaries
start_districts = time.time()
districts_file = 'bezirksgrenzen.geojson'
districts = load_districts(districts_file)
end_districts = time.time()

# Measure time for loading streetlight GeoJSON
start_streetlights = time.time()
streetlights_file = 'pruned_streetlight.geojson'
streetlights = load_streetlights(streetlights_file)
end_streetlights = time.time()

# Load traffic data
traffic_data = load_traffic_data()

# Debugging output
st.sidebar.text(f"Loaded {len(traffic_data)} segments")

# Streamlit select box for choosing the district
st.sidebar.title("Map Options")
selected_district = st.sidebar.selectbox("Choose a District", districts['Gemeinde_name'].unique())

# Streamlit select box for choosing the hour
selected_hour = st.sidebar.selectbox("Choose an Hour", list(range(24)))

# Measure time for filtering the selected district
start_filter_district = time.time()
district = districts[districts['Gemeinde_name'] == selected_district]
end_filter_district = time.time()

# Initialize session state for dark mode if it doesn't exist
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# Toggle dark mode state
def toggle_dark_mode():
    st.session_state.dark_mode = not st.session_state.dark_mode

# Button to toggle between light and dark mode
if st.sidebar.button("Dark Mode"):
    toggle_dark_mode()

# Measure time for creating the folium map
start_map_creation = time.time()
m = folium.Map(
    location=[district.geometry.centroid.y.values[0], district.geometry.centroid.x.values[0]],
    zoom_start=12
)
if st.session_state.dark_mode:
    folium.TileLayer('cartodbdark_matter', name='Dark Mode').add_to(m)
else:
    folium.TileLayer('OpenStreetMap', name='Light Mode').add_to(m)
folium.GeoJson(district).add_to(m)
end_map_creation = time.time()

# Measure time for filtering streetlights within the selected district
start_filter_streetlights = time.time()
streetlights_in_district = streetlights[streetlights.geometry.within(district.geometry.squeeze())]
end_filter_streetlights = time.time()

# Measure time for adding streetlights to the map
start_add_streetlights = time.time()
for _, row in streetlights_in_district.iterrows():
    for point in row.geometry.geoms:  # Iterate through each point in the MultiPoint
        folium.CircleMarker(
            location=[point.y, point.x],
            radius=0.5,
            color='yellow',
            fill=True,
            fill_color='yellow'
        ).add_to(m)
end_add_streetlights = time.time()

# Add segments with traffic data to the map
for segment_id, data in traffic_data.items():
    averages = data["averages"][selected_hour]
    coordinates = data["coordinates"]
    avg_car = averages["avg_car"]
    avg_bike = averages["avg_bike"]
    avg_pedestrian = averages["avg_pedestrian"]

    folium.CircleMarker(
        location=[coordinates[1], coordinates[0]],  # Assuming coordinates are [lon, lat]
        radius=5,
        color='blue',
        fill=True,
        fill_color='blue',
        popup=f"Hour: {selected_hour}\nCars: {avg_car:.2f}\nBikes: {avg_bike:.2f}\nPedestrians: {avg_pedestrian:.2f}"
    ).add_to(m)

# Display the map with Streamlit
st.title("Berlin Streetlights and Traffic Data Map")
st_folium(m, width=700, height=500)

# Measure total end time
end_total = time.time()

# Print results
st.text(f"Total runtime: {end_total - start_total:.2f} seconds")
st.text(f"Loading districts file: {end_districts - start_districts:.2f} seconds")
st.text(f"Loading streetlights file: {end_streetlights - start_streetlights:.2f} seconds")
st.text(f"Filtering selected district: {end_filter_district - start_filter_district:.2f} seconds")
st.text(f"Creating the folium map: {end_map_creation - start_map_creation:.2f} seconds")
st.text(f"Filtering streetlights: {end_filter_streetlights - start_filter_streetlights:.2f} seconds")
st.text(f"Adding streetlights to the map: {end_add_streetlights - start_add_streetlights:.2f} seconds")