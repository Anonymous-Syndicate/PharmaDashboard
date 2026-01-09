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
    
    /* Full-Screen Center Loading */
    #loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: #0b0d12; display: flex; flex-direction: column;
        justify-content: center; align-items: center; z-index: 9999;
    }
    .loader-icon { font-size: 80px; animation: pulse 1.5s infinite; color: #00FFFF; }
    @keyframes pulse { 0% { transform: scale(1); opacity: 0.5; } 50% { transform: scale(1.1); opacity: 1; } 100% { transform: scale(1); opacity: 0.5; } }

    /* Modern Boxed Map */
    .map-frame {
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 15px; background: rgba(17, 19, 26, 0.9);
        padding: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.8); margin-bottom: 25px;
    }

    /* Intelligence Dashboard Cards */
    .intel-card {
        background: rgba(30, 33, 48, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px; padding: 20px; min-height: 180px;
    }
    .m-label { color: #808495; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; }
    .m-value { color: #ffffff; font-size: 1.4rem; font-weight: bold; margin-top: 5px; }
    
    .status-pill {
        padding: 10px 18px; border-radius: 8px; font-size: 0.9rem; font-weight: bold;
        display: block; margin-bottom: 20px; border-left: 6px solid;
    }
    .status-safe { background: rgba(0, 255, 127, 0.1); color: #00FF7F; border-color: #00FF7F; }
    .status-alert { background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border-color: #FF4B4B; animation: blink 1.5s infinite; }
    
    .thermal-hero {
        background: #12151c; border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px; padding: 15px; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATASETS (STABLE RESCUE HUBS) ---
@st.cache_data
def get_india_rescue_network():
    # DO NOT CHANGE THESE LOCATIONS
    hubs = [
        {"name": "Delhi-Vault", "lat": 28.6139, "lon": 77.2090}, {"name": "Mumbai-Apex", "lat": 19.0760, "lon": 72.8777},
        {"name": "Bangalore-Chill", "lat": 12.9716, "lon": 77.5946}, {"name": "Chennai-Hub", "lat": 13.0827, "lon": 80.2707},
        {"name": "Kolkata-Safe", "lat": 22.5726, "lon": 88.3639}, {"name": "Hyderabad-Vault", "lat": 17.3850, "lon": 78.4867},
        {"name": "Ahmedabad-Bio", "lat": 23.0225, "lon": 72.5714}, {"name": "Pune-Rescue", "lat": 18.5204, "lon": 73.8567},
        {"name": "Lucknow-Safe", "lat": 26.8467, "lon": 80.9462}, {"name": "Nagpur-Central", "lat": 21.1458, "lon": 79.0882},
        {"name": "Jaipur-Vault", "lat": 26.9124, "lon": 75.7873}, {"name": "Patna-Cold", "lat": 25.5941, "lon": 85.1376}
    ]
    random.seed(10) # Keeping seed identical to maintain locations
    for i in range(88):
        hubs.append({"name": f"Rescue-Node-{100+i}", "lat": round(random.uniform(9.0, 33.0), 2), "lon": round(random.uniform(70.0, 92.0), 2)})
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

def draw_rescue_nodes(map_obj):
    for hub in RESCUE_HUBS:
        folium.CircleMarker(
            [hub['lat'], hub['lon']], radius=2.5, color="#00FFFF", 
            weight=1, fill=True, fill_opacity=0.6, popup=hub['name']
        ).add_to(map_obj)

# --- 5. INITIALIZATION ---
loading_placeholder = st.empty()
with loading_placeholder:
    st.markdown('<div id="loading-overlay"><div class="loader-icon">❄️</div><div style="color:white; letter-spacing:5px;">SECURING NATIONAL LOGISTICS...</div></div>', unsafe_allow_html=True)

if 'fleet' not in st.session_state:
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

if 'planner_results' not in st.session_state:
    st.session_state.planner_results = None

time.sleep(0.8)
loading_placeholder.empty()

# --- 6. APP LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")
tabs = st.tabs(["🌐 Live Fleet Map", "🌡️ Thermal hero Monitor", "🛤️ Trip Planner"])

# --- TAB 1: LIVE MAP ---
with tabs[0]:
    selected_id = st.selectbox("🎯 Select Vehicle for Live Analysis:", [t['id'] for t in st.session_state.fleet])
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    st.markdown('<div class="map-frame">', unsafe_allow_html=True)
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    folium.LatLngPopup().add_to(m)
    draw_rescue_nodes(m)

    for t in st.session_state.fleet:
        is_sel = t['id'] == selected_id
        color = "#00FFFF" if is_sel else ("#FF4B4B" if t['is_fail'] else "#00FF7F")
        folium.PolyLine(t['path'], color=color, weight=6 if is_sel else 1.5, opacity=0.8 if is_sel else 0.2).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color="purple" if is_sel else ("red" if t['is_fail'] else "green"), icon="truck", prefix="fa")).add_to(m)
    st_folium(m, width="100%", height=480, key="main_map")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- SYSTEMATIC INTELLIGENCE DASHBOARD ---
    st.markdown(f"### 🛡️ System Intelligence: {selected_id}")
    n_hub = min(RESCUE_HUBS, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    n_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], n_hub['lat'], n_hub['lon']), 1)
    
    if selected_truck['is_fail']:
        st.markdown(f'<div class="status-pill status-alert">🛑 MISSION ALERT: THERMAL BREACH AT {selected_truck["temp"]}°C - DIVERT TO {n_hub["name"].upper()}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-pill status-safe">✅ MISSION STATUS: CONTINUE / SAFE | Environment Nominal.</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="intel-card"><div class="m-label">Driver</div><div class="m-value">{selected_truck["driver"]}</div><div style="color:#00FFFF; margin-top:10px;">Active {selected_truck["hrs"]} hrs</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="intel-card"><div class="m-label">Live Temp</div><div class="m-value" style="color:{"#FF4B4B" if selected_truck["is_fail"] else "#00FF7F"}">{selected_truck["temp"]}°C</div><div style="color:#9ea0a9; margin-top:10px;">Safe Range: -10 to 5°C</div></div>', unsafe_allow_html=True)
    with c3:
        eta_arrival = (datetime.now() + timedelta(hours=selected_truck['dist_rem']/60)).strftime("%H:%M")
        st.markdown(f'<div class="intel-card"><div class="m-label">Trip Progress</div><div class="m-value">{selected_truck["dist_covered"]} km</div><div style="color:#00FFFF; margin-top:10px;">Remaining: {selected_truck["dist_rem"]} km</div><div style="color:#9ea0a9; font-size:0.8rem;">ETA: {eta_arrival}</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="intel-card" style="border-left: 4px solid {"#FF4B4B" if selected_truck["is_fail"] else "#3498db"}"><div class="m-label">Nearest Hub</div><div class="m-value" style="font-size:1.2rem;">{n_hub["name"]}</div><div style="color:#00FFFF; margin-top:10px;">{n_dist} km precisely off-route</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div style="background:rgba(30,33,48,0.5); padding:15px; border-radius:8px; border:1px solid rgba(255,255,255,0.05); margin-top:10px;">🛣️ <b>Active Corridor:</b> {selected_truck["origin"]} ———▶ {selected_truck["dest"]} (Total: {selected_truck["total_km"]} km)</div>', unsafe_allow_html=True)

# --- TAB 2: THERMAL HERO ---
with tabs[1]:
    st.subheader("Sub-Zero Thermal Hero Monitor")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            st.markdown(f'<div class="thermal-hero"><div style="display:flex; justify-content:space-between; margin-bottom:10px;"><span style="color:#9ea0a9;">{t["id"]}</span><span style="color:{"#FF4B4B" if t["is_fail"] else "#00FF7F"}; font-weight:bold;">{"BREACH" if t["is_fail"] else "STABLE"}</span></div>', unsafe_allow_html=True)
            df_p = pd.DataFrame({"Temp": t['forecast'], "Max": [5.0]*12, "Min": [-10.0]*12})
            st.line_chart(df_p, height=200)
            st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: TRIP PLANNER (PERSISTENCE FIXED) ---
with tabs[2]:
    st.header("National Safety Audit Planner")
    p1, p2, p3 = st.columns([1,1,1])
    s_node = p1.selectbox("Departure Point", [w['name'] for w in RESCUE_HUBS], key="planner_start")
    e_node = p2.selectbox("Destination Hub", [w['name'] for w in RESCUE_HUBS if w['name'] != s_node], key="planner_end")
    radius_audit = p3.slider("Search Buffer (km)", 20, 150, 60, key="audit_radius")
    
    if st.button("Generate National Audit"):
        s_c = next(w for w in RESCUE_HUBS if w['name'] == s_node)
        e_c = next(w for w in RESCUE_HUBS if w['name'] == e_node)
        path, d = get_road_route([s_c['lat'], s_c['lon']], [e_c['lat'], e_c['lon']])
        
        # Scan corridor for hubs
        rescues_found = []
        for wh in RESCUE_HUBS:
            # Min distance to any point on the route polyline
            dist_to_path = min([haversine(wh['lat'], wh['lon'], pt[0], pt[1]) for pt in path[::20]])
            if dist_to_path <= radius_audit:
                rescues_found.append({"Hub Name": wh['name'], "Deviation (km)": round(dist_to_path, 1), "lat": wh['lat'], "lon": wh['lon']})
        
        # Persistence: Store results in session_state
        st.session_state.planner_results = {
            "path": path, "dist": d, "start": s_node, "end": e_node, 
            "coords": [s_c['lat'], s_c['lon']], "rescues": rescues_found
        }

    # Render results if they exist in session state
    if st.session_state.planner_results:
        res = st.session_state.planner_results
        
        # Display Audit Data Cards
        d1, d2, d3 = st.columns(3)
        with d1: st.markdown(f'<div class="intel-card"><div class="m-label">Total Road Distance</div><div class="m-value">{res["dist"]} km</div><div class="card-sub">Verified Highway Geometry</div></div>', unsafe_allow_html=True)
        with d2:
            est_time = round(res["dist"]/45, 1) # Avg speed for reefer logistics
            st.markdown(f'<div class="intel-card"><div class="m-label">Estimated Transit Time</div><div class="m-value">{est_time} hrs</div><div class="card-sub">At Avg Speed: 45 km/h</div></div>', unsafe_allow_html=True)
        with d3: st.markdown(f'<div class="intel-card"><div class="m-label">Safety Network Density</div><div class="m-value">{len(res["rescues"])} Hubs</div><div class="card-sub">Available in {radius_audit}km corridor</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="map-frame">', unsafe_allow_html=True)
        pm = folium.Map(location=res['coords'], zoom_start=6, tiles="CartoDB dark_matter")
        draw_rescue_nodes(pm) # Draw ALL hubs for scale
        folium.PolyLine(res['path'], color="#00FFFF", weight=5).add_to(pm)
        # Highlight specific hubs along the route in Orange
        for rh in res["rescues"]:
            folium.Marker([rh['lat'], rh['lon']], icon=folium.Icon(color="orange", icon="shield-heart", prefix="fa"), popup=f"{rh['Hub Name']}").add_to(pm)
        st_folium(pm, width="100%", height=450, key="plan_map")
        st.markdown('</div>', unsafe_allow_html=True)
