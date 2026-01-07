import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random
import requests
import polyline
import math

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="AI Pharma Logistics")

# --- DATASETS ---
PHARMA_HUBS = {
    "Baddi (HP)": [30.9578, 76.7914],
    "Ahmedabad (GJ)": [23.0225, 72.5714],
    "Vizag Pharma City (AP)": [17.6868, 83.2185],
    "Hyderabad (TS)": [17.4500, 78.6000],
    "Goa (GA)": [15.2993, 74.1240]
}

DESTINATIONS = {
    "Mumbai Port": [18.9438, 72.8387],
    "Delhi Airport": [28.5562, 77.1000],
    "Bangalore Dist.": [12.9716, 77.5946],
    "Chennai Cargo": [13.0827, 80.2707],
    "Kolkata Terminal": [22.5726, 88.3639]
}

# Global Cold Storage Network (Rescue Points)
COLD_STORAGE_NETWORK = [
    {"name": "Indore Cold-Link", "lat": 22.7196, "lon": 75.8577},
    {"name": "Nagpur Bio-Vault", "lat": 21.1458, "lon": 79.0882},
    {"name": "Pune Pharma-Chill", "lat": 18.5204, "lon": 73.8567},
    {"name": "Vijayawada Rescue Hub", "lat": 16.5062, "lon": 80.6480},
    {"name": "Jhansi Central Storage", "lat": 25.4484, "lon": 78.5685},
    {"name": "Belgaum Pharma Storage", "lat": 15.8497, "lon": 74.4977},
    {"name": "Surat Coastal Chill", "lat": 21.1702, "lon": 72.8311}
]

# --- HELPER FUNCTIONS ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371 # Earth radius in km
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def get_road_route(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full"
    try:
        r = requests.get(url).json()
        return polyline.decode(r['routes'][0]['geometry'])
    except: return [start, end]

def get_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        return requests.get(url).json()['current_weather']['temperature']
    except: return 32.0

# --- APP LOGIC ---
st.title("❄️ PharmaGuard: Intelligence-Led Cold Chain")
st.markdown("### Real-Time Route Optimization & Emergency Warehouse Mapping")

# Generate 6 Demo Trucks
if 'fleet' not in st.session_state:
    fleet = []
    for i in range(6):
        origin_name = random.choice(list(PHARMA_HUBS.keys()))
        dest_name = random.choice(list(DESTINATIONS.keys()))
        path = get_road_route(PHARMA_HUBS[origin_name], DESTINATIONS[dest_name])
        
        # Position truck randomly along the route
        pos_idx = int(len(path) * random.uniform(0.2, 0.8))
        truck_pos = path[pos_idx]
        
        # Proximity Search: Find nearest warehouse to current truck position
        distances = [(wh, haversine(truck_pos[0], truck_pos[1], wh['lat'], wh['lon'])) for wh in COLD_STORAGE_NETWORK]
        nearest_wh, dist_km = min(distances, key=lambda x: x[1])
        
        ambient = get_weather(truck_pos[0], truck_pos[1])
        cargo = round(random.uniform(2.5, 9.0), 1)
        
        fleet.append({
            "Truck ID": f"PH-{random.randint(100, 999)}",
            "Origin": origin_name,
            "Destination": dest_name,
            "Path": path,
            "Position": truck_pos,
            "Cargo Temp": cargo,
            "Ambient Temp": ambient,
            "Nearest WH": f"{nearest_wh['name']} ({round(dist_km)} km away)",
            "WH_Coords": [nearest_wh['lat'], nearest_wh['lon']],
            "Alert": "CRITICAL" if cargo > 8.0 else "NORMAL"
        })
    st.session_state.fleet = fleet

# --- UI DISPLAY ---
col1, col2 = st.columns([7, 3])

with col1:
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    
    for trk in st.session_state.fleet:
        # 1. Draw Route
        folium.PolyLine(trk['Path'], color="#3498db", weight=2, opacity=0.4).add_to(m)
        
        # 2. Draw Truck Marker
        icon_purity = "green" if trk['Alert'] == "NORMAL" else "red"
        folium.Marker(
            trk['Position'],
            icon=folium.Icon(color=icon_purity, icon="truck", prefix="fa"),
            popup=f"<b>{trk['Truck ID']}</b><br>From: {trk['Origin']}<br>To: {trk['Destination']}<br>Temp: {trk['Cargo Temp']}°C"
        ).add_to(m)
        
        # 3. Draw ONLY the nearest warehouse for THIS truck (if alert is high)
        if trk['Alert'] == "CRITICAL":
            folium.Marker(
                trk['WH_Coords'],
                icon=folium.Icon(color='blue', icon='medkit', prefix='fa'),
                popup=f"RESCUE POINT: {trk['Nearest WH']}"
            ).add_to(m)
            # Draw emergency line to warehouse
            folium.PolyLine([trk['Position'], trk['WH_Coords']], color="red", weight=2, dash_array='5').add_to(m)

    st_folium(m, width="100%", height=600)

with col2:
    st.subheader("Fleet Command Center")
    for trk in st.session_state.fleet:
        with st.expander(f"🚚 {trk['Truck ID']} ({trk['Origin']} ➔ {trk['Destination']})"):
            st.write(f"**Cargo Condition:** {trk['Cargo Temp']}°C")
            st.write(f"**Outdoor Forecast:** {trk['Ambient Temp']}°C")
            st.write(f"**Emergency Hub:** {trk['Nearest WH']}")
            
            if trk['Alert'] == "CRITICAL":
                st.error("⚠️ TEMP EXCURSION: Rerouting Suggested")
            else:
                st.success("✅ On Track")

# Data Table for quick review
st.subheader("Full Logistics Manifest")
df_display = pd.DataFrame(st.session_state.fleet).drop(columns=['Path', 'Position', 'WH_Coords'])
st.table(df_display)
