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
st.set_page_config(layout="wide", page_title="PharmaGuard | Command Center", page_icon="❄️")

# --- 2. GLOBAL UI STYLING ---
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
    @keyframes pulse { 
        0% { transform: scale(1); opacity: 0.7; } 
        50% { transform: scale(1.1); opacity: 1; color: #00FFFF; } 
        100% { transform: scale(1); opacity: 0.7; } 
    }
    
    /* Glassmorphism Card Design */
    .intel-card {
        background: rgba(30, 33, 48, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px; padding: 20px; margin-bottom: 15px; min-height: 220px;
    }
    .card-label { color: #9ea0a9; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; }
    .card-value { color: #ffffff; font-size: 1.4rem; font-weight: 700; margin-bottom: 2px; }
    .card-sub { color: #00FFFF; font-size: 0.85rem; font-weight: 400; }
    
    /* Visual Progress Bar */
    .progress-container { width: 100%; background-color: #262730; border-radius: 10px; margin: 15px 0; height: 10px; }
    .progress-fill { height: 10px; border-radius: 10px; background: linear-gradient(90deg, #00FFFF, #3498db); }
    
    /* Status Badges */
    .status-badge { padding: 10px 16px; border-radius: 8px; font-size: 0.9rem; font-weight: bold; display: block; margin-bottom: 20px; border-left: 5px solid; }
    .status-safe { background: rgba(0, 255, 127, 0.1); color: #00FF7F; border-color: #00FF7F; }
    .status-alert { background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border-color: #FF4B4B; animation: blink 1.5s infinite; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 100 REAL INDIAN CITIES DATASET ---
WAREHOUSE_NETWORK = [
    {"name": "Delhi-Vault", "lat": 28.61, "lon": 77.21}, {"name": "Mumbai-Apex", "lat": 19.08, "lon": 72.88},
    {"name": "Bangalore-Chill", "lat": 12.98, "lon": 77.59}, {"name": "Chennai-Hub", "lat": 13.08, "lon": 80.27},
    {"name": "Kolkata-Safe", "lat": 22.57, "lon": 88.36}, {"name": "Hyderabad-Vault", "lat": 17.39, "lon": 78.49},
    {"name": "Ahmedabad-Bio", "lat": 23.02, "lon": 72.57}, {"name": "Pune-Rescue", "lat": 18.52, "lon": 73.86},
    {"name": "Lucknow-Safe", "lat": 26.85, "lon": 80.95}, {"name": "Nagpur-Central", "lat": 21.15, "lon": 79.09},
    {"name": "Jaipur-Vault", "lat": 26.91, "lon": 75.79}, {"name": "Kanpur-Apex", "lat": 26.45, "lon": 80.33},
    {"name": "Surat-Safe", "lat": 21.17, "lon": 72.83}, {"name": "Patna-Cold", "lat": 25.59, "lon": 85.14},
    {"name": "Vadodara-Chill", "lat": 22.31, "lon": 73.18}, {"name": "Ludhiana-Hub", "lat": 30.90, "lon": 75.86},
    {"name": "Nashik-Apex", "lat": 20.00, "lon": 73.79}, {"name": "Ranchi-Safe", "lat": 23.34, "lon": 85.31},
    {"name": "Raipur-Rescue", "lat": 21.25, "lon": 81.63}, {"name": "Meerut-Vault", "lat": 28.98, "lon": 77.71},
    {"name": "Rajkot-Safe", "lat": 22.30, "lon": 70.80}, {"name": "Varanasi-Bio", "lat": 25.32, "lon": 82.97},
    {"name": "Srinagar-Chill", "lat": 34.08, "lon": 74.80}, {"name": "Amritsar-Safe", "lat": 31.63, "lon": 74.87},
    {"name": "Jodhpur-Vault", "lat": 26.24, "lon": 73.02}, {"name": "Chandigarh-Chill", "lat": 30.73, "lon": 76.78},
    {"name": "Gwalior-Cold", "lat": 26.22, "lon": 78.18}, {"name": "Vijayawada-Vault", "lat": 16.51, "lon": 80.65},
    {"name": "Madurai-Safe", "lat": 9.93, "lon": 78.12}, {"name": "Guwahati-Bio", "lat": 26.14, "lon": 91.74},
    {"name": "Hubli-Vault", "lat": 15.36, "lon": 75.12}, {"name": "Bareilly-Hub", "lat": 28.37, "lon": 79.43},
    {"name": "Salem-Vault", "lat": 11.66, "lon": 78.15}, {"name": "Kochi-Hub", "lat": 9.93, "lon": 76.27},
    {"name": "Udaipur-Vault", "lat": 24.59, "lon": 73.71}, {"name": "Dehradun-Chill", "lat": 30.32, "lon": 78.03},
    {"name": "Jammu-Safe", "lat": 32.72, "lon": 74.85}, {"name": "Bhopal-Hub", "lat": 23.26, "lon": 77.41},
    {"name": "Trivandrum-Bio", "lat": 8.52, "lon": 76.94}, {"name": "Shimla-Rescue", "lat": 31.10, "lon": 77.17},
    {"name": "Agartala-Safe", "lat": 23.83, "lon": 91.29}, {"name": "Imphal-Apex", "lat": 24.81, "lon": 93.93},
    {"name": "Aizawl-Bio", "lat": 23.72, "lon": 92.71}, {"name": "Shillong-Safe", "lat": 25.58, "lon": 91.89},
    {"name": "Gangtok-Vault", "lat": 27.33, "lon": 88.61}, {"name": "Leh-Portal", "lat": 34.15, "lon": 77.57},
    {"name": "Port Blair-Apex", "lat": 11.62, "lon": 92.72}, {"name": "Panaji-Safe", "lat": 15.49, "lon": 73.82},
    {"name": "Mysore-Chill", "lat": 12.30, "lon": 76.64}, {"name": "Tirupati-Hub", "lat": 13.63, "lon": 79.42},
    {"name": "Gulbarga-Vault", "lat": 17.33, "lon": 76.83}, {"name": "Jamnagar-Bio", "lat": 22.47, "lon": 70.06},
    {"name": "Ujjain-Safe", "lat": 23.18, "lon": 75.78}, {"name": "Jhansi-Hub", "lat": 25.44, "lon": 78.56},
    {"name": "Nellore-Vault", "lat": 14.44, "lon": 79.99}, {"name": "Kurnool-Chill", "lat": 15.83, "lon": 78.04},
    {"name": "Warangal-Apex", "lat": 17.97, "lon": 79.59}, {"name": "Dhanbad-Hub", "lat": 23.80, "lon": 86.43},
    {"name": "Muzaffarpur-Safe", "lat": 26.12, "lon": 85.36}, {"name": "Rourkela-Bio", "lat": 22.26, "lon": 84.85},
    {"name": "Bilaspur-Vault", "lat": 22.08, "lon": 82.14}, {"name": "Korba-Safe", "lat": 22.35, "lon": 82.68},
    {"name": "Bhilai-Chill", "lat": 21.19, "lon": 81.35}, {"name": "Ahmednagar-Bio", "lat": 19.10, "lon": 74.74},
    {"name": "Aligarh-Safe", "lat": 27.88, "lon": 78.08}, {"name": "Saharanpur-Vault", "lat": 29.97, "lon": 77.55},
    {"name": "Gorakhpur-Chill", "lat": 26.76, "lon": 83.37}, {"name": "Bikaner-Bio", "lat": 28.02, "lon": 73.31},
    {"name": "Firozabad-Safe", "lat": 27.15, "lon": 78.39}, {"name": "Bhavnagar-Vault", "lat": 21.76, "lon": 72.15},
    {"name": "Ajmer-Chill", "lat": 26.45, "lon": 74.64}, {"name": "Akola-Bio", "lat": 20.70, "lon": 77.01},
    {"name": "Gulbarga-Safe", "lat": 17.33, "lon": 76.83}, {"name": "Durg-Vault", "lat": 21.19, "lon": 81.28},
    {"name": "Solapur-Chill", "lat": 17.66, "lon": 75.91}, {"name": "Gaya-Bio", "lat": 24.79, "lon": 85.00},
    {"name": "Mathura-Safe", "lat": 27.49, "lon": 77.67}, {"name": "Alwar-Vault", "lat": 27.55, "lon": 76.60},
    {"name": "Etawah-Chill", "lat": 26.77, "lon": 79.02}, {"name": "Bharatpur-Bio", "lat": 27.22, "lon": 77.49},
    {"name": "Ratlam-Safe", "lat": 23.33, "lon": 75.04}, {"name": "Haldia-Vault", "lat": 22.06, "lon": 88.06},
    {"name": "Koraput-Bio", "lat": 18.81, "lon": 82.71}, {"name": "Ankleshwar-Safe", "lat": 21.63, "lon": 73.01},
    {"name": "Vapi-Vault", "lat": 20.37, "lon": 72.90}, {"name": "Siliguri-Safe", "lat": 26.72, "lon": 88.40},
    {"name": "Tezpur-Bio", "lat": 26.63, "lon": 92.79}, {"name": "Hospet-Vault", "lat": 15.27, "lon": 76.39},
    {"name": "Gandhidham-Safe", "lat": 23.08, "lon": 70.13}, {"name": "Bellary-Chill", "lat": 15.14, "lon": 76.92},
    {"name": "Guntur-Vault", "lat": 16.30, "lon": 80.44}, {"name": "Anantapur-Bio", "lat": 14.68, "lon": 77.60},
    {"name": "Sagar-Safe", "lat": 23.84, "lon": 78.74}, {"name": "Satna-Vault", "lat": 24.58, "lon": 80.83},
    {"name": "Rohtak-Bio", "lat": 28.90, "lon": 76.61}, {"name": "Panipat-Vault", "lat": 29.39, "lon": 76.96}
]

# --- 4. HELPERS ---
@st.cache_data(ttl=3600)
def get_road_route(start_coords, end_coords):
    url = f"http://router.project-osrm.org/route/v1/driving/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}?overview=full"
    try:
        r = requests.get(url, timeout=5).json()
        return polyline.decode(r['routes'][0]['geometry']), round(r['routes'][0]['distance']/1000)
    except: return [start_coords, end_coords], 500 

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def generate_forecast(is_failing=False):
    data = []
    base = 8.8 if is_failing else -4.2
    for _ in range(12):
        val = base + random.uniform(-0.4, 0.4)
        if random.random() < 0.15: val += random.uniform(1.2, 2.5)
        if not is_failing: val = max(-9.5, min(4.8, val))
        data.append(round(val, 2))
    return data

# --- 5. INITIALIZATION ---
loading_placeholder = st.empty()
with loading_placeholder:
    st.markdown('<div id="loading-overlay"><div class="loader">❄️</div><div class="loading-text">SPREADING NATIONAL NETWORK...</div></div>', unsafe_allow_html=True)

if 'fleet' not in st.session_state:
    fleet = []
    drivers = ["N. Modi", "A. Shah", "S. Jaishankar", "R. Gandhi", "M. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor", "Arjun Kapur", "Deepak Punia"]
    
    for i in range(15):
        # Pick random unique pairs from the 100 cities for maximum spread
        loc_pair = random.sample(WAREHOUSE_NETWORK, 2)
        s, e = loc_pair[0], loc_pair[1]
        
        path, dist = get_road_route([s['lat'], s['lon']], [e['lat'], e['lon']])
        prog = random.uniform(0.3, 0.7)
        pos = path[int(len(path)*prog)]
        is_fail = (i == 5)
        f_data = generate_forecast(is_fail)
        
        fleet.append({
            "id": f"IND-EXP-{1000+i}", "driver": drivers[i % len(drivers)],
            "origin": s['name'], "dest": e['name'], "pos": pos, "path": path,
            "total_km": dist, "dist_covered": round(dist * prog), "dist_rem": round(dist * (1-prog)),
            "hrs_driven": round(prog * 15, 1), "temp": f_data[0], "prog_pct": round(prog*100),
            "forecast": f_data
        })
    st.session_state.fleet = fleet
else:
    time.sleep(1.2) # Delay for refresh effect

loading_placeholder.empty()

# --- 6. APP LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")
tab1, tab2, tab3 = st.tabs(["🌐 Live Fleet Map", "🌡️ Thermal Forecasts", "🛤️ Trip Planner"])

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

    # --- SYSTEM INTELLIGENCE ---
    st.markdown(f"### 🛡️ System Intelligence: {selected_id}")
    is_critical = selected_truck['temp'] > 5 or selected_truck['temp'] < -10
    n_hub = min(WAREHOUSE_NETWORK, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    n_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], n_hub['lat'], n_hub['lon']))
    
    if is_critical:
        st.markdown(f'<div class="status-badge status-alert">🚨 ALERT: THERMAL BREACH - DIVERT TO {n_hub["name"].upper()}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge status-safe">✅ MISSION STATUS: CONTINUE / SAFE | Environment Nominal.</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.2, 2, 1.2])
    with c1:
        st.markdown(f"""<div class="intel-card">
            <div class="card-label">Vehicle & Driver</div><div class="card-value">{selected_truck['driver']}</div>
            <div class="card-sub">Active for {selected_truck['hrs_driven']} hrs</div><hr style="opacity:0.1; margin:10px 0;">
            <div class="card-label">Cargo Temperature</div><div class="card-value" style="color:{'#FF4B4B' if is_critical else '#00FF7F'}">{selected_truck['temp']}°C</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        eta = (datetime.now() + timedelta(hours=selected_truck['dist_rem']/60)).strftime("%H:%M, %d %b")
        st.markdown(f"""<div class="intel-card">
            <div class="card-label">Trip Progress</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;"><span style="color:white; font-weight:bold;">{selected_truck['dist_covered']} km</span><span style="color:#9ea0a9;">{selected_truck['total_km']} km Total</span></div>
            <div class="progress-container"><div class="progress-fill" style="width:{selected_truck['prog_pct']}%"></div></div>
            <div style="display:flex; justify-content:space-between; margin-top:15px;"><div><div class="card-label">Remaining</div><div class="card-value" style="font-size:1.2rem;">{selected_truck['dist_rem']} km</div></div><div style="text-align:right;"><div class="card-label">Est. Arrival</div><div class="card-value" style="font-size:1.2rem;">{eta}</div></div></div>
            <hr style="opacity:0.1; margin:10px 0;"><div class="card-label">Logistics Corridor</div><div style="font-size:0.85rem; color:#00FFFF; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{selected_truck['origin']} ➔ {selected_truck['dest']}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div class="intel-card" style="border-left: 4px solid {'#FF4B4B' if is_critical else '#3498db'}">
            <div class="card-label">Nearest Rescue Node</div><div class="card-value" style="font-size:1.3rem;">{n_hub['name']}</div>
            <div class="card-sub">{n_dist} km deviation</div><hr style="opacity:0.1; margin:15px 0;">
            <div class="card-label">Emergency Protocol</div><div style="font-size:0.8rem; color:#9ea0a9;">{'Contact hub manager for immediate offload.' if is_critical else 'Maintain current heading.'}</div>
        </div>""", unsafe_allow_html=True)

# --- TAB 2: THERMAL FORECASTS ---
with tab2:
    st.subheader("Sub-Zero Thermal Stability Forecast (-10°C to 5°C)")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            is_t_alert = t['temp'] > 5
            st.markdown(f"""<div class="intel-card" style="min-height:280px; border-top: 4px solid {'#FF4B4B' if is_t_alert else '#00FF7F'}">
                <div class="card-label">Truck {t['id']}</div>
                <div class="card-value" style="font-size:1.1rem; color:{'#FF4B4B' if is_t_alert else '#00FF7F'}">{'🚨 THERMAL BREACH' if is_t_alert else '✅ STABLE'}</div>
            </div>""", unsafe_allow_html=True)
            df_c = pd.DataFrame({"Temp": t['forecast'], "Max": [5]*12, "Min": [-10]*12})
            st.line_chart(df_c, height=150)

# --- TAB 3: TRIP PLANNER ---
with tab3:
    st.header("Strategic Route Safety Audit")
    p1, p2, p3 = st.columns([1,1,1])
    s_node = p1.selectbox("Departure Hub", [w['name'] for w in WAREHOUSE_NETWORK], key="p_s")
    e_node = p2.selectbox("Destination Hub", [w['name'] for w in WAREHOUSE_NETWORK if w['name'] != s_node], key="p_e")
    radius = p3.slider("Rescue Search Buffer (km)", 20, 150, 60)
    
    if st.button("Generate Road Safety Audit"):
        s_c = next(w for w in WAREHOUSE_NETWORK if w['name'] == s_node)
        e_c = next(w for w in WAREHOUSE_NETWORK if w['name'] == e_node)
        path, d = get_road_route([s_c['lat'], s_c['lon']], [e_c['lat'], e_c['lon']])
        
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1: st.markdown(f'<div class="intel-card"><div class="card-label">Distance</div><div class="card-value">{d} km</div><div class="card-sub">National Highways</div></div>', unsafe_allow_html=True)
        with c_p2: st.markdown(f'<div class="intel-card"><div class="card-label">Est. Time</div><div class="card-value">{round(d/60, 1)} hrs</div><div class="card-sub">Avg: 60km/h</div></div>', unsafe_allow_html=True)
        with c_p3:
            hubs_near = [w for w in WAREHOUSE_NETWORK if min([haversine(w['lat'], w['lon'], pt[0], pt[1]) for pt in path[::25]]) <= radius]
            st.markdown(f'<div class="intel-card"><div class="card-label">Safety Coverage</div><div class="card-value">{len(hubs_near)} Nodes</div><div class="card-sub">{radius}km radius</div></div>', unsafe_allow_html=True)
            
        pm = folium.Map(location=[s_c['lat'], s_c['lon']], zoom_start=6, tiles="CartoDB dark_matter")
        folium.PolyLine(path, color="#00FFFF", weight=4).add_to(pm)
        for wh in hubs_near:
            folium.Marker([wh['lat'], wh['lon']], icon=folium.Icon(color="orange", icon="shield-heart", prefix="fa"), popup=wh['name']).add_to(pm)
        st_folium(pm, width="100%", height=450, key="plan_map")
