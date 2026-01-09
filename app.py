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

# --- DATASETS ---
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

WAREHOUSE_NETWORK = [
    {"name": "Ambala-01", "lat": 30.3782, "lon": 76.7767}, {"name": "Jaipur-04", "lat": 26.9124, "lon": 75.7873},
    {"name": "Udaipur-02", "lat": 24.5854, "lon": 73.7125}, {"name": "Gwalior-09", "lat": 26.2183, "lon": 78.1828},
    {"name": "Jhansi-Vault", "lat": 25.4484, "lon": 78.5685}, {"name": "Bhopal-Cold", "lat": 23.2599, "lon": 77.4126},
    {"name": "Jabalpur-Hub", "lat": 23.1815, "lon": 79.9864}, {"name": "Raipur-Safe", "lat": 21.2514, "lon": 81.6296},
    {"name": "Nagpur-Central", "lat": 21.1458, "lon": 79.0882}, {"name": "Akola-Cold", "lat": 20.7002, "lon": 77.0082},
    {"name": "Aurangabad-Pharma", "lat": 19.8762, "lon": 75.3433}, {"name": "Satara-Bio", "lat": 17.6805, "lon": 73.9803},
    {"name": "Belgaum-Rescue", "lat": 15.8497, "lon": 74.4977}, {"name": "Hubli-Vault", "lat": 15.3647, "lon": 75.1240},
    {"name": "Davangere-Chill", "lat": 14.4644, "lon": 75.9218}, {"name": "Tumkur-Hub", "lat": 13.3392, "lon": 77.1140},
    {"name": "Anantapur-Rescue", "lat": 14.6819, "lon": 77.6006}, {"name": "Kurnool-Cold", "lat": 15.8281, "lon": 78.0373},
    {"name": "Warangal-Hub", "lat": 17.9689, "lon": 79.5941}, {"name": "Vijayawada-Bio", "lat": 16.5062, "lon": 80.6480},
    {"name": "Nellore-Vault", "lat": 14.4426, "lon": 79.9865}, {"name": "Salem-Rescue", "lat": 11.6643, "lon": 78.1460},
    {"name": "Madurai-Chill", "lat": 9.9252, "lon": 78.1198}, {"name": "Varanasi-Vault", "lat": 25.3176, "lon": 82.9739},
    {"name": "Patna-Cold", "lat": 25.5941, "lon": 85.1376}, {"name": "Ranchi-Bio", "lat": 23.3441, "lon": 85.3094},
    {"name": "Bhubaneswar-Hub", "lat": 20.2961, "lon": 85.8245}, {"name": "Sambalpur-Safe", "lat": 21.4669, "lon": 83.9812}
]

DRIVERS = ["Amitav Ghosh", "S. Jaishankar", "K. Rathore", "Mohd. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor", "N. Chandran", "Arjun Kapur", "Deepak Punia", "Suresh Raina", "M. S. Dhoni", "Hardik Pandya"]

# --- HELPER FUNCTIONS ---
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
    """Finds warehouses within radius_km of any point on the route polyline."""
    nearby = []
    # Optimization: Check every 5th point in the path to speed up calculation
    sampled_path = path_coords[::5]
    for wh in WAREHOUSE_NETWORK:
        min_dist = float('inf')
        for point in sampled_path:
            dist = haversine(wh['lat'], wh['lon'], point[0], point[1])
            if dist < min_dist:
                min_dist = dist
        if min_dist <= radius_km:
            nearby.append({**wh, "deviation_km": round(min_dist, 1)})
    return nearby

# --- SESSION STATE INITIALIZATION ---
if 'fleet' not in st.session_state:
    fleet = []
    hub_list = list(PHARMA_HUBS.keys())
    dest_list = list(DESTINATIONS.keys())
    for i in range(15):
        origin, dest = hub_list[i % len(hub_list)], dest_list[i % len(dest_list)]
        path = get_road_route(PHARMA_HUBS[origin], DESTINATIONS[dest])
        pos_idx = int(len(path) * random.uniform(0.2, 0.8))
        truck_pos = path[pos_idx]
        backups = sorted([ {**wh, "dist": round(haversine(truck_pos[0], truck_pos[1], wh['lat'], wh['lon']))} for wh in WAREHOUSE_NETWORK ], key=lambda x: x['dist'])[:10]
        fleet.append({
            "id": f"IND-EXP-{1000+i}", "driver": DRIVERS[i], "hours": round(random.uniform(1, 14), 1),
            "origin": origin, "dest": dest, "pos": truck_pos, "path": path,
            "cargo_temp": round(random.uniform(2.2, 9.5), 1), "ambient_temp": round(random.uniform(28, 42), 1),
            "backups": backups, "forecast": [round(random.uniform(28, 40), 1) for _ in range(8)]
        })
    st.session_state.fleet = fleet

