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

# --- 2. ADVANCED UI STYLING (THE MODERN LOOK) ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0d12; }
    
    /* Loading Animation */
    #loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: #0b0d12; display: flex; flex-direction: column;
        justify-content: center; align-items: center; z-index: 9999;
    }
    .loader { font-size: 100px; animation: pulse 1.5s infinite; color: #00FFFF; }
    @keyframes pulse { 0% { transform: scale(1); opacity: 0.5; } 50% { transform: scale(1.1); opacity: 1; } 100% { transform: scale(1); opacity: 0.5; } }

    /* Map and Graph Framed Containers */
    .element-container:has(#map-frame) { margin-top: -30px; }
    .modern-frame {
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 15px;
        background: rgba(17, 19, 26, 0.8);
        padding: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }

    /* Thermal Card - Focus on Graph */
    .graph-card {
        background: #161a23;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 20px;
    }
    .graph-header {
        display: flex;
        justify-content: space-between;
        padding: 5px 10px;
        font-family: monospace;
    }
    .status-dot {
        height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 5px;
    }
    .pulse-green { background-color: #00FF7F; box-shadow: 0 0 10px #00FF7F; }
    .pulse-red { background-color: #FF4B4B; box-shadow: 0 0 10px #FF4B4B; animation: blink 1s infinite; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }

    /* Bottom Intelligence Panel */
    .intel-box {
        background: rgba(30, 33, 48, 0.5);
        border-radius: 10px;
        padding: 20px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .metric-label { color: #808495; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { color: #ffffff; font-size: 1.4rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 100 REAL INDIAN CITIES RESCUE HUB DATASET ---
# List contains 100 strategic points across all Indian zones
RESCUE_HUBS = [
    {"name": "Delhi-Vault", "lat": 28.61, "lon": 77.21}, {"name": "Mumbai-Apex", "lat": 19.08, "lon": 72.88},
    {"name": "Bangalore-Chill", "lat": 12.98, "lon": 77.59}, {"name": "Chennai-Hub", "lat": 13.08, "lon": 80.27},
    {"name": "Kolkata-Safe", "lat": 22.57, "lon": 88.36}, {"name": "Hyderabad-Vault", "lat": 17.39, "lon": 78.49},
    {"name": "Ahmedabad-Bio", "lat": 23.02, "lon": 72.57}, {"name": "Pune-Rescue", "lat": 18.52, "lon": 73.86},
    {"name": "Lucknow-Safe", "lat": 26.85, "lon": 80.95}, {"name": "Nagpur-Central", "lat": 21.15, "lon": 79.09},
    {"name": "Jaipur-Vault", "lat": 26.91, "lon": 75.79}, {"name": "Patna-Cold", "lat": 25.59, "lon": 85.14},
    {"name": "Srinagar-Safe", "lat": 34.08, "lon": 74.80}, {"name": "Guwahati-Hub", "lat": 26.14, "lon": 91.74},
    {"name": "Kochi-Safe", "lat": 9.93, "lon": 76.27}, {"name": "Indore-Vault", "lat": 22.72, "lon": 75.86},
    {"name": "Chandigarh-Safe", "lat": 30.73, "lon": 76.78}, {"name": "Bhubaneswar-Apex", "lat": 20.30, "lon": 85.82},
    {"name": "Shimla-Rescue", "lat": 31.10, "lon": 77.17}, {"name": "Leh-Portal", "lat": 34.15, "lon": 77.57},
    {"name": "Port Blair-Apex", "lat": 11.62, "lon": 92.72}, {"name": "Bhuj-Vault", "lat": 23.24, "lon": 69.66}
]
# Fill remaining to reach 100 density
for i in range(78):
    RESCUE_HUBS.append({"name": f"Rescue-Node-{100+i}", "lat": random.uniform(8.5, 34.0), "lon": random.uniform(68.5, 95.0)})

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
    base = 8.5 if is_failing else -4.5
    return [round(base + random.uniform(-0.6, 0.6) + (random.uniform(1, 2) if random.random() < 0.1 else 0), 2) for _ in range(12)]

# --- 5. INITIALIZATION ---
loading_placeholder = st.empty()
with loading_placeholder:
    st.markdown('<div id="loading-overlay"><div class="loader">❄️</div><div style="color:white; letter-spacing:5px;">PHARMAGUARD AI ACTIVE</div></div>', unsafe_allow_html=True)

if 'fleet' not in st.session_state:
    fleet = []
    drivers = ["N. Modi", "A. Shah", "S. Jaishankar", "R. Gandhi", "M. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor"]
    for i in range(15):
        pair = random.sample(RESCUE_HUBS, 2)
        s, e = pair[0], pair[1]
        path, dist = get_road_route([s['lat'], s['lon']], [e['lat'], e['lon']])
        prog = random.uniform(0.3, 0.7)
        pos = path[int(len(path)*prog)]
        is_fail = (i == 5)
        f_data = generate_forecast(is_fail)
        fleet.append({
            "id": f"IND-EXP-{1000+i}", "driver": drivers[i % len(drivers)],
            "origin": s['name'], "dest": e['name'], "pos": pos, "path": path,
            "total_km": dist, "dist_covered": round(dist * prog), "dist_rem": round(dist * (1-prog)),
            "hrs_driven": round(prog * 15, 1), "temp": f_data[0], "forecast": f_data, "is_fail": is_fail
        })
    st.session_state.fleet = fleet
    time.sleep(1)
loading_placeholder.empty()

# --- 6. APP LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")
tabs = st.tabs(["🌐 Live Fleet Map", "🌡️ Thermal Stability", "🛤️ Route Safety Planner"])

# --- TAB 1: LIVE MAP ---
with tabs[0]:
    selected_id = st.selectbox("🎯 Select Vehicle for Live Analysis:", [t['id'] for t in st.session_state.fleet])
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    # MAP INSIDE MODERN FRAME
    st.markdown('<div class="modern-frame">', unsafe_allow_html=True)
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    folium.LatLngPopup().add_to(m)

    for wh in RESCUE_HUBS:
        folium.CircleMarker([wh['lat'], wh['lon']], radius=2, color="#3498db", fill=True).add_to(m)

    for t in st.session_state.fleet:
        is_sel = t['id'] == selected_id
        color = "#00FFFF" if is_sel else ("#FF4B4B" if t['is_fail'] else "#00FF7F")
        folium.PolyLine(t['path'], color=color, weight=5 if is_sel else 1.2, opacity=0.8 if is_sel else 0.2).add_to(m)
        folium.Marker(t['pos'], tooltip=f"Truck {t['id']} | {t['temp']}°C", icon=folium.Icon(color="purple" if is_sel else ("red" if t['is_fail'] else "green"), icon="truck", prefix="fa")).add_to(m)
    
    st_folium(m, width="100%", height=480, key="main_map")
    st.markdown('</div>', unsafe_allow_html=True)

    # Clean Intelligence Section
    st.markdown(f"### 🛡️ Intelligence Dashboard: {selected_id}")
    n_hub = min(RESCUE_HUBS, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    n_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], n_hub['lat'], n_hub['lon']), 1)
    
    # Simple Status Bar
    if selected_truck['is_fail']:
        st.error(f"🚨 ALERT: Critical thermal breach. Reroute to {n_hub['name']} ({n_dist} km deviation).")
    else:
        st.success("✅ MISSION STATUS: All environmental systems operating within nominal parameters.")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="intel-box"><div class="metric-label">Driver</div><div class="metric-value">{selected_truck["driver"]}</div><div style="color:#00FFFF; font-size:0.8rem;">Active {selected_truck["hrs_driven"]}h</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="intel-box"><div class="metric-label">Cargo Temp</div><div class="metric-value" style="color:{"#FF4B4B" if selected_truck["is_fail"] else "#00FF7F"}">{selected_truck["temp"]}°C</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="intel-box"><div class="metric-label">Progress</div><div class="metric-value">{selected_truck["dist_covered"]} km</div><div style="color:#9ea0a9; font-size:0.8rem;">of {selected_truck["total_km"]} km</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="intel-box"><div class="metric-label">Nearest Hub</div><div class="metric-value" style="font-size:1.1rem;">{n_hub["name"]}</div><div style="color:#00FFFF; font-size:0.8rem;">{n_dist} km away</div></div>', unsafe_allow_html=True)

    st.info(f"🛣️ **Full Route:** {selected_truck['origin']} ➔ {selected_truck['dest']}")

# --- TAB 2: THERMAL STABILITY (GRAPH EMPHASIZED) ---
with tabs[1]:
    st.subheader("Sub-Zero Real-Time Monitoring (-10°C to 5°C)")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            status_class = "pulse-red" if t['is_fail'] else "pulse-green"
            status_text = "BREACH" if t['is_fail'] else "STABLE"
            
            # Slim Minimal Header
            st.markdown(f"""
                <div class="graph-card">
                    <div class="graph-header">
                        <span style="color:white; font-weight:bold;">{t['id']}</span>
                        <span><span class="status-dot {status_class}"></span><span style="color:#9ea0a9; font-size:0.7rem;">{status_text}</span></span>
                    </div>
            """, unsafe_allow_html=True)
            
            # The Graph is the Hero
            df_c = pd.DataFrame({
                "Temp": t['forecast'],
                "Max": [5.0]*12,
                "Min": [-10.0]*12
            })
            st.line_chart(df_c, height=250, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: TRIP PLANNER ---
with tabs[2]:
    st.header("Strategic Pre-Trip Audit")
    p1, p2, p3 = st.columns([1,1,1])
    s_node = p1.selectbox("Start", [w['name'] for w in RESCUE_HUBS], key="ps")
    e_node = p2.selectbox("End", [w['name'] for w in RESCUE_HUBS if w['name'] != s_node], key="pe")
    if st.button("Generate Road Audit"):
        s_c = next(w for w in RESCUE_HUBS if w['name'] == s_node)
        e_c = next(w for w in RESCUE_HUBS if w['name'] == e_node)
        path, d = get_road_route([s_c['lat'], s_c['lon']], [e_c['lat'], e_c['lon']])
        st.markdown(f'<div class="intel-box"><div class="metric-label">Calculated Route Distance</div><div class="metric-value">{d} km</div></div>', unsafe_allow_html=True)
        pm = folium.Map(location=[s_c['lat'], s_c['lon']], zoom_start=6, tiles="CartoDB dark_matter")
        folium.PolyLine(path, color="#00FFFF", weight=4).add_to(pm)
        st_folium(pm, width="100%", height=450, key="plan_map")
