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

# --- STRATEGIC HUB DATASETS ---
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

# --- 80 REAL INDIAN CITIES FOR RESCUE HUBS ---
WAREHOUSE_NETWORK = [
    {"name": "Delhi-Vault", "lat": 28.61, "lon": 77.21}, {"name": "Mumbai-Apex", "lat": 19.08, "lon": 72.88},
    {"name": "Bangalore-Chill", "lat": 12.98, "lon": 77.59}, {"name": "Chennai-Hub", "lat": 13.08, "lon": 80.27},
    {"name": "Kolkata-Safe", "lat": 22.57, "lon": 88.36}, {"name": "Hyderabad-Vault", "lat": 17.39, "lon": 78.49},
    {"name": "Ahmedabad-Bio", "lat": 23.02, "lon": 72.57}, {"name": "Pune-Rescue", "lat": 18.52, "lon": 73.86},
    {"name": "Lucknow-Safe", "lat": 26.85, "lon": 80.95}, {"name": "Nagpur-Central", "lat": 21.15, "lon": 79.09},
    {"name": "Jaipur-Vault", "lat": 26.91, "lon": 75.79}, {"name": "Kanpur-Apex", "lat": 26.45, "lon": 80.33},
    {"name": "Surat-Safe", "lat": 21.17, "lon": 72.83}, {"name": "Patna-Cold", "lat": 25.59, "lon": 85.14},
    {"name": "Vadodara-Chill", "lat": 22.31, "lon": 73.18}, {"name": "Ludhiana-Hub", "lat": 30.90, "lon": 75.86},
    {"name": "Agra-Vault", "lat": 27.18, "lon": 78.01}, {"name": "Nashik-Apex", "lat": 20.00, "lon": 73.79},
    {"name": "Ranchi-Safe", "lat": 23.34, "lon": 85.31}, {"name": "Raipur-Rescue", "lat": 21.25, "lon": 81.63},
    {"name": "Guwahati-Vault", "lat": 26.14, "lon": 91.74}, {"name": "Chandigarh-Safe", "lat": 30.73, "lon": 76.78},
    {"name": "Bhubaneswar-Apex", "lat": 20.30, "lon": 85.82}, {"name": "Coimbatore-Chill", "lat": 11.02, "lon": 76.96},
    {"name": "Vijayawada-Hub", "lat": 16.51, "lon": 80.65}, {"name": "Madurai-Safe", "lat": 9.93, "lon": 78.12},
    {"name": "Jodhpur-Vault", "lat": 26.24, "lon": 73.02}, {"name": "Kochi-Bio", "lat": 9.93, "lon": 76.27},
    {"name": "Dehradun-Rescue", "lat": 30.32, "lon": 78.03}, {"name": "Ambala-Cold", "lat": 30.38, "lon": 76.78},
    {"name": "Gorakhpur-Apex", "lat": 26.76, "lon": 83.37}, {"name": "Amritsar-Safe", "lat": 31.63, "lon": 74.87},
    {"name": "Jammu-Vault", "lat": 32.73, "lon": 74.86}, {"name": "Srinagar-Safe", "lat": 34.08, "lon": 74.80},
    {"name": "Shillong-Apex", "lat": 25.58, "lon": 91.89}, {"name": "Gangtok-Bio", "lat": 27.33, "lon": 88.61},
    {"name": "Imphal-Rescue", "lat": 24.82, "lon": 93.94}, {"name": "Itanagar-Safe", "lat": 27.08, "lon": 93.61},
    {"name": "Panaji-Vault", "lat": 15.49, "lon": 73.83}, {"name": "Mysore-Chill", "lat": 12.30, "lon": 76.64},
    {"name": "Tirupati-Hub", "lat": 13.63, "lon": 79.42}, {"name": "Pondicherry-Safe", "lat": 11.94, "lon": 79.81},
    {"name": "Salem-Apex", "lat": 11.66, "lon": 78.15}, {"name": "Udaipur-Vault", "lat": 24.59, "lon": 73.71},
    {"name": "Bikaner-Cold", "lat": 28.02, "lon": 73.31}, {"name": "Ajmer-Safe", "lat": 26.45, "lon": 74.64},
    {"name": "Bhuj-Vault", "lat": 23.24, "lon": 69.67}, {"name": "Rajkot-Apex", "lat": 22.30, "lon": 70.80},
    {"name": "Varanasi-Chill", "lat": 25.32, "lon": 82.97}, {"name": "Jamshedpur-Safe", "lat": 22.80, "lon": 86.20},
    {"name": "Bhopal-Hub", "lat": 23.26, "lon": 77.41}, {"name": "Indore-Vault"
