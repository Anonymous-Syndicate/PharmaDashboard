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
    "Mumbai Port": [18.9438, 72.8387],
    "Delhi Air Cargo": [28.5562, 77.1000],
    "Bangalore Dist.": [12.9716, 77.5946],
    "Chennai Terminal": [13.0827, 80.2707],
    "Kolkata Port": [22.5726, 88.3639],
    "Guwahati Hub": [26.1445, 91.7362],
    "Cochin Port": [9.9312, 76.2673],
    "Chandigarh Dry Port": [30.7333, 76.7794],
    "Nagpur Hub": [21.1458, 79.0882],
    "Lucknow Logistics": [26.8467, 80.9462]
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

def find_backups_for_route(route_path, radius_km):
    found = []
    # Optimization: Only check every 10th point of the route to save processing
    sampled_route = route_path[::10] 
    for wh in WAREHOUSE_NETWORK:
        for point in sampled_route:
            dist = haversine(wh['lat'], wh['lon'], point[0], point[1])
            if dist <= radius_km:
                found.append({**wh, "dist_from_route": round(dist, 1)})
                break
    return found

# --- INITIALIZE FLEET DATA ---
if 'fleet' not in st.session_state:
    fleet = []
    hubs = list(PHARMA_HUBS.keys())
    dests = list(DESTINATIONS.keys())
    for i in range(15):
        origin, dest = hubs[i % len(hubs)], dests[i % len(dests)]
        path = get_road_route(PHARMA_HUBS[origin], DESTINATIONS[dest])
        pos = path[int(len(path)*0.5)]
        fleet.append({
            "id": f"IND-{100+i}", "origin": origin, "dest": dest, "pos": pos, "path": path,
            "cargo_temp": round(random.uniform(2, 9), 1), "hours": round(random.uniform(2, 12), 1)
        })
    st.session_state.fleet = fleet

# --- UI ---
st.title("❄️ PharmaGuard National Command Center")

tab1, tab2, tab3, tab4 = st.tabs([
    "🌐 Live National Map", 
    "📊 Fleet Status", 
    "📋 Dispatch Log", 
    "🛤️ Trip Planner & Safety Audit"
])

# --- TAB 1 & 2 & 3 (EXISTING LOGIC ABBREVIATED) ---
with tab1:
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    for t in st.session_state.fleet:
        color = "red" if t['cargo_temp'] > 8 else "green"
        folium.PolyLine(t['path'], color=color, weight=2, opacity=0.5).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color=color, icon="truck", prefix="fa")).add_to(m)
    st_folium(m, width="100%", height=500)

with tab2:
    st.write("Thermal and Fatigue KPI metrics go here...")

with tab3:
    st.dataframe(pd.DataFrame(st.session_state.fleet)[["id", "origin", "dest", "cargo_temp", "hours"]])

# --- NEW TAB 4: TRIP PLANNER ---
with tab4:
    st.header("Route Pre-Planning & Emergency Audit")
    st.markdown("Select a route to identify all cold-storage rescue points within a safety buffer.")
    
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        start_node = st.selectbox("Select Origin Hub", list(PHARMA_HUBS.keys()))
    with c2:
        end_node = st.selectbox("Select Destination Port", list(DESTINATIONS.keys()))
    with c3:
        radius = st.slider("Safety Radius (km)", 10, 100, 40)
    
    if st.button("Generate Safety Audit"):
        with st.spinner("Calculating route and scanning warehouse network..."):
            # 1. Get Route
            route = get_road_route(PHARMA_HUBS[start_node], DESTINATIONS[end_node])
            
            # 2. Find backups within 'X' km of the route
            backups = find_backups_for_route(route, radius)
            
            # 3. Layout Results
            res_left, res_right = st.columns([3, 2])
            
            with res_left:
                # Build Map
                plan_map = folium.Map(location=PHARMA_HUBS[start_node], zoom_start=6, tiles="CartoDB dark_matter")
                
                # Draw the Route
                folium.PolyLine(route, color="#3498db", weight=5, opacity=0.8, tooltip="Planned Path").add_to(plan_map)
                
                # Markers for Start and End
                folium.Marker(PHARMA_HUBS[start_node], icon=folium.Icon(color="blue", icon="play")).add_to(plan_map)
                folium.Marker(DESTINATIONS[end_node], icon=folium.Icon(color="black", icon="flag-checkered", prefix="fa")).add_to(plan_map)
                
                # Markers for found warehouses
                for b in backups:
                    folium.Marker(
                        [b['lat'], b['lon']],
                        tooltip=f"Backup: {b['name']}",
                        icon=folium.Icon(color="orange", icon="shield-virus", prefix="fa")
                    ).add_to(plan_map)
                    # Show the radius
                    folium.Circle([b['lat'], b['lon']], radius=radius*1000, color="white", weight=1, fill=True, opacity=0.1).add_to(plan_map)
                
                st_folium(plan_map, width="100%", height=600, key="audit_map")
                
            with res_right:
                st.subheader("Audit Summary")
                st.metric("Emergency Points Found", len(backups))
                
                if backups:
                    st.success(f"Route is secured. Found {len(backups)} facilities within {radius}km.")
                    df_backups = pd.DataFrame(backups).sort_values("dist_from_route")
                    st.table(df_backups[['name', 'dist_from_route']].rename(columns={
                        "name": "Facility Name", 
                        "dist_from_route": "Dist from Route (km)"
                    }))
                    
                    # Gap analysis
                    st.info("💡 **Gap Analysis:** Ensure driver has contact details for the nearest hub: " + backups[0]['name'])
                else:
                    st.error("⚠️ CRITICAL: No emergency warehouses found within the selected radius. Recommend route adjustment or increasing search radius.")

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2862/2862410.png", width=80)
    st.title("PharmaGuard AI")
    st.divider()
    st.caption("Active Regional Nodes: 28")
    st.caption("API Status: Connected (OSRM)")
