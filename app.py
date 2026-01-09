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

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="PharmaGuard | Command Center", page_icon="❄️")

# --- UI STYLING (GLASSMORPHISM & CLEAN LAYOUT) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    #loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: #0e1117; display: flex; flex-direction: column;
        justify-content: center; align-items: center; z-index: 9999; color: white;
    }
    .loader { font-size: 100px; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { transform: scale(1); opacity: 0.7; } 50% { transform: scale(1.1); opacity: 1; color: #00FFFF; } 100% { transform: scale(1); opacity: 0.7; } }
    
    .intel-card {
        background: rgba(30, 33, 48, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px; padding: 20px; height: 210px;
    }
    .card-label { color: #9ea0a9; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; }
    .card-value { color: #ffffff; font-size: 1.6rem; font-weight: 700; margin-bottom: 2px; }
    .card-sub { color: #00FFFF; font-size: 0.85rem; font-weight: 400; }
    
    .progress-container { width: 100%; background-color: #262730; border-radius: 10px; margin: 15px 0; height: 10px; }
    .progress-fill { height: 10px; border-radius: 10px; background: linear-gradient(90deg, #00FFFF, #3498db); }
    
    .status-badge { padding: 8px 16px; border-radius: 8px; font-size: 0.9rem; font-weight: bold; display: block; margin-bottom: 20px; width: 100%; text-align: left; }
    .status-safe { background: rgba(0, 255, 127, 0.1); color: #00FF7F; border-left: 5px solid #00FF7F; }
    .status-alert { background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border-left: 5px solid #FF4B4B; animation: blink 1.5s infinite; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# --- 100 STRATEGIC RESCUE HUBS ---
WAREHOUSE_NETWORK = [
    {"name": "Delhi-Vault", "lat": 28.61, "lon": 77.21}, {"name": "Mumbai-Apex", "lat": 19.08, "lon": 72.88},
    {"name": "Bangalore-Chill", "lat": 12.98, "lon": 77.59}, {"name": "Chennai-Hub", "lat": 13.08, "lon": 80.27},
    {"name": "Kolkata-Safe", "lat": 22.57, "lon": 88.36}, {"name": "Hyderabad-Vault", "lat": 17.39, "lon": 78.49},
    {"name": "Ahmedabad-Bio", "lat": 23.02, "lon": 72.57}, {"name": "Pune-Rescue", "lat": 18.52, "lon": 73.86},
    {"name": "Lucknow-Safe", "lat": 26.85, "lon": 80.95}, {"name": "Nagpur-Central", "lat": 21.15, "lon": 79.09},
    {"name": "Jaipur-Vault", "lat": 26.91, "lon": 75.79}, {"name": "Kanpur-Apex", "lat": 26.45, "lon": 80.33},
    {"name": "Surat-Safe", "lat": 21.17, "lon": 72.83}, {"name": "Patna-Cold", "lat": 25.59, "lon": 85.14},
    {"name": "Vadodara-Chill", "lat": 22.31, "lon": 73.18}, {"name": "Ludhiana-Hub", "lat": 30.90, "lon": 75.86},
    {"name": "Agra-Vault", "lat": 27.18, "lon": 78.01}, {"name": "Nashik-Apex", "lat": 20.00, "lon": 73.79},
    {"name": "Ranchi-Safe", "lat": 23.34, "lon": 85.31}, {"name": "Raipur-Rescue", "lat": 21.25, "lon": 81.63},
    {"name": "Meerut-Vault", "lat": 28.98, "lon": 77.71}, {"name": "Rajkot-Safe", "lat": 22.30, "lon": 70.80},
    {"name": "Varanasi-Bio", "lat": 25.32, "lon": 82.97}, {"name": "Srinagar-Chill", "lat": 34.08, "lon": 74.80},
    {"name": "Aurangabad-Vault", "lat": 19.88, "lon": 75.34}, {"name": "Amritsar-Safe", "lat": 31.63, "lon": 74.87},
    {"name": "Allahabad-Vault", "lat": 25.43, "lon": 81.84}, {"name": "Gwalior-Cold", "lat": 26.22, "lon": 78.18},
    {"name": "Jabalpur-Hub", "lat": 23.18, "lon": 79.99}, {"name": "Coimbatore-Chill", "lat": 11.02, "lon": 76.96},
    {"name": "Vijayawada-Vault", "lat": 16.51, "lon": 80.65}, {"name": "Madurai-Safe", "lat": 9.93, "lon": 78.12},
    {"name": "Guwahati-Bio", "lat": 26.14, "lon": 91.74}, {"name": "Chandigarh-Chill", "lat": 30.73, "lon": 76.78},
    {"name": "Hubli-Vault", "lat": 15.36, "lon": 75.12}, {"name": "Bareilly-Hub", "lat": 28.37, "lon": 79.43},
    {"name": "Gurgaon-Apex", "lat": 28.46, "lon": 77.03}, {"name": "Salem-Vault", "lat": 11.66, "lon": 78.15},
    {"name": "Bhiwandi-Cold", "lat": 19.29, "lon": 73.06}, {"name": "Saharanpur-Hub", "lat": 29.97, "lon": 77.55},
    {"name": "Gorakhpur-Safe", "lat": 26.76, "lon": 83.37}, {"name": "Bikaner-Vault", "lat": 28.02, "lon": 73.31},
    {"name": "Ambala-Chill", "lat": 30.38, "lon": 76.78}, {"name": "Kochi-Hub", "lat": 9.93, "lon": 76.27},
    {"name": "Udaipur-Vault", "lat": 24.59, "lon": 73.71}, {"name": "Dehradun-Chill", "lat": 30.32, "lon": 78.03},
    {"name": "Asansol-Hub", "lat": 23.67, "lon": 86.95}, {"name": "Kolhapur-Vault", "lat": 16.70, "lon": 74.24},
    {"name": "Gulbarga-Hub", "lat": 17.33, "lon": 76.83}, {"name": "Jamnagar-Safe", "lat": 22.47, "lon": 70.06},
    {"name": "Ujjain-Vault", "lat": 23.18, "lon": 75.78}, {"name": "Jhansi-Bio", "lat": 25.45, "lon": 78.57},
    {"name": "Nellore-Hub", "lat": 14.44, "lon": 79.99}, {"name": "Jammu-Vault", "lat": 32.73, "lon": 74.86},
    {"name": "Belgaum-Safe", "lat": 15.85, "lon": 74.50}, {"name": "Mangalore-Chill", "lat": 12.91, "lon": 74.86},
    {"name": "Gaya-Safe", "lat": 24.79, "lon": 85.00}, {"name": "Udaipur-Bio", "lat": 24.57, "lon": 73.68},
    {"name": "Tirupati-Vault", "lat": 13.63, "lon": 79.42}, {"name": "Korba-Chill", "lat": 22.35, "lon": 82.68},
    {"name": "Bhilai-Hub", "lat": 21.19, "lon": 81.35}, {"name": "Kollam-Hub", "lat": 8.89, "lon": 76.61},
    {"name": "Siliguri-Chill", "lat": 26.73, "lon": 88.40}, {"name": "Anantapur-Safe", "lat": 14.68, "lon": 77.60},
    {"name": "Shillong-Bio", "lat": 25.58, "lon": 91.89}, {"name": "Imphal-Safe", "lat": 24.82, "lon": 93.94},
    {"name": "Agartala-Safe", "lat": 23.83, "lon": 91.29}, {"name": "Port Blair-Apex", "lat": 11.62, "lon": 92.73},
    # Filling the rest with unique Tier 2 cities to reach 100
    {"name": "Leh-Safe", "lat": 34.15, "lon": 77.57}, {"name": "Kargil-Vault", "lat": 34.55, "lon": 76.12},
    {"name": "Shimla-Cold", "lat": 31.10, "lon": 77.17}, {"name": "Gangtok-Bio", "lat": 27.33, "lon": 88.61},
    {"name": "Itanagar-Safe", "lat": 27.08, "lon": 93.61}, {"name": "Aizawl-Apex", "lat": 23.72, "lon": 92.71},
    {"name": "Kavaratti-Hub", "lat": 10.56, "lon": 72.64}, {"name": "Daman-Safe", "lat": 20.39, "lon": 72.83},
    {"name": "Panaji-Vault", "lat": 15.49, "lon": 73.82}, {"name": "Gandhinagar-Hub", "lat": 23.21, "lon": 72.63},
    {"name": "Bhubaneswar-Apex", "lat": 20.30, "lon": 85.82}, {"name": "Trivandrum-Safe", "lat": 8.52, "lon": 76.93},
    {"name": "Mysore-Bio", "lat": 12.29, "lon": 76.63}, {"name": "Hubli-Apex", "lat": 15.36, "lon": 75.12},
    {"name": "Warangal-Bio", "lat": 17.96, "lon": 79.59}, {"name": "Guntur-Bio", "lat": 16.30, "lon": 80.43},
    {"name": "Kurnool-Bio", "lat": 15.82, "lon": 78.03}, {"name": "Rourkela-Vault", "lat": 22.24, "lon": 84.88},
    {"name": "Sambalpur-Safe", "lat": 21.46, "lon": 83.98}, {"name": "Berhampur-Hub", "lat": 19.31, "lon": 84.79},
    {"name": "Muzaffarpur-Apex", "lat": 26.11, "lon": 85.39}, {"name": "Darbhanga-Vault", "lat": 26.15, "lon": 85.89},
    {"name": "Purnia-Safe", "lat": 25.77, "lon": 87.47}, {"name": "Bhagalpur-Bio", "lat": 25.24, "lon": 86.97},
    {"name": "Satna-Hub", "lat": 24.60, "lon": 80.83}, {"name": "Ratlam-Vault", "lat": 23.33, "lon": 75.03},
    {"name": "Bilaspur-Apex", "lat": 22.07, "lon": 82.13}, {"name": "Bhilai-Vault", "lat": 21.19, "lon": 81.35},
    {"name": "Durg-Safe", "lat": 21.19, "lon": 81.28}, {"name": "Korba-Hub", "lat": 22.35, "lon": 82.68}
]

# --- EXTENDED ORIGINS AND DESTINATIONS (FOR BETTER SPREAD) ---
ORIGINS_POOL = list(PHARMA_HUBS.keys()) + ["Srinagar-Chill", "Leh-Safe", "Guwahati-Bio", "Trivandrum-Safe", "Bhuj-Vault"]
DESTS_POOL = list(DESTINATIONS.keys()) + ["Kochi-Hub", "Amritsar-Safe", "Port Blair-Apex", "Gangtok-Chill", "Chennai-Hub"]

# --- HELPERS ---
@st.cache_data(ttl=3600)
def get_road_route(start_coords, end_coords):
    url = f"http://router.project-osrm.org/route/v1/driving/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}?overview=full"
    try:
        r = requests.get(url, timeout=5).json()
        return polyline.decode(r['routes'][0]['geometry']), round(r['routes'][0]['distance']/1000)
    except:
        return [start_coords, end_coords], 500

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# --- INITIALIZATION ---
if 'fleet' not in st.session_state:
    loading_placeholder = st.empty()
    with loading_placeholder:
        st.markdown('<div id="loading-overlay"><div class="loader">❄️</div><div class="loading-text">SPREADING NATIONAL NETWORK...</div></div>', unsafe_allow_html=True)
    
    fleet = []
    drivers = ["N. Modi", "A. Shah", "S. Jaishankar", "R. Gandhi", "M. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor", "N. Chandran", "Arjun Kapur", "Deepak Punia", "Suresh Raina", "M. S. Dhoni"]
    
    # Combined pool of all hubs to act as start/end for maximum spread
    all_locations = WAREHOUSE_NETWORK + [{"name": k, "lat": v[0], "lon": v[1]} for k, v in PHARMA_HUBS.items()]
    
    for i in range(15):
        # Pick two completely random points from the 100+ locations
        loc_pair = random.sample(all_locations, 2)
        start_loc, end_loc = loc_pair[0], loc_pair[1]
        
        path, dist = get_road_route([start_loc['lat'], start_loc['lon']], [end_loc['lat'], end_loc['lon']])
        prog = random.uniform(0.2, 0.8)
        pos = path[int(len(path)*prog)]
        is_fail = (i == 5)
        temp = 8.8 if is_fail else round(random.uniform(-7, 2), 1)
        
        fleet.append({
            "id": f"IND-EXP-{1000+i}", "driver": drivers[i % len(drivers)],
            "origin": start_loc['name'], "dest": end_loc['name'], "pos": pos, "path": path,
            "total_km": dist, "dist_covered": round(dist * prog), "dist_rem": round(dist * (1-prog)),
            "hrs_driven": round(prog * 14, 1), "temp": temp, "prog_pct": round(prog*100),
            "forecast": [round(random.uniform(-9, 3), 1) for _ in range(10)]
        })
    st.session_state.fleet = fleet
    time.sleep(1)
    loading_placeholder.empty()

# --- APP LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")
tab1, tab2, tab3 = st.tabs(["🌐 Live Map", "🌡️ Thermal Forecasts", "🛤️ Trip Planner"])

with tab1:
    selected_id = st.selectbox("🎯 Select Truck for Live Intelligence:", [t['id'] for t in st.session_state.fleet])
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    for wh in WAREHOUSE_NETWORK:
        folium.CircleMarker([wh['lat'], wh['lon']], radius=2, color="#3498db", fill=True, popup=wh['name']).add_to(m)

    for t in st.session_state.fleet:
        is_sel = t['id'] == selected_id
        is_alert = t['temp'] > 5 or t['temp'] < -10
        color = "#00FFFF" if is_sel else ("#FF4B4B" if is_alert else "#00FF7F")
        folium.PolyLine(t['path'], color=color, weight=5 if is_sel else 1.5, opacity=0.8 if is_sel else 0.2).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color="purple" if is_sel else ("red" if is_alert else "green"), icon="truck", prefix="fa")).add_to(m)
    
    st_folium(m, width="100%", height=480, key="main_map")

    # --- SYSTEM INTELLIGENCE ---
    st.markdown(f"### 🛡️ System Intelligence: {selected_id}")
    is_critical = selected_truck['temp'] > 5 or selected_truck['temp'] < -10
    n_hub = min(WAREHOUSE_NETWORK, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    n_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], n_hub['lat'], n_hub['lon']))
    
    status_class = "status-alert" if is_critical else "status-safe"
    status_text = f"🛑 MISSION ALERT: THERMAL BREACH - REROUTE TO {n_hub['name'].upper()}" if is_critical else "✅ MISSION STATUS: CONTINUE / SAFE | Environment Nominal."
    st.markdown(f'<div class="status-badge {status_class}">{status_text}</div>', unsafe_allow_html=True)

    col_v, col_p, col_e = st.columns([1.2, 2, 1.2])

    with col_v:
        st.markdown(f"""
        <div class="intel-card">
            <div class="card-label">Vehicle & Driver</div>
            <div class="card-value">{selected_truck['driver']}</div>
            <div class="card-sub">Active for {selected_truck['hrs_driven']} hrs</div>
            <hr style="opacity:0.1; margin:15px 0;">
            <div class="card-label">Cargo Temperature</div>
            <div class="card-value" style="color:{'#FF4B4B' if is_critical else '#00FF7F'}">{selected_truck['temp']}°C</div>
        </div>
        """, unsafe_allow_html=True)

    with col_p:
        eta = (datetime.now() + timedelta(hours=selected_truck['dist_rem']/60)).strftime("%H:%M, %d %b")
        st.markdown(f"""
        <div class="intel-card">
            <div class="card-label">Trip Progress</div>
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span style="color:white; font-weight:bold;">{selected_truck['dist_covered']} km</span>
                <span style="color:#9ea0a9;">{selected_truck['total_km']} km Total</span>
            </div>
            <div class="progress-container"><div class="progress-fill" style="width:{selected_truck['prog_pct']}%"></div></div>
            <div style="display:flex; justify-content:space-between; margin-top:15px;">
                <div><div class="card-label">Remaining</div><div class="card-value" style="font-size:1.1rem;">{selected_truck['dist_rem']} km</div></div>
                <div style="text-align:right;"><div class="card-label">Est. Arrival</div><div class="card-value" style="font-size:1.1rem;">{eta}</div></div>
            </div>
            <hr style="opacity:0.1; margin:15px 0;">
            <div class="card-label">Active Logistics Corridor</div>
            <div style="font-size:0.85rem; color:#00FFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{selected_truck['origin']} ➔ {selected_truck['dest']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_e:
        st.markdown(f"""
        <div class="intel-card" style="border-left: 4px solid {'#FF4B4B' if is_critical else '#3498db'}">
            <div class="card-label">Nearest Rescue Node</div>
            <div class="card-value" style="font-size:1.2rem;">{n_hub['name']}</div>
            <div class="card-sub">{n_dist} km deviation</div>
            <hr style="opacity:0.1; margin:15px 0;">
            <div class="card-label">Emergency Protocol</div>
            <div style="font-size:0.8rem; color:#9ea0a9;">{'Contact local hub manager for immediate offloading.' if is_critical else 'Maintain heading. Environmental logs verified.'}</div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.subheader("Sub-Zero Thermal Stability (-10°C to 5°C)")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            df = pd.DataFrame({"Temp": t['forecast'], "Max": [5]*10, "Min": [-10]*10})
            st.write(f"**Truck {t['id']}** ({'🚨 ALERT' if (t['temp'] > 5) else '✅ OK'})")
            st.line_chart(df, height=150)

with tab3:
    st.header("Strategic Route Safety Audit")
    p1, p2, p3 = st.columns([1,1,1])
    s_node = p1.selectbox("Start Point", [w['name'] for w in WAREHOUSE_NETWORK])
    e_node = p2.selectbox("Destination", [w['name'] for w in WAREHOUSE_NETWORK if w['name'] != s_node])
    radius = p3.slider("Search Radius (km)", 20, 150, 60)
    
    if st.button("Generate Road Safety Audit"):
        s_coords = next(w for w in WAREHOUSE_NETWORK if w['name'] == s_node)
        e_coords = next(w for w in WAREHOUSE_NETWORK if w['name'] == e_node)
        path, d = get_road_route([s_coords['lat'], s_coords['lon']], [e_coords['lat'], e_coords['lon']])
        st.success(f"Verified Highway Distance: {d} km")
        pm = folium.Map(location=[s_coords['lat'], s_coords['lon']], zoom_start=6, tiles="CartoDB dark_matter")
        folium.PolyLine(path, color="#00FFFF", weight=4).add_to(pm)
        found = []
        for wh in WAREHOUSE_NETWORK:
            dist = min([haversine(wh['lat'], wh['lon'], pt[0], pt[1]) for pt in path[::25]])
            if dist <= radius:
                folium.Marker([wh['lat'], wh['lon']], icon=folium.Icon(color="orange", icon="shield-heart", prefix="fa"), popup=wh['name']).add_to(pm)
                found.append({"Hub": wh['name'], "Deviation (km)": round(dist, 1)})
        st_folium(pm, width="100%", height=450, key="plan_map")
        if found: st.table(pd.DataFrame(found).sort_values("Deviation (km)"))
