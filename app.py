import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import random
import requests
import polyline
import math

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="PharmaGuard AI | Focus Mode", page_icon="💊")

# --- DATASETS ---
PHARMA_HUBS = {
    "Baddi Hub": [30.9578, 76.7914], "Sikkim Cluster": [27.3314, 88.6138],
    "Ahmedabad": [23.0225, 72.5714], "Hyderabad": [17.4500, 78.6000],
    "Vizag City": [17.6868, 83.2185], "Goa Plant": [15.2993, 74.1240],
    "Indore SEZ": [22.7196, 75.8577], "Pune Bio": [18.5204, 73.8567]
}

DESTINATIONS = {
    "Mumbai Port": [18.9438, 72.8387], "Delhi Cargo": [28.5562, 77.1000],
    "Bangalore Dist": [12.9716, 77.5946], "Chennai Port": [13.0827, 80.2707],
    "Kolkata Port": [22.5726, 88.3639], "Guwahati Hub": [26.1445, 91.7362],
    "Cochin Port": [9.9312, 76.2673], "Lucknow Dist": [26.8467, 80.9462]
}

WAREHOUSE_NETWORK = [
    {"name": "Ambala-01", "lat": 30.3782, "lon": 76.7767}, {"name": "Jaipur-04", "lat": 26.9124, "lon": 75.7873},
    {"name": "Gwalior-09", "lat": 26.2183, "lon": 78.1828}, {"name": "Bhopal-Cold", "lat": 23.2599, "lon": 77.4126},
    {"name": "Nagpur-Central", "lat": 21.1458, "lon": 79.0882}, {"name": "Satara-Bio", "lat": 17.6805, "lon": 73.9803},
    {"name": "Belgaum-Rescue", "lat": 15.8497, "lon": 74.4977}, {"name": "Anantapur-Rescue", "lat": 14.6819, "lon": 77.6006},
    {"name": "Vijayawada-Bio", "lat": 16.5062, "lon": 80.6480}, {"name": "Varanasi-Vault", "lat": 25.3176, "lon": 82.9739},
    {"name": "Patna-Cold", "lat": 25.5941, "lon": 85.1376}, {"name": "Sambalpur-Safe", "lat": 21.4669, "lon": 83.9812}
]

DRIVERS = ["Amitav Ghosh", "S. Jaishankar", "K. Rathore", "Mohd. Salim", "Pritam Singh", "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor", "N. Chandran", "Arjun Kapur", "Deepak Punia", "Suresh Raina", "M. S. Dhoni", "Hardik Pandya"]

# --- HELPERS ---
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

# --- GENERATE DATA ---
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

# --- INTERACTION STATE ---
if 'selected_truck' not in st.session_state:
    st.session_state.selected_truck = None

# --- UI HEADER ---
st.title("🛡️ PharmaGuard National Command Center")

# --- EMERGENCY LOOKUP SECTION (PLACED ABOVE MAP FOR INTERACTION) ---
with st.container():
    st.subheader("🚨 Emergency Proximity & Rescue Lookup")
    c1, c2, c3 = st.columns([2, 1, 1])
    
    with c1:
        truck_options = ["--- Select a Truck ID to Inspect ---"] + [t['id'] for t in st.session_state.fleet]
        selection = st.selectbox("Search for Truck in Distress:", truck_options)
        
    with c2:
        if st.button("🔄 Reset to Global View", use_container_width=True):
            st.session_state.selected_truck = None
            st.rerun()
            
    if selection != "--- Select a Truck ID to Inspect ---":
        st.session_state.selected_truck = next(t for t in st.session_state.fleet if t['id'] == selection)

# --- MAP LOGIC ---
st.write("---")
view_col, data_col = st.columns([7, 3])

with view_col:
    # Set Map Center
    if st.session_state.selected_truck:
        center = st.session_state.selected_truck['pos']
        zoom = 7
    else:
        center = [22, 78]
        zoom = 5
        
    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB dark_matter")

    for t in st.session_state.fleet:
        is_selected = st.session_state.selected_truck and st.session_state.selected_truck['id'] == t['id']
        
        # Determine Visual Style
        if st.session_state.selected_truck and not is_selected:
            # Dim other routes
            color = "#333333"
            weight = 1
            opacity = 0.1
        else:
            # Highlight selected or show all normally
            color = "#ff4b4b" if t['cargo_temp'] > 8 else "#00ffcc"
            weight = 4 if is_selected else 2
            opacity = 1.0 if is_selected else 0.4
        
        folium.PolyLine(t['path'], color=color, weight=weight, opacity=opacity).add_to(m)

        # Marker for Truck
        if not st.session_state.selected_truck or is_selected:
            folium.Marker(
                t['pos'], 
                icon=folium.Icon(color="red" if t['cargo_temp'] > 8 else "green", icon="truck", prefix="fa"),
                popup=f"ID: {t['id']} | Temp: {t['cargo_temp']}°C"
            ).add_to(m)

        # If selected, show its nearest rescue point
        if is_selected:
            nearest_wh = t['backups'][0]
            folium.Marker(
                [nearest_wh['lat'], nearest_wh['lon']],
                icon=folium.Icon(color='orange', icon='medkit', prefix='fa'),
                popup=f"NEAREST RESCUE: {nearest_wh['name']}"
            ).add_to(m)
            # Draw rescue line
            folium.PolyLine([t['pos'], [nearest_wh['lat'], nearest_wh['lon']]], color="white", weight=3, dash_array='10').add_to(m)

    st_folium(m, width="100%", height=600, key="national_map")

with data_col:
    if st.session_state.selected_truck:
        t = st.session_state.selected_truck
        st.success(f"### Inspecting: {t['id']}")
        st.write(f"**Driver:** {t['driver']}")
        st.write(f"**Status:** {'🚨 TEMP EXCURSION' if t['cargo_temp'] > 8 else '✅ NORMAL'}")
        st.metric("Current Cargo Temp", f"{t['cargo_temp']}°C")
        st.metric("Driver Hours", f"{t['hours']}h")
        
        st.write("**Top 3 Backup Facilities:**")
        for b in t['backups'][:3]:
            st.info(f"🏥 {b['name']} - {b['dist']}km away")
            
        st.write("**Thermal Forecast:**")
        st.line_chart(t['forecast'])
    else:
        st.info("### Fleet Overview")
        st.write("Select a truck ID from the dropdown above to engage **Emergency Focus Mode.**")
        st.divider()
        st.metric("Total Fleet", "15 Units")
        st.metric("Active Excursions", f"{len([t for t in st.session_state.fleet if t['cargo_temp'] > 8])}")

# --- BOTTOM LOGISTICS TABLE ---
st.subheader("National Logistics Log")
df_data = [{
    "Truck": t['id'], "Origin": t['origin'], "Destination": t['dest'], 
    "Temp": f"{t['cargo_temp']}°C", "Driver": t['driver'], "Hours": t['hours']
} for t in st.session_state.fleet]
st.table(pd.DataFrame(df_data))
