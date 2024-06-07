import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# Load district boundaries GeoJSON
districts_file = 'bezirksgrenzen.geojson'
districts = gpd.read_file(districts_file)

# Load streetlight GeoJSON
streetlights_file = 'pruned_streetlight.geojson'
streetlights = gpd.read_file(streetlights_file)

# Streamlit select box for choosing the district
st.sidebar.title("Map Options")
selected_district = st.sidebar.selectbox("Choose a District", districts['Gemeinde_name'].unique())

# Filter the selected district
district = districts[districts['Gemeinde_name'] == selected_district]

# Create a folium map centered on the selected district with dark mode
m = folium.Map(
    location=[district.geometry.centroid.y.values[0], district.geometry.centroid.x.values[0]],
    zoom_start=12,
    tiles=None
)
folium.TileLayer('cartodbdark_matter', name='Dark Mode').add_to(m)

# Add district boundary to the map
folium.GeoJson(district).add_to(m)

# Filter streetlights within the selected district
streetlights_in_district = streetlights[streetlights.geometry.within(district.geometry.squeeze())]

# Add streetlights to the map as yellow dots
for _, row in streetlights_in_district.iterrows():
    for point in row.geometry.geoms:  # Iterate through each point in the MultiPoint
        folium.CircleMarker(
            location=[point.y, point.x],
            radius=1,
            color='yellow',
            fill=True,
            fill_color='yellow'
        ).add_to(m)

# Display the map with Streamlit
st.title("Berlin Streetlights Map")
st_folium(m, width=700, height=500)