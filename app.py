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

# (Abbreviated Rescue Hubs list for performance - total 80 nodes)
WAREHOUSE_NETWORK = [
    {"name": "Leh-Vault", "lat": 34.1526, "lon": 77.5771}, {"name": "Srinagar-Cold", "lat": 34.0837, "lon": 74.7973},
    {"name": "Jaipur-Safe", "lat": 26.9124, "lon": 75.7873}, {"name": "Bhopal-Bio", "lat": 23.2599, "lon": 77.4126},
    {"name": "Guwahati-Apex", "lat": 26.1445, "lon": 91.7362}, {"name": "Kochi-South", "lat": 9.9312, "lon": 76.2673},
    {"name": "Lucknow-Safe", "lat": 26.8467, "lon": 80.9462}, {"name": "Nagpur-Central", "lat": 21.1458, "lon": 79.0882}
]
# Generate additional mock hubs to fill 80 for visual density
for i in range(72):
    WAREHOUSE_NETWORK.append({
        "name": f"Rescue-Node-{100+i}",
        "lat": random.uniform(8.5, 34.0),
        "lon": random.uniform(68.5, 95.0)
    })

DRIVERS = ["Amitav Ghosh", "S. Jaishankar", "K. Rathore", "Mohd. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor", "N. Chandran", "Arjun Kapur", "Deepak Punia", "Suresh Raina", "M. S. Dhoni", "Hardik Pandya"]

# --- FUNCTIONS ---
def get_road_route(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full"
    try:
        r = requests.get(url, timeout=3).json()
        return polyline.decode(r['routes'][0]['geometry']), round(r['routes'][0]['distance']/1000)
    except: 
        return [start, end], 500 # Fallback

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# --- INITIALIZE FLEET ---
if 'fleet' not in st.session_state:
    with st.spinner("Initializing National Command Center..."):
        fleet = []
        hub_names = list(PHARMA_HUBS.keys())
        dest_names = list(DESTINATIONS.keys())
        for i in range(15):
            o, d = hub_names[i % len(hub_names)], dest_names[i % len(dest_names)]
            path, dist = get_road_route(PHARMA_HUBS[o], DESTINATIONS[d])
            prog = random.uniform(0.3, 0.7)
            pos = path[int(len(path)*prog)]
            
            fleet.append({
                "id": f"IND-EXP-{1000+i}", "driver": DRIVERS[i],
                "origin": o, "dest": d, "pos": pos, "path": path,
                "total_km": dist, "dist_covered": round(dist * prog),
                "dist_rem": round(dist * (1-prog)), "hrs_driven": round(prog * 12, 1),
                "temp": round(random.uniform(-8, 2), 1),
                "forecast": [round(random.uniform(-8, 20), 1) for _ in range(8)]
            })
        st.session_state.fleet = fleet

# --- UI LAYOUT ---
st.title("❄️ PharmaGuard National Command Center")

tab1, tab2, tab3 = st.tabs(["🌐 Live Map", "🌡️ Thermal Forecasts", "🛤️ Trip Planner"])

with tab1:
    # Highlighting Logic
    truck_ids = [t['id'] for t in st.session_state.fleet]
    selected_id = st.selectbox("🎯 Select Truck for Live Intelligence:", truck_ids)
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

    # MAP
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    
    # Render Hubs
    for wh in WAREHOUSE_NETWORK:
        folium.CircleMarker([wh['lat'], wh['lon']], radius=2, color="#3498db", fill=True).add_to(m)

    # Render Trucks
    for t in st.session_state.fleet:
        is_sel = t['id'] == selected_id
        color = "#00FFFF" if is_sel else ("red" if t['temp'] > 0 else "green")
        folium.PolyLine(t['path'], color=color, weight=5 if is_sel else 1, opacity=0.8 if is_sel else 0.2).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color="purple" if is_sel else color, icon="truck", prefix="fa")).add_to(m)
    
    st_folium(m, width="100%", height=500, key="main_map")

    # SYSTEMATIC INTELLIGENCE
    st.markdown(f"### 📊 Systematic Intelligence: {selected_id}")
    col1, col2, col3, col4 = st.columns(4)
    
    # Nearest Hub Calculation
    n_hub = min(WAREHOUSE_NETWORK, key=lambda x: haversine(selected_truck['pos'][0], selected_truck['pos'][1], x['lat'], x['lon']))
    n_dist = round(haversine(selected_truck['pos'][0], selected_truck['pos'][1], n_hub['lat'], n_hub['lon']))

    col1.metric("Driver", selected_truck['driver'])
    col1.metric("Current Temp", f"{selected_truck['temp']}°C")
    
    col2.metric("Distance Covered", f"{selected_truck['dist_covered']} km")
    col2.metric("Distance Remaining", f"{selected_truck['dist_rem']} km")
    
    col3.metric("Time Driven", f"{selected_truck['hrs_driven']} hrs")
    col3.metric("Route", f"{selected_truck['origin'][:10]}...")

    col4.subheader("Nearest Rescue Hub")
    col4.info(f"**{n_hub['name']}**\n\nDistance: {n_dist} km")

with tab2:
    st.subheader("Thermal Forecasts (-10°C to Ambient)")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            st.write(f"**Truck {t['id']}**")
            st.line_chart(t['forecast'])

with tab3:
    st.header("Strategic Route Planner")
    p1, p2 = st.columns(2)
    start = p1.selectbox("Start Node", list(PHARMA_HUBS.keys()))
    end = p2.selectbox("End Node", list(DESTINATIONS.keys()))
    
    if st.button("Plan Trip"):
        route_path, route_dist = get_road_route(PHARMA_HUBS[start], DESTINATIONS[end])
        st.success(f"Estimated Distance: {route_dist} km")
        
        pm = folium.Map(location=PHARMA_HUBS[start], zoom_start=6, tiles="CartoDB dark_matter")
        folium.PolyLine(route_path, color="cyan", weight=4).add_to(pm)
        
        # Show nearby hubs
        found = 0
        for wh in WAREHOUSE_NETWORK:
            d = min([haversine(wh['lat'], wh['lon'], p[0], p[1]) for p in route_path[::20]])
            if d < 60:
                folium.Marker([wh['lat'], wh['lon']], icon=folium.Icon(color="orange", icon="shield-heart", prefix="fa")).add_to(pm)
                found += 1
        
        st_folium(pm, width="100%", height=400, key="planner_map")
        st.write(f"Rescue Hubs along route: {found}")

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2862/2862410.png", width=80)
    st.title("PharmaGuard AI")
    st.write(f"System Time: {datetime.now().strftime('%H:%M')}")
