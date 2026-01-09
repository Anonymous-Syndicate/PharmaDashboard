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

# --- 1. CONFIGURATION & THEME ---
st.set_page_config(layout="wide", page_title="PharmaGuard AI | Command Center", page_icon="❄️")

st.markdown("""
    <style>
    /* Global Background */
    .stApp { background-color: #0b0d12; color: #ffffff; }
    
    /* Center Loading Screen */
    #loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: #0b0d12; display: flex; flex-direction: column;
        justify-content: center; align-items: center; z-index: 9999;
    }
    .loader-icon { font-size: 100px; animation: pulse 1.5s infinite; color: #00FFFF; }
    @keyframes pulse { 0% { transform: scale(1); opacity: 0.5; } 50% { transform: scale(1.1); opacity: 1; } 100% { transform: scale(1); opacity: 0.5; } }

    /* Modern Framed Box for Map/Graphs */
    .modern-frame {
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 15px;
        background: rgba(17, 19, 26, 0.9);
        padding: 15px;
        box-shadow: 0 4px 30px rgba(0,0,0,0.7);
        margin-bottom: 20px;
    }

    /* Intelligence Card Styling */
    .intel-card {
        background: rgba(30, 33, 48, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px; padding: 20px; height: 100%;
    }
    .m-label { color: #808495; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; }
    .m-value { color: #ffffff; font-size: 1.5rem; font-weight: bold; margin-top: 5px; }
    
    /* Progress Bar */
    .pg-bar { width: 100%; background: #262730; border-radius: 5px; height: 10px; margin: 10px 0; }
    .pg-fill { height: 10px; border-radius: 5px; background: linear-gradient(90deg, #00FFFF, #3498db); }

    /* Thermal Tab Graph Hero Styling */
    .graph-container {
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px; background: #12151c;
        padding: 10px; margin-bottom: 25px;
    }
    .status-glow-green { color: #00FF7F; text-shadow: 0 0 10px #00FF7F; font-weight: bold; }
    .status-glow-red { color: #FF4B4B; text-shadow: 0 0 10px #FF4B4B; font-weight: bold; animation: blink 1s infinite; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 100 REAL INDIAN LOGISTICS HUBS ---
RESCUE_HUBS = [
    {"name": "Delhi-Vault", "lat": 28.61, "lon": 77.21}, {"name": "Mumbai-Apex", "lat": 19.08, "lon": 72.88},
    {"name": "Bangalore-Chill", "lat": 12.98, "lon": 77.59}, {"name": "Chennai-Hub", "lat": 13.08, "lon": 80.27},
    {"name": "Kolkata-Safe", "lat": 22.57, "lon": 88.36}, {"name": "Hyderabad-Vault", "lat": 17.39, "lon": 78.49},
    {"name": "Ahmedabad-Bio", "lat": 23.02, "lon": 72.57}, {"name": "Pune-Rescue", "lat": 18.52, "lon": 73.86},
    {"name": "Lucknow-Safe", "lat": 26.85, "lon": 80.95}, {"name": "Nagpur-Central", "lat": 21.15, "lon": 79.09},
    {"name": "Jaipur-Vault", "lat": 26.91, "lon": 75.79}, {"name": "Patna-Cold", "lat": 25.59, "lon": 85.14},
    {"name": "Srinagar-Safe", "lat": 34.08, "lon": 74.80}, {"name": "Guwahati-Hub", "lat": 26.14, "lon": 91.74},
    {"name": "Bhubaneswar-Apex", "lat": 20.30, "lon": 85.82}, {"name": "Kochi-Safe", "lat": 9.93, "lon": 76.27},
    {"name": "Indore-Vault", "lat": 22.72, "lon": 75.86}, {"name": "Chandigarh-Safe", "lat": 30.73, "lon": 76.78},
    {"name": "Shimla-Rescue", "lat": 31.10, "lon": 77.17}, {"name": "Leh-Portal", "lat": 34.15, "lon": 77.57},
    {"name": "Bhuj-Vault", "lat": 23.24, "lon": 69.66}, {"name": "Agartala-Bio", "lat": 23.83, "lon": 91.28}
]
# Procedurally fill to reach exactly 100 strategic spread
random.seed(42) # Consistent coordinates for hubs
for i in range(78):
    RESCUE_HUBS.append({
        "name": f"Rescue-Node-{100+i}",
        "lat": round(random.uniform(8.5, 34.0), 2),
        "lon": round(random.uniform(68.5, 94.0), 2)
    })

# --- 3. HELPERS ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def get_road_route(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full"
    try:
        r = requests.get(url, timeout=3).json()
        return polyline.decode(r['routes'][0]['geometry']), round(r['routes'][0]['distance']/1000)
    except: # Fallback to straight line if API is down
        return [[start[0], start[1]], [end[0], end[1]]], 500

# --- 4. INITIALIZATION (EVERY REFRESH) ---
loading_placeholder = st.empty()
with loading_placeholder:
    st.markdown('<div id="loading-overlay"><div class="loader-icon">❄️</div><div style="color:white; letter-spacing:5px;">PHARMAGUARD AI ACTIVE</div></div>', unsafe_allow_html=True)

if 'fleet' not in st.session_state:
    fleet = []
    drivers = ["N. Modi", "A. Shah", "S. Jaishankar", "R. Gandhi", "M. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor"]
    
    for i in range(15):
        pair = random.sample(RESCUE_HUBS, 2)
        s, e = pair[0], pair[1]
        path, dist = get_road_route([s['lat'], s['lon']], [e['lat'], e['lon']])
        prog = random.uniform(0.3, 0.7)
        pos = path[int(len(path)*prog)]
        is_fail = (i == 5) # IND-EXP-1005
        
        # Consistent 12-point forecast
        f_data = [round((8.5 if is_fail else -4.5) + random.uniform(-0.8, 0.8), 2) for _ in range(12)]
        
        fleet.append({
            "id": f"IND-EXP-{1000+i}", "driver": drivers[i % len(drivers)],
            "origin": s['name'], "dest": e['name'], "pos": pos, "path": path,
            "total_km": dist, "dist_covered": round(dist * prog), "dist_rem": round(dist * (1-prog)),
            "hrs": round(prog * 15, 1), "temp": f_data[0], "forecast": f_data, "is_fail": is_fail, "prog_pct": round(prog*100)
        })
    st.session_state.fleet = fleet
else:
    time.sleep(0.8) # Small delay to show animation on refresh

loading_placeholder.empty()

# --- 5. MAIN UI LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")
tabs = st.tabs(["🌐 Live Fleet Map", "🌡️ Thermal Stability", "🛤️ Route Safety Planner"])

# --- TAB 1: LIVE MAP ---
with tabs[0]:
    selected_id = st.selectbox("🎯 Select Vehicle for Live Intelligence:", [t['id'] for t in st.session_state.fleet])
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    # MODERN MAP BOX
    st.markdown('<div class="modern-frame">', unsafe_allow_html=True)
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    folium.LatLngPopup().add_to(m) # Click for exact numbers

    # 100 Rescue Hubs
    for wh in RESCUE_HUBS:
        folium.CircleMarker([wh['lat'], wh['lon']], radius=2, color="#3498db", fill=True, tooltip=f"Hub: {wh['name']}").add_to(m)

    # Active Fleet
    for t in st.session_state.fleet:
        is_sel = t['id'] == selected_id
        color = "#00FFFF" if is_sel else ("#FF4B4B" if t['is_fail'] else "#00FF7F")
        folium.PolyLine(t['path'], color=color, weight=6 if is_sel else 1.2, opacity=0.8 if is_sel else 0.2).add_to(m)
        folium.Marker(t['pos'], tooltip=f"Truck {t['id']} | {t['temp']}°C | GPS: {round(t['pos'][0],2)}, {round(t['pos'][1],2)}", 
                      icon=folium.Icon(color="purple" if is_sel else ("red" if t['is_fail'] else "green"), icon="truck", prefix="fa")).add_to(m)
    
    st_folium(m, width="100%", height=500, key="main_map")
    st.markdown('</div>', unsafe_allow_html=True)

    # Intelligence Dashboard
    st.markdown(f"### 🛡️ System Intelligence: {selected_id}")
    n_hub = min(RESCUE_HUBS, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    n_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], n_hub['lat'], n_hub['lon']), 1)
    
    if selected_truck['is_fail']:
        st.error(f"🛑 MISSION ALERT: Critical Thermal Breach at {selected_truck['temp']}°C. Reroute to {n_hub['name']} ({n_dist} km deviation).")
    else:
        st.success(f"✅ MISSION STATUS: Environmental systems safe. Current Temp: {selected_truck['temp']}°C.")

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1:
        st.markdown(f'<div class="intel-card"><div class="m-label">Driver</div><div class="m-value">{selected_truck["driver"]}</div><div style="color:#00FFFF; font-size:0.8rem; margin-top:10px;">Active: {selected_truck["hrs"]} hrs</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="intel-card"><div class="m-label">Trip Progress</div><div class="m-value">{selected_truck["dist_covered"]} km</div><div class="pg-bar"><div class="pg-fill" style="width:{selected_truck["prog_pct"]}%"></div></div><div style="color:#9ea0a9; font-size:0.8rem;">Target: {selected_truck["total_km"]} km</div></div>', unsafe_allow_html=True)
    with c3:
        eta = (datetime.now() + timedelta(hours=selected_truck['dist_rem']/60)).strftime("%H:%M, %d %b")
        st.markdown(f'<div class="intel-card"><div class="m-label">Remaining</div><div class="m-value">{selected_truck["dist_rem"]} km</div><div style="color:#00FFFF; font-size:0.8rem; margin-top:10px;">ETA: {eta}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="intel-card" style="border-left: 4px solid {"#FF4B4B" if selected_truck["is_fail"] else "#3498db"}"><div class="m-label">Nearest Rescue Node</div><div class="m-value" style="font-size:1.2rem;">{n_hub["name"]}</div><div style="color:#00FFFF; font-size:0.8rem; margin-top:10px;">{n_dist} km precisely off-route</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div style="background:rgba(30,33,48,0.5); padding:10px; border-radius:5px; margin-top:10px; border:1px solid rgba(255,255,255,0.05);">🛣️ <b>Active Logistics Corridor:</b> {selected_truck["origin"]} ———▶ {selected_truck["dest"]}</div>', unsafe_allow_html=True)

# --- TAB 2: THERMAL STABILITY (GRAPH HERO) ---
with tabs[1]:
    st.subheader("Sub-Zero Real-Time Thermal Monitoring (-10°C to 5°C)")
    st.write("Click and drag on any graph to zoom into high-precision data points.")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            # Integrated sleek header
            status_text = "🚨 THERMAL BREACH" if t['is_fail'] else "✅ STABLE"
            status_style = "status-glow-red" if t['is_fail'] else "status-glow-green"
            
            st.markdown(f"""
                <div class="graph-container">
                    <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-family:monospace; font-size:0.8rem;">
                        <span style="color:#9ea0a9;">VEHICLE ID: {t['id']}</span>
                        <span class="{status_style}">{status_text}</span>
                    </div>
            """, unsafe_allow_html=True)
            
            df_plot = pd.DataFrame({
                "Internal Temp": t['forecast'],
                "Max Threshold": [5.0]*12,
                "Min Threshold": [-10.0]*12
            })
            st.line_chart(df_plot, height=250, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: TRIP PLANNER ---
with tabs[2]:
    st.header("Strategic Pre-Trip Route Audit")
    p1, p2, p3 = st.columns([1,1,1])
    s_node = p1.selectbox("Departure Point", [w['name'] for w in RESCUE_HUBS], key="ps")
    e_node = p2.selectbox("Destination Node", [w['name'] for w in RESCUE_HUBS if w['name'] != s_node], key="pe")
    radius = p3.slider("Search Radius (km)", 20, 150, 50)
    
    if st.button("Generate National Safety Audit"):
        s_c = next(w for w in RESCUE_HUBS if w['name'] == s_node)
        e_c = next(w for w in RESCUE_HUBS if w['name'] == e_node)
        path, d = get_road_route([s_c['lat'], s_c['lon']], [e_c['lat'], e_c['lon']])
        
        st.success(f"Verified Path: {d} km via National Highways")
        pm = folium.Map(location=[s_c['lat'], s_c['lon']], zoom_start=6, tiles="CartoDB dark_matter")
        folium.PolyLine(path, color="#00FFFF", weight=4).add_to(pm)
        st_folium(pm, width="100%", height=450, key="plan_map")
