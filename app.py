import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random
import requests
import polyline
import math

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="PharmaGuard | National Command Center", page_icon="❄️")

# --- EXPANDED NATIONAL DATASETS ---
PHARMA_HUBS = {
    "Baddi Hub (North)": [30.9578, 76.7914],
    "Sikkim Cluster (East)": [27.3314, 88.6138],
    "Ahmedabad (West)": [23.0225, 72.5714],
    "Hyderabad (South)": [17.4500, 78.6000],
    "Vizag Pharma City": [17.6868, 83.2185],
    "Goa Manufacturing": [15.2993, 74.1240],
    "Indore SEZ": [22.7196, 75.8577],
    "Pune Bio-Cluster": [18.5204, 73.8567]
}

DESTINATIONS = {
    "Mumbai Port": [18.9438, 72.8387], "Delhi Air Cargo": [28.5562, 77.1000],
    "Bangalore Dist.": [12.9716, 77.5946], "Chennai Terminal": [13.0827, 80.2707],
    "Kolkata Port": [22.5726, 88.3639], "Guwahati Hub": [26.1445, 91.7362],
    "Cochin Port": [9.9312, 76.2673], "Chandigarh Dry Port": [30.7333, 76.7794],
    "Nagpur Hub": [21.1458, 79.0882], "Lucknow Logistics": [26.8467, 80.9462]
}

# --- MASSIVELY EXPANDED WAREHOUSE NETWORK (50+ NODES) ---
WAREHOUSE_NETWORK = [
    {"name": "Ambala-01", "lat": 30.3782, "lon": 76.7767}, {"name": "Jaipur-Safe", "lat": 26.9124, "lon": 75.7873},
    {"name": "Udaipur-Vault", "lat": 24.5854, "lon": 73.7125}, {"name": "Gwalior-Cold", "lat": 26.2183, "lon": 78.1828},
    {"name": "Jhansi-Hub", "lat": 25.4484, "lon": 78.5685}, {"name": "Bhopal-Bio", "lat": 23.2599, "lon": 77.4126},
    {"name": "Jabalpur-Central", "lat": 23.1815, "lon": 79.9864}, {"name": "Raipur-Rescue", "lat": 21.2514, "lon": 81.6296},
    {"name": "Nagpur-Apex", "lat": 21.1458, "lon": 79.0882}, {"name": "Akola-Vault", "lat": 20.7002, "lon": 77.0082},
    {"name": "Aurangabad-Pharma", "lat": 19.8762, "lon": 75.3433}, {"name": "Satara-Cold", "lat": 17.6805, "lon": 73.9803},
    {"name": "Belgaum-Rescue", "lat": 15.8497, "lon": 74.4977}, {"name": "Hubli-Safe", "lat": 15.3647, "lon": 75.1240},
    {"name": "Davangere-Chill", "lat": 14.4644, "lon": 75.9218}, {"name": "Tumkur-Apex", "lat": 13.3392, "lon": 77.1140},
    {"name": "Anantapur-Rescue", "lat": 14.6819, "lon": 77.6006}, {"name": "Kurnool-Vault", "lat": 15.8281, "lon": 78.0373},
    {"name": "Warangal-Apex", "lat": 17.9689, "lon": 79.5941}, {"name": "Vijayawada-Bio", "lat": 16.5062, "lon": 80.6480},
    {"name": "Nellore-Cold", "lat": 14.4426, "lon": 79.9865}, {"name": "Salem-Rescue", "lat": 11.6643, "lon": 78.1460},
    {"name": "Madurai-Vault", "lat": 9.9252, "lon": 78.1198}, {"name": "Varanasi-Safe", "lat": 25.3176, "lon": 82.9739},
    {"name": "Patna-Bio", "lat": 25.5941, "lon": 85.1376}, {"name": "Ranchi-Apex", "lat": 23.3441, "lon": 85.3094},
    {"name": "Bhubaneswar-Cold", "lat": 20.2961, "lon": 85.8245}, {"name": "Sambalpur-Vault", "lat": 21.4669, "lon": 83.9812},
    {"name": "Ludhiana-North", "lat": 30.9010, "lon": 75.8573}, {"name": "Dehradun-Hill", "lat": 30.3165, "lon": 78.0322},
    {"name": "Agra-Logistics", "lat": 27.1767, "lon": 78.0081}, {"name": "Kanpur-Central", "lat": 26.4499, "lon": 80.3319},
    {"name": "Siliguri-Gateway", "lat": 26.7271, "lon": 88.3953}, {"name": "Shillong-East", "lat": 25.5788, "lon": 91.8933},
    {"name": "Agartala-Vault", "lat": 23.8315, "lon": 91.2868}, {"name": "Haldia-Port-Side", "lat": 22.0667, "lon": 88.0698},
    {"name": "Visakhapatnam-Pharma", "lat": 17.6868, "lon": 83.2185}, {"name": "Tirupati-Rescue", "lat": 13.6285, "lon": 79.4192},
    {"name": "Coimbatore-Bio", "lat": 11.0168, "lon": 76.9558}, {"name": "Kochi-South", "lat": 9.9312, "lon": 76.2673},
    {"name": "Mangalore-Vault", "lat": 12.9141, "lon": 74.8560}, {"name": "Panaji-Safe", "lat": 15.4909, "lon": 73.8278},
    {"name": "Nashik-Apex", "lat": 19.9975, "lon": 73.7898}, {"name": "Surat-West", "lat": 21.1702, "lon": 72.8311},
    {"name": "Rajkot-Vault", "lat": 22.3039, "lon": 70.8022}, {"name": "Jodhpur-Dry", "lat": 26.2389, "lon": 73.0243},
    {"name": "Bikaner-Cold", "lat": 28.0229, "lon": 73.3119}, {"name": "Rohtak-Rescue", "lat": 28.8955, "lon": 76.6066},
    {"name": "Asansol-Hub", "lat": 23.6739, "lon": 86.9524}, {"name": "Kollam-Cold", "lat": 8.8932, "lon": 76.6141}
]

