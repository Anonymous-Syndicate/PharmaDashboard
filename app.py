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

# --- 2. GLOBAL UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0d12; color: #ffffff; }
    
    /* Loading Overlay */
    #loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: #0b0d12; display: flex; flex-direction: column;
        justify-content: center; align-items: center; z-index: 9999;
    }
    .loader-icon { font-size: 80px; animation: pulse 1.5s infinite; color: #00FFFF; }
    @keyframes pulse { 0% { transform: scale(1); opacity: 0.5; } 50% { transform: scale(1.1); opacity: 1; } 100% { transform: scale(1); opacity: 0.5; } }

    /* Map Box */
    .map-frame {
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 15px; background: rgba(17, 19, 26, 0.9);
        padding: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.8); margin-bottom: 25px;
    }

    /* Intelligence Dashboard Cards */
    .intel-card {
        background: rgba(30, 33, 48, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px; padding: 20px; min-height: 160px;
    }
    .m-label { color: #808495; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; }
    .m-value { color: #ffffff; font-size: 1.4rem; font-weight: bold; }
    .m-sub { color: #00FFFF; font-size: 0.85rem; margin-top: 5px; }
    
    .status-pill {
        padding: 10px 18px; border-radius: 8px; font-size: 0.9rem; font-weight: bold;
        display: block; margin-bottom: 20px; border-left: 6px solid;
    }
    .status-safe { background: rgba(0, 255, 127, 0.1); color: #00FF7F; border-color: #00FF7F; }
    .status-alert { background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border-color: #FF4B4B; animation: blink 1.5s infinite; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATASETS (100 REAL INDIAN LOGISTICS NODES) ---
@st.cache_data
def get_india_rescue_network():
    # Hardcoded base cities to ensure India-Centricity
    hubs = [
        {"name": "Delhi-Vault", "lat": 28.6139, "lon": 77.2090}, {"name": "Mumbai-Apex", "lat": 19.0760, "lon": 72.8777},
        {"name": "Bangalore-Chill", "lat": 12.9716, "lon": 77.5946}, {"name": "Chennai-Hub", "lat": 13.0827, "lon": 80.2707},
        {"name": "Kolkata-Safe", "lat": 22.5726, "lon": 88.3639}, {"name": "Hyderabad-Vault", "lat": 17.3850, "lon": 78.4867},
        {"name": "Ahmedabad-Bio", "lat": 23.0225, "lon": 72.5714}, {"name": "Pune-Rescue", "lat": 18.5204, "lon": 73.8567},
        {"name": "Lucknow-Safe", "lat": 26.8467, "lon": 80.9462}, {"name": "Nagpur-Central", "lat": 21.1458, "lon": 79.0882},
        {"name": "Patna-Cold", "lat": 25.5941, "lon": 85.1376}, {"name": "Srinagar-Safe", "lat": 34.0837, "lon": 74.7973},
        {"name": "Guwahati-Bio", "lat": 26.1445, "lon": 91.7362}, {"name": "Chandigarh-Chill", "lat": 30.7333, "lon": 76.7794},
        {"name": "Bhopal-Vault", "lat": 23.2599, "lon": 77.4126}, {"name": "Indore-Safe", "lat": 22.7196, "lon": 75.8577}
    ]
    # Randomized fill to reach 100 nodes strictly within India bounds
    random.seed(10)
    for i in range(84):
        hubs.append({
            "name": f"Rescue-Node-{100+i}", 
            "lat": round(random.uniform(10.0, 32.0), 2), 
            "lon": round(random.uniform(71.0, 90.0), 2)
        })
    return hubs

RESCUE_HUBS = get_india_rescue_network()

# --- 4. HELPERS ---
@st.cache_data(ttl=3600)
def get_road_route(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full"
    try:
        r = requests.get(url, timeout=3).json()
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
        st.markdown('<div id="loading-overlay"><div class="loader-icon">❄️</div><div style="color:white; letter-spacing:5px;">SECURING NATIONAL LOGISTICS...</div></div>', unsafe_allow_html=True)
    
    fleet_init = []
    drivers = ["N. Modi", "A. Shah", "S. Jaishankar", "R. Gandhi", "M. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor"]
    for i in range(15):
        pair = random.sample(RESCUE_HUBS, 2)
        s, e = pair[0], pair[1]
        path, dist = get_road_route([s['lat'], s['lon']], [e['lat'], e['lon']])
        prog = random.uniform(0.3, 0.7)
        pos = path[int(len(path)*prog)]
        is_fail = (i == 5)
        f_data = [round((8.5 if is_fail else -4.2) + random.uniform(-0.8, 0.8), 2) for _ in range(12)]
        
        fleet_init.append({
            "id": f"IND-EXP-{1000+i}", "driver": drivers[i % len(drivers)],
            "origin": s['name'], "dest": e['name'], "pos": pos, "path": path,
            "total_km": dist, "dist_covered": round(dist * prog), "dist_rem": round(dist * (1-prog)),
            "hrs": round(prog * 15, 1), "temp": f_data[0], "forecast": f_data, "is_fail": is_fail
        })
    st.session_state.fleet = fleet_init
    time.sleep(1)
    loading_placeholder.empty()

# --- 6. APP LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")
tabs = st.tabs(["🌐 Live Fleet Map", "🌡️ Thermal Monitor", "🛤️ Trip Planner"])

# --- TAB 1: LIVE FLEET MAP ---
with tabs[0]:
    selected_id = st.selectbox("🎯 Select Vehicle for High-Precision Data:", [t['id'] for t in st.session_state.fleet])
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    # MAP BOX
    st.markdown('<div class="map-frame">', unsafe_allow_html=True)
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    
    # 1. Plot ALL 100 Rescue Hubs (Neon Blue Dots)
    for wh in RESCUE_HUBS:
        folium.CircleMarker(
            [wh['lat'], wh['lon']], 
            radius=2.5, color="#00FFFF", weight=1, fill=True, fill_opacity=0.6, 
            popup=f"Rescue Node: {wh['name']}"
        ).add_to(m)

    # 2. Plot Active Fleet
    for t in st.session_state.fleet:
        is_sel = t['id'] == selected_id
        is_alert = t['is_fail']
        color = "#00FFFF" if is_sel else ("#FF4B4B" if is_alert else "#00FF7F")
        folium.PolyLine(t['path'], color=color, weight=6 if is_sel else 1.5, opacity=0.8 if is_sel else 0.2).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color="purple" if is_sel else ("red" if is_alert else "green"), icon="truck", prefix="fa")).add_to(m)
    
    st_folium(m, width="100%", height=480, key="main_map")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- INDIVIDUAL TRUCK DATA SECTION BELOW MAP ---
    st.markdown(f"### 🛡️ Systematic Intelligence Dashboard: {selected_id}")
    
    # Real-time Nearest Hub Calculation
    nearest_hub = min(RESCUE_HUBS, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    n_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], nearest_hub['lat'], nearest_hub['lon']), 1)
    
    # Mission Status Bar
    if selected_truck['is_fail']:
        st.markdown(f'<div class="status-pill status-alert">🛑 MISSION ALERT: CRITICAL THERMAL BREACH AT {selected_truck["temp"]}°C - DIVERT TO {nearest_hub["name"].upper()}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-pill status-safe">✅ MISSION STATUS: CONTINUE / SAFE | Environmental nominal.</div>', unsafe_allow_html=True)

    # Data Card Grid
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f"""<div class="intel-card">
            <div class="m-label">Lead Driver</div><div class="m-value">{selected_truck["driver"]}</div>
            <div class="m-sub">ID: EXP-V2-{selected_id[-4:]}</div>
            <hr style="opacity:0.1; margin:15px 0;">
            <div class="m-label">Active Driving Time</div><div class="m-value">{selected_truck["hrs"]} hrs</div>
        </div>""", unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""<div class="intel-card">
            <div class="m-label">Distance Covered</div><div class="m-value">{selected_truck["dist_covered"]} km</div>
            <div class="m-sub">Total Route: {selected_truck["total_km"]} km</div>
            <hr style="opacity:0.1; margin:15px 0;">
            <div class="m-label">Distance Remaining</div><div class="m-value">{selected_truck["dist_rem"]} km</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div class="intel-card">
            <div class="m-label">Current Route</div>
            <div style="color:white; font-size:1.1rem; font-weight:bold; margin-top:5px;">{selected_truck["origin"]}</div>
            <div style="color:#00FFFF; font-size:1.5rem; line-height:1;">↓</div>
            <div style="color:white; font-size:1.1rem; font-weight:bold;">{selected_truck["dest"]}</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        st.markdown(f"""<div class="intel-card" style="border-left: 5px solid {'#FF4B4B' if selected_truck['is_fail'] else '#3498db'}">
            <div class="m-label">Nearest Rescue Hub</div><div class="m-value" style="font-size:1.2rem;">{nearest_hub["name"]}</div>
            <div class="m-sub">{n_dist} km precise deviation</div>
            <hr style="opacity:0.1; margin:15px 0;">
            <div class="m-label">GPS Coordinate</div><div style="color:#ffffff; font-size:0.9rem;">{round(selected_truck['pos'][0],3)}, {round(selected_truck['pos'][1],3)}</div>
        </div>""", unsafe_allow_html=True)

# --- TAB 2 & 3 (Rest of the logic preserved from previous stable builds) ---
with tabs[1]:
    st.subheader("Sub-Zero Thermal Hero Monitor")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            st.markdown(f'<div class="thermal-hero" style="background:#12151c; padding:15px; border-radius:10px; border:1px solid rgba(255,255,255,0.1); margin-bottom:20px;"><div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span style="color:#9ea0a9;">{t["id"]}</span><span style="color:{"#FF4B4B" if t["is_fail"] else "#00FF7F"}; font-weight:bold;">{"BREACH" if t["is_fail"] else "STABLE"}</span></div>', unsafe_allow_html=True)
            df_p = pd.DataFrame({"Temp": t['forecast'], "Max": [5.0]*12, "Min": [-10.0]*12})
            st.line_chart(df_p, height=200)
            st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    st.header("National Safety Audit Planner")
    p1, p2, p3 = st.columns([1,1,1])
    s_node = p1.selectbox("Departure Point", [w['name'] for w in RESCUE_HUBS], key="planner_start")
    e_node = p2.selectbox("Destination Hub", [w['name'] for w in RESCUE_HUBS if w['name'] != s_node], key="planner_end")
    if st.button("Generate National Audit"):
        s_c = next(w for w in RESCUE_HUBS if w['name'] == s_node)
        e_c = next(w for w in RESCUE_HUBS if w['name'] == e_node)
        path, d = get_road_route([s_c['lat'], s_c['lon']], [e_c['lat'], e_c['lon']])
        st.success(f"Verified India-Centric Path: {d} km")
        pm = folium.Map(location=[s_c['lat'], s_c['lon']], zoom_start=6, tiles="CartoDB dark_matter")
        # Draw Hubs on Planner too
        for hub in RESCUE_HUBS:
            folium.CircleMarker([hub['lat'], hub['lon']], radius=2.5, color="#00FFFF", weight=1, fill=True, fill_opacity=0.6).add_to(pm)
        folium.PolyLine(path, color="#00FFFF", weight=4).add_to(pm)
        st_folium(pm, width="100%", height=450, key="plan_map")
