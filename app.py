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

# --- CUSTOM CSS FOR LOADING SCREEN ---
st.markdown("""
    <style>
    #loading-overlay {
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-color: #0e1117;
        display: flex; flex-direction: column;
        justify-content: center; align-items: center;
        z-index: 9999; color: white;
    }
    .loader { font-size: 120px; animation: pulse 2s infinite; margin-bottom: 25px; }
    @keyframes pulse {
        0% { transform: scale(1); opacity: 0.7; }
        50% { transform: scale(1.2); opacity: 1; color: #00FFFF; }
        100% { transform: scale(1); opacity: 0.7; }
    }
    .loading-text { font-size: 28px; font-weight: 300; letter-spacing: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- 80 REAL STRATEGIC RESCUE HUBS ---
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
    {"name": "Bhopal-Hub", "lat": 23.26, "lon": 77.41}, {"name": "Indore-Vault", "lat": 22.72, "lon": 75.86},
    {"name": "Jabalpur-Safe", "lat": 23.18, "lon": 79.99}, {"name": "Gwalior-Apex", "lat": 26.22, "lon": 78.18},
    {"name": "Shimla-Chill", "lat": 31.10, "lon": 77.17}, {"name": "Mangalore-Rescue", "lat": 12.91, "lon": 74.86},
    {"name": "Kozhikode-Safe", "lat": 11.26, "lon": 75.78}, {"name": "Thrissur-Vault", "lat": 10.53, "lon": 76.21},
    {"name": "Siliguri-Hub", "lat": 26.73, "lon": 88.40}, {"name": "Asansol-Safe", "lat": 23.67, "lon": 86.95},
    {"name": "Dhanbad-Vault", "lat": 23.80, "lon": 86.43}, {"name": "Rourkela-Apex", "lat": 22.26, "lon": 84.85},
    {"name": "Guntur-Cold", "lat": 16.31, "lon": 80.44}, {"name": "Nellore-Safe", "lat": 14.44, "lon": 79.99},
    {"name": "Kurnool-Vault", "lat": 15.83, "lon": 78.04}, {"name": "Warangal-Hub", "lat": 17.97, "lon": 79.59},
    {"name": "Gaya-Apex", "lat": 24.79, "lon": 85.00}, {"name": "Bhagalpur-Safe", "lat": 25.24, "lon": 86.97},
    {"name": "Bhavnagar-Vault", "lat": 21.76, "lon": 72.15}, {"name": "Jamnagar-Safe", "lat": 22.47, "lon": 70.06},
    {"name": "Bareilly-Hub", "lat": 28.37, "lon": 79.43}, {"name": "Aligarh-Safe", "lat": 27.88, "lon": 78.08},
    {"name": "Meerut-Vault", "lat": 28.98, "lon": 77.71}, {"name": "Jhansi-Apex", "lat": 25.45, "lon": 78.57},
    {"name": "Bilaspur-Chill", "lat": 22.08, "lon": 82.14}, {"name": "Gulbarga-Safe", "lat": 17.33, "lon": 76.83},
    {"name": "Bellary-Vault", "lat": 15.14, "lon": 76.92}, {"name": "Belgaum-Rescue", "lat": 15.85, "lon": 74.50},
    {"name": "Hubli-Safe", "lat": 15.36, "lon": 75.12}, {"name": "Trivandrum-Bio", "lat": 8.52, "lon": 76.94}
]

PHARMA_HUBS = {
    "Baddi Hub (North)": [30.9578, 76.7914], "Sikkim Cluster (East)": [27.3314, 88.6138],
    "Ahmedabad (West)": [23.0225, 72.5714], "Hyderabad (South)": [17.4500, 78.6000],
    "Vizag Pharma City": [17.6868, 83.2185], "Goa Manufacturing": [15.2993, 74.1240],
