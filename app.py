import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random
import requests
import polyline
import math
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="PharmaGuard | National Command Center", page_icon="❄️")

# --- DATASETS ---
PHARMA_HUBS = {
    "Baddi Hub (North)": [30.9578, 76.7914], "Sikkim Cluster (East)": [27.3314, 88.6138],
    "Ahmedabad (West)": [23.0225, 72.5714], "Hyderabad (South)": [17.4500, 78.6000],
    "Vizag Pharma City": [17.6868, 83.2185], "Goa Manufacturing": [15.2993, 74.1240],
    "Indore SEZ": [22.7196, 75.8577], "Pune Bio-Cluster": [18.5204, 73.8567]
}

DESTINATIONS = {
    "Mumbai Port": [18.9438, 72.8387], "Delhi Air Cargo": [28.5562, 77.1000],
    "Bangalore Dist.": [12.9716, 77.5946], "Chennai Terminal": [13.0827, 80.2707],
    "Kolkata Port": [22.5726, 88.3639], "Guwahati Hub": [26.1445, 91.7362],
    "Cochin Port": [9.9312, 76.2673], "Chandigarh Dry Port": [30.7333, 76.7794],
    "Nagpur Hub": [21.1458, 79.0882], "Lucknow Logistics": [26.8467, 80.9462]
}

WAREHOUSE_NETWORK = [
    {"name": "Ambala-01", "lat": 30.3782, "lon": 76.7767}, {"name": "Jaipur-Safe", "lat": 26.9124, "lon": 75.7873},
    {"name": "Udaipur-Vault", "lat": 24.5854, "lon": 73.7125}, {"name": "Gwalior-Cold", "lat": 26.2183, "lon": 78.1828},
    {"name": "Jhansi-Hub", "lat": 25.4484, "lon": 78.5685}, {"name": "Bhopal-Bio", "lat": 23.2599, "lon": 77.4126},
    {"name": "Jabalpur-Central", "lat": 23.1815, "lon": 79.9864}, {"name": "Raipur-Rescue", "lat": 21.2514, "lon": 81.6296},
    {"name": "Nagpur-Apex", "lat": 21.1458, "lon": 79.0882}, {"name": "Akola-Vault", "lat": 20.7002, "lon": 77.0082},
    {"name": "Aurangabad-Pharma", "lat": 19.8762, "lon": 75.3433}, {"name": "Satara-Cold", "lat": 17.6805, "lon": 73.9803}
]

DRIVERS = ["Amitav Ghosh", "S. Jaishankar", "K. Rathore", "Mohd. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor", "N. Chandran", "Arjun Kapur", "Deepak Punia", "Suresh Raina", "M. S. Dhoni", "Hardik Pandya"]

# --- HELPER FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_real_forecast(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m&forecast_days=1"
    try:
        r = requests.get(url, timeout=5).json()
        return r['hourly']['temperature_2m'][:8]
    except: return [25.0] * 8 

