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
    k = 0.12  # Heat transfer coefficient
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
        pos_idx = int(len(path) * random.uniform(0.2, 0.8))
        truck_pos = path[pos_idx]
        ambient_forecast = get_real_forecast(truck_pos[0], truck_pos[1])
        cargo_forecast = simulate_thermal_excursion(random.uniform(-9, -4), ambient_forecast)
        fleet.append({
            "id": f"IND-EXP-{1000+i}", "driver": DRIVERS[i], "origin": origin, "dest": dest,
            "pos": truck_pos, "path": path, "total_km": total_km,
            "cargo_temp": cargo_forecast[0], "ambient_forecast": ambient_forecast, "cargo_forecast": cargo_forecast
        })
    st.session_state.fleet = fleet

# --- UI ---
st.title("❄️ PharmaGuard National Command Center")

tab1, tab2, tab3, tab4 = st.tabs(["🌐 National Fleet Map", "🌡️ Real-Time Thermal Forecast", "📋 Manifest", "🛤️ Trip Safety Planner"])

with tab1:
    # 1. Map First
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    for wh in WAREHOUSE_NETWORK:
        folium.CircleMarker([wh['lat'], wh['lon']], radius=2.5, color="#3498db", fill=True, popup=wh['name']).add_to(m)
    
    for t in st.session_state.fleet:
        color = "red" if t['cargo_temp'] > 0 else "green"
        folium.PolyLine(t['path'], color=color, weight=2, opacity=0.3).add_to(m)
        folium.Marker(t['pos'], icon=folium.Icon(color=color, icon="truck", prefix="fa")).add_to(m)
    
    st_folium(m, width="100%", height=500, key="main_map")
    
    # 2. Controls Below Map
    st.divider()
    selected_id = st.selectbox("Select Truck to Inspect Details:", [t['id'] for t in st.session_state.fleet])
    selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)
    
    st.subheader(f"📊 Live Intelligence: {selected_id}")
    det1, det2, det3 = st.columns(3)
    det1.info(f"**Driver:** {selected_truck['driver']}\n\n**Origin:** {selected_truck['origin']}")
    det2.warning(f"**Route Destination:** {selected_truck['dest']}\n\n**Distance:** {selected_truck['total_km']} km")
    det3.metric("Cargo Temperature", f"{selected_truck['cargo_temp']}°C", delta="Thermal Risk" if selected_truck['cargo_temp'] > 0 else "Stable")

with tab2:
    st.subheader("Simulated Thermal Excursion (Sub-Zero to Ambient)")
    st.caption("Newtonian heating model based on live Open-Meteo weather data.")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            st.markdown(f"**Truck {t['id']}**")
            st.line_chart(pd.DataFrame({
                "Real Ambient": t['ambient_forecast'],
                "Simulated Cargo": t['cargo_forecast']
            }))

with tab3:
    st.dataframe(pd.DataFrame(st.session_state.fleet)[["id", "driver", "origin", "dest", "cargo_temp", "total_km"]], use_container_width=True)

with tab4:
    st.header("New Trip Route Audit")
    inp1, inp2, inp3 = st.columns([1,1,1])
    origin_sel = inp1.selectbox("Start Point:", list(PHARMA_HUBS.keys()))
    dest_sel = inp2.selectbox("Destination:", list(DESTINATIONS.keys()))
    radius_sel = inp3.slider("Search Buffer (km):", 10, 100, 40)
    
    if st.button("Generate Safety Audit"):
        path, dist_km, dur_hr = get_road_route_data(PHARMA_HUBS[origin_sel], DESTINATIONS[dest_sel])
        
        # UI Metrics
        st.success(f"Path Verified: {dist_km} km | Approx. Time: {dur_hr} hrs")
        
        # Logic to find hubs
        rescue_hubs = []
        sampled_path = path[::10]
        for wh in WAREHOUSE_NETWORK:
            min_dev = 999
            closest_idx = 0
            for i, pt in enumerate(sampled_path):
                d = haversine(wh['lat'], wh['lon'], pt[0], pt[1])
                if d < min_dev:
                    min_dev = d
                    closest_idx = i
            
            if min_dev <= radius_sel:
                km_mark = round(closest_idx * (dist_km / len(sampled_path)), 1)
                rescue_hubs.append({"Hub": wh['name'], "Location (KM Mark)": km_mark, "Deviation (KM)": round(min_dev, 1), "lat": wh['lat'], "lon": wh['lon']})
        
        # Map Display
        m_planner = folium.Map(location=PHARMA_HUBS[origin_sel], zoom_start=6, tiles="CartoDB dark_matter")
        folium.PolyLine(path, color="#3498db", weight=5, opacity=0.8).add_to(m_planner)
        folium.Marker(PHARMA_HUBS[origin_sel], icon=folium.Icon(color="blue", icon="play")).add_to(m_planner)
        folium.Marker(DESTINATIONS[dest_sel], icon=folium.Icon(color="black", icon="flag-checkered", prefix="fa")).add_to(m_planner)
        
        for rh in rescue_hubs:
            folium.Marker(
                [rh['lat'], rh['lon']], 
                icon=folium.Icon(color="orange", icon="shield-heart", prefix="fa"),
                popup=f"{rh['Hub']} - {rh['Deviation (KM)']}km off route"
            ).add_to(m_planner)
        
        st_folium(m_planner, width="100%", height=500, key="planner_map")
        
        # Results Table
        st.write(f"**Safety Network:** {len(rescue_hubs)} Rescue points found.")
        st.table(pd.DataFrame(rescue_hubs).drop(columns=['lat', 'lon']).sort_values("Location (KM Mark)"))

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2862/2862410.png", width=80)
    st.title("PharmaGuard AI")
    st.caption(f"Network Status: Active | {datetime.now().year}")
