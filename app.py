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

# --- NATIONAL HUB DATASETS ---
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

# --- 80 STRATEGIC RESCUE HUBS ACROSS INDIA ---
WAREHOUSE_NETWORK = [
    # North India (15)
    {"name": "Leh-Vault", "lat": 34.1526, "lon": 77.5771}, {"name": "Srinagar-Cold", "lat": 34.0837, "lon": 74.7973},
    {"name": "Jammu-Apex", "lat": 32.7266, "lon": 74.8570}, {"name": "Amritsar-Safe", "lat": 31.6340, "lon": 74.8723},
    {"name": "Ludhiana-Hub", "lat": 30.9010, "lon": 75.8573}, {"name": "Shimla-Rescue", "lat": 31.1048, "lon": 77.1734},
    {"name": "Ambala-North", "lat": 30.3782, "lon": 76.7767}, {"name": "Rohtak-Vault", "lat": 28.8955, "lon": 76.6066},
    {"name": "Gurgaon-Central", "lat": 28.4595, "lon": 77.0266}, {"name": "Dehradun-Chill", "lat": 30.3165, "lon": 78.0322},
    {"name": "Agra-Vault", "lat": 27.1767, "lon": 78.0081}, {"name": "Meerut-Safe", "lat": 28.9845, "lon": 77.7064},
    {"name": "Bareilly-Bio", "lat": 28.3670, "lon": 79.4304}, {"name": "Gorakhpur-Apex", "lat": 26.7606, "lon": 83.3731},
    {"name": "Varanasi-Vault", "lat": 25.3176, "lon": 82.9739},
    # West India (15)
    {"name": "Jaipur-Safe", "lat": 26.9124, "lon": 75.7873}, {"name": "Jodhpur-Dry", "lat": 26.2389, "lon": 73.0243},
    {"name": "Bikaner-Cold", "lat": 28.0229, "lon": 73.3119}, {"name": "Udaipur-Vault", "lat": 24.5854, "lon": 73.7125},
    {"name": "Gandhinagar-Bio", "lat": 23.2156, "lon": 72.6369}, {"name": "Rajkot-Vault", "lat": 22.3039, "lon": 70.8022},
    {"name": "Surat-West", "lat": 21.1702, "lon": 72.8311}, {"name": "Nashik-Apex", "lat": 19.9975, "lon": 73.7898},
    {"name": "Aurangabad-Safe", "lat": 19.8762, "lon": 75.3433}, {"name": "Thane-Hub", "lat": 19.2183, "lon": 72.9781},
    {"name": "Pune-Bio", "lat": 18.5204, "lon": 73.8567}, {"name": "Solapur-Cold", "lat": 17.6599, "lon": 75.9064},
    {"name": "Kolhapur-Rescue", "lat": 16.7050, "lon": 74.2433}, {"name": "Ratnagiri-Vault", "lat": 16.9902, "lon": 73.3120},
    {"name": "Panaji-Safe", "lat": 15.4909, "lon": 73.8278},
    # Central India (10)
    {"name": "Gwalior-Cold", "lat": 26.2183, "lon": 78.1828}, {"name": "Jhansi-Hub", "lat": 25.4484, "lon": 78.5685},
    {"name": "Bhopal-Bio", "lat": 23.2599, "lon": 77.4126}, {"name": "Indore-Central", "lat": 22.7196, "lon": 75.8577},
    {"name": "Jabalpur-Apex", "lat": 23.1815, "lon": 79.9864}, {"name": "Sagar-Vault", "lat": 23.8388, "lon": 78.7378},
    {"name": "Raipur-Rescue", "lat": 21.2514, "lon": 81.6296}, {"name": "Nagpur-Apex", "lat": 21.1458, "lon": 79.0882},
    {"name": "Bilaspur-Cold", "lat": 22.0797, "lon": 82.1391}, {"name": "Durg-Safe", "lat": 21.1904, "lon": 81.2849},
    # East India (15)
    {"name": "Patna-Bio", "lat": 25.5941, "lon": 85.1376}, {"name": "Gaya-Vault", "lat": 24.7914, "lon": 85.0002},
    {"name": "Muzaffarpur-Safe", "lat": 26.1209, "lon": 85.3647}, {"name": "Ranchi-Apex", "lat": 23.3441, "lon": 85.3094},
    {"name": "Jamshedpur-Cold", "lat": 22.8046, "lon": 86.2029}, {"name": "Dhanbad-Rescue", "lat": 23.7957, "lon": 86.4304},
    {"name": "Asansol-Hub", "lat": 23.6739, "lon": 86.9524}, {"name": "Siliguri-Gateway", "lat": 26.7271, "lon": 88.3953},
    {"name": "Durgapur-Vault", "lat": 23.5204, "lon": 87.3119}, {"name": "Kolkata-Central", "lat": 22.5726, "lon": 88.3639},
    {"name": "Haldia-Port", "lat": 22.0667, "lon": 88.0698}, {"name": "Bhubaneswar-Cold", "lat": 20.2961, "lon": 85.8245},
    {"name": "Cuttack-Apex", "lat": 20.4625, "lon": 85.8830}, {"name": "Rourkela-Safe", "lat": 22.2604, "lon": 84.8536},
    {"name": "Sambalpur-Vault", "lat": 21.4669, "lon": 83.9812},
    # South India (15)
    {"name": "Visakhapatnam-Bio", "lat": 17.6868, "lon": 83.2185}, {"name": "Vijayawada-Hub", "lat": 16.5062, "lon": 80.6480},
    {"name": "Nellore-Cold", "lat": 14.4426, "lon": 79.9865}, {"name": "Tirupati-Vault", "lat": 13.6285, "lon": 79.4192},
    {"name": "Bangalore-Apex", "lat": 12.9716, "lon": 77.5946}, {"name": "Mysore-Rescue", "lat": 12.2958, "lon": 76.6394},
    {"name": "Hubli-Safe", "lat": 15.3647, "lon": 75.1240}, {"name": "Mangalore-Vault", "lat": 12.9141, "lon": 74.8560},
    {"name": "Chennai-Port", "lat": 13.0827, "lon": 80.2707}, {"name": "Coimbatore-Bio", "lat": 11.0168, "lon": 76.9558},
    {"name": "Salem-Rescue", "lat": 11.6643, "lon": 78.1460}, {"name": "Madurai-Apex", "lat": 9.9252, "lon": 78.1198},
    {"name": "Kochi-South", "lat": 9.9312, "lon": 76.2673}, {"name": "Kozhikode-Vault", "lat": 11.2588, "lon": 75.7804},
    {"name": "Trivandrum-Safe", "lat": 8.5241, "lon": 76.9366},
    # Northeast India (10)
    {"name": "Guwahati-Apex", "lat": 26.1445, "lon": 91.7362}, {"name": "Shillong-East", "lat": 25.5788, "lon": 91.8933},
    {"name": "Itanagar-Vault", "lat": 27.0844, "lon": 93.6053}, {"name": "Dibrugarh-Cold", "lat": 27.4728, "lon": 94.9120},
    {"name": "Dimapur-Rescue", "lat": 25.9064, "lon": 93.7270}, {"name": "Kohima-Safe", "lat": 25.6751, "lon": 94.1086},
    {"name": "Imphal-Bio", "lat": 24.8170, "lon": 93.9368}, {"name": "Agartala-Vault", "lat": 23.8315, "lon": 91.2868},
    {"name": "Aizawl-Apex", "lat": 23.7271, "lon": 92.7176}, {"name": "Gangtok-Safe", "lat": 27.3314, "lon": 88.6138}
]

DRIVERS = [
    "Amitav Ghosh", "S. Jaishankar", "K. Rathore", "Mohd. Salim", "Pritam Singh", 
    "R. Deshmukh", "Gurdeep Paaji", "Vijay Mallya", "S. Tharoor", "N. Chandran", 
    "Arjun Kapur", "Deepak Punia", "Suresh Raina", "M. S. Dhoni", "Hardik Pandya"
]

# --- HELPER FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_real_forecast(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m&forecast_days=1"
    try:
        r = requests.get(url, timeout=5).json()
        return r['hourly']['temperature_2m'][:8]
    except: return [28.0] * 8 

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
    k = 0.15
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