def get_road_route_data(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=polyline"
    try:
        r = requests.get(url, timeout=5).json()
        path = polyline.decode(r['routes'][0]['geometry'])
        dist = round(r['routes'][0]['distance'] / 1000, 1)
        dur = round(r['routes'][0]['duration'] / 3600, 1)
        return path, dist, dur
    except: return [start, end], 0, 0

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def simulate_thermal_excursion(start_temp, ambient_forecast):
    cargo_temps = [start_temp]
    k = 0.12
    for ambient in ambient_forecast[1:]:
        new_temp = cargo_temps[-1] + k * (ambient - cargo_temps[-1])
        cargo_temps.append(round(new_temp, 1))
    return cargo_temps

# --- INITIALIZE FLEET ---
if 'fleet' not in st.session_state:
    fleet = []
    hub_list, dest_list = list(PHARMA_HUBS.keys()), list(DESTINATIONS.keys())
    for i in range(15):
        origin, dest = hub_list[i % len(hub_list)], dest_list[i % len(dest_list)]
        path, total_km, total_hrs = get_road_route_data(PHARMA_HUBS[origin], DESTINATIONS[dest])
        
        prog_ratio = random.uniform(0.2, 0.8)
        pos_idx = int(len(path) * prog_ratio)
        dist_covered = round(total_km * prog_ratio, 1)
        hrs_driven = round(total_hrs * prog_ratio, 1)
        
        truck_pos = path[pos_idx]
        ambient_forecast = get_real_forecast(truck_pos[0], truck_pos[1])
        cargo_forecast = simulate_thermal_excursion(random.uniform(-9, -4), ambient_forecast)
        
        fleet.append({
            "id": f"IND-EXP-{1000+i}", "driver": DRIVERS[i],
            "origin": origin, "dest": dest, "pos": truck_pos, "path": path, 
            "total_km": total_km, "dist_covered": dist_covered, "dist_remaining": round(total_km - dist_covered, 1),
            "total_hrs": total_hrs, "hrs_driven": hrs_driven,
            "cargo_temp": cargo_forecast[0], "ambient_forecast": ambient_forecast, "cargo_forecast": cargo_forecast
        })
    st.session_state.fleet = fleet

# --- UI ---
st.title("❄️ PharmaGuard National Command Center")

tab1, tab2, tab3, tab4 = st.tabs(["🌐 National Fleet Map", "🌡️ Thermal Forecast", "📋 Manifest", "🛤️ Trip Planner"])

with tab1:
    # 1. TRUCK SELECTION (Needs to be at top of tab for Map to reflect selection)
    selected_id = st.selectbox("🎯 Select Truck for Live Intelligence (Highlights in Purple):", [t['id'] for t in st.session_state.fleet])
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    # 2. MAP COMPONENT
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    
    # Static Rescue Hubs
    for wh in WAREHOUSE_NETWORK:
        folium.CircleMarker([wh['lat'], wh['lon']], radius=2.5, color="#3498db", fill=True, popup=wh['name']).add_to(m)
    
    # Fleet Loop
    for t in st.session_state.fleet:
        is_selected = (t['id'] == selected_id)
        
        if is_selected:
            route_color = "#00FFFF"  # Cyan highlight
            weight = 6
            opacity = 1.0
            icon_color = "purple"
        else:
            route_color = "red" if t['cargo_temp'] > 0 else "green"
            weight = 2
            opacity = 0.2
            icon_color = "red" if t['cargo_temp'] > 0 else "green"
            
        folium.PolyLine(t['path'], color=route_color, weight=weight, opacity=opacity).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color=icon_color, icon="truck", prefix="fa"), tooltip=f"{t['id']}").add_to(m)
    
    st_folium(m, width="100%", height=500, key="main_map")
    
    # 3. SYSTEMATIC INTELLIGENCE DASHBOARD
    st.divider()
    nearest_hub_data = min(WAREHOUSE_NETWORK, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    hub_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], nearest_hub_data['lat'], nearest_hub_data['lon']), 1)

    st.markdown(f"### 📊 Systematic Intelligence: {selected_id}")
    
    row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
    row1_col1.metric("Driver", selected_truck['driver'])
    row1_col2.metric("Origin Node", selected_truck['origin'])
    row1_col3.metric("Destination Node", selected_truck['dest'])
    row1_col4.metric("Cargo Temp", f"{selected_truck['cargo_temp']}°C", delta="RISK" if selected_truck['cargo_temp'] > 0 else "STABLE")

    row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4)
    row2_col1.metric("Distance Covered", f"{selected_truck['dist_covered']} km")
    row2_col2.metric("Distance Remaining", f"{selected_truck['dist_remaining']} km", delta="-Remaining")
    row2_col3.metric("Total Driving Time", f"{selected_truck['hrs_driven']} hrs", f"Limit: {selected_truck['total_hrs']}h")
    
    with row2_col4:
        st.markdown(f"""
        <div style="background-color:#1e2130; padding:12px; border-radius:8px; border-left: 5px solid #00FFFF;">
            <p style="margin:0; font-size:0.7rem; color:#9ea0a9; text-transform:uppercase;">Nearest Rescue Hub</p>
            <p style="margin:0; font-size:1.1rem; font-weight:bold; color:#ffffff;">{nearest_hub_data['name']}</p>
            <p style="margin:0; font-size:0.9rem; color:#00FFFF;">{hub_dist} km away</p>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.subheader("Thermal Failure Simulation (-10°C to Ambient)")
    cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with cols[i % 3]:
            st.line_chart(pd.DataFrame({"Ambient": t['ambient_forecast'], "Cargo": t['cargo_forecast']}))

with tab3:
    st.dataframe(pd.DataFrame(st.session_state.fleet)[["id", "driver", "origin", "dest", "cargo_temp", "dist_covered", "dist_remaining"]])

with tab4:
    st.header("New Trip Route Audit")
    inp1, inp2, inp3 = st.columns([1,1,1])
    origin_sel = inp1.selectbox("Start Point:", list(PHARMA_HUBS.keys()))
    dest_sel = inp2.selectbox("Destination:", list(DESTINATIONS.keys()))
    radius_sel = inp3.slider("Search Buffer (km):", 10, 100, 40)
    
    if st.button("Generate Safety Audit"):
        path, dist_km, dur_hr = get_road_route_data(PHARMA_HUBS[origin_sel], DESTINATIONS[dest_sel])
        
        rescue_hubs = []
        for wh in WAREHOUSE_NETWORK:
            min_dev = min([haversine(wh['lat'], wh['lon'], pt[0], pt[1]) for pt in path[::10]])
            if min_dev <= radius_sel:
                rescue_hubs.append({"Hub": wh['name'], "Deviation": round(min_dev, 1), "lat": wh['lat'], "lon": wh['lon']})
        
        m_planner = folium.Map(location=PHARMA_HUBS[origin_sel], zoom_start=6, tiles="CartoDB dark_matter")
        folium.PolyLine(path, color="#3498db", weight=5).add_to(m_planner)
        for rh in rescue_hubs:
            folium.Marker([rh['lat'], rh['lon']], icon=folium.Icon(color="orange", icon="shield-heart", prefix="fa")).add_to(m_planner)
        
        st_folium(m_planner, width="100%", height=400, key="planner_map")
        st.table(pd.DataFrame(rescue_hubs).drop(columns=['lat', 'lon']))

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2862/2862410.png", width=80)
    st.title("PharmaGuard AI")
    st.caption(f"Sync: {datetime.now().strftime('%H:%M:%S')}")
