import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random
import requests
import polyline

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="AI Pharma Cold-Chain")

# --- DATA & API HELPERS ---
PHARMA_HUBS = {
    "Baddi (Himachal)": [30.9578, 76.7914],
    "Ahmedabad": [23.0225, 72.5714],
    "Vizag Pharma City": [17.6868, 83.2185],
    "Hyderabad": [17.4500, 78.6000]
}

DESTINATIONS = {
    "Mumbai Port": [18.9438, 72.8387],
    "Delhi Cargo": [28.5562, 77.1000],
    "Bangalore Dist.": [12.9716, 77.5946],
    "Chennai Port": [13.0827, 80.2707]
}

def get_road_route(start_coords, end_coords):
    """Fetches real road geometry from OSRM"""
    url = f"http://router.project-osrm.org/route/v1/driving/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}?overview=full"
    r = requests.get(url)
    res = r.json()
    if res['code'] == 'Ok':
        geometry = res['routes'][0]['geometry']
        return polyline.decode(geometry)
    return [start_coords, end_coords]

def get_weather(lat, lon):
    """Fetches real-time ambient temperature forecast"""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        r = requests.get(url).json()
        return r['current_weather']['temperature']
    except:
        return 30.0 # Default fallback

# --- DASHBOARD LOGIC ---
st.title("❄️ Pharma AI: Real Road & Weather Monitor")

# Generate 5 Random Routes
if 'fleet' not in st.session_state:
    fleet = []
    for i in range(5):
        h_name, h_coords = random.choice(list(PHARMA_HUBS.items()))
        d_name, d_coords = random.choice(list(DESTINATIONS.items()))
        
        # Get real road path
        path = get_road_route(h_coords, d_coords)
        # Place truck 40-60% along the actual road
        pos_idx = int(len(path) * random.uniform(0.4, 0.6))
        truck_pos = path[pos_idx]
        
        ambient_temp = get_weather(truck_pos[0], truck_pos[1])
        cargo_temp = round(random.uniform(3.0, 6.0), 1)
        
        # Recommendation Engine
        suggestion = "Maintain Speed"
        if ambient_temp > 35:
            suggestion = "High External Heat: Increase Compressor Power"
        elif cargo_temp > 7.0:
            suggestion = "URGENT: Reroute to nearest warehouse"
        
        fleet.append({
            "ID": f"TRK-{random.randint(1000, 9999)}",
            "Path": path,
            "Position": truck_pos,
            "Cargo Temp": cargo_temp,
            "Ambient Temp": ambient_temp,
            "Suggestion": suggestion,
            "Status": "Normal" if cargo_temp < 7 else "Warning"
        })
    st.session_state.fleet = fleet

# --- UI DISPLAY ---
col1, col2 = st.columns([3, 1])

with col1:
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB Positron")
    for trk in st.session_state.fleet:
        # Draw Real Road Route
        folium.PolyLine(trk['Path'], color="blue", weight=2, opacity=0.5).add_to(m)
        
        # Truck Marker
        color = "green" if trk['Status'] == "Normal" else "red"
        folium.Marker(
            trk['Position'],
            icon=folium.Icon(color=color, icon="truck", prefix="fa"),
            popup=f"Cargo: {trk['Cargo Temp']}°C | Air: {trk['Ambient Temp']}°C"
        ).add_to(m)
    
    st_folium(m, width="100%", height=600)

with col2:
    st.subheader("Live Forecast Alerts")
    for trk in st.session_state.fleet:
        with st.expander(f"Truck {trk['ID']}"):
            st.write(f"**Cargo:** {trk['Cargo Temp']}°C")
            st.write(f"**Outside Air:** {trk['Ambient Temp']}°C")
            st.info(f"💡 {trk['Suggestion']}")

st.dataframe(pd.DataFrame(st.session_state.fleet).drop(columns=['Path', 'Position']))
