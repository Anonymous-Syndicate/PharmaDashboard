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

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="PharmaGuard | Command Center", page_icon="❄️")

# --- UI STYLING (THE "CLEANER" LOOK) ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #0e1117; }
    
    /* Loading Overlay */
    #loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: #0e1117; display: flex; flex-direction: column;
        justify-content: center; align-items: center; z-index: 9999; color: white;
    }
    .loader { font-size: 100px; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { transform: scale(1); opacity: 0.7; } 50% { transform: scale(1.1); opacity: 1; color: #00FFFF; } 100% { transform: scale(1); opacity: 0.7; } }

    /* Custom Intelligence Cards */
    .intel-card {
        background: rgba(30, 33, 48, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 10px;
    }
    .card-label { color: #9ea0a9; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .card-value { color: #ffffff; font-size: 1.5rem; font-weight: 600; }
    .card-sub { color: #00FFFF; font-size: 0.85rem; margin-top: 5px; }
    
    /* Progress Bar */
    .progress-container { width: 100%; background-color: #262730; border-radius: 10px; margin: 10px 0; height: 8px; }
    .progress-fill { height: 8px; border-radius: 10px; background: linear-gradient(90deg, #00FFFF, #3498db); }
    
    /* Status Badge */
    .status-badge {
        padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: bold;
        display: inline-block; margin-bottom: 15px;
    }
    .status-safe { background: rgba(0, 255, 127, 0.2); color: #00FF7F; border: 1px solid #00FF7F; }
    .status-alert { background: rgba(255, 75, 75, 0.2); color: #FF4B4B; border: 1px solid #FF4B4B; animation: blink 1s infinite; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- DATASETS (Hubs, Destinations, Drivers) ---
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
    {"name": "Udaipur-Vault", "lat": 24.59, "lon": 73.71}, {"name": "Trivandrum-Bio", "lat": 8.52, "lon": 76.94}
]

PHARMA_HUBS = {
    "Baddi Hub (North)": [30.9578, 76.7914], "Sikkim Cluster (East)": [27.3314, 88.6138],
    "Ahmedabad (West)": [23.0225, 72.5714], "Hyderabad (South)": [17.4500, 78.6000]
}

DESTINATIONS = {
    "Mumbai Port": [18.9438, 72.8387], "Delhi Air Cargo": [28.5562, 77.1000],
    "Bangalore Dist.": [12.9716, 77.5946], "Chennai Terminal": [13.0827, 80.2707]
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

# --- INITIALIZATION ---
if 'fleet' not in st.session_state:
    loading_placeholder = st.empty()
    with loading_placeholder:
        st.markdown('<div id="loading-overlay"><div class="loader">❄️</div><div class="loading-text">BOOTING NATIONAL NETWORK...</div></div>', unsafe_allow_html=True)
    
    fleet = []
    h_keys, d_keys = list(PHARMA_HUBS.keys()), list(DESTINATIONS.keys())
    drivers = ["N. Modi", "A. Shah", "S. Jaishankar", "R. Gandhi", "M. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji"]
    
    for i in range(12):
        o, d = h_keys[i % len(h_keys)], d_keys[i % len(d_keys)]
        path, dist = get_road_route(PHARMA_HUBS[o], DESTINATIONS[d])
        prog = random.uniform(0.3, 0.7)
        pos = path[int(len(path)*prog)]
        is_fail = (i == 5)
        cargo_temp = 8.5 if is_fail else round(random.uniform(-7, 2), 1)
        
        fleet.append({
            "id": f"IND-EXP-{1000+i}", "driver": drivers[i % len(drivers)],
            "origin": o, "dest": d, "pos": pos, "path": path,
            "total_km": dist, "dist_covered": round(dist * prog), "dist_rem": round(dist * (1-prog)),
            "hrs_driven": round(prog * 12, 1), "temp": cargo_temp, "prog_pct": round(prog*100),
            "forecast": [round(random.uniform(-9, 4), 1) for _ in range(10)]
        })
    st.session_state.fleet = fleet
    time.sleep(1)
    loading_placeholder.empty()

# --- APP LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")
tab1, tab2, tab3 = st.tabs(["🌐 Live Map", "🌡️ Thermal Forecasts", "🛤️ Trip Planner"])

with tab1:
    selected_id = st.selectbox("🎯 Select Truck for Analysis:", [t['id'] for t in st.session_state.fleet])
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    for wh in WAREHOUSE_NETWORK:
        folium.CircleMarker([wh['lat'], wh['lon']], radius=2, color="#3498db", fill=True).add_to(m)

    for t in st.session_state.fleet:
        is_sel = t['id'] == selected_id
        is_alert = t['temp'] > 5 or t['temp'] < -10
        color = "#00FFFF" if is_sel else ("#FF4B4B" if is_alert else "#00FF7F")
        folium.PolyLine(t['path'], color=color, weight=5 if is_sel else 1.5, opacity=0.8 if is_sel else 0.2).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color="purple" if is_sel else ("red" if is_alert else "green"), icon="truck", prefix="fa")).add_to(m)
    
    st_folium(m, width="100%", height=450, key="main_map")

    # --- CLEANER SYSTEMATIC INTELLIGENCE ---
    st.markdown(f"### 🛡️ System Intelligence: {selected_id}")
    
    is_critical = selected_truck['temp'] > 5 or selected_truck['temp'] < -10
    n_hub = min(WAREHOUSE_NETWORK, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    n_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], n_hub['lat'], n_hub['lon']))
    
    # Header Status Pill
    if is_critical:
        st.markdown(f'<div class="status-badge status-alert">🚨 ALERT: REROUTE TO {n_hub["name"].upper()}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-badge status-safe">✅ MISSION STATUS: CONTINUE / SAFE</div>', unsafe_allow_html=True)

    # Main Grid
    col_v, col_p, col_e = st.columns([1.2, 2, 1.2])

    with col_v:
        st.markdown(f"""
        <div class="intel-card">
            <div class="card-label">Vehicle & Driver</div>
            <div class="card-value">{selected_truck['driver']}</div>
            <div class="card-sub">Active for {selected_truck['hrs_driven']} hrs</div>
            <hr style="opacity:0.1; margin:10px 0;">
            <div class="card-label">Current Temperature</div>
            <div class="card-value" style="color:{'#FF4B4B' if is_critical else '#00FF7F'}">{selected_truck['temp']}°C</div>
        </div>
        """, unsafe_allow_html=True)

    with col_p:
        eta_time = (datetime.now() + timedelta(hours=selected_truck['dist_rem']/60)).strftime("%H:%M")
        st.markdown(f"""
        <div class="intel-card">
            <div class="card-label">Trip Progress</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span style="color:white; font-weight:bold;">{selected_truck['dist_covered']} km</span>
                <span style="color:#9ea0a9;">{selected_truck['total_km']} km Total</span>
            </div>
            <div class="progress-container"><div class="progress-fill" style="width:{selected_truck['prog_pct']}%"></div></div>
            <div style="display:flex; justify-content:space-between; margin-top:15px;">
                <div><div class="card-label">Remaining</div><div class="card-value" style="font-size:1.1rem;">{selected_truck['dist_rem']} km</div></div>
                <div style="text-align:right;"><div class="card-label">Est. Arrival</div><div class="card-value" style="font-size:1.1rem;">{eta_time}</div></div>
            </div>
            <hr style="opacity:0.1; margin:10px 0;">
            <div class="card-label">Logistics Corridor</div>
            <div style="font-size:0.9rem; color:#00FFFF;">{selected_truck['origin']} ➔ {selected_truck['dest']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_e:
        st.markdown(f"""
        <div class="intel-card" style="border-left: 4px solid {'#FF4B4B' if is_critical else '#3498db'}">
            <div class="card-label">Nearest Rescue Node</div>
            <div class="card-value" style="font-size:1.2rem;">{n_hub['name']}</div>
            <div class="card-sub">{n_dist} km deviation from current GPS</div>
            <hr style="opacity:0.1; margin:10px 0;">
            <div class="card-label">Protocol</div>
            <div style="font-size:0.85rem; color:#9ea0a9;">{'Immediate diversion required. Contact local hub manager.' if is_critical else 'Maintain current heading. Monitor sensor jitter.'}</div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.subheader("Sub-Zero Thermal Forecasts")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            df_chart = pd.DataFrame({"Temp": t['forecast'], "Max": [5]*10, "Min": [-10]*10})
            st.write(f"**Truck {t['id']}**")
            st.line_chart(df_chart, height=150)

with tab3:
    st.header("Strategic Route Planner")
    c1, c2, c3 = st.columns([1,1,1])
    s_node = c1.selectbox("Start", list(PHARMA_HUBS.keys()))
    e_node = c2.selectbox("End", list(DESTINATIONS.keys()))
    if st.button("Plan Safety Audit"):
        p, d = get_road_route(PHARMA_HUBS[s_node], DESTINATIONS[e_node])
        st.success(f"Verified Distance: {d} km")
        pm = folium.Map(location=PHARMA_HUBS[s_node], zoom_start=6, tiles="CartoDB dark_matter")
        folium.PolyLine(p, color="#00FFFF", weight=4).add_to(pm)
        st_folium(pm, width="100%", height=400, key="plan_map")
