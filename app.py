import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random
import requests
import polyline
import math
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="PharmaGuard AI v3.0")

# --- EXPANDED DATASETS ---
PHARMA_HUBS = {
    "Baddi (HP)": [30.9578, 76.7914], "Ahmedabad (GJ)": [23.0225, 72.5714],
    "Vizag (AP)": [17.6868, 83.2185], "Hyderabad (TS)": [17.4500, 78.6000],
    "Sikkim Cluster": [27.3314, 88.6138], "Goa Hub": [15.2993, 74.1240]
}

DESTINATIONS = {
    "Mumbai Port": [18.9438, 72.8387], "Delhi Cargo": [28.5562, 77.1000],
    "Bangalore Dist.": [12.9716, 77.5946], "Chennai Port": [13.0827, 80.2707],
    "Kolkata Terminal": [22.5726, 88.3639], "Guwahati Hub": [26.1445, 91.7362]
}

# Extensive Warehouse Network (Rescue Points)
WAREHOUSE_NETWORK = [
    {"name": "Ambala Chill", "lat": 30.3782, "lon": 76.7767}, {"name": "Jaipur Cold-Link", "lat": 26.9124, "lon": 75.7873},
    {"name": "Udaipur Bio-Vault", "lat": 24.5854, "lon": 73.7125}, {"name": "Indore Pharma Hub", "lat": 22.7196, "lon": 75.8577},
    {"name": "Nagpur Central", "lat": 21.1458, "lon": 79.0882}, {"name": "Pune Rescue", "lat": 18.5204, "lon": 73.8567},
    {"name": "Satara Bio-Storage", "lat": 17.6805, "lon": 73.9803}, {"name": "Belgaum Chill", "lat": 15.8497, "lon": 74.4977},
    {"name": "Hubli Pharma-Vault", "lat": 15.3647, "lon": 75.1240}, {"name": "Anantapur Hub", "lat": 14.6819, "lon": 77.6006},
    {"name": "Nellore Cold-Point", "lat": 14.4426, "lon": 79.9865}, {"name": "Vijayawada Bio", "lat": 16.5062, "lon": 80.6480},
    {"name": "Warangal Rescue", "lat": 17.9689, "lon": 79.5941}, {"name": "Jabalpur Hub", "lat": 23.1815, "lon": 79.9864},
    {"name": "Jhansi Vault", "lat": 25.4484, "lon": 78.5685}, {"name": "Gwalior Cold", "lat": 26.2183, "lon": 78.1828},
    {"name": "Mathura Chill", "lat": 27.4924, "lon": 77.6737}, {"name": "Raipur Pharma", "lat": 21.2514, "lon": 81.6296},
    {"name": "Sambalpur Rescue", "lat": 21.4669, "lon": 83.9812}, {"name": "Kharagpur Hub", "lat": 22.3460, "lon": 87.2320},
    {"name": "Vapi Cold-Point", "lat": 20.3717, "lon": 72.9102}, {"name": "Surat Bio-Vault", "lat": 21.1702, "lon": 72.8311}
]

DRIVER_NAMES = ["Rajesh Kumar", "Sanjay Singh", "Vikram Rathore", "Dharmendra Pal", "Amit Sharma", "Gurpreet Singh", "Manoj Tiwari"]

# --- HELPERS ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def get_road_route(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full"
    try:
        r = requests.get(url).json()
        return polyline.decode(r['routes'][0]['geometry'])
    except: return [start, end]

