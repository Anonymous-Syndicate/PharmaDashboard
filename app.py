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
    #loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: #0b0d12; display: flex; flex-direction: column;
        justify-content: center; align-items: center; z-index: 9999;
    }
    .loader-icon { font-size: 80px; animation: pulse 1.5s infinite; color: #00FFFF; }
    @keyframes pulse { 0% { transform: scale(1); opacity: 0.5; } 50% { transform: scale(1.1); opacity: 1; } 100% { transform: scale(1); opacity: 0.5; } }
    .map-frame { border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 15px; background: rgba(17, 19, 26, 0.9); padding: 12px; margin-bottom: 25px; }
    .intel-card { background: rgba(30, 33, 48, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 20px; min-height: 180px; }
    .m-label { color: #808495; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; }
    .m-value { color: #ffffff; font-size: 1.4rem; font-weight: bold; margin-top: 5px; }
    .status-pill { padding: 10px 18px; border-radius: 8px; font-size: 0.9rem; font-weight: bold; display: block; margin-bottom: 20px; border-left: 6px solid; }
    .status-safe { background: rgba(0, 255, 127, 0.1); color: #00FF7F; border-color: #00FF7F; }
    .status-alert { background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border-color: #FF4B4B; animation: blink 1.5s infinite; }
    .thermal-hero { background: #12151c; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 15px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 100 REAL INDIAN INLAND CITIES (ON-LAND ONLY) ---
@st.cache_data
def get_india_inland_network():
    # Curated list of 100 inland cities across India (Strictly on land)
    hubs = [
        {"name": "Delhi-NCR", "lat": 28.6139, "lon": 77.2090}, {"name": "Ludhiana", "lat": 30.9010, "lon": 75.8573},
        {"name": "Ambala", "lat": 30.3782, "lon": 76.7767}, {"name": "Rohtak", "lat": 28.8955, "lon": 76.6066},
        {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873}, {"name": "Ajmer", "lat": 26.4499, "lon": 74.6399},
        {"name": "Udaipur", "lat": 24.5854, "lon": 73.7125}, {"name": "Indore", "lat": 22.7196, "lon": 75.8577},
        {"name": "Bhopal", "lat": 23.2599, "lon": 77.4126}, {"name": "Nagpur", "lat": 21.1458, "lon": 79.0882},
        {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867}, {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
        {"name": "Nashik", "lat": 19.9975, "lon": 73.7898}, {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
        {"name": "Vadodara", "lat": 22.3072, "lon": 73.1812}, {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462},
        {"name": "Kanpur", "lat": 26.4499, "lon": 80.3319}, {"name": "Agra", "lat": 27.1767, "lon": 78.0081},
        {"name": "Varanasi", "lat": 25.3176, "lon": 82.9739}, {"name": "Allahabad", "lat": 25.4358, "lon": 81.8463},
        {"name": "Patna", "lat": 25.5941, "lon": 85.1376}, {"name": "Gaya", "lat": 24.7914, "lon": 85.0002},
        {"name": "Ranchi", "lat": 23.3441, "lon": 85.3094}, {"name": "Jamshedpur", "lat": 22.8046, "lon": 86.2029},
        {"name": "Raipur", "lat": 21.2514, "lon": 81.6296}, {"name": "Bilaspur", "lat": 22.0797, "lon": 82.1391},
        {"name": "Jabalpur", "lat": 23.1815, "lon": 79.9864}, {"name": "Gwalior", "lat": 26.2183, "lon": 78.1828},
        {"name": "Jhansi", "lat": 25.4484, "lon": 78.5685}, {"name": "Aurangabad", "lat": 19.8762, "lon": 75.3433},
        {"name": "Solapur", "lat": 17.6599, "lon": 75.9064}, {"name": "Hubli", "lat": 15.3647, "lon": 75.1240},
        {"name": "Belgaum", "lat": 15.8497, "lon": 74.4977}, {"name": "Dharwad", "lat": 15.4589, "lon": 75.0078},
        {"name": "Mysore", "lat": 12.2958, "lon": 76.6394}, {"name": "Salem", "lat": 11.6643, "lon": 78.1460},
        {"name": "Coimbatore", "lat": 11.0168, "lon": 76.9558}, {"name": "Madurai", "lat": 9.9252, "lon": 78.1198},
        {"name": "Tirupati", "lat": 13.6285, "lon": 79.4192}, {"name": "Kurnool", "lat": 15.8281, "lon": 78.0373},
        {"name": "Warangal", "lat": 17.9689, "lon": 79.5941}, {"name": "Gulbarga", "lat": 17.3297, "lon": 76.8343},
        {"name": "Akola", "lat": 20.7002, "lon": 77.0082}, {"name": "Amaravati", "lat": 20.9320, "lon": 77.7523},
        {"name": "Jalgaon", "lat": 21.0077, "lon": 75.5626}, {"name": "Latur", "lat": 18.4088, "lon": 76.5604},
        {"name": "Mathura", "lat": 27.4924, "lon": 77.6737}, {"name": "Meerut", "lat": 28.9845, "lon": 77.7064},
        {"name": "Bareilly", "lat": 28.3670, "lon": 79.4304}, {"name": "Aligarh", "lat": 27.8813, "lon": 78.0882},
        {"name": "Muzaffarnagar", "lat": 29.4727, "lon": 77.7085}, {"name": "Saharanpur", "lat": 29.9680, "lon": 77.5552},
        {"name": "Moradabad", "lat": 28.8385, "lon": 78.7733}, {"name": "Firozabad", "lat": 27.1504, "lon": 78.3958},
        {"name": "Etawah", "lat": 26.7776, "lon": 79.0300}, {"name": "Bikaner", "lat": 28.0229, "lon": 73.3119},
        {"name": "Jodhpur", "lat": 26.2389, "lon": 73.0243}, {"name": "Kota", "lat": 25.2138, "lon": 75.8648},
        {"name": "Bhilwara", "lat": 25.3407, "lon": 74.6313}, {"name": "Sagar", "lat": 23.8388, "lon": 78.7378},
        {"name": "Rewa", "lat": 24.5362, "lon": 81.3037}, {"name": "Satna", "lat": 24.6000, "lon": 80.8300},
        {"name": "Katni", "lat": 23.8354, "lon": 80.3944}, {"name": "Singrauli", "lat": 24.1992, "lon": 82.6645},
        {"name": "Ratlam", "lat": 23.3315, "lon": 75.0367}, {"name": "Ujjain", "lat": 23.1760, "lon": 75.7885},
        {"name": "Khandwa", "lat": 21.8284, "lon": 76.3564}, {"name": "Burhanpur", "lat": 21.3121, "lon": 76.2272},
        {"name": "Dewas", "lat": 22.9624, "lon": 76.0507}, {"name": "Korba", "lat": 22.3511, "lon": 82.6839},
        {"name": "Durg", "lat": 21.1904, "lon": 81.2849}, {"name": "Rajandgaon", "lat": 21.0963, "lon": 81.0351},
        {"name": "Sambalpur", "lat": 21.4669, "lon": 83.9812}, {"name": "Rourkela", "lat": 22.2604, "lon": 84.8536},
        {"name": "Berhampur", "lat": 19.3150, "lon": 84.7941}, {"name": "Kurnool", "lat": 15.8281, "lon": 78.0373},
        {"name": "Anantapur", "lat": 14.6819, "lon": 77.6006}, {"name": "Nellore", "lat": 14.4426, "lon": 79.9865},
        {"name": "Chittoor", "lat": 13.2172, "lon": 79.1003}, {"name": "Guntur", "lat": 16.3067, "lon": 80.4365},
        {"name": "Bellary", "lat": 15.1394, "lon": 76.9214}, {"name": "Tumkur", "lat": 13.3392, "lon": 77.1140},
        {"name": "Shimoga", "lat": 13.9299, "lon": 75.5681}, {"name": "Hassan", "lat": 13.0070, "lon": 76.1029},
        {"name": "Davanagere", "lat": 14.4644, "lon": 75.9218}, {"name": "Gulbarga", "lat": 17.3297, "lon": 76.8343},
        {"name": "Bidar", "lat": 17.9120, "lon": 77.5188}, {"name": "Raichur", "lat": 16.2120, "lon": 77.3556},
        {"name": "Nizamabad", "lat": 18.6725, "lon": 78.0941}, {"name": "Karimnagar", "lat": 18.4386, "lon": 79.1288},
        {"name": "Ramagundam", "lat": 18.7580, "lon": 79.5147}, {"name": "Khammam", "lat": 17.2473, "lon": 80.1514},
        {"name": "Muzaffarpur", "lat": 26.1209, "lon": 85.3647}, {"name": "Bhagalpur", "lat": 25.2425, "lon": 86.9718},
        {"name": "Darbhanga", "lat": 26.1542, "lon": 85.8918}, {"name": "Arrah", "lat": 25.5564, "lon": 84.6603},
        {"name": "Begusarai", "lat": 25.4182, "lon": 86.1272}, {"name": "Katihar", "lat": 25.5501, "lon": 87.5721},
        {"name": "Munger", "lat": 25.3748, "lon": 86.4735}, {"name": "Dehradun", "lat": 30.3165, "lon": 78.0322},
        {"name": "Haridwar", "lat": 29.9457, "lon": 78.1642}, {"name": "Haldwani", "lat": 29.2183, "lon": 79.5130}
    ]
    return hubs

RESCUE_HUBS = get_india_inland_network()

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
    st.markdown('<div id="loading-overlay"><div class="loader-icon">❄️</div><div style="color:white; letter-spacing:5px;">SECURING PHARMA CORRIDORS...</div></div>', unsafe_allow_html=True)

if 'fleet' not in st.session_state:
    fleet_init = []
    # Major Pharma Hubs as Origins
    pharma_clusters = ["Delhi-NCR", "Ludhiana", "Ahmedabad", "Pune", "Hyderabad", "Bhopal", "Varanasi", "Dehradun"]
    drivers = ["N. Modi", "A. Shah", "S. Jaishankar", "R. Gandhi", "M. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor"]
    
    for i in range(15):
        start_node_name = pharma_clusters[i % len(pharma_clusters)]
        start_node = next(h for h in RESCUE_HUBS if h['name'] == start_node_name)
        end_node = random.choice(RESCUE_HUBS)
        while end_node['name'] == start_node['name']: end_node = random.choice(RESCUE_HUBS)
        
        path, dist = get_road_route([start_node['lat'], start_node['lon']], [end_node['lat'], end_node['lon']])
        prog = random.uniform(0.3, 0.7)
        pos = path[int(len(path)*prog)]
        is_fail = (i == 5) # IND-EXP-1005 is always the failure scenario
        f_data = [round((8.5 if is_fail else -4.2) + random.uniform(-0.8, 0.8), 2) for _ in range(12)]
        
        fleet_init.append({
            "id": f"IND-EXP-{1000+i}", "driver": drivers[i % len(drivers)],
            "origin": start_node['name'], "dest": end_node['name'], "pos": pos, "path": path,
            "total_km": dist, "dist_covered": round(dist * prog), "dist_rem": round(dist * (1-prog)),
            "hrs": round(prog * 15, 1), "temp": f_data[0], "forecast": f_data, "is_fail": is_fail
        })
    st.session_state.fleet = fleet_init

if 'planner_state' not in st.session_state:
    st.session_state.planner_state = None

time.sleep(1)
loading_placeholder.empty()

# --- 6. APP LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")
tabs = st.tabs(["🌐 Live Fleet Map", "🌡️ Thermal Monitor", "🛤️ Trip Planner"])

# --- TAB 1: LIVE FLEET MAP ---
with tabs[0]:
    selected_id = st.selectbox("🎯 Select Vehicle for High-Precision Data:", [t['id'] for t in st.session_state.fleet])
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    st.markdown('<div class="map-frame">', unsafe_allow_html=True)
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    draw_rescue_nodes(m)
    for t in st.session_state.fleet:
        is_sel = t['id'] == selected_id
        color = "#00FFFF" if is_sel else ("#FF4B4B" if t['is_fail'] else "#00FF7F")
        folium.PolyLine(t['path'], color=color, weight=6 if is_sel else 1.5, opacity=0.8 if is_sel else 0.2).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color="purple" if is_sel else ("red" if t['is_fail'] else "green"), icon="truck", prefix="fa")).add_to(m)
    st_folium(m, width="100%", height=480, key="main_map")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"### 🛡️ System Intelligence: {selected_id}")
    n_hub = min(RESCUE_HUBS, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    n_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], n_hub['lat'], n_hub['lon']), 1)
    
    if selected_truck['is_fail']:
        st.markdown(f'<div class="status-pill status-alert">🛑 MISSION ALERT: THERMAL BREACH AT {selected_truck["temp"]}°C - DIVERT TO {n_hub["name"].upper()}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-pill status-safe">✅ MISSION STATUS: CONTINUE / SAFE | Environment Nominal.</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="intel-card"><div class="m-label">Driver</div><div class="m-value">{selected_truck["driver"]}</div><div style="color:#00FFFF; margin-top:10px;">Active {selected_truck["hrs"]} hrs</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="intel-card"><div class="m-label">Live Temp</div><div class="m-value" style="color:{"#FF4B4B" if selected_truck["is_fail"] else "#00FF7F"}">{selected_truck["temp"]}°C</div><div style="color:#9ea0a9; margin-top:10px;">Range: -10 to 5°C</div></div>', unsafe_allow_html=True)
    with c3:
        eta_arrival = (datetime.now() + timedelta(hours=selected_truck['dist_rem']/45)).strftime("%H:%M")
        st.markdown(f'<div class="intel-card"><div class="m-label">Trip Progress</div><div class="m-value">{selected_truck["dist_covered"]} km</div><div style="color:#00FFFF; margin-top:10px;">Remaining: {selected_truck["dist_rem"]} km</div><div style="color:#9ea0a9; font-size:0.8rem;">ETA: {eta_arrival}</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="intel-card" style="border-left: 4px solid {"#FF4B4B" if selected_truck["is_fail"] else "#3498db"}"><div class="m-label">Nearest Hub</div><div class="m-value" style="font-size:1.2rem;">{n_hub["name"]}</div><div style="color:#00FFFF; margin-top:10px;">{n_dist} km deviation</div></div>', unsafe_allow_html=True)
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

# --- TAB 3: TRIP PLANNER ---
with tabs[2]:
    st.header("National Safety Audit Planner")
    p1, p2, p3 = st.columns([1,1,1])
    s_node = p1.selectbox("Departure Hub", [w['name'] for w in RESCUE_HUBS], key="planner_start")
    e_node = p2.selectbox("Destination Node", [w['name'] for w in RESCUE_HUBS if w['name'] != s_node], key="planner_end")
    radius_audit = p3.slider("Audit Search Radius (km)", 20, 150, 60, key="audit_radius")
    
    if st.button("Generate National Audit"):
        s_c = next(w for w in RESCUE_HUBS if w['name'] == s_node)
        e_c = next(w for w in RESCUE_HUBS if w['name'] == e_node)
        path, d = get_road_route([s_c['lat'], s_c['lon']], [e_c['lat'], e_c['lon']])
        
        rescues_found = []
        for wh in RESCUE_HUBS:
            # Min distance to any point on the route polyline
            dist_to_path = min([haversine(wh['lat'], wh['lon'], pt[0], pt[1]) for pt in path[::20]])
            if dist_to_path <= radius_audit:
                rescues_found.append({"Hub Name": wh['name'], "Deviation (km)": round(dist_to_path, 1), "lat": wh['lat'], "lon": wh['lon']})
        
        st.session_state.planner_state = {
            "path": path, "dist": d, "start": s_node, "end": e_node, 
            "coords": [s_c['lat'], s_c['lon']], "rescues": rescues_found, "radius": radius_audit
        }

    if st.session_state.planner_state:
        ps = st.session_state.planner_state
        d1, d2, d3 = st.columns(3)
        with d1: st.markdown(f'<div class="intel-card"><div class="m-label">Verified Distance</div><div class="m-value">{ps["dist"]} km</div><div class="card-sub">Road Network Map</div></div>', unsafe_allow_html=True)
        with d2:
            est_time = round(ps["dist"]/45, 1)
            st.markdown(f'<div class="intel-card"><div class="m-label">Est. Transit Time</div><div class="m-value">{est_time} hrs</div><div class="card-sub">Logistics Avg: 45 km/h</div></div>', unsafe_allow_html=True)
        with d3: st.markdown(f'<div class="intel-card"><div class="m-label">Rescue Coverage</div><div class="m-value">{len(ps["rescues"])} Hubs</div><div class="card-sub">Within {ps["radius"]}km Buffer</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="map-frame">', unsafe_allow_html=True)
        pm = folium.Map(location=ps['coords'], zoom_start=6, tiles="CartoDB dark_matter")
        draw_rescue_nodes(pm)
        folium.PolyLine(ps['path'], color="#00FFFF", weight=5).add_to(pm)
        for rh in ps["rescues"]:
            folium.Marker([rh['lat'], rh['lon']], icon=folium.Icon(color="orange", icon="shield-heart", prefix="fa"), popup=f"{rh['Hub Name']}").add_to(pm)
        st_folium(pm, width="100%", height=450, key="plan_map")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # New Feature: Rescue Hub List Table
        if ps["rescues"]:
            st.write("### 📋 Safety Audit: Available Rescue Infrastructure")
            audit_df = pd.DataFrame(ps["rescues"])[["Hub Name", "Deviation (km)"]].sort_values(by="Deviation (km)")
            st.dataframe(audit_df, use_container_width=True, hide_index=True)
