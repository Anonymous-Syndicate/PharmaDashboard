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

# --- 2. GLOBAL UI STYLING (MODERN & GRAPH-CENTRIC) ---
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
    
    /* Modern Box for the Map and Charts */
    .modern-box {
        background: rgba(30, 33, 48, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
    }

    /* Minimalist Thermal Card */
    .thermal-card-header {
        background: rgba(30, 33, 48, 0.8);
        border-radius: 10px 10px 0 0;
        padding: 8px 15px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Intelligence Cards */
    .intel-card {
        background: rgba(30, 33, 48, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px; padding: 20px; margin-bottom: 15px;
    }
    .card-label { color: #9ea0a9; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1.2px; }
    .card-value { color: #ffffff; font-size: 1.4rem; font-weight: 700; }
    
    .progress-container { width: 100%; background-color: #262730; border-radius: 10px; margin: 12px 0; height: 8px; }
    .progress-fill { height: 8px; border-radius: 10px; background: linear-gradient(90deg, #00FFFF, #3498db); }
    
    .status-badge { padding: 10px 16px; border-radius: 8px; font-size: 0.9rem; font-weight: bold; display: block; margin-bottom: 20px; border-left: 5px solid; }
    .status-safe { background: rgba(0, 255, 127, 0.1); color: #00FF7F; border-color: #00FF7F; }
    .status-alert { background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border-color: #FF4B4B; animation: blink 1.5s infinite; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 100 REAL INDIAN CITIES RESCUE HUB DATASET ---
WAREHOUSE_NETWORK = [
    {"name": "Delhi-Vault", "lat": 28.61, "lon": 77.21}, {"name": "Mumbai-Apex", "lat": 19.08, "lon": 72.88},
    {"name": "Bangalore-Chill", "lat": 12.98, "lon": 77.59}, {"name": "Chennai-Hub", "lat": 13.08, "lon": 80.27},
    {"name": "Kolkata-Safe", "lat": 22.57, "lon": 88.36}, {"name": "Hyderabad-Vault", "lat": 17.39, "lon": 78.49},
    {"name": "Ahmedabad-Bio", "lat": 23.02, "lon": 72.57}, {"name": "Pune-Rescue", "lat": 18.52, "lon": 73.86},
    {"name": "Lucknow-Safe", "lat": 26.85, "lon": 80.95}, {"name": "Nagpur-Central", "lat": 21.15, "lon": 79.09},
    {"name": "Jaipur-Vault", "lat": 26.91, "lon": 75.79}, {"name": "Patna-Cold", "lat": 25.59, "lon": 85.14},
    {"name": "Ludhiana-Hub", "lat": 30.90, "lon": 75.86}, {"name": "Nashik-Apex", "lat": 20.00, "lon": 73.79},
    {"name": "Ranchi-Safe", "lat": 23.34, "lon": 85.31}, {"name": "Raipur-Rescue", "lat": 21.25, "lon": 81.63},
    {"name": "Meerut-Vault", "lat": 28.98, "lon": 77.71}, {"name": "Rajkot-Safe", "lat": 22.30, "lon": 70.80},
    {"name": "Varanasi-Bio", "lat": 25.32, "lon": 82.97}, {"name": "Srinagar-Chill", "lat": 34.08, "lon": 74.80}
]
# Fill up to 100 for density
for i in range(80):
    WAREHOUSE_NETWORK.append({"name": f"Rescue-Node-{100+i}", "lat": random.uniform(9.0, 33.0), "lon": random.uniform(70.0, 92.0)})

PHARMA_HUBS = {"Baddi Hub (North)": [30.95, 76.79], "Sikkim Cluster": [27.33, 88.61], "Vizag City": [17.68, 83.21], "Goa Manufacturing": [15.29, 74.12]}
DESTINATIONS = {"Mumbai Port": [18.94, 72.83], "Delhi Cargo": [28.55, 77.10], "Bangalore Dist": [12.97, 77.59]}

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

# --- 5. INITIALIZATION ---
if 'fleet' not in st.session_state:
    loading_placeholder = st.empty()
    with loading_placeholder:
        st.markdown('<div id="loading-overlay"><div class="loader">❄️</div><div class="loading-text">PHARMAGUARD AI: INITIALIZING...</div></div>', unsafe_allow_html=True)
    
    fleet = []
    drivers = ["N. Modi", "A. Shah", "S. Jaishankar", "R. Gandhi", "M. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji"]
    all_locs = WAREHOUSE_NETWORK + [{"name": k, "lat": v[0], "lon": v[1]} for k, v in PHARMA_HUBS.items()]
    
    for i in range(15):
        pair = random.sample(all_locs, 2)
        s, e = pair[0], pair[1]
        path, dist = get_road_route([s['lat'], s['lon']], [e['lat'], e['lon']])
        prog = random.uniform(0.3, 0.7)
        pos = path[int(len(path)*prog)]
        is_fail = (i == 5) # IND-EXP-1005 is the breach truck
        
        fleet.append({
            "id": f"IND-EXP-{1000+i}", "driver": drivers[i % len(drivers)],
            "origin": s['name'], "dest": e['name'], "pos": pos, "path": path,
            "total_km": dist, "dist_covered": round(dist * prog), "dist_rem": round(dist * (1-prog)),
            "hrs_driven": round(prog * 15, 1), "temp": 8.5 if is_fail else round(random.uniform(-7, 2), 2),
            "prog_pct": round(prog*100),
            "forecast": [round(random.uniform(-9, 3 if not is_fail else 12), 2) for _ in range(12)]
        })
    st.session_state.fleet = fleet
    time.sleep(1)
    loading_placeholder.empty()

# --- 6. APP LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")
tabs = st.tabs(["🌐 Live Fleet Map", "🌡️ Thermal Stability", "🛤️ Trip Safety Planner"])

# --- TAB 1: LIVE MAP ---
with tabs[0]:
    selected_id = st.selectbox("🎯 Select Truck for Analysis:", [t['id'] for t in st.session_state.fleet])
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    st.markdown('<div class="modern-box">', unsafe_allow_html=True)
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    folium.LatLngPopup().add_to(m)

    for wh in WAREHOUSE_NETWORK:
        folium.CircleMarker([wh['lat'], wh['lon']], radius=1.5, color="#3498db", fill=True).add_to(m)

    for t in st.session_state.fleet:
        is_sel = t['id'] == selected_id
        is_alert = t['temp'] > 5
        color = "#00FFFF" if is_sel else ("#FF4B4B" if is_alert else "#00FF7F")
        folium.PolyLine(t['path'], color=color, weight=5 if is_sel else 1.2, opacity=0.8 if is_sel else 0.2).add_to(m)
        folium.Marker(t['pos'], tooltip=f"{t['id']}: {t['temp']}°C", icon=folium.Icon(color="purple" if is_sel else ("red" if is_alert else "green"), icon="truck", prefix="fa")).add_to(m)
    
    st_folium(m, width="100%", height=480, key="main_map")
    st.markdown('</div>', unsafe_allow_html=True)

    # Systematic Intelligence
    st.markdown(f"### 🛡️ System Intelligence: {selected_id}")
    is_critical = selected_truck['temp'] > 5
    n_hub = min(WAREHOUSE_NETWORK, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    n_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], n_hub['lat'], n_hub['lon']), 1)
    
    status_class = "status-alert" if is_critical else "status-safe"
    status_text = f"🛑 ALERT: BREACH AT {selected_truck['temp']}°C - REROUTE TO {n_hub['name'].upper()}" if is_critical else "✅ MISSION STATUS: CONTINUE / SAFE"
    st.markdown(f'<div class="status-badge {status_class}">{status_text}</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.8, 1.2])
    with c1:
        st.markdown(f"""<div class="intel-card">
            <div class="card-label">Driver</div><div class="card-value">{selected_truck['driver']}</div>
            <div class="card-sub">{selected_truck['hrs_driven']} hrs Active</div><hr style="opacity:0.1;">
            <div class="card-label">Cargo Temp</div><div class="card-value" style="color:{'#FF4B4B' if is_critical else '#00FF7F'}">{selected_truck['temp']}°C</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        eta = (datetime.now() + timedelta(hours=selected_truck['dist_rem']/60)).strftime("%H:%M")
        st.markdown(f"""<div class="intel-card">
            <div class="card-label">Trip Progress</div><div style="display:flex; justify-content:space-between;"><span style="color:white; font-weight:bold;">{selected_truck['dist_covered']} km</span><span style="color:#9ea0a9;">{selected_truck['total_km']} km Total</span></div>
            <div class="progress-container"><div class="progress-fill" style="width:{selected_truck['prog_pct']}%"></div></div>
            <div style="display:flex; justify-content:space-between;"><div><div class="card-label">Remaining</div><div class="card-value" style="font-size:1.1rem;">{selected_truck['dist_rem']} km</div></div><div style="text-align:right;"><div class="card-label">Est. Arrival</div><div class="card-value" style="font-size:1.1rem;">{eta}</div></div></div>
            <hr style="opacity:0.1;"><div class="card-label">Corridor</div><div style="font-size:0.8rem; color:#00FFFF;">{selected_truck['origin']} ➔ {selected_truck['dest']}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="intel-card" style="border-left: 4px solid {'#FF4B4B' if is_critical else '#3498db'}">
            <div class="card-label">Rescue Hub</div><div class="card-value" style="font-size:1.2rem;">{n_hub['name']}</div>
            <div style="color:#00FFFF; font-size:0.85rem;">{n_dist} km deviation</div><hr style="opacity:0.1;">
            <div class="card-label">Protocol</div><div style="font-size:0.8rem; color:#9ea0a9;">{'Emergency diversion suggested.' if is_critical else 'No action required.'}</div>
        </div>""", unsafe_allow_html=True)

# --- TAB 2: THERMAL FORECASTS (GRAPH HIGHLIGHTED) ---
with tabs[1]:
    st.subheader("Sub-Zero Thermal Stability Forecast (-10°C to 5°C)")
    st.markdown("---")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            is_t_alert = t['temp'] > 5
            border_color = "#FF4B4B" if is_t_alert else "#00FF7F"
            
            # Slim Integrated Header
            st.markdown(f"""
                <div class="thermal-card-header" style="border-top: 3px solid {border_color};">
                    <span style="color:#9ea0a9; font-size:0.75rem; font-weight:bold;">{t['id']}</span>
                    <span style="color:{border_color}; font-size:0.75rem; font-weight:bold;">{'🚨 BREACH' if is_t_alert else '✅ STABLE'}</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Chart Area with subtle background
            with st.container():
                st.markdown('<div style="background: rgba(255,255,255,0.02); padding: 15px; border: 1px solid rgba(255,255,255,0.05); border-top:none; border-radius: 0 0 10px 10px;">', unsafe_allow_html=True)
                df_c = pd.DataFrame({
                    "Temp": t['forecast'],
                    "Max (5°C)": [5.0]*12,
                    "Min (-10°C)": [-10.0]*12
                })
                # Highlighted Graph
                st.line_chart(df_c, height=220, use_container_width=True)
                st.markdown('</div><br>', unsafe_allow_html=True)

# --- TAB 3: TRIP PLANNER ---
with tabs[2]:
    st.header("Strategic Route Planner")
    p1, p2, p3 = st.columns([1,1,1])
    s_node = p1.selectbox("Start", [w['name'] for w in WAREHOUSE_NETWORK], key="ps")
    e_node = p2.selectbox("End", [w['name'] for w in WAREHOUSE_NETWORK if w['name'] != s_node], key="pe")
    radius = p3.slider("Radius (km)", 20, 150, 50)
    if st.button("Generate Audit"):
        s_c = next(w for w in WAREHOUSE_NETWORK if w['name'] == s_node)
        e_c = next(w for w in WAREHOUSE_NETWORK if w['name'] == e_node)
        path, d = get_road_route([s_c['lat'], s_c['lon']], [e_c['lat'], e_c['lon']])
        
        st.markdown(f'<div class="intel-card"><div class="card-label">Audit Result</div><div class="card-value">{d} km National Highway Path</div></div>', unsafe_allow_html=True)
        pm = folium.Map(location=[s_c['lat'], s_c['lon']], zoom_start=6, tiles="CartoDB dark_matter")
        folium.PolyLine(path, color="#00FFFF", weight=4).add_to(pm)
        st_folium(pm, width="100%", height=450, key="plan_map")