def get_weather_forecast(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m&current_weather=true"
        data = requests.get(url).json()
        return data['current_weather']['temperature'], data['hourly']['temperature_2m'][:8] # Next 8 hours
    except: return 30.0, [30, 31, 32, 33, 34, 33, 31, 29]

# --- APP LOGIC ---
st.title("🛡️ PharmaGuard Elite: Precision Cold-Chain Dashboard")

if 'fleet' not in st.session_state:
    fleet = []
    for i in range(7):
        o_name = random.choice(list(PHARMA_HUBS.keys()))
        d_name = random.choice(list(DESTINATIONS.keys()))
        path = get_road_route(PHARMA_HUBS[o_name], DESTINATIONS[d_name])
        
        pos_idx = int(len(path) * random.uniform(0.3, 0.7))
        truck_pos = path[pos_idx]
        
        # Calculate 7-12 backup warehouses for THIS truck based on route proximity
        nearby_whs = []
        for wh in WAREHOUSE_NETWORK:
            dist = haversine(truck_pos[0], truck_pos[1], wh['lat'], wh['lon'])
            if dist < 600: # Broad range to find 7-12 candidates
                nearby_whs.append({**wh, "dist": round(dist)})
        
        nearby_whs = sorted(nearby_whs, key=lambda x: x['dist'])[:10] # Top 10 closest
        
        ambient, forecast = get_weather_forecast(truck_pos[0], truck_pos[1])
        cargo = round(random.uniform(2.5, 9.2), 1)
        hours = round(random.uniform(2, 11), 1)
        
        fleet.append({
            "Truck ID": f"PH-LX-{random.randint(1000, 9999)}",
            "Driver": random.choice(DRIVER_NAMES),
            "Driving Hours": hours,
            "Origin": o_name,
            "Destination": d_name,
            "Path": path,
            "Position": truck_pos,
            "Cargo Temp": cargo,
            "Ambient Temp": ambient,
            "8h Forecast": forecast,
            "Backups": nearby_whs,
            "Alert": "CRITICAL" if cargo > 8.0 or hours > 9.0 else "NORMAL"
        })
    st.session_state.fleet = fleet

# --- UI TABS ---
tab_map, tab_forecast, tab_drivers = st.tabs(["🗺️ Live Network Map", "📈 Predictive Forecasting", "👨‍✈️ Driver & Fleet Health"])

with tab_map:
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    for trk in st.session_state.fleet:
        folium.PolyLine(trk['Path'], color="#00d2ff", weight=2, opacity=0.3).add_to(m)
        
        # Plot ALL 7-12 Backup Warehouses for this specific truck
        for wh in trk['Backups']:
            folium.CircleMarker(
                [wh['lat'], wh['lon']], radius=3, color='yellow', fill=True,
                popup=f"Backup: {wh['name']} ({wh['dist']}km from {trk['Truck ID']})"
            ).add_to(m)
        
        # Truck Icon
        icon_color = "green" if trk['Alert'] == "NORMAL" else "red"
        folium.Marker(
            trk['Position'], icon=folium.Icon(color=icon_color, icon="truck", prefix="fa"),
            popup=f"Driver: {trk['Driver']}<br>Temp: {trk['Cargo Temp']}°C<br>Hours: {trk['Driving Hours']}h"
        ).add_to(m)
        
    st_folium(m, width="100%", height=600)

with tab_forecast:
    st.subheader("24-Hour Thermal Risk Forecast")
    cols = st.columns(len(st.session_state.fleet))
    for idx, trk in enumerate(st.session_state.fleet):
        with cols[idx]:
            st.metric(f"🚚 {trk['Truck ID']}", f"{trk['Ambient Temp']}°C")
            st.line_chart(trk['8h Forecast'])
            st.caption("Next 8h Ambient Temp Trend")

with tab_drivers:
    st.subheader("Crew Safety & Compliance")
    driver_df = pd.DataFrame([{
        "Truck ID": t['Truck ID'], "Driver": t['Driver'], 
        "Driving Hours": t['Driving Hours'], "Status": "Fatigue Risk" if t['Driving Hours'] > 9 else "Active"
    } for t in st.session_state.fleet])
    st.dataframe(driver_df.style.apply(lambda x: ['background-color: #ffcccc' if x.Status == "Fatigue Risk" else '' for i in x], axis=1))

# --- BOTTOM SECTION: ROUTE LOGISTICS ---
st.subheader("Route Rescue Log")
for trk in st.session_state.fleet:
    with st.expander(f"Route: {trk['Origin']} ➔ {trk['Destination']} ({trk['Truck ID']})"):
        c1, c2 = st.columns([1, 2])
        c1.write(f"**Primary Driver:** {trk['Driver']}")
        c1.write(f"**Current Cargo Temp:** {trk['Cargo Temp']}°C")
        if trk['Cargo Temp'] > 8.0:
            st.error("🚨 EMERGENCY REROUTE TRIGGERED")
        
        c2.write("**Optimized Backup Network (Along Route):**")
        wh_names = ", ".join([f"{w['name']} ({w['dist']}km)" for w in trk['Backups']])
        st.info(wh_names)
