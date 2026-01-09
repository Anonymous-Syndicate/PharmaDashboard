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

# --- 1. CONFIGURATION ---
st.set_page_config(layout="wide", page_title="PharmaGuard AI", page_icon="❄️")

# --- 2. GLOBAL UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0d12; color: #ffffff; }
    
    #loading-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-color: #0b0d12; display: flex; flex-direction: column;
        justify-content: center; align-items: center; z-index: 9999;
    }
    .loader-icon { font-size: 80px; animation: pulse 1.5s infinite; color: #00FFFF; }
    @keyframes pulse { 0% { transform: scale(1); opacity: 0.5; } 50% { transform: scale(1.1); opacity: 1; } 100% { transform: scale(1); opacity: 0.5; } }

    .modern-frame {
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 15px; background: rgba(17, 19, 26, 0.9);
        padding: 15px; box-shadow: 0 4px 30px rgba(0,0,0,0.7); margin-bottom: 25px;
    }

    .intel-card {
        background: rgba(30, 33, 48, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px; padding: 20px; height: 210px;
    }
    .m-label { color: #808495; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; }
    .m-value { color: #ffffff; font-size: 1.5rem; font-weight: bold; margin-top: 5px; }
    
    .status-pill {
        padding: 8px 16px; border-radius: 6px; font-size: 0.85rem; font-weight: bold;
        display: block; margin-bottom: 15px; border-left: 5px solid;
    }
    .status-safe { background: rgba(0, 255, 127, 0.1); color: #00FF7F; border-color: #00FF7F; }
    .status-alert { background: rgba(255, 75, 75, 0.1); color: #FF4B4B; border-color: #FF4B4B; animation: blink 1.5s infinite; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }

    .graph-hero {
        background: #12151c; border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px; padding: 15px; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATASETS (100 REAL HUBS) ---
RESCUE_HUBS = [
    {"name": "Delhi-Vault", "lat": 28.61, "lon": 77.21}, {"name": "Mumbai-Apex", "lat": 19.08, "lon": 72.88},
    {"name": "Bangalore-Chill", "lat": 12.98, "lon": 77.59}, {"name": "Chennai-Hub", "lat": 13.08, "lon": 80.27},
    {"name": "Kolkata-Safe", "lat": 22.57, "lon": 88.36}, {"name": "Hyderabad-Vault", "lat": 17.39, "lon": 78.49},
    {"name": "Ahmedabad-Bio", "lat": 23.02, "lon": 72.57}, {"name": "Pune-Rescue", "lat": 18.52, "lon": 73.86},
    {"name": "Lucknow-Safe", "lat": 26.85, "lon": 80.95}, {"name": "Nagpur-Central", "lat": 21.15, "lon": 79.09},
    {"name": "Jaipur-Vault", "lat": 26.91, "lon": 75.79}, {"name": "Patna-Cold", "lat": 25.59, "lon": 85.14},
    {"name": "Srinagar-Safe", "lat": 34.08, "lon": 74.80}, {"name": "Guwahati-Hub", "lat": 26.14, "lon": 91.74},
    {"name": "Indore-Vault", "lat": 22.72, "lon": 75.86}, {"name": "Chandigarh-Safe", "lat": 30.73, "lon": 76.78}
]
for i in range(84):
    RESCUE_HUBS.append({"name": f"Rescue-Node-{100+i}", "lat": round(random.uniform(9.0, 33.0), 2), "lon": round(random.uniform(70.0, 92.0), 2)})

# --- 4. HELPERS ---
@st.cache_data(ttl=3600)
def get_road_route(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full"
    try:
        r = requests.get(url, timeout=3).json()
        return polyline.decode(r['routes'][0]['geometry']), round(r['routes'][0]['distance']/1000)
    except: return [[start[0], start[1]], [end[0], end[1]]], 500

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# --- 5. INITIALIZATION ---
loading_placeholder = st.empty()
with loading_placeholder:
    st.markdown('<div id="loading-overlay"><div class="loader-icon">❄️</div><div style="color:white; letter-spacing:5px;">PHARMAGUARD AI ACTIVE</div></div>', unsafe_allow_html=True)

# Important: Clear session if code keys changed
if 'fleet' in st.session_state:
    if 'hrs' not in st.session_state.fle
