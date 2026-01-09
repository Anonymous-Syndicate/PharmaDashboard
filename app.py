import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random
import requests
import polyline
import math

# --- 1. CONFIGURATION ---
st.set_page_config(layout="wide", page_title="PharmaGuard | Command Center", page_icon="❄️")

# --- 2. UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0d12; }
    
    .modern-frame {
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 15px;
        background: rgba(17, 19, 26, 0.8);
        padding: 15px;
        margin-bottom: 20px;
    }

    .intel-box {
        background: rgba(30, 33, 48, 0.6);
        border-radius: 10px;
        padding: 15px;
        border-left: 4px solid #00FFFF;
        margin-bottom: 10px;
    }
    .metric-label { color: #808495; font-size: 0.75rem; text-transform: uppercase; }
    .metric-value { color: #ffffff; font-size: 1.5rem; font-weight: bold; }
    
    /* Remove extra padding from chart containers */
    [data-testid="stVerticalBlock"] > div:has(div.stAreaChart) {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 8px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA HELPERS ---
RESCUE_HUBS = [{"name": f"Hub-{i}", "lat": random.uniform(8.5, 34.0), "lon": random.uniform(68.5, 95.0)} for i in range(20)]

def get_road_route(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full"
    try:
        r = requests.get(url, timeout=5).json()
        return polyline.decode(r['routes'][0]['geometry']), round(r['routes'][0]['distance']/1000)
    except: return [[start[0], start[1]], [end[0], end[1]]], 500 

def generate_forecast(is_failing=False):
    base = 8.5 if is_failing else -4.5
    return [round(base + random.uniform(-1.2, 1.2), 2) for _ in range(20)]

# --- 4. INITIALIZATION ---
if 'fleet' not in st.session_state:
    fleet = []
    for i in range(12):
        is_fail = (i % 5 == 0)
        fleet.append({
            "id": f"IND-{1000+i}",
            "pos": [random.uniform(10, 30), random.uniform(70, 90)],
            "temp": 0,
            "forecast": generate_forecast(is_fail),
            "is_fail": is_fail
        })
    st.session_state.fleet = fleet

if 'planner_result' not in st.session_state:
    st.session_state.planner_result = None

# --- 5. APP LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")
tabs = st.tabs(["🌐 Live Fleet Map", "🌡️ Thermal Telemetry", "🛤️ Route Planner"])

# --- TAB 1: LIVE MAP ---
with tabs[0]:
    col_m, col_i = st.columns([3, 1])
    selected_id = col_i.selectbox("🎯 Select Vehicle:", [t['id'] for t in st.session_state.fleet])
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    with col_m:
        st.markdown('<div class="modern-frame">', unsafe_allow_html=True)
        m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
        for t in st.session_state.fleet:
            color = "red" if t['is_fail'] else "blue"
            if t['id'] == selected_id: color = "cadetblue"
            folium.Marker(t['pos'], icon=folium.Icon(color=color)).add_to(m)
        st_folium(m, width="100%", height=500, key="main_map")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_i:
        st.markdown(f'<div class="intel-box"><div class="metric-label">Live Temperature</div><div class="metric-value" style="color:{"#FF4B4B" if selected_truck["is_fail"] else "#00FF7F"}">{selected_truck["forecast"][-1]}°C</div></div>', unsafe_allow_html=True)

# --- TAB 2: THERMAL TELEMETRY (ONLY GRAPHS) ---
with tabs[1]:
    st.caption("Real-time cold chain sensor arrays (Historical & Predicted)")
    
    # Create a 4-column grid for the graphs
    grid_cols = st.columns(4)
    for i, t in enumerate(st.session_state.fleet):
        with grid_cols[i % 4]:
            # Creating a simple DataFrame for the graph
            chart_data = pd.DataFrame(t['forecast'], columns=["Temp"])
            
            # Displaying only the graph
            st.area_chart(chart_data, height=180, use_container_width=True)

# --- TAB 3: ROUTE PLANNER (FIXED REFRESH) ---
with tabs[2]:
    st.header("Strategic Pre-Trip Audit")
    with st.expander("Route Settings", expanded=True):
        c1, c2 = st.columns(2)
        s_node = c1.selectbox("Source", [w['name'] for w in RESCUE_HUBS], key="src")
        e_node = c2.selectbox("Destination", [w['name'] for w in RESCUE_HUBS if w['name'] != s_node], key="dst")
        
        if st.button("Generate Audit"):
            s_c = next(w for w in RESCUE_HUBS if w['name'] == s_node)
            e_c = next(w for w in RESCUE_HUBS if w['name'] == e_node)
            path, d = get_road_route([s_c['lat'], s_c['lon']], [e_c['lat'], e_c['lon']])
            st.session_state.planner_result = {"path": path, "dist": d, "start": [s_c['lat'], s_c['lon']]}

    if st.session_state.planner_result:
        res = st.session_state.planner_result
        st.markdown(f'<div class="intel-box"><div class="metric-label">Route Distance</div><div class="metric-value">{res["dist"]} KM</div></div>', unsafe_allow_html=True)
        pm = folium.Map(location=res['start'], zoom_start=6, tiles="CartoDB dark_matter")
        folium.PolyLine(res['path'], color="#00FFFF", weight=5).add_to(pm)
        st_folium(pm, width="100%", height=400, key="planner_map")
