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

# --- 2. ADVANCED UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0d12; }
    
    /* Modern Card Frame */
    .modern-frame {
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 15px;
        background: rgba(17, 19, 26, 0.8);
        padding: 15px;
        margin-bottom: 20px;
    }

    /* Thermal Card UI Fixes */
    .thermal-card {
        background: #161a23;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        margin-bottom: 15px;
        transition: 0.3s;
    }
    .thermal-card:hover { border-color: rgba(0, 255, 255, 0.5); }
    
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        font-family: 'Courier New', Courier, monospace;
    }
    
    .id-badge { color: #00FFFF; font-weight: bold; font-size: 0.9rem; }
    .temp-badge { font-size: 1.2rem; font-weight: bold; }
    
    .status-pill {
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.65rem;
        text-transform: uppercase;
    }
    .pill-safe { background: rgba(0, 255, 127, 0.2); color: #00FF7F; border: 1px solid #00FF7F; }
    .pill-danger { background: rgba(255, 75, 75, 0.2); color: #FF4B4B; border: 1px solid #FF4B4B; animation: blink 1s infinite; }

    /* Intelligence Panel */
    .intel-box {
        background: rgba(30, 33, 48, 0.6);
        border-radius: 10px;
        padding: 15px;
        border-left: 4px solid #00FFFF;
        margin-bottom: 10px;
    }
    .metric-label { color: #808495; font-size: 0.75rem; text-transform: uppercase; }
    .metric-value { color: #ffffff; font-size: 1.5rem; font-weight: bold; }

    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA & HELPERS ---
RESCUE_HUBS = [
    {"name": "Delhi-Vault", "lat": 28.61, "lon": 77.21}, {"name": "Mumbai-Apex", "lat": 19.08, "lon": 72.88},
    {"name": "Bangalore-Chill", "lat": 12.98, "lon": 77.59}, {"name": "Chennai-Hub", "lat": 13.08, "lon": 80.27},
    {"name": "Kolkata-Safe", "lat": 22.57, "lon": 88.36}, {"name": "Hyderabad-Vault", "lat": 17.39, "lon": 78.49},
    {"name": "Ahmedabad-Bio", "lat": 23.02, "lon": 72.57}, {"name": "Pune-Rescue", "lat": 18.52, "lon": 73.86}
]
for i in range(42): # Fill density
    RESCUE_HUBS.append({"name": f"Node-{100+i}", "lat": random.uniform(8.5, 34.0), "lon": random.uniform(68.5, 95.0)})

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
    return [round(base + random.uniform(-0.8, 0.8), 2) for _ in range(15)]

# --- 4. INITIALIZATION ---
if 'fleet' not in st.session_state:
    fleet = []
    drivers = ["N. Modi", "A. Shah", "S. Jaishankar", "R. Gandhi", "S. Tharoor"]
    for i in range(12):
        pair = random.sample(RESCUE_HUBS, 2)
        s, e = pair[0], pair[1]
        path, dist = get_road_route([s['lat'], s['lon']], [e['lat'], e['lon']])
        prog = random.uniform(0.2, 0.8)
        is_fail = (i == 3 or i == 7)
        f_data = generate_forecast(is_fail)
        fleet.append({
            "id": f"IND-{1000+i}", "driver": drivers[i % len(drivers)],
            "origin": s['name'], "dest": e['name'], "pos": path[int(len(path)*prog)], "path": path,
            "total_km": dist, "dist_covered": round(dist * prog), "temp": f_data[-1], "forecast": f_data, "is_fail": is_fail
        })
    st.session_state.fleet = fleet

# Persistent state for Trip Planner
if 'planner_result' not in st.session_state:
    st.session_state.planner_result = None

# --- 5. MAIN UI ---
st.title("❄️ PharmaGuard Command")
tabs = st.tabs(["🌐 Live Fleet Map", "🌡️ Thermal Stability", "🛤️ Route Safety Planner"])

# --- TAB 1: LIVE MAP ---
with tabs[0]:
    col_m, col_i = st.columns([3, 1])
    selected_id = col_i.selectbox("🎯 Focus Vehicle:", [t['id'] for t in st.session_state.fleet])
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    with col_m:
        st.markdown('<div class="modern-frame">', unsafe_allow_html=True)
        m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
        for t in st.session_state.fleet:
            color = "#FF4B4B" if t['is_fail'] else "#00FF7F"
            if t['id'] == selected_id: color = "#00FFFF"
            folium.Marker(t['pos'], icon=folium.Icon(color="red" if t['is_fail'] else "blue", icon="truck", prefix="fa")).add_to(m)
        st_folium(m, width="100%", height=500, key="main_map")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_i:
        st.markdown(f'<div class="intel-box"><div class="metric-label">Cargo Temp</div><div class="metric-value" style="color:{"#FF4B4B" if selected_truck["is_fail"] else "#00FF7F"}">{selected_truck["temp"]}°C</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="intel-box"><div class="metric-label">Operator</div><div class="metric-value">{selected_truck["driver"]}</div></div>', unsafe_allow_html=True)
        st.info(f"Route: {selected_truck['origin']} to {selected_truck['dest']}")

# --- TAB 2: THERMAL STABILITY (FIXED UI) ---
with tabs[1]:
    st.subheader("Real-Time Thermal Telemetry")
    cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with cols[i % 3]:
            status_pill = "pill-danger" if t['is_fail'] else "pill-safe"
            status_txt = "Breach Detected" if t['is_fail'] else "Optimal"
            temp_color = "#FF4B4B" if t['is_fail'] else "#00FF7F"
            
            # Custom Card Container
            st.markdown(f"""
                <div class="thermal-card">
                    <div class="card-header">
                        <span class="id-badge">{t['id']}</span>
                        <span class="status-pill {status_pill}">{status_txt}</span>
                    </div>
                    <div style="display:flex; align-items:baseline; gap:10px; margin-bottom:10px;">
                        <span class="temp-badge" style="color:{temp_color}">{t['temp']}°C</span>
                        <span style="color:#808495; font-size:0.8rem;">Internal Ambient</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Chart placed precisely below the custom HTML header
            chart_data = pd.DataFrame({"Temperature": t['forecast']})
            st.area_chart(chart_data, height=150, use_container_width=True)
            st.write("---")

# --- TAB 3: TRIP PLANNER (FIXED REFRESH BUG) ---
with tabs[2]:
    st.header("Strategic Pre-Trip Audit")
    
    # Input Area
    with st.expander("Configure Route Parameters", expanded=True):
        p1, p2 = st.columns(2)
        s_node = p1.selectbox("Source Hub", [w['name'] for w in RESCUE_HUBS], key="src")
        e_node = p2.selectbox("Destination Hub", [w['name'] for w in RESCUE_HUBS if w['name'] != s_node], key="dest")
        
        if st.button("Calculate Safety Protocol"):
            s_c = next(w for w in RESCUE_HUBS if w['name'] == s_node)
            e_c = next(w for w in RESCUE_HUBS if w['name'] == e_node)
            path, d = get_road_route([s_c['lat'], s_c['lon']], [e_c['lat'], e_c['lon']])
            
            # CRITICAL FIX: Save to session state
            st.session_state.planner_result = {
                "path": path,
                "distance": d,
                "start": [s_c['lat'], s_c['lon']],
                "end": [e_c['lat'], e_c['lon']]
            }

    # Display Area: This checks session state so it persists during map interaction
    if st.session_state.planner_result:
        res = st.session_state.planner_result
        
        st.markdown(f"""
            <div class="intel-box">
                <div class="metric-label">Calculated Path Distance</div>
                <div class="metric-value">{res['distance']} KM</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Display the Map
        pm = folium.Map(location=res['start'], zoom_start=6, tiles="CartoDB dark_matter")
        folium.PolyLine(res['path'], color="#00FFFF", weight=5, opacity=0.8).add_to(pm)
        folium.Marker(res['start'], tooltip="Start").add_to(pm)
        folium.Marker(res['end'], tooltip="End").add_to(pm)
        
        st_folium(pm, width="100%", height=500, key="planner_map_unique")