DRIVERS = ["Amitav Ghosh", "S. Jaishankar", "K. Rathore", "Mohd. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor", "N. Chandran", "Arjun Kapur", "Deepak Punia", "Suresh Raina", "M. S. Dhoni", "Hardik Pandya"]

# --- FUNCTIONS ---
def get_road_route(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full"
    try:
        r = requests.get(url, timeout=5).json()
        return polyline.decode(r['routes'][0]['geometry'])
    except: return [start, end]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def find_warehouses_along_route(path_coords, radius_km):
    nearby = []
    sampled_path = path_coords[::10] # Efficiency
    for wh in WAREHOUSE_NETWORK:
        min_dist = float('inf')
        for point in sampled_path:
            dist = haversine(wh['lat'], wh['lon'], point[0], point[1])
            if dist < min_dist: min_dist = dist
        if min_dist <= radius_km:
            nearby.append({**wh, "deviation_km": round(min_dist, 1)})
    return nearby

# --- SESSION STATE INITIALIZATION ---
if 'fleet' not in st.session_state:
    fleet = []
    hub_list, dest_list = list(PHARMA_HUBS.keys()), list(DESTINATIONS.keys())
    for i in range(15):
        origin, dest = hub_list[i % len(hub_list)], dest_list[i % len(dest_list)]
        path = get_road_route(PHARMA_HUBS[origin], DESTINATIONS[dest])
        pos_idx = int(len(path) * random.uniform(0.2, 0.8))
        truck_pos = path[pos_idx]
        
        # Recalibrated logic for -10C to 5C
        cargo_temp = round(random.uniform(-9.0, 4.5), 1)
        forecast = [round(random.uniform(-9.8, 4.8), 1) for _ in range(8)]
        
        backups = sorted([ {**wh, "dist": round(haversine(truck_pos[0], truck_pos[1], wh['lat'], wh['lon']))} for wh in WAREHOUSE_NETWORK ], key=lambda x: x['dist'])[:12]
        
        fleet.append({
            "id": f"IND-EXP-{1000+i}", "driver": DRIVERS[i], "hours": round(random.uniform(1, 14), 1),
            "origin": origin, "dest": dest, "pos": truck_pos, "path": path,
            "cargo_temp": cargo_temp, "backups": backups, "forecast": forecast
        })
    st.session_state.fleet = fleet

# --- UI STYLING ---
st.markdown("<style>.main { background-color: #0e1117; }</style>", unsafe_allow_html=True)

# --- HEADER ---
st.title("❄️ PharmaGuard National Command Center")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
# Alerts: Logic updated to flag if temp goes above 5C or below -10C
thermal_alerts = len([t for t in st.session_state.fleet if t['cargo_temp'] > 5 or t['cargo_temp'] < -10])

with kpi1: st.metric("Active Fleet", "15 Trucks")
with kpi2: st.metric("Thermal Excursions", thermal_alerts, delta="Ultra-Cold Chain", delta_color="inverse")
with kpi3: st.metric("Rescue Network", f"{len(WAREHOUSE_NETWORK)} Hubs")
with kpi4: st.metric("Safety Standard", "-10°C to 5°C")

# --- MAIN TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🌐 National Fleet Map", "🌡️ -10°C to 5°C Forecasting", "📋 Fleet Manifest", "🛤️ Trip Safety Planner"])

with tab1:
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    for t in st.session_state.fleet:
        # Update alert color logic for new range
        route_color = "#e74c3c" if (t['cargo_temp'] > 5 or t['cargo_temp'] < -10 or t['hours'] > 9) else "#2ecc71"
        folium.PolyLine(t['path'], color=route_color, weight=2, opacity=0.4).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color="red" if route_color == "#e74c3c" else "green", icon="truck", prefix="fa")).add_to(m)
    st_folium(m, width="100%", height=600, key="main_map")

