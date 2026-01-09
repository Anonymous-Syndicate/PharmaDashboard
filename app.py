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

# --- CUSTOM CSS FOR FULL-SCREEN LOADING ---
st.markdown("""
    <style>
    #loading-overlay {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: #0e1117;
        display: flex; flex-direction: column;
        justify-content: center; align-items: center;
        z-index: 9999; color: white;
    }
    .loader { font-size: 120px; animation: pulse 1.5s infinite; margin-bottom: 25px; }
    @keyframes pulse {
        0% { transform: scale(1); opacity: 0.7; }
        50% { transform: scale(1.2); opacity: 1; color: #00FFFF; text-shadow: 0 0 20px #00FFFF; }
        100% { transform: scale(1); opacity: 0.7; }
    }
    .loading-text { font-size: 24px; font-weight: 300; letter-spacing: 5px; font-family: sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- 80 REAL STRATEGIC RESCUE HUBS ---
WAREHOUSE_NETWORK = [
    {"name": "Delhi-Vault", "lat": 28.61, "lon": 77.21}, {"name": "Mumbai-Apex", "lat": 19.08, "lon": 72.88},
    {"name": "Bangalore-Chill", "lat": 12.98, "lon": 77.59}, {"name": "Chennai-Hub", "lat": 13.08, "lon": 80.27},
    {"name": "Kolkata-Safe", "lat": 22.57, "lon": 88.36}, {"name": "Hyderabad-Vault", "lat": 17.39, "lon": 78.49},
    {"name": "Ahmedabad-Bio", "lat": 23.02, "lon": 72.57}, {"name": "Pune-Rescue", "lat": 18.52, "lon": 73.86},
    {"name": "Lucknow-Safe", "lat": 26.85, "lon": 80.95}, {"name": "Nagpur-Central", "lat": 21.15, "lon": 79.09},
    {"name": "Jaipur-Vault", "lat": 26.91, "lon": 75.79}, {"name": "Kanpur-Apex", "lat": 26.45, "lon": 80.33},
    {"name": "Surat-Safe", "lat": 21.17, "lon": 72.83}, {"name": "Patna-Cold", "lat": 25.59, "lon": 85.14},
    {"name": "Vadodara-Chill", "lat": 22.31, "lon": 73.18}, {"name": "Ludhiana-Hub", "lat": 30.90, "lon": 75.86},
    {"name": "Agra-Vault", "lat": 27.18, "lon": 78.01}, {"name": "Nashik-Apex", "lat": 20.00, "lon": 73.79},
    {"name": "Ranchi-Safe", "lat": 23.34, "lon": 85.31}, {"name": "Raipur-Rescue", "lat": 21.25, "lon": 81.63},
    {"name": "Guwahati-Vault", "lat": 26.14, "lon": 91.74}, {"name": "Chandigarh-Safe", "lat": 30.73, "lon": 76.78},
    {"name": "Bhubaneswar-Apex", "lat": 20.30, "lon": 85.82}, {"name": "Coimbatore-Chill", "lat": 11.02, "lon": 76.96},
    {"name": "Vijayawada-Hub", "lat": 16.51, "lon": 80.65}, {"name": "Madurai-Safe", "lat": 9.93, "lon": 78.12},
    {"name": "Jodhpur-Vault", "lat": 26.24, "lon": 73.02}, {"name": "Kochi-Bio", "lat": 9.93, "lon": 76.27},
    {"name": "Dehradun-Rescue", "lat": 30.32, "lon": 78.03}, {"name": "Ambala-Cold", "lat": 30.38, "lon": 76.78},
    {"name": "Gorakhpur-Apex", "lat": 26.76, "lon": 83.37}, {"name": "Amritsar-Safe", "lat": 31.63, "lon": 74.87},
    {"name": "Jammu-Vault", "lat": 32.73, "lon": 74.86}, {"name": "Srinagar-Safe", "lat": 34.08, "lon": 74.80},
    {"name": "Shillong-Apex", "lat": 25.58, "lon": 91.89}, {"name": "Gangtok-Bio", "lat": 27.33, "lon": 88.61},
    {"name": "Imphal-Rescue", "lat": 24.82, "lon": 93.94}, {"name": "Itanagar-Safe", "lat": 27.08, "lon": 93.61},
    {"name": "Panaji-Vault", "lat": 15.49, "lon": 73.83}, {"name": "Mysore-Chill", "lat": 12.30, "lon": 76.64},
    {"name": "Tirupati-Hub", "lat": 13.63, "lon": 79.42}, {"name": "Pondicherry-Safe", "lat": 11.94, "lon": 79.81},
    {"name": "Salem-Apex", "lat": 11.66, "lon": 78.15}, {"name": "Udaipur-Vault", "lat": 24.59, "lon": 73.71},
    {"name": "Bikaner-Cold", "lat": 28.02, "lon": 73.31}, {"name": "Ajmer-Safe", "lat": 26.45, "lon": 74.64},
    {"name": "Bhuj-Vault", "lat": 23.24, "lon": 69.67}, {"name": "Rajkot-Apex", "lat": 22.30, "lon": 70.80},
    {"name": "Varanasi-Chill", "lat": 25.32, "lon": 82.97}, {"name": "Jamshedpur-Safe", "lat": 22.80, "lon": 86.20},
    {"name": "Bhopal-Hub", "lat": 23.26, "lon": 77.41}, {"name": "Indore-Vault", "lat": 22.72, "lon": 75.86},
    {"name": "Jabalpur-Safe", "lat": 23.18, "lon": 79.99}, {"name": "Gwalior-Apex", "lat": 26.22, "lon": 78.18},
    {"name": "Shimla-Chill", "lat": 31.10, "lon": 77.17}, {"name": "Mangalore-Rescue", "lat": 12.91, "lon": 74.86},
    {"name": "Kozhikode-Safe", "lat": 11.26, "lon": 75.78}, {"name": "Thrissur-Vault", "lat": 10.53, "lon": 76.21},
    {"name": "Siliguri-Hub", "lat": 26.73, "lon": 88.40}, {"name": "Asansol-Safe", "lat": 23.67, "lon": 86.95},
    {"name": "Dhanbad-Vault", "lat": 23.80, "lon": 86.43}, {"name": "Rourkela-Apex", "lat": 22.26, "lon": 84.85},
    {"name": "Guntur-Cold", "lat": 16.31, "lon": 80.44}, {"name": "Nellore-Safe", "lat": 14.44, "lon": 79.99},
    {"name": "Kurnool-Vault", "lat": 15.83, "lon": 78.04}, {"name": "Warangal-Hub", "lat": 17.97, "lon": 79.59},
    {"name": "Gaya-Apex", "lat": 24.79, "lon": 85.00}, {"name": "Bhagalpur-Safe", "lat": 25.24, "lon": 86.97},
    {"name": "Bhavnagar-Vault", "lat": 21.76, "lon": 72.15}, {"name": "Jamnagar-Safe", "lat": 22.47, "lon": 70.06},
    {"name": "Bareilly-Hub", "lat": 28.37, "lon": 79.43}, {"name": "Aligarh-Safe", "lat": 27.88, "lon": 78.08},
    {"name": "Meerut-Vault", "lat": 28.98, "lon": 77.71}, {"name": "Jhansi-Apex", "lat": 25.45, "lon": 78.57},
    {"name": "Bilaspur-Chill", "lat": 22.08, "lon": 82.14}, {"name": "Gulbarga-Safe", "lat": 17.33, "lon": 76.83},
    {"name": "Bellary-Vault", "lat": 15.14, "lon": 76.92}, {"name": "Belgaum-Rescue", "lat": 15.85, "lon": 74.50},
    {"name": "Hubli-Safe", "lat": 15.36, "lon": 75.12}, {"name": "Trivandrum-Bio", "lat": 8.52, "lon": 76.94}
]

PHARMA_HUBS = {
    "Baddi Hub": [30.9578, 76.7914], "Sikkim Cluster": [27.3314, 88.6138],
    "Ahmedabad (W)": [23.0225, 72.5714], "Hyderabad (S)": [17.4500, 78.6000],
    "Vizag City": [17.6868, 83.2185], "Goa Manufacturing": [15.2993, 74.1240],
    "Indore SEZ": [22.7196, 75.8577], "Pune Bio-Cluster": [18.5204, 73.8567]
}

DESTINATIONS = {
    "Mumbai Port": [18.9438, 72.8387], "Delhi Cargo": [28.5562, 77.1000],
    "Bangalore Dist": [12.9716, 77.5946], "Chennai Term": [13.0827, 80.2707],
    "Kolkata Port": [22.5726, 88.3639], "Guwahati Hub": [26.1445, 91.7362]
}

# --- HELPERS ---
@st.cache_data(ttl=3600)
def get_road_route(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full"
    try:
        r = requests.get(url, timeout=5).json()
        return polyline.decode(r['routes'][0]['geometry']), round(r['routes'][0]['distance']/1000)
    except: return [start, end], 500 

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def generate_forecast(is_failing=False):
    data = []
    base = 8.8 if is_failing else -4.2
    for _ in range(12):
        noise = random.uniform(-0.3, 0.3)
        spike = random.uniform(1.2, 2.8) if random.random() < 0.12 else 0
        val = base + noise + spike
        if not is_failing: val = max(-9.5, min(4.8, val))
        data.append(round(val, 2))
    return data

# --- EVERY-REFRESH LOADING ANIMATION ---
loading_placeholder = st.empty()
with loading_placeholder:
    st.markdown("""
        <div id="loading-overlay">
            <div class="loader">❄️</div>
            <div class="loading-text">PHARMAGUARD AI: ANALYZING NETWORK...</div>
        </div>
        """, unsafe_allow_html=True)

# Data Initialization Logic
if 'fleet' not in st.session_state:
    fleet = []
    h_keys, d_keys = list(PHARMA_HUBS.keys()), list(DESTINATIONS.keys())
    # Adjusted driver names to match screenshot request
    drivers = ["N. Modi", "A. Shah", "R. Gandhi", "M. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor", "N. Chandran", "Arjun Kapur", "Deepak Punia", "Suresh Raina", "M. S. Dhoni", "Hardik Pandya"]
    for i in range(15):
        o, d = h_keys[i % len(h_keys)], d_keys[i % len(d_keys)]
        path, dist = get_road_route(PHARMA_HUBS[o], DESTINATIONS[d])
        prog = random.uniform(0.3, 0.7)
        pos = path[int(len(path)*prog)]
        is_fail = (i == 5)
        f_data = generate_forecast(is_fail)
        fleet.append({
            "id": f"IND-EXP-{1000+i}", "driver": drivers[i % len(drivers)],
            "origin": o, "dest": d, "pos": pos, "path": path,
            "total_km": dist, "dist_covered": round(dist * prog), "dist_rem": round(dist * (1-prog)),
            "hrs_driven": round(prog * 12, 1), "temp": f_data[0], "forecast": f_data
        })
    st.session_state.fleet = fleet
else:
    time.sleep(1.2)

loading_placeholder.empty()

# --- APP LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")
tab1, tab2, tab3 = st.tabs(["🌐 Live Map", "🌡️ Thermal Forecasts", "🛤️ Trip Planner"])

with tab1:
    selected_id = st.selectbox("🎯 Select Truck for Live Intelligence:", [t['id'] for t in st.session_state.fleet])
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    for wh in WAREHOUSE_NETWORK:
        folium.CircleMarker([wh['lat'], wh['lon']], radius=2.5, color="#3498db", fill=True, popup=wh['name']).add_to(m)

    for t in st.session_state.fleet:
        is_sel = t['id'] == selected_id
        is_alert = t['temp'] > 5 or t['temp'] < -10
        if is_alert:
            tgt = min(WAREHOUSE_NETWORK, key=lambda x: haversine(t['pos'][0], t['pos'][1], x['lat'], x['lon']))
            folium.PolyLine([t['pos'], [tgt['lat'], tgt['lon']]], color="red", weight=2, dash_array='5, 10', opacity=0.8).add_to(m)
            folium.Marker([tgt['lat'], tgt['lon']], icon=folium.Icon(color="red", icon="medkit", prefix="fa")).add_to(m)

        color = "#00FFFF" if is_sel else ("red" if is_alert else "green")
        folium.PolyLine(t['path'], color=color, weight=5 if is_sel else 1.5, opacity=0.8 if is_sel else 0.3).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color="purple" if is_sel else ("red" if is_alert else "green"), icon="truck", prefix="fa")).add_to(m)
    
    st_folium(m, width="100%", height=550, key="main_map")

    st.markdown(f"### 📊 Systematic Intelligence: {selected_id}")
    n_hub = min(WAREHOUSE_NETWORK, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    n_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], n_hub['lat'], n_hub['lon']))
    is_critical = selected_truck['temp'] > 5 or selected_truck['temp'] < -10
    
    # STATUS BAR
    if is_critical:
        st.error(f"🛑 **MISSION STATUS: REROUTE TO NEAREST HUB** | Temp Breach ({selected_truck['temp']}°C). Reroute: **{n_hub['name']}**")
    else:
        st.success(f"✅ **MISSION STATUS: CONTINUE / SAFE** | Environment Nominal.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Driver", selected_truck['driver'])
    col1.metric("Live Temp", f"{selected_truck['temp']}°C", delta="SAFE" if not is_critical else "FAIL", delta_color="normal")
    col2.metric("Covered", f"{selected_truck['dist_covered']} km")
    col2.metric("Remaining", f"{selected_truck['dist_rem']} km")
    col3.metric("Time", f"{selected_truck['hrs_driven']} hrs")
    # FIX: REMOVED [:8] SLICING TO SHOW FULL ROUTE NAMES
    col3.metric("Route", f"{selected_truck['origin']} ➔ {selected_truck['dest']}")
    
    with col4:
        st.markdown(f"""
        <div style="background-color:#1e2130; padding:12px; border-radius:8px; border-left: 5px solid {'#ff4b4b' if is_critical else '#3498db'};">
            <p style="margin:0; font-size:0.8rem; color:#9ea0a9; text-transform:uppercase;">📍 Rescue Target</p>
            <p style="margin:0; font-size:1rem; font-weight:bold; color:#ffffff;">{n_hub['name']}</p>
            <p style="margin:0; font-size:0.85rem; color:{'#ff4b4b' if is_critical else '#3498db'};">Dev: {n_dist} km</p>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.subheader("Sub-Zero Thermal Profile (-10°C to 5°C)")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            df_chart = pd.DataFrame({
                "Temp": t['forecast'],
                "Upper Limit": [5.0] * len(t['forecast']),
                "Lower Limit": [-10.0] * len(t['forecast'])
            })
            st.write(f"**Truck {t['id']}** ({'🚨 ALERT' if (t['temp'] > 5 or t['temp'] < -10) else '✅ OK'})")
            st.line_chart(df_chart, height=180)

with tab3:
    st.header("Strategic Route Safety Audit")
    p1, p2, p3 = st.columns([1,1,1])
    start_n = p1.selectbox("Start Point", list(PHARMA_HUBS.keys()))
    end_n = p2.selectbox("Destination", list(DESTINATIONS.keys()))
    radius = p3.slider("Rescue Buffer (km)", 20, 150, 60)
    if st.button("Generate Road Safety Audit"):
        p
