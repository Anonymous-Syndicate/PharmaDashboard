import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random
import requests
import polyline
import math
import time
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="PharmaGuard | National Command Center", page_icon="❄️")

# --- CUSTOM CSS FOR LARGE CENTERED LOADING SCREEN ---
st.markdown("""
    <style>
    /* Full screen overlay */
    #loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: #0e1117;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        color: white;
        font-family: 'Source Sans Pro', sans-serif;
    }
    /* Animated snowflake pulse */
    .loader {
        font-size: 100px;
        animation: pulse 2s infinite;
        margin-bottom: 20px;
    }
    @keyframes pulse {
        0% { transform: scale(1); opacity: 0.8; }
        50% { transform: scale(1.2); opacity: 1; color: #00FFFF; }
        100% { transform: scale(1); opacity: 0.8; }
    }
    .loading-text {
        font-size: 24px;
        letter-spacing: 2px;
        font-weight: 300;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATASETS ---
PHARMA_HUBS = {
    "Baddi Hub (North)": [30.9578, 76.7914], "Sikkim Cluster (East)": [27.3314, 88.6138],
    "Ahmedabad (West)": [23.0225, 72.5714], "Hyderabad (South)": [17.4500, 78.6000],
    "Vizag Pharma City": [17.6868, 83.2185], "Goa Manufacturing": [15.2993, 74.1240],
    "Indore SEZ": [22.7196, 75.8577], "Pune Bio-Cluster": [18.5204, 73.8567]
}

DESTINATIONS = {
    "Mumbai Port": [18.9438, 72.8387], "Delhi Air Cargo": [28.5562, 77.1000],
    "Bangalore Dist.": [12.9716, 77.5946], "Chennai Terminal": [13.0827, 80.2707],
    "Kolkata Port": [22.5726, 88.3639], "Guwahati Hub": [26.1445, 91.7362],
    "Cochin Port": [9.9312, 76.2673], "Chandigarh Dry Port": [30.7333, 76.7794],
    "Nagpur Hub": [21.1458, 79.0882], "Lucknow Logistics": [26.8467, 80.9462]
}

WAREHOUSE_NETWORK = [
    {"name": "Leh-Vault", "lat": 34.1526, "lon": 77.5771}, {"name": "Srinagar-Cold", "lat": 34.0837, "lon": 74.7973},
    {"name": "Jaipur-Safe", "lat": 26.9124, "lon": 75.7873}, {"name": "Bhopal-Bio", "lat": 23.2599, "lon": 77.4126},
    {"name": "Guwahati-Apex", "lat": 26.1445, "lon": 91.7362}, {"name": "Kochi-South", "lat": 9.9312, "lon": 76.2673},
    {"name": "Lucknow-Safe", "lat": 26.8467, "lon": 80.9462}, {"name": "Nagpur-Central", "lat": 21.1458, "lon": 79.0882}
]
for i in range(72):
    WAREHOUSE_NETWORK.append({
        "name": f"Rescue-Node-{100+i}",
        "lat": random.uniform(8.5, 34.0),
        "lon": random.uniform(68.5, 95.0)
    })

DRIVERS = ["Amitav Ghosh", "S. Jaishankar", "K. Rathore", "Mohd. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor", "N. Chandran", "Arjun Kapur", "Deepak Punia", "Suresh Raina", "M. S. Dhoni", "Hardik Pandya"]

# --- FUNCTIONS ---
def get_road_route(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full"
    try:
        r = requests.get(url, timeout=3).json()
        return polyline.decode(r['routes'][0]['geometry']), round(r['routes'][0]['distance']/1000)
    except: 
        return [start, end], 500 

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# --- INITIALIZE FLEET WITH LOADING SCREEN ---
if 'fleet' not in st.session_state:
    # 1. Display the custom full-screen loader
    loading_placeholder = st.empty()
    with loading_placeholder:
        st.markdown("""
            <div id="loading-overlay">
                <div class="loader">❄️</div>
                <div class="loading-text">INITIALIZING PHARMAGUARD AI...</div>
            </div>
            """, unsafe_allow_html=True)
    
    # 2. Run the actual heavy computation
    fleet = []
    hub_names = list(PHARMA_HUBS.keys())
    dest_names = list(DESTINATIONS.keys())
    for i in range(15):
        o, d = hub_names[i % len(hub_names)], dest_names[i % len(dest_names)]
        path, dist = get_road_route(PHARMA_HUBS[o], DESTINATIONS[d])
        prog = random.uniform(0.3, 0.7)
        pos = path[int(len(path)*prog)]
        
        fleet.append({
            "id": f"IND-EXP-{1000+i}", "driver": DRIVERS[i],
            "origin": o, "dest": d, "pos": pos, "path": path,
            "total_km": dist, "dist_covered": round(dist * prog),
            "dist_rem": round(dist * (1-prog)), "hrs_driven": round(prog * 12, 1),
            "temp": round(random.uniform(-8, 2), 1),
            "forecast": [round(random.uniform(-8, 20), 1) for _ in range(8)]
        })
    
    st.session_state.fleet = fleet
    # 3. Clear the placeholder to reveal the app
    loading_placeholder.empty()

# --- ACTUAL UI LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")

tab1, tab2, tab3 = st.tabs(["🌐 Live Map", "🌡️ Thermal Forecasts", "🛤️ Trip Planner"])

with tab1:
    truck_ids = [t['id'] for t in st.session_state.fleet]
    selected_id = st.selectbox("🎯 Select Truck for Live Intelligence:", truck_ids)
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    for wh in WAREHOUSE_NETWORK:
        folium.CircleMarker([wh['lat'