with tab2:
    st.subheader("Sub-Zero Predictive Analysis (8hr Window)")
    st.caption("Standard Range: -10°C (Min) to 5°C (Max)")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            st.markdown(f"**Truck {t['id']}**")
            # Create a dataframe for the line chart to show the target range
            chart_data = pd.DataFrame({
                "Forecasted Temp": t['forecast'],
                "Upper Limit (5°C)": [5.0] * 8,
                "Lower Limit (-10°C)": [-10.0] * 8
            })
            st.line_chart(chart_data)

with tab3:
    st.subheader("Compliance Manifest")
    log_data = []
    for t in st.session_state.fleet:
        status = "✅ STABLE"
        if t['cargo_temp'] > 5: status = "🚨 OVERHEAT"
        if t['cargo_temp'] < -10: status = "🚨 CRITICAL COLD"
        if t['hours'] > 9: status = "⚠️ FATIGUE"
        
        log_data.append({
            "Truck ID": t['id'], "Driver": t['driver'], "Current Temp": f"{t['cargo_temp']}°C",
            "Route": f"{t['origin']} ➔ {t['dest']}", "Status": status
        })
    st.table(pd.DataFrame(log_data))

with tab4:
    st.header("Pre-Trip Route Safety Audit")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: ori = st.selectbox("Origin Hub:", list(PHARMA_HUBS.keys()))
    with c2: des = st.selectbox("Destination:", list(DESTINATIONS.keys()))
    with c3: rad = st.slider("Rescue Buffer (km):", 10, 150, 60)

    if st.button("Generate Audit"):
        path = get_road_route(PHARMA_HUBS[ori], DESTINATIONS[des])
        rescuers = find_warehouses_along_route(path, rad)
        
        col_m, col_t = st.columns([2, 1])
        with col_m:
            pm = folium.Map(location=PHARMA_HUBS[ori], zoom_start=6, tiles="CartoDB dark_matter")
            folium.PolyLine(path, color="#3498db", weight=4).add_to(pm)
            for r in rescuers:
                folium.Marker([r['lat'], r['lon']], icon=folium.Icon(color="orange", icon="shield-heart", prefix="fa"), 
                              popup=f"{r['name']} ({r['deviation_km']}km)").add_to(pm)
            st_folium(pm, width="100%", height=500, key="plan_map")
        with col_t:
            st.metric("Rescue Hubs Found", len(rescuers))
            st.dataframe(pd.DataFrame(rescuers)[['name', 'deviation_km']].rename(columns={"name": "Hub", "deviation_km": "Dist (km)"}), hide_index=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2862/2862410.png", width=80)
    st.title("PharmaGuard AI")
    st.info("Operating in Ultra-Cold Mode (-10°C to 5°C)")
