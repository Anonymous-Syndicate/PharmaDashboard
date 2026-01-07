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

# --- GENERATE 15 ROUTES ---
if 'fleet' not in st.session_state:
    fleet = []
    # Mix of random hubs and destinations
    hub_list = list(PHARMA_HUBS.keys())
    dest_list = list(DESTINATIONS.keys())
    
    for i in range(15):
        origin = hub_list[i % len(hub_list)]
        dest = dest_list[i % len(dest_list)]
        path = get_road_route(PHARMA_HUBS[origin], DESTINATIONS[dest])
        
        pos_idx = int(len(path) * random.uniform(0.2, 0.8))
        truck_pos = path[pos_idx]
        
        # 7-12 Backup Warehouses
        backups = sorted([ {**wh, "dist": round(haversine(truck_pos[0], truck_pos[1], wh['lat'], wh['lon']))} for wh in WAREHOUSE_NETWORK ], key=lambda x: x['dist'])[:10]
        
        fleet.append({
            "id": f"IND-EXP-{1000+i}",
            "driver": DRIVERS[i],
            "hours": round(random.uniform(1, 14), 1),
            "origin": origin,
            "dest": dest,
            "pos": truck_pos,
            "path": path,
            "cargo_temp": round(random.uniform(2.2, 9.5), 1),
            "ambient_temp": round(random.uniform(28, 42), 1),
            "backups": backups,
            "forecast": [round(random.uniform(28, 40), 1) for _ in range(8)]
        })
    st.session_state.fleet = fleet

# --- UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .metric-card { background-color: #1e2130; padding: 20px; border-radius: 10px; border: 1px solid #3e4251; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2862/2862410.png", width=100)
    st.title("PharmaGuard AI")
    st.info("System Status: Operational")
    search = st.text_input("Search Truck ID (e.g. IND-EXP-1005)")
    st.write("---")
    st.caption("v4.0.2 National Network")

# --- TOP ROW: KPI COMMAND CENTER ---
st.title("📦 National Cold-Chain Command Center")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
total_alerts = len([t for t in st.session_state.fleet if t['cargo_temp'] > 8 or t['hours'] > 9])

with kpi1: st.metric("Active Fleet", "15 Trucks", "National")
with kpi2: st.metric("Thermal Excursions", f"{len([t for t in st.session_state.fleet if t['cargo_temp'] > 8])}", "-2", delta_color="inverse")
with kpi3: st.metric("Fatigue Alerts", f"{len([t for t in st.session_state.fleet if t['hours'] > 9])}", "Driver Safety")
with kpi4: st.metric("Network Coverage", "28 Rescue Hubs", "98% Efficiency")

# --- MAIN TABS ---
tab1, tab2, tab3 = st.tabs(["🌐 Live National Map", "🌡️ Thermal Forecasting", "📋 Fleet Manifest"])

with tab1:
    m = folium.Map(location=[22, 78], zoom_start=5, tiles="CartoDB dark_matter")
    for t in st.session_state.fleet:
        # Route color logic
        route_color = "#e74c3c" if (t['cargo_temp'] > 8 or t['hours'] > 9) else "#2ecc71"
        
        # Path
        folium.PolyLine(t['path'], color=route_color, weight=2, opacity=0.4).add_to(m)
        
        # Rescue Warehouses (Yellow Dots)
        for b in t['backups']:
            folium.CircleMarker([b['lat'], b['lon']], radius=2, color='orange', fill=True, opacity=0.3).add_to(m)
        
        # Truck Marker
        folium.Marker(
            t['pos'], 
            icon=folium.Icon(color="red" if route_color == "#e74c3c" else "green", icon="truck", prefix="fa"),
            popup=f"<b>{t['id']}</b><br>Driver: {t['driver']}<br>Temp: {t['cargo_temp']}°C"
        ).add_to(m)
    
    st_folium(m, width="100%", height=600)

with tab2:
    st.subheader("Predictive Thermal Analysis (Next 8 Hours)")
    f_cols = st.columns(3)
    for i, t in enumerate(st.session_state.fleet):
        with f_cols[i % 3]:
            with st.container():
                st.markdown(f"**Truck {t['id']}** ({t['origin']} → {t['dest']})")
                st.line_chart(t['forecast'], height=150)
                st.caption(f"Ambient Forecast Avg: {sum(t['forecast'])/8:.1f}°C")

with tab3:
    st.subheader("Driver Compliance & Logistics Log")
    log_data = []
    for t in st.session_state.fleet:
        log_data.append({
            "Truck ID": t['id'],
            "Driver": t['driver'],
            "Driving Time": f"{t['hours']}h",
            "Route": f"{t['origin']} ➔ {t['dest']}",
            "Cargo Temp": f"{t['cargo_temp']}°C",
            "Status": "🚨 ALERT" if (t['cargo_temp'] > 8 or t['hours'] > 9) else "✅ OK",
            "Rescue Hubs": f"{len(t['backups'])} Available"
        })
    df = pd.DataFrame(log_data)
    
    def color_status(val):
        color = '#ff4b4b' if val == "🚨 ALERT" else '#00cc66'
        return f'background-color: {color}; color: white; font-weight: bold'

    st.table(df.style.applymap(color_status, subset=['Status']))

# --- BOTTOM SECTION: EMERGENCY LOOKUP ---
st.divider()
st.subheader("Emergency Warehouse Proximity Lookup")
selected_id = st.selectbox("Select Truck to view Backup Facilities:", [t['id'] for t in st.session_state.fleet])
selected_truck = next(t for t in st.session_state.fleet if t['id'] == selected_id)

c1, c2 = st.columns([1, 2])
with c1:
    st.write(f"**Driver:** {selected_truck['driver']}")
    st.write(f"**Hours Logged:** {selected_truck['hours']}h")
    if selected_truck['hours'] > 9: st.warning("Fatigue Protocol: Suggest Immediate Stop")
with c2:
    st.info(f"The following 10 cold-storage units are pre-assigned to this route. Nearest: **{selected_truck['backups'][0]['name']}**")
    st.write(", ".join([f"{b['name']} ({b['dist']}km)" for b in selected_truck['backups']]))
