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

# --- 2. GLOBAL UI STYLING (GLASSMORPHISM) ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0d12; color: #ffffff; }
    #loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: #0b0d12; display: flex; flex-direction: column;
        justify-content: center; align-items: center; z-index: 9999;
    }
    .loader { font-size: 80px; animation: pulse 1.5s infinite; color: #00FFFF; }
    @keyframes pulse { 0% { transform: scale(1); opacity: 0.5; } 50% { transform: scale(1.1); opacity: 1; } 100% { transform: scale(1); opacity: 0.5; } }
    
    .map-frame { border: 1px solid rgba(0, 255, 255, 0.2); border-radius: 15px; background: rgba(17, 19, 26, 0.9); padding: 12px; margin-bottom: 25px; }
    .intel-card { background: rgba(30, 33, 48, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 20px; min-height: 200px; }
    .m-label { color: #808495; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; }
    .m-value { color: #ffffff; font-size: 1.5rem; font-weight: bold; margin-top: 5px; }
    
    .status-pill { padding: 10px 18px; border-radius: 8px; font-size: 0.9rem; font-weight: bold; display: block; margin-bottom: 20px; border-left: 6px solid; }
    .status-safe { background: rgba(0, 255, 127, 0.1); color: #00FF7F; border-color: #00FF7F; }
    .status-alert { background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border-color: #FF4B4B; animation: blink 1.5s infinite; }
    
    .thermal-hero { background: #12151c; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 15px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 100 REAL INDIAN CITIES (STRICTLY INDIA-CENTRIC) ---
@st.cache_data
def get_india_rescue_network():
    return [
        {"name": "Delhi", "lat": 28.6139, "lon": 77.2090}, {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946}, {"name": "Chennai", "lat": 13.0827, "lon": 80.2707},
        {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639}, {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
        {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714}, {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
        {"name": "Surat", "lat": 21.1702, "lon": 72.8311}, {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873},
        {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462}, {"name": "Kanpur", "lat": 26.4499, "lon": 80.3319},
        {"name": "Nagpur", "lat": 21.1458, "lon": 79.0882}, {"name": "Indore", "lat": 22.7196, "lon": 75.8577},
        {"name": "Thane", "lat": 19.2183, "lon": 72.9781}, {"name": "Bhopal", "lat": 23.2599, "lon": 77.4126},
        {"name": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185}, {"name": "Pimpri-Chinchwad", "lat": 18.6298, "lon": 73.7997},
        {"name": "Patna", "lat": 25.5941, "lon": 85.1376}, {"name": "Vadodara", "lat": 22.3072, "lon": 73.1812},
        {"name": "Ghaziabad", "lat": 28.6692, "lon": 77.4538}, {"name": "Ludhiana", "lat": 30.9010, "lon": 75.8573},
        {"name": "Agra", "lat": 27.1767, "lon": 78.0081}, {"name": "Nashik", "lat": 19.9975, "lon": 73.7898},
        {"name": "Faridabad", "lat": 28.4089, "lon": 77.3178}, {"name": "Meerut", "lat": 28.9845, "lon": 77.7064},
        {"name": "Rajkot", "lat": 22.3039, "lon": 70.8022}, {"name": "Kalyan-Dombivli", "lat": 19.2348, "lon": 73.1290},
        {"name": "Vasai-Virar", "lat": 19.3919, "lon": 72.8397}, {"name": "Varanasi", "lat": 25.3176, "lon": 82.9739},
        {"name": "Srinagar", "lat": 34.0837, "lon": 74.7973}, {"name": "Aurangabad", "lat": 19.8762, "lon": 75.3433},
        {"name": "Dhanbad", "lat": 23.7957, "lon": 86.4304}, {"name": "Amritsar", "lat": 31.6340, "lon": 74.8723},
        {"name": "Navi Mumbai", "lat": 19.0330, "lon": 73.0297}, {"name": "Allahabad", "lat": 25.4358, "lon": 81.8463},
        {"name": "Ranchi", "lat": 23.3441, "lon": 85.3094}, {"name": "Howrah", "lat": 22.5867, "lon": 88.3174},
        {"name": "Jabalpur", "lat": 23.1815, "lon": 79.9864}, {"name": "Gwalior", "lat": 26.2183, "lon": 78.1828},
        {"name": "Vijayawada", "lat": 16.5062, "lon": 80.6480}, {"name": "Jodhpur", "lat": 26.2389, "lon": 73.0243},
        {"name": "Madurai", "lat": 9.9252, "lon": 78.1198}, {"name": "Raipur", "lat": 21.2514, "lon": 81.6296},
        {"name": "Kota", "lat": 25.2138, "lon": 75.8648}, {"name": "Guwahati", "lat": 26.1445, "lon": 91.7362},
        {"name": "Chandigarh", "lat": 30.7333, "lon": 76.7794}, {"name": "Solapur", "lat": 17.6599, "lon": 75.9064},
        {"name": "Hubli-Dharwad", "lat": 15.3647, "lon": 75.1240}, {"name": "Bareilly", "lat": 28.3670, "lon": 79.4304},
        {"name": "Moradabad", "lat": 28.8385, "lon": 78.7733}, {"name": "Mysore", "lat": 12.2958, "lon": 76.6394},
        {"name": "Gurgaon", "lat": 28.4595, "lon": 77.0266}, {"name": "Aligarh", "lat": 27.8813, "lon": 78.0882},
        {"name": "Jalandhar", "lat": 31.3260, "lon": 75.5762}, {"name": "Tiruchirappalli", "lat": 10.7905, "lon": 78.7047},
        {"name": "Bhubaneswar", "lat": 20.2961, "lon": 85.8245}, {"name": "Salem", "lat": 11.6643, "lon": 78.1460},
        {"name": "Mira-Bhayandar", "lat": 19.2813, "lon": 72.8557}, {"name": "Trivandrum", "lat": 8.5241, "lon": 76.9366},
        {"name": "Bhiwandi", "lat": 19.2967, "lon": 73.0597}, {"name": "Saharanpur", "lat": 29.9680, "lon": 77.5552},
        {"name": "Gorakhpur", "lat": 26.7606, "lon": 83.3731}, {"name": "Guntur", "lat": 16.3067, "lon": 80.4365},
        {"name": "Bikaner", "lat": 28.0229, "lon": 73.3119}, {"name": "Amravati", "lat": 20.9320, "lon": 77.7523},
        {"name": "Noida", "lat": 28.5355, "lon": 77.3910}, {"name": "Jamshedpur", "lat": 22.8046, "lon": 86.2029},
        {"name": "Bhilai", "lat": 21.1938, "lon": 81.3509}, {"name": "Cuttack", "lat": 20.4625, "lon": 85.8830},
        {"name": "Firozabad", "lat": 27.1504, "lon": 78.3958}, {"name": "Kochi", "lat": 9.9312, "lon": 76.2673},
        {"name": "Nellore", "lat": 14.4426, "lon": 79.9865}, {"name": "Bhavnagar", "lat": 21.7645, "lon": 72.1519},
        {"name": "Dehradun", "lat": 30.3165, "lon": 78.0322}, {"name": "Durgapur", "lat": 23.5204, "lon": 87.3119},
        {"name": "Asansol", "lat": 23.6739, "lon": 86.9524}, {"name": "Rourkela", "lat": 22.2604, "lon": 84.8536},
        {"name": "Nanded", "lat": 19.1429, "lon": 77.3037}, {"name": "Kolhapur", "lat": 16.7050, "lon": 74.2433},
        {"name": "Ajmer", "lat": 26.4499, "lon": 74.6399}, {"name": "Akola", "lat": 20.7002, "lon": 77.0082},
        {"name": "Gulbarga", "lat": 17.3297, "lon": 76.8343}, {"name": "Jamnagar", "lat": 22.4707, "lon": 70.0577},
        {"name": "Ujjain", "lat": 23.1760, "lon": 75.7885}, {"name": "Loni", "lat": 28.7314, "lon": 77.2845},
        {"name": "Siliguri", "lat": 26.7271, "lon": 88.3953}, {"name": "Jhansi", "lat": 25.4484, "lon": 78.5685},
        {"name": "Ulhasnagar", "lat": 19.2215, "lon": 73.1645}, {"name": "Jammu", "lat": 32.7266, "lon": 74.8570},
        {"name": "Sangli", "lat": 16.8524, "lon": 74.5815}, {"name": "Mangalore", "lat": 12.9141, "lon": 74.8560},
        {"name": "Erode", "lat": 11.3410, "lon": 77.7172}, {"name": "Belgaum", "lat": 15.8497, "lon": 74.4977},
        {"name": "Kargil", "lat": 34.5539, "lon": 76.1349}, {"name": "Tirunelveli", "lat": 8.7139, "lon": 77.7567},
        {"name": "Malegaon", "lat": 20.5517, "lon": 74.5089}, {"name": "Gaya", "lat": 24.7914, "lon": 85.0002},
        {"name": "Jalgaon", "lat": 21.0077, "lon": 75.5626}, {"name": "Udaipur", "lat": 24.5854, "lon": 73.7125}
    ]

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
    st.markdown('<div id="loading-overlay"><div class="loader">❄️</div><div style="color:white; letter-spacing:5px;">SECURING NATIONAL LOGISTICS...</div></div>', unsafe_allow_html=True)

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

if 'planner_state' not in st.session_state:
    st.session_state.planner_state = None

time.sleep(1)
loading_placeholder.empty()

# --- 6. APP LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")
tabs = st.tabs(["🌐 Live Fleet Map", "🌡️ Thermal Hero Monitor", "🛤️ Trip Planner"])

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

    # Intelligence Dashboard
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
        eta = (datetime.now() + timedelta(hours=selected_truck['dist_rem']/60)).strftime("%H:%M")
        st.markdown(f'<div class="intel-card"><div class="m-label">Trip Progress</div><div class="m-value">{selected_truck["dist_covered"]} km</div><div style="color:#00FFFF; margin-top:10px;">Remaining: {selected_truck["dist_rem"]} km</div><div style="color:#9ea0a9; font-size:0.8rem;">ETA: {eta}</div></div>', unsafe_allow_html=True)
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
    s_node = p1.selectbox("Departure Point", [w['name'] for w in RESCUE_HUBS], key="planner_start")
    e_node = p2.selectbox("Destination Hub", [w['name'] for w in RESCUE_HUBS if w['name'] != s_node], key="planner_end")
    
    if st.button("Generate National Audit"):
        s_c = next(w for w in RESCUE_HUBS if w['name'] == s_node)
        e_c = next(w for w in RESCUE_HUBS if w['name'] == e_node)
        path, d = get_road_route([s_c['lat'], s_c['lon']], [e_c['lat'], e_c['lon']])
        st.session_state.planner_state = {"path": path, "dist": d, "start": s_node, "end": e_node, "coords": [s_c['lat'], s_c['lon']]}

    if st.session_state.planner_state:
        ps = st.session_state.planner_state
        st.success(f"Verified India-Centric Path: {ps['dist']} km")
        pm = folium.Map(location=ps['coords'], zoom_start=6, tiles="CartoDB dark_matter")
        draw_rescue_nodes(pm)
        folium.PolyLine(ps['path'], color="#00FFFF", weight=4).add_to(pm)
        st_folium(pm, width="100%", height=450, key="plan_map")
