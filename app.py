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
st.set_page_config(layout="wide", page_title="PharmaGuard | National Command Center", page_icon="❄️")

# --- UI STYLING (GLASSMORPHISM) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    #loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: #0e1117; display: flex; flex-direction: column;
        justify-content: center; align-items: center; z-index: 9999; color: white;
    }
    .loader { font-size: 100px; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { transform: scale(1); opacity: 0.7; } 50% { transform: scale(1.1); opacity: 1; color: #00FFFF; } 100% { transform: scale(1); opacity: 0.7; } }
    .intel-card {
        background: rgba(30, 33, 48, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px; padding: 20px; margin-bottom: 10px;
    }
    .card-label { color: #9ea0a9; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .card-value { color: #ffffff; font-size: 1.4rem; font-weight: 600; }
    .card-sub { color: #00FFFF; font-size: 0.85rem; margin-top: 5px; }
    .progress-container { width: 100%; background-color: #262730; border-radius: 10px; margin: 10px 0; height: 8px; }
    .progress-fill { height: 8px; border-radius: 10px; background: linear-gradient(90deg, #00FFFF, #3498db); }
    .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; display: inline-block; margin-bottom: 15px; }
    .status-safe { background: rgba(0, 255, 127, 0.1); color: #00FF7F; border: 1px solid #00FF7F; }
    .status-alert { background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border: 1px solid #FF4B4B; animation: blink 1s infinite; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- 100 REAL INDIAN CITIES (RESCUE HUBS) ---
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
    {"name": "Meerut-Vault", "lat": 28.98, "lon": 77.71}, {"name": "Rajkot-Safe", "lat": 22.30, "lon": 70.80},
    {"name": "Varanasi-Bio", "lat": 25.32, "lon": 82.97}, {"name": "Srinagar-Chill", "lat": 34.08, "lon": 74.80},
    {"name": "Aurangabad-Vault", "lat": 19.88, "lon": 75.34}, {"name": "Amritsar-Safe", "lat": 31.63, "lon": 74.87},
    {"name": "Navi Mumbai-Hub", "lat": 19.03, "lon": 73.02}, {"name": "Allahabad-Vault", "lat": 25.43, "lon": 81.84},
    {"name": "Howrah-Safe", "lat": 22.58, "lon": 88.31}, {"name": "Gwalior-Cold", "lat": 26.22, "lon": 78.18},
    {"name": "Jabalpur-Hub", "lat": 23.18, "lon": 79.99}, {"name": "Coimbatore-Chill", "lat": 11.02, "lon": 76.96},
    {"name": "Vijayawada-Vault", "lat": 16.51, "lon": 80.65}, {"name": "Madurai-Safe", "lat": 9.93, "lon": 78.12},
    {"name": "Guwahati-Bio", "lat": 26.14, "lon": 91.74}, {"name": "Chandigarh-Chill", "lat": 30.73, "lon": 76.78},
    {"name": "Hubli-Vault", "lat": 15.36, "lon": 75.12}, {"name": "Solapur-Safe", "lat": 17.66, "lon": 75.91},
    {"name": "Bareilly-Hub", "lat": 28.37, "lon": 79.43}, {"name": "Moradabad-Vault", "lat": 28.84, "lon": 78.77},
    {"name": "Gurgaon-Apex", "lat": 28.46, "lon": 77.03}, {"name": "Aligarh-Safe", "lat": 27.88, "lon": 78.08},
    {"name": "Jamshedpur-Cold", "lat": 22.80, "lon": 86.20}, {"name": "Bhubaneswar-Bio", "lat": 20.30, "lon": 85.82},
    {"name": "Salem-Vault", "lat": 11.66, "lon": 78.15}, {"name": "Warangal-Hub", "lat": 17.97, "lon": 79.59},
    {"name": "Guntur-Safe", "lat": 16.31, "lon": 80.44}, {"name": "Bhiwandi-Cold", "lat": 19.29, "lon": 73.06},
    {"name": "Saharanpur-Hub", "lat": 29.97, "lon": 77.55}, {"name": "Gorakhpur-Safe", "lat": 26.76, "lon": 83.37},
    {"name": "Bikaner-Vault", "lat": 28.02, "lon": 73.31}, {"name": "Ambala-Chill", "lat": 30.38, "lon": 76.78},
    {"name": "Noida-Bio", "lat": 28.53, "lon": 77.39}, {"name": "Jodhpur-Safe", "lat": 26.24, "lon": 73.02},
    {"name": "Kochi-Hub", "lat": 9.93, "lon": 76.27}, {"name": "Udaipur-Vault", "lat": 24.59, "lon": 73.71},
    {"name": "Bhavnagar-Safe", "lat": 21.76, "lon": 72.15}, {"name": "Dehradun-Chill", "lat": 30.32, "lon": 78.03},
    {"name": "Asansol-Hub", "lat": 23.67, "lon": 86.95}, {"name": "Nanded-Safe", "lat": 19.14, "lon": 77.32},
    {"name": "Kolhapur-Vault", "lat": 16.70, "lon": 74.24}, {"name": "Ajmer-Bio", "lat": 26.45, "lon": 74.64},
    {"name": "Gulbarga-Hub", "lat": 17.33, "lon": 76.83}, {"name": "Jamnagar-Safe", "lat": 22.47, "lon": 70.06},
    {"name": "Ujjain-Vault", "lat": 23.18, "lon": 75.78}, {"name": "Loni-Safe", "lat": 28.75, "lon": 77.29},
    {"name": "Jhansi-Bio", "lat": 25.45, "lon": 78.57}, {"name": "Nellore-Hub", "lat": 14.44, "lon": 79.99},
    {"name": "Jammu-Vault", "lat": 32.73, "lon": 74.86}, {"name": "Belgaum-Safe", "lat": 15.85, "lon": 74.50},
    {"name": "Mangalore-Chill", "lat": 12.91, "lon": 74.86}, {"name": "Tirunelveli-Hub", "lat": 8.71, "lon": 77.76},
    {"name": "Malegaon-Vault", "lat": 20.55, "lon": 74.51}, {"name": "Gaya-Safe", "lat": 24.79, "lon": 85.00},
    {"name": "Jalgaon-Hub", "lat": 21.01, "lon": 75.56}, {"name": "Udaipur-Bio", "lat": 24.57, "lon": 73.68},
    {"name": "Tirupati-Vault", "lat": 13.63, "lon": 79.42}, {"name": "Rohtak-Safe", "lat": 28.90, "lon": 76.61},
    {"name": "Korba-Chill", "lat": 22.35, "lon": 82.68}, {"name": "Bhilai-Hub", "lat": 21.19, "lon": 81.35},
    {"name": "Muzaffarpur-Vault", "lat": 26.12, "lon": 85.36}, {"name": "Ahmednagar-Safe", "lat": 19.10, "lon": 74.74},
    {"name": "Kollam-Hub", "lat": 8.89, "lon": 76.61}, {"name": "Rourkela-Bio", "lat": 22.26, "lon": 84.85},
    {"name": "Panipat-Vault", "lat": 29.39, "lon": 76.96}, {"name": "Gandhinagar-Safe", "lat": 23.22, "lon": 72.64},
    {"name": "Siliguri-Chill", "lat": 26.73, "lon": 88.40}, {"name": "Bilaspur-Hub", "lat": 22.08, "lon": 82.14},
    {"name": "Sagar-Vault", "lat": 23.84, "lon": 78.74}, {"name": "Anantapur-Safe", "lat": 14.68, "lon": 77.60},
    {"name": "Kurnool-Hub", "lat": 15.83, "lon": 78.04}, {"name": "Dhanbad-Vault", "lat": 23.80, "lon": 86.44},
    {"name": "Shillong-Bio", "lat": 25.58, "lon": 91.89}, {"name": "Imphal-Safe", "lat": 24.82, "lon": 93.94},
    {"name": "Aizawl-Hub", "lat": 23.73, "lon": 92.72}, {"name": "Itanagar-Vault", "lat": 27.08, "lon": 93.61},
    {"name": "Gangtok-Chill", "lat": 27.33, "lon": 88.61}, {"name": "Agartala-Safe", "lat": 23.83, "lon": 91.29},
    {"name": "Pondicherry-Vault", "lat": 11.94, "lon": 79.81}, {"name": "Port Blair-Apex", "lat": 11.62, "lon": 92.73}
]

PHARMA_HUBS = {
    "Baddi Hub (North)": [30.95, 76.79], "Sikkim Cluster": [27.33, 88.61],
    "Ahmedabad (W)": [23.02, 72.57], "Hyderabad (S)": [17.45, 78.60],
    "Vizag City": [17.68, 83.21], "Goa Plant": [15.29, 74.12],
    "Indore SEZ": [22.71, 75.85], "Pune Bio-Cluster": [18.52, 73.85]
}

DESTINATIONS = {
    "Mumbai Port": [18.94, 72.83], "Delhi Cargo": [28.55, 77.10],
    "Bangalore Dist": [12.97, 77.59], "Chennai Term": [13.08, 80.27],
    "Kolkata Port": [22.57, 88.36], "Guwahati Hub": [26.14, 91.73]
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
        st.markdown('<div id="loading-overlay"><div class="loader">❄️</div><div class="loading-text">MAPPING 100 RESCUE NODES...</div></div>', unsafe_allow_html=True)
    
    fleet = []
    hub_keys = list(PHARMA_HUBS.keys())
    dest_keys = list(DESTINATIONS.keys())
    drivers = ["N. Modi", "A. Shah", "S. Jaishankar", "R. Gandhi", "M. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor", "N. Chandran", "Arjun Kapur", "Deepak Punia", "Suresh Raina", "M. S. Dhoni"]
    
    # Generate 15 Randomized Unique Routes
    for i in range(15):
        # Pick random distinct origin and destination
        o_name = random.choice(hub_keys)
        d_name = random.choice(dest_keys)
        while o_name == d_name: d_name = random.choice(dest_keys)
        
        path, dist = get_road_route(PHARMA_HUBS[o_name], DESTINATIONS[d_name])
        prog = random.uniform(0.3, 0.7)
        pos = path[int(len(path)*prog)]
        is_fail = (i == 5) # IND-EXP-1005 failure simulation
        temp = 8.8 if is_fail else round(random.uniform(-7, 2), 1)
        
        fleet.append({
            "id": f"IND-EXP-{1000+i}", "driver": drivers[i % len(drivers)],
            "origin": o_name, "dest": d_name, "pos": pos, "path": path,
            "total_km": dist, "dist_covered": round(dist * prog), "dist_rem": round(dist * (1-prog)),
            "hrs_driven": round(prog * 12, 1), "temp": temp, "prog_pct": round(prog*100),
            "forecast": [round(random.uniform(-8, 3), 1) for _ in range(10)]
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

    # MAP RENDER
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    
    # Render all 100 Rescue Hubs
    for wh in WAREHOUSE_NETWORK:
        folium.CircleMarker([wh['lat'], wh['lon']], radius=2, color="#3498db", fill=True, popup=wh['name']).add_to(m)

    for t in st.session_state.fleet:
        is_sel = t['id'] == selected_id
        is_alert = t['temp'] > 5 or t['temp'] < -10
        color = "#00FFFF" if is_sel else ("#FF4B4B" if is_alert else "#00FF7F")
        folium.PolyLine(t['path'], color=color, weight=5 if is_sel else 1.5, opacity=0.8 if is_sel else 0.2).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color="purple" if is_sel else ("red" if is_alert else "green"), icon="truck", prefix="fa")).add_to(m)
    
    st_folium(m, width="100%", height=450, key="main_map")

    # --- SYSTEMATIC INTELLIGENCE ---
    st.markdown(f"### 🛡️ System Intelligence: {selected_id}")
    is_critical = selected_truck['temp'] > 5 or selected_truck['temp'] < -10
    n_hub = min(WAREHOUSE_NETWORK, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    n_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], n_hub['lat'], n_hub['lon']))
    
    if is_critical:
        st.markdown(f'<div class="status-badge status-alert">🚨 ALERT: THERMAL BREACH - REROUTE TO {n_hub["name"].upper()}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-badge status-safe">✅ MISSION STATUS: CONTINUE / SAFE</div>', unsafe_allow_html=True)

    c_status, c_prog, c_emergency = st.columns([1.2, 2, 1.2])

    with c_status:
        st.markdown(f"""
        <div class="intel-card">
            <div class="card-label">Vehicle & Driver</div>
            <div class="card-value">{selected_truck['driver']}</div>
            <div class="card-sub">Active for {selected_truck['hrs_driven']} hrs</div>
            <hr style="opacity:0.1; margin:10px 0;">
            <div class="card-label">Cargo Temp</div>
            <div class="card-value" style="color:{'#FF4B4B' if is_critical else '#00FF7F'}">{selected_truck['temp']}°C</div>
        </div>
        """, unsafe_allow_html=True)

    with c_prog:
        eta = (datetime.now() + timedelta(hours=selected_truck['dist_rem']/60)).strftime("%H:%M")
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
                <div style="text-align:right;"><div class="card-label">Est. Arrival</div><div class="card-value" style="font-size:1.1rem;">{eta}</div></div>
            </div>
            <hr style="opacity:0.1; margin:10px 0;">
            <div class="card-label">Route Corridor</div>
            <div style="font-size:0.9rem; color:#00FFFF;">{selected_truck['origin']} ➔ {selected_truck['dest']}</div>
        </div>
        """, unsafe_allow_html=True)

    with c_emergency:
        st.markdown(f"""
        <div class="intel-card" style="border-left: 4px solid {'#FF4B4B' if is_critical else '#3498db'}">
            <div class="card-label">Nearest Rescue Node</div>
            <div class="card-value" style="font-size:1.2rem;">{n_hub['name']}</div>
            <div class="card-sub">{n_dist} km deviation</div>
            <hr style="opacity:0.1; margin:10px 0;">
            <div class="card-label">Emergency Protocol</div>
            <div style="font-size:0.85rem; color:#9ea0a9;">{'Divert immediately. Contact hub for maintenance.' if is_critical else 'Maintain heading. Environmental logs nominal.'}</div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.subheader("Sub-Zero Thermal Stability (-10°C to 5°C)")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            df_chart = pd.DataFrame({"Temp": t['forecast'], "Max": [5]*10, "Min": [-10]*10})
            st.write(f"**Truck {t['id']}**")
            st.line_chart(df_chart, height=150)

with tab3:
    st.header("Strategic Route Safety Audit")
    p1, p2, p3 = st.columns([1,1,1])
    s_node = p1.selectbox("Start Point", list(PHARMA_HUBS.keys()), key="plan_start")
    e_node = p2.selectbox("Destination", list(DESTINATIONS.keys()), key="plan_end")
    rad = p3.slider("Search Buffer (km)", 20, 150, 60)
    
    if st.button("Generate Road Safety Audit"):
        path, d = get_road_route(PHARMA_HUBS[s_node], DESTINATIONS[e_node])
        st.success(f"Verified Highway Distance: {d} km")
        pm = folium.Map(location=PHARMA_HUBS[s_node], zoom_start=6, tiles="CartoDB dark_matter")
        folium.PolyLine(path, color="#00FFFF", weight=4).add_to(pm)
        found = []
        for wh in WAREHOUSE_NETWORK:
            dist = min([haversine(wh['lat'], wh['lon'], pt[0], pt[1]) for pt in path[::20]])
            if dist <= rad:
                folium.Marker([wh['lat'], wh['lon']], icon=folium.Icon(color="orange", icon="shield-heart", prefix="fa"), popup=wh['name']).add_to(pm)
                found.append({"Hub": wh['name'], "Deviation (km)": round(dist, 1)})
        st_folium(pm, width="100%", height=450, key="plan_map")
        if found: st.table(pd.DataFrame(found).sort_values("Deviation (km)"))
