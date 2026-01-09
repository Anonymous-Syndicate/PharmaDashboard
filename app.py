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

# --- 2. GLOBAL UI STYLING (MODERN COMMAND CENTER) ---
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

    .map-frame {
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 15px; background: rgba(17, 19, 26, 0.9);
        padding: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.8); margin-bottom: 25px;
    }

    .intel-card {
        background: rgba(30, 33, 48, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px; padding: 20px; min-height: 180px;
    }
    .m-label { color: #808495; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; }
    .m-value { color: #ffffff; font-size: 1.4rem; font-weight: bold; }
    
    .status-pill {
        padding: 10px 18px; border-radius: 8px; font-size: 0.9rem; font-weight: bold;
        display: block; margin-bottom: 20px; border-left: 6px solid;
    }
    .status-safe { background: rgba(0, 255, 127, 0.1); color: #00FF7F; border-color: #00FF7F; }
    .status-alert { background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border-color: #FF4B4B; animation: blink 1.5s infinite; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 100 REAL INDIAN CITIES (RESCUE HUBS) ---
@st.cache_data
def get_india_hubs():
    return [
        {"name": "Delhi-NCR Vault", "lat": 28.6139, "lon": 77.2090}, {"name": "Mumbai-Apex", "lat": 19.0760, "lon": 72.8777},
        {"name": "Bangalore-Chill", "lat": 12.9716, "lon": 77.5946}, {"name": "Chennai-Port", "lat": 13.0827, "lon": 80.2707},
        {"name": "Kolkata-Hub", "lat": 22.5726, "lon": 88.3639}, {"name": "Hyderabad-Vault", "lat": 17.3850, "lon": 78.4867},
        {"name": "Ahmedabad-Bio", "lat": 23.0225, "lon": 72.5714}, {"name": "Pune-Rescue", "lat": 18.5204, "lon": 73.8567},
        {"name": "Lucknow-Safe", "lat": 26.8467, "lon": 80.9462}, {"name": "Nagpur-Central", "lat": 21.1458, "lon": 79.0882},
        {"name": "Jaipur-Vault", "lat": 26.9124, "lon": 75.7873}, {"name": "Patna-Cold", "lat": 25.5941, "lon": 85.1376},
        {"name": "Srinagar-Safe", "lat": 34.0837, "lon": 74.7973}, {"name": "Guwahati-Bio", "lat": 26.1445, "lon": 91.7362},
        {"name": "Chandigarh-Chill", "lat": 30.7333, "lon": 76.7794}, {"name": "Bhopal-Vault", "lat": 23.2599, "lon": 77.4126},
        {"name": "Indore-Safe", "lat": 22.7196, "lon": 75.8577}, {"name": "Vadodara-Chill", "lat": 22.3072, "lon": 73.1812},
        {"name": "Coimbatore-Apex", "lat": 11.0168, "lon": 76.9558}, {"name": "Ludhiana-Hub", "lat": 30.9010, "lon": 75.8573},
        {"name": "Agra-Vault", "lat": 27.1767, "lon": 78.0081}, {"name": "Nashik-Apex", "lat": 19.9975, "lon": 73.7898},
        {"name": "Ranchi-Safe", "lat": 23.3441, "lon": 85.3094}, {"name": "Meerut-Vault", "lat": 28.9845, "lon": 77.7064},
        {"name": "Rajkot-Safe", "lat": 22.3039, "lon": 70.8022}, {"name": "Varanasi-Bio", "lat": 25.3176, "lon": 82.9739},
        {"name": "Amritsar-Apex", "lat": 31.6340, "lon": 74.8723}, {"name": "Allahabad-Vault", "lat": 25.4358, "lon": 81.8463},
        {"name": "Visakhapatnam-Bio", "lat": 17.6868, "lon": 83.2185}, {"name": "Jabalpur-Hub", "lat": 23.1815, "lon": 79.9864},
        {"name": "Aurangabad-Vault", "lat": 19.8762, "lon": 75.3433}, {"name": "Solapur-Safe", "lat": 17.6599, "lon": 75.9064},
        {"name": "Sikkim-Cold", "lat": 27.3314, "lon": 88.6138}, {"name": "Leh-Vault", "lat": 34.1526, "lon": 77.5771},
        {"name": "Kochi-Port", "lat": 9.9312, "lon": 76.2673}, {"name": "Mysore-Chill", "lat": 12.2958, "lon": 76.6394},
        {"name": "Dehradun-Rescue", "lat": 30.3165, "lon": 78.0322}, {"name": "Salem-Apex", "lat": 11.6643, "lon": 78.1460},
        {"name": "Jodhpur-Dry", "lat": 26.2389, "lon": 73.0243}, {"name": "Gwalior-Vault", "lat": 26.2183, "lon": 78.1828},
        {"name": "Vijayawada-Hub", "lat": 16.5062, "lon": 80.6480}, {"name": "Madurai-Safe", "lat": 9.9252, "lon": 78.1198},
        {"name": "Raipur-Rescue", "lat": 21.2514, "lon": 81.6296}, {"name": "Bhubaneswar-Bio", "lat": 20.2961, "lon": 85.8245},
        {"name": "Hubli-Safe", "lat": 15.3647, "lon": 75.1240}, {"name": "Shimla-Cold", "lat": 31.1048, "lon": 77.1734},
        {"name": "Gaya-Vault", "lat": 24.7914, "lon": 85.0002}, {"name": "Udaipur-Chill", "lat": 24.5854, "lon": 73.7125},
        {"name": "Nellore-Port", "lat": 14.4426, "lon": 79.9865}, {"name": "Bhuj-Safe", "lat": 23.2420, "lon": 69.6669},
        # Adding more unique locations to reach 100
        {"name": "Kargil-Rescue", "lat": 34.5539, "lon": 76.1349}, {"name": "Anantapur-Vault", "lat": 14.6819, "lon": 77.6006},
        {"name": "Bilaspur-Bio", "lat": 22.0797, "lon": 82.1391}, {"name": "Muzaffarpur-Safe", "lat": 26.1209, "lon": 85.3647},
        {"name": "Agartala-Hub", "lat": 23.8315, "lon": 91.2868}, {"name": "Port Blair-Port", "lat": 11.6234, "lon": 92.7265},
        {"name": "Imphal-Cold", "lat": 24.8170, "lon": 93.9368}, {"name": "Shimoga-Safe", "lat": 13.9299, "lon": 75.5681},
        {"name": "Hampi-Vault", "lat": 15.3350, "lon": 76.4600}, {"name": "Kanyakumari-Node", "lat": 8.0883, "lon": 77.5385},
        {"name": "Mangalore-Safe", "lat": 12.9141, "lon": 74.8560}, {"name": "Ajmer-Chill", "lat": 26.4499, "lon": 74.6399},
        {"name": "Haridwar-Bio", "lat": 29.9457, "lon": 78.1642}, {"name": "Darbhanga-Vault", "lat": 26.1542, "lon": 85.8918},
        {"name": "Kurnool-Safe", "lat": 15.8281, "lon": 78.0373}, {"name": "Alwar-Hub", "lat": 27.5530, "lon": 76.6346},
        {"name": "Firozabad-Vault", "lat": 27.1504, "lon": 78.3958}, {"name": "Mathura-Chill", "lat": 27.4924, "lon": 77.6737},
        {"name": "Panipat-Safe", "lat": 29.3909, "lon": 76.9635}, {"name": "Aligarh-Hub", "lat": 27.8813, "lon": 78.0882},
        {"name": "Jhansi-Bio", "lat": 25.4484, "lon": 78.5685}, {"name": "Rourkela-Safe", "lat": 22.2604, "lon": 84.8536},
        {"name": "Bhilai-Vault", "lat": 21.1938, "lon": 81.3509}, {"name": "Tirupati-Rescue", "lat": 13.6285, "lon": 79.4192},
        {"name": "Warangal-Apex", "lat": 17.9689, "lon": 79.5941}, {"name": "Gulbarga-Chill", "lat": 17.3297, "lon": 76.8343},
        {"name": "Gandhinagar-Vault", "lat": 23.2156, "lon": 72.6369}, {"name": "Jamnagar-Safe", "lat": 22.4707, "lon": 70.0577},
        {"name": "Siliguri-Safe", "lat": 26.7271, "lon": 88.3953}, {"name": "Ujjain-Vault", "lat": 23.1760, "lon": 75.7885},
        {"name": "Ratlam-Hub", "lat": 23.3315, "lon": 75.0367}, {"name": "Bikaner-Cold", "lat": 28.0229, "lon": 73.3119},
        {"name": "Sagar-Safe", "lat": 23.8388, "lon": 78.7378}, {"name": "Korba-Vault", "lat": 22.3511, "lon": 82.6839},
        {"name": "Akola-Chill", "lat": 20.7002, "lon": 77.0082}, {"name": "Loni-Safe", "lat": 28.7314, "lon": 77.2845},
        {"name": "Muzaffarnagar-Hub", "lat": 29.4727, "lon": 77.7085}, {"name": "Bharatpur-Vault", "lat": 27.2152, "lon": 77.4936},
        {"name": "Etawah-Safe", "lat": 26.7776, "lon": 79.0300}, {"name": "Satna-Bio", "lat": 24.6000, "lon": 80.8300},
        {"name": "Durg-Chill", "lat": 21.1904, "lon": 81.2849}, {"name": "Purnia-Safe", "lat": 25.7771, "lon": 87.4753},
        {"name": "Guntur-Vault", "lat": 16.3067, "lon": 80.4365}, {"name": "Nanded-Safe", "lat": 19.1429, "lon": 77.3037},
        {"name": "Ichalkaranji-Hub", "lat": 16.7000, "lon": 74.4700}, {"name": "Pallavaram-Safe", "lat": 12.9675, "lon": 80.1491},
        {"name": "Noida-Bio", "lat": 28.5355, "lon": 77.3910}, {"name": "Karnal-Vault", "lat": 29.6857, "lon": 76.9907}
    ]

RESCUE_HUBS = get_india_hubs()

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
else:
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
    
    # RENDER 100 RESCUE NODES (Ensured layer)
    for wh in RESCUE_HUBS:
        folium.CircleMarker(
            [wh['lat'], wh['lon']], 
            radius=2.5, color="#00FFFF", weight=1, fill=True, fill_opacity=0.6, 
            popup=f"Rescue Node: {wh['name']}"
        ).add_to(m)

    # RENDER ACTIVE FLEET
    for t in st.session_state.fleet:
        is_sel = t['id'] == selected_id
        color = "#00FFFF" if is_sel else ("#FF4B4B" if t['is_fail'] else "#00FF7F")
        folium.PolyLine(t['path'], color=color, weight=6 if is_sel else 1.5, opacity=0.8 if is_sel else 0.2).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color="purple" if is_sel else ("red" if t['is_fail'] else "green"), icon="truck", prefix="fa")).add_to(m)
    
    st_folium(m, width="100%", height=480, key="main_map")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- SYSTEMATIC INTELLIGENCE DASHBOARD BELOW MAP ---
    st.markdown(f"### 🛡️ Intelligence Dashboard: {selected_id}")
    
    # Calc Nearest Hub for this truck
    nearest_hub = min(RESCUE_HUBS, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    n_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], nearest_hub['lat'], nearest_hub['lon']), 1)
    
    if selected_truck['is_fail']:
        st.markdown(f'<div class="status-pill status-alert">🛑 MISSION ALERT: THERMAL BREACH AT {selected_truck["temp"]}°C - DIVERT TO {nearest_hub["name"].upper()}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-pill status-safe">✅ MISSION STATUS: CONTINUE / SAFE | Environmental nominal.</div>', unsafe_allow_html=True)

    # Systematic Grid
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="intel-card">
            <div class="m-label">Lead Driver</div><div class="m-value">{selected_truck["driver"]}</div>
            <hr style="opacity:0.1; margin:15px 0;">
            <div class="m-label">Active Drive Time</div><div class="m-value">{selected_truck["hrs"]} hrs</div>
        </div>""", unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""<div class="intel-card">
            <div class="m-label">Distance Covered</div><div class="m-value">{selected_truck["dist_covered"]} km</div>
            <hr style="opacity:0.1; margin:15px 0;">
            <div class="m-label">Distance Remaining</div><div class="m-value">{selected_truck["dist_rem"]} km</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div class="intel-card">
            <div class="m-label">Current Route</div>
            <div style="color:white; font-size:1.1rem; font-weight:bold; margin-top:5px;">{selected_truck["origin"]}</div>
            <div style="color:#00FFFF; font-size:1.3rem; margin:2px 0;">↓</div>
            <div style="color:white; font-size:1.1rem; font-weight:bold;">{selected_truck["dest"]}</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        st.markdown(f"""<div class="intel-card" style="border-left: 4px solid {'#FF4B4B' if selected_truck['is_fail'] else '#3498db'}">
            <div class="m-label">Nearest Rescue Hub</div><div class="m-value" style="font-size:1.2rem;">{nearest_hub["name"]}</div>
            <div style="color:#00FFFF; font-size:0.85rem; margin-top:5px;">{n_dist} km deviation</div>
            <hr style="opacity:0.1; margin:15px 0;">
            <div class="m-label">Current Location</div><div style="color:#ffffff; font-size:0.8rem;">{round(selected_truck['pos'][0],2)}, {round(selected_truck['pos'][1],2)}</div>
        </div>""", unsafe_allow_html=True)

# --- TAB 2 & 3 (Preserved Stability) ---
with tabs[1]:
    st.subheader("Sub-Zero Thermal hero Monitor")
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
    s_node = p1.selectbox("Start", [w['name'] for w in RESCUE_HUBS], key="planner_start")
    e_node = p2.selectbox("End", [w['name'] for w in RESCUE_HUBS if w['name'] != s_node], key="planner_end")
    if st.button("Generate National Audit"):
        s_c = next(w for w in RESCUE_HUBS if w['name'] == s_node)
        e_c = next(w for w in RESCUE_HUBS if w['name'] == e_node)
        path, d = get_road_route([s_c['lat'], s_c['lon']], [e_c['lat'], e_c['lon']])
        st.success(f"Verified India-Centric Path: {d} km")
        pm = folium.Map(location=[s_c['lat'], s_c['lon']], zoom_start=6, tiles="CartoDB dark_matter")
        for hub in RESCUE_HUBS:
            folium.CircleMarker([hub['lat'], hub['lon']], radius=2, color="#00FFFF", weight=1, fill=True).add_to(pm)
        folium.PolyLine(path, color="#00FFFF", weight=4).add_to(pm)
        st_folium(pm, width="100%", height=450, key="plan_map")