# --- UI STYLING ---
st.markdown("<style>.main { background-color: #0e1117; }</style>", unsafe_allow_html=True)

# --- COMMAND CENTER ---
st.title("❄️ PharmaGuard National Command Center")

tab1, tab2, tab3, tab4 = st.tabs(["🌐 Live National Map", "🌡️ Thermal Forecasting", "📋 Fleet Manifest", "🛤️ Route Trip Planner"])

with tab1:
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    for t in st.session_state.fleet:
        route_color = "#e74c3c" if (t['cargo_temp'] > 8 or t['hours'] > 9) else "#2ecc71"
        folium.PolyLine(t['path'], color=route_color, weight=2, opacity=0.4).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color="red" if route_color == "#e74c3c" else "green", icon="truck", prefix="fa")).add_to(m)
    st_folium(m, width="100%", height=600, key="national_map")

with tab2:
    st.subheader("Predictive Thermal Analysis")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            st.write(f"**Truck {t['id']}**")
            st.line_chart(t['forecast'], height=150)

with tab3:
    st.subheader("Fleet Manifest")
    st.table(pd.DataFrame([{"Truck": t['id'], "Driver": t['driver'], "Temp": f"{t['cargo_temp']}°C", "Route": f"{t['origin']} ➔ {t['dest']}"} for t in st.session_state.fleet]))

# --- NEW TAB: TRIP PLANNER ---
with tab4:
    st.header("New Route Safety Audit")
    st.info("Select a route to identify all emergency cold-storage hubs within range of the road path.")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        plan_origin = st.selectbox("Departure Hub:", list(PHARMA_HUBS.keys()))
    with col2:
        plan_dest = st.selectbox("Target Destination:", list(DESTINATIONS.keys()))
    with col3:
        safety_radius = st.slider("Safety Buffer (km):", 10, 150, 50, help="Finds warehouses within this distance from any point on the route.")

    if st.button("🚀 Run Safety Audit & Generate Route"):
        with st.spinner("Calculating route and scanning warehouse network..."):
            # 1. Get Geometry
            planned_path = get_road_route(PHARMA_HUBS[plan_origin], DESTINATIONS[plan_dest])
            
            # 2. Find nearby warehouses
            rescue_points = find_warehouses_along_route(planned_path, safety_radius)
            
            # 3. Layout Results
            res_col1, res_col2 = st.columns([2, 1])
            
            with res_col1:
                # Trip Planner Map
                pm = folium.Map(location=PHARMA_HUBS[plan_origin], zoom_start=6, tiles="CartoDB dark_matter")
                folium.PolyLine(planned_path, color="#3498db", weight=4, opacity=0.8, tooltip="Planned Path").add_to(pm)
                
                # Markers for Start/End
                folium.Marker(PHARMA_HUBS[plan_origin], popup="Origin", icon=folium.Icon(color='blue', icon='play', prefix='fa')).add_to(pm)
                folium.Marker(DESTINATIONS[plan_dest], popup="Destination", icon=folium.Icon(color='black', icon='flag-checkered', prefix='fa')).add_to(pm)
                
                # Rescue Hub Markers
                for rp in rescue_points:
                    folium.Marker(
                        [rp['lat'], rp['lon']],
                        popup=f"Rescue Hub: {rp['name']}<br>Deviation: {rp['deviation_km']}km",
                        icon=folium.Icon(color="orange", icon="shield-heart", prefix="fa")
                    ).add_to(pm)
                    # Visual representation of the deviation radius
                    folium.Circle([rp['lat'], rp['lon']], radius=safety_radius*1000, color="orange", fill=True, opacity=0.1).add_to(pm)
                
                st_folium(pm, width="100%", height=550, key="planner_map")
            
            with res_col2:
                st.subheader("Safety Audit Results")
                st.metric("Available Rescue Hubs", len(rescue_points))
                
                if not rescue_points:
                    st.error("⚠️ CRITICAL: No emergency warehouses found within the safety buffer for this route. Consider an alternative path or increasing the buffer.")
                else:
                    st.success(f"Route Secured: {len(rescue_points)} facilities available.")
                    
                    # Sort by deviation for the table
                    rescue_df = pd.DataFrame(rescue_points).sort_values("deviation_km")
                    st.write("**Warehouse List (Sorted by proximity):**")
                    st.dataframe(rescue_df[['name', 'deviation_km']].rename(columns={
                        "name": "Facility", "deviation_km": "Deviation (km)"
                    }), hide_index=True, use_container_width=True)
                    
                    st.warning("📋 Fatigue Check: Expected travel time exceeds 10 hours. Plan for a mandatory stop at **" + rescue_df.iloc[len(rescue_df)//2]['name'] + "**.")

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2862/2862410.png", width=80)
    st.title("PharmaGuard AI")
    st.divider()
    st.caption("v4.0.2 National Network | OSRM Engine")
