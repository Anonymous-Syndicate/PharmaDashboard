import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random
import requests
import polyline
import math
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(layout="wide", page_title="PharmaGuard | National Command Center", page_icon="❄️")

# --- 2. GLOBAL UI STYLING (Consistency across all tabs) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    
    /* Center Loading Screen */
    #loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: #0e1117; display: flex; flex-direction: column;
        justify-content: center; align-items: center; z-index: 9999; color: white;
    }
    .loader { font-size: 100px; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { transform: scale(1); opacity: 0.7; } 50% { transform: scale(1.1); opacity: 1; color: #00FFFF; } 100% { transform: scale(1); opacity: 0.7; } }
    
    /* Shared Card Design */
    .intel-card {
        background: rgba(30, 33, 48, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px; padding: 20px; margin-bottom: 15px; min-height: 200px;
    }
    .card-label { color: #9ea0a9; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; }
    .card-value { color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 2px; }
    .card-sub { color: #00FFFF; font-size: 0.85rem; font-weight: 400; }
    
    /* Progress Bar */
    .progress-container { width: 100%; background-color: #262730; border-radius: 10px; margin: 12px 0; height: 10px; }
    .progress-fill { height: 10px; border-radius: 10px; background: linear-gradient(90deg, #00FFFF, #3498db); }
    
    /* Status Badges */
    .status-badge { padding: 10px 16px; border-radius: 8px; font-size: 0.9rem; font-weight: bold; display: block; margin-bottom: 20px; border-left: 5px solid; }
    .status-safe { background: rgba(0, 255, 127, 0.1); color: #00FF7F; border-color: #00FF7F; }
    .status-alert { background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border-color: #FF4B4B; animation: blink 1.5s infinite; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATASETS (100 RESCUE HUBS) ---
WAREHOUSE_NETWORK = [
    {"name": "Delhi-Vault", "lat": 28.61, "lon": 77.21}, {"name": "Mumbai-Apex", "lat": 19.08, "lon": 72.88},
    {"name": "Bangalore-Chill", "lat": 12.98, "lon": 77.59}, {"name": "Chennai-Hub", "lat": 13.08, "lon": 80.27},
    {"name": "Kolkata-Safe", "lat": 22.57, "lon": 88.36}, {"name": "Hyderabad-Vault", "lat": 17.39, "lon": 78.49},
    {"name": "Ahmedabad-Bio", "lat": 23.02, "lon": 72.57}, {"name": "Pune-Rescue", "lat": 18.52, "lon": 73.86},
    {"name": "Lucknow-Safe", "lat": 26.85, "lon": 80.95}, {"name": "Nagpur-Central", "lat": 21.15, "lon": 79.09},
    {"name": "Jaipur-Vault", "lat": 26.91, "lon": 75.79}, {"name": "Patna-Cold", "lat": 25.59, "lon": 85.14},
    {"name": "Srinagar-Safe", "lat": 34.08, "lon": 74.80}, {"name": "Guwahati-Hub", "lat": 26.14, "lon": 91.74},
    {"name": "Bhubaneswar-Apex", "lat": 20.30, "lon": 85.82}, {"name": "Kochi-Safe", "lat": 9.93, "lon": 76.27},
    {"name": "Indore-Vault", "lat": 22.72, "lon": 75.86}, {"name": "Chandigarh-Safe", "lat": 30.73, "lon": 76.78}
]
# Generate additional unique hubs to reach 100
for i in range(82):
    WAREHOUSE_NETWORK.append({
        "name": f"Rescue-Node-{100+i}",
        "lat": random.uniform(8.5, 34.0),
        "lon": random.uniform(68.5, 95.0)
    })

PHARMA_HUBS = {
    "Baddi Hub": [30.95, 76.79], "Sikkim Cluster": [27.33, 88.61],
    "Ahmedabad SEZ": [23.02, 72.57], "Hyderabad Hub": [17.45, 78.60],
    "Vizag Pharma": [17.68, 83.21], "Leh Portal": [34.15, 77.57],
    "Trivandrum Node": [8.52, 76.93], "Bhuj Vault": [23.24, 69.66]
}

DESTINATIONS = {
    "Mumbai Port": [18.94, 72.83], "Delhi Cargo": [28.55, 77.10],
    "Bangalore Dist": [12.97, 77.59], "Chennai Term": [13.08, 80.27],
    "Kolkata Port": [22.57, 88.36], "Guwahati Hub": [26.14, 91.73]
}

# --- 4. HELPERS ---
@st.cache_data(ttl=3600)
def get_road_route(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full"
    try:
        r = requests.get(url, timeout=5).json()
        return polyline.decode(r['routes'][0]['geometry']), round(r['routes'][0]['distance']/1000)
    except: return [[start[0], start[1]], [end[0], end[1]]], 500 

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def generate_forecast(is_failing=False):
    data = []
    base = 8.8 if is_failing else -4.2
    for _ in range(12):
        val = base + random.uniform(-0.5, 0.5)
        if random.random() < 0.1: val += random.uniform(1.5, 3.0) # Minute spikes
        if not is_failing: val = max(-9.5, min(4.8, val))
        data.append(round(val, 2))
    return data

# --- 5. INITIALIZATION & REFRESH LOADING ---
loading_placeholder = st.empty()
with loading_placeholder:
    st.markdown('<div id="loading-overlay"><div class="loader">❄️</div><div class="loading-text">PHARMAGUARD AI: ANALYZING NETWORK...</div></div>', unsafe_allow_html=True)

if 'fleet' not in st.session_state:
    fleet = []
    drivers = ["N. Modi", "A. Shah", "S. Jaishankar", "R. Gandhi", "M. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor"]
    all_locs = WAREHOUSE_NETWORK + [{"name": k, "lat": v[0], "lon": v[1]} for k, v in PHARMA_HUBS.items()]
    
    for i in range(15):
        pair = random.sample(all_locs, 2)
        s, e = pair[0], pair[1]
        path, dist = get_road_route([s['lat'], s['lon']], [e['lat'], e['lon']])
        prog = random.uniform(0.2, 0.8)
        pos = path[int(len(path)*prog)]
        is_fail = (i == 5)
        temp = 8.8 if is_fail else round(random.uniform(-7, 2), 1)
        
        fleet.append({
            "id": f"IND-EXP-{1000+i}", "driver": drivers[i % len(drivers)],
            "origin": s['name'], "dest": e['name'], "pos": pos, "path": path,
            "total_km": dist, "dist_covered": round(dist * prog), "dist_rem": round(dist * (1-prog)),
            "hrs_driven": round(prog * 15, 1), "temp": temp, "prog_pct": round(prog*100),
            "forecast": generate_forecast(is_fail)
        })
    st.session_state.fleet = fleet
else:
    time.sleep(1) # Artificial delay for refresh effect
loading_placeholder.empty()

# --- 6. APP LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")
tab1, tab2, tab3 = st.tabs(["🌐 Live Fleet Map", "🌡️ Thermal Stability", "🛤️ Route Safety Planner"])

# --- TAB 1: LIVE MAP ---
with tab1:
    selected_id = st.selectbox("🎯 Select Truck for Analysis:", [t['id'] for t in st.session_state.fleet])
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    for wh in WAREHOUSE_NETWORK:
        folium.CircleMarker([wh['lat'], wh['lon']], radius=2, color="#3498db", fill=True, popup=wh['name']).add_to(m)

    for t in st.session_state.fleet:
        is_sel = t['id'] == selected_id
        is_alert = t['temp'] > 5 or t['temp'] < -10
        color = "#00FFFF" if is_sel else ("#FF4B4B" if is_alert else "#00FF7F")
        folium.PolyLine(t['path'], color=color, weight=5 if is_sel else 1.5, opacity=0.8 if is_sel else 0.2).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color="purple" if is_sel else ("red" if is_alert else "green"), icon="truck", prefix="fa")).add_to(m)
    
    st_folium(m, width="100%", height=450, key="main_map")

    # Consistent Card Dashboard
    st.markdown(f"### 🛡️ System Intelligence: {selected_id}")
    is_critical = selected_truck['temp'] > 5 or selected_truck['temp'] < -10
    n_hub = min(WAREHOUSE_NETWORK, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    n_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], n_hub['lat'], n_hub['lon']))
    
    status_class = "status-alert" if is_critical else "status-safe"
    status_text = f"🛑 MISSION ALERT: BREACH AT {selected_truck['temp']}°C - DIVERT TO {n_hub['name'].upper()}" if is_critical else "✅ MISSION STATUS: CONTINUE / SAFE | Environment Nominal."
    st.markdown(f'<div class="status-badge {status_class}">{status_text}</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.8, 1.2])
    with col1:
        st.markdown(f"""<div class="intel-card">
            <div class="card-label">Vehicle & Driver</div><div class="card-value">{selected_truck['driver']}</div>
            <div class="card-sub">IND-EXP Fleet • {selected_truck['hrs_driven']} hrs</div><hr style="opacity:0.1; margin:15px 0;">
            <div class="card-label">Cargo Temp</div><div class="card-value" style="color:{'#FF4B4B' if is_critical else '#00FF7F'}">{selected_truck['temp']}°C</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        eta = (datetime.now() + timedelta(hours=selected_truck['dist_rem']/60)).strftime("%H:%M")
        st.markdown(f"""<div class="intel-card">
            <div class="card-label">Trip Progress</div><div style="display:flex; justify-content:space-between; margin-bottom:5px;"><span style="color:white; font-weight:bold;">{selected_truck['dist_covered']} km</span><span style="color:#9ea0a9;">{
