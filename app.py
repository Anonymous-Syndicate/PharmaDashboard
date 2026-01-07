import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random
import math

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Global Pharma Cold-Chain AI")

# --- DATA GENERATION ---
PHARMA_HUBS = {
    "Baddi Hub": [30.9578, 76.7914],
    "Ahmedabad Cluster": [23.0225, 72.5714],
    "Vizag Pharma City": [17.6868, 83.2185],
    "Goa Manufacturing": [15.2993, 74.1240],
    "Hyderabad Genome Valley": [17.4500, 78.6000]
}

DESTINATIONS = {
    "Mumbai Port": [18.9438, 72.8387],
    "Delhi Airport": [28.5562, 77.1000],
    "Bangalore Distribution": [12.9716, 77.5946],
    "Kolkata Terminal": [22.5726, 88.3639],
    "Chennai Cargo": [13.0827, 80.2707]
}

WAREHOUSES = [
    {"name": "Nagpur Central Cold-Store", "lat": 21.1458, "lon": 79.0882},
    {"name": "Indore Pharma Logic", "lat": 22.7196, "lon": 75.8577},
    {"name": "Belgaum Cold-Link", "lat": 15.8497, "lon": 74.4977},
    {"name": "Vijayawada Bio-Storage", "lat": 16.5062, "lon": 80.6480},
    {"name": "Chandigarh Thermal Hub", "lat": 30.7333, "lon": 76.7794}
]

def haversine(lat1, lon1, lat2, lon2):
    # Calculates distance between two points in km
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# Create 7 Randomized Routes with 2 trucks each
fleet_data = []
for i in range(7):
    origin_name, origin_coords = random.choice(list(PHARMA_HUBS.items()))
    dest_name, dest_coords = random.choice(list(DESTINATIONS.items()))
    
    for truck_no in range(1, 3):
        # Simulate truck at a random point along the route (0.1 to 0.9 progress)
        progress = random.uniform(0.1, 0.9)
        t_lat = origin_coords[0] + (dest_coords[0] - origin_coords[0]) * progress
        t_lon = origin_coords[1] + (dest_coords[1] - origin_coords[1]) * progress
        
        # Sensor data
        temp = round(random.uniform(2.1, 9.5), 1)
        
        # Find Nearest Warehouse
        distances = [(wh['name'], haversine(t_lat, t_lon, wh['lat'], wh['lon'])) for wh in WAREHOUSES]
        nearest_wh, dist_val = min(distances, key=lambda x: x[1])

        fleet_data.append({
            "Truck ID": f"PH-{100 + i*2 + truck_no}",
            "Origin": origin_name,
            "Destination": dest_name,
            "Lat": t_lat,
            "Lon": t_lon,
            "Temp (°C)": temp,
            "Status": "STABLE" if temp <= 8.0 else "EXCURSION ALERT",
            "Nearest Rescue WH": f"{nearest_wh} ({round(dist_val)} km)",
            "Origin_Coords": origin_coords,
            "Dest_Coords": dest_coords
        })

df = pd.DataFrame(fleet_data)

# --- UI LAYOUT ---
st.title("📦 Pharma Cold-Chain: Real-Time Web Dashboard")
st.markdown("### Route Optimization & Temperature Monitoring")

# Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Active Fleet", len(df))
c2.metric("Critical Alerts", len(df[df['Status'] == "EXCURSION ALERT"]))
c3.metric("Avg Temp", f"{df['Temp (°C)'].mean():.1f}°C")

# Sidebar Filter
st.sidebar.header("Filter Controls")
selected_hub = st.sidebar.multiselect("Select Manufacturing Hubs", list(PHARMA_HUBS.keys()), default=list(PHARMA_HUBS.keys()))
filtered_df = df[df['Origin'].isin(selected_hub)]

# Map Section
st.subheader("Live Fleet Map")
m = folium.Map(location=[22.0, 78.0], zoom_start=5, tiles="CartoDB dark_matter")

# Add Warehouses to Map
for wh in WAREHOUSES:
    folium.Marker([wh['lat'], wh['lon']], icon=folium.Icon(color='blue', icon='info-sign'), popup=f"Warehouse: {wh['name']}").add_to(m)

# Add Trucks and Routes to Map
for _, row in filtered_df.iterrows():
    # Draw the planned route line
    folium.PolyLine([row['Origin_Coords'], row['Dest_Coords']], color="white", weight=1, opacity=0.3).add_to(m)
    
    # Truck marker color logic
    icon_color = "green" if row['Status'] == "STABLE" else "red"
    
    folium.Marker(
        [row['Lat'], row['Lon']],
        popup=f"ID: {row['Truck ID']} | Temp: {row['Temp (°C)']}°C",
        icon=folium.Icon(color=icon_color, icon="truck", prefix="fa")
    ).add_to(m)

st_folium(m, width="100%", height=500)

# Data Table
st.subheader("Fleet Logistics Detail")
def color_status(val):
    color = 'red' if val == "EXCURSION ALERT" else 'green'
    return f'color: {color}'

st.dataframe(filtered_df.drop(columns=['Origin_Coords', 'Dest_Coords']).style.applymap(color_status, subset=['Status']))

st.info("Simulation Note: Data updates every time the page is refreshed or a filter is applied.")
