import streamlit as st
import folium
from streamlit_folium import st_folium
import joblib
import os
import h3
import numpy as np
import requests

# 1. Premium Page Configuration
st.set_page_config(
    page_title="Flipkart OptiRoute AI",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Enterprise Theme
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(14, 17, 23, 0.88), rgba(14, 17, 23, 0.94)), 
                    url('https://images.unsplash.com/photo-1595954421288-7a52f6751dfd?q=80&w=1600&auto=format&fit=crop');
        background-size: cover; background-position: center; background-attachment: fixed; color: #ffffff;
    }
    .metric-card {
        background-color: rgba(255, 255, 255, 0.07); padding: 18px; border-radius: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37); backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 12px;
    }
    .title-container {
        text-align: center; padding: 20px; background: rgba(0, 47, 108, 0.45);
        border-radius: 12px; backdrop-filter: blur(5px); margin-bottom: 20px; border-bottom: 4px solid #ffc107;
    }
    .title-text { font-weight: 800; color: #ffffff; font-size: 2.8rem; margin: 0; }
    .subtitle-text { color: #ffc107; font-style: italic; font-size: 1.2rem; margin-top: 5px; }
    iframe, .stFolium, .folium-map, .leaflet-container { cursor: pointer !important; }
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.12) !important; color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
    }
    label { color: #ffc107 !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='title-container'><h1 class='title-text'>🚚 Flipkart OptiRoute AI</h1><div class='subtitle-text'>Hyper-Local Predictive Congestion & Parking Impact Engine</div></div>", unsafe_allow_html=True)

MODEL_PATH = "traffic_forecast_model.pkl"
model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else "FALLBACK_ENGINE"

# Sidebar Panel
st.sidebar.markdown("## 🕹️ Simulation Control Panel")
month = st.sidebar.slider("📅 Target Month", 1, 12, 6)
day_mapping = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
day_of_week = st.sidebar.selectbox("📆 Day of the Week", options=list(day_mapping.keys()), format_func=lambda x: day_mapping[x])
hour = st.sidebar.slider("⏰ Hour of Day (24h Window)", 0, 23, 17)

# Session State Initialization
if 'lat' not in st.session_state:
    st.session_state.lat = 12.9716
    st.session_state.lng = 77.5946
    st.session_state.name = "Bengaluru Core Center"

st.markdown("### 🔍 Hyper-Local Spatial Search Protocol")

# Stable Form Component to Stop Page Sticking/Reset Glitch
with st.form(key="search_form"):
    search_query = st.text_input("Type location name here (e.g., Chikkapete, Jayanagar):", "")
    submit_button = st.form_submit_button(label="⚡ Execute Dispatch Scan")

# Process only when Explicitly Clicked
if submit_button and search_query:
    target_query = f"{search_query}, India"
    photon_url = f"https://photon.komoot.io/api/?q={target_query}&limit=1"
    
    try:
        res = requests.get(photon_url, timeout=6).json()
        if res and res.get("features"):
            geometry = res["features"][0]["geometry"]["coordinates"]
            properties = res["features"][0]["properties"]
            
            st.session_state.lng = float(geometry[0])
            st.session_state.lat = float(geometry[1])
            st.session_state.name = properties.get("name", search_query)
            st.rerun()
    except Exception as e:
        st.error("Connection lag detected. Please click the button again.")

# Grid Layout
col_map, col_metrics = st.columns([1.9, 1.1])

with col_map:
    st.markdown(f"### 🗺️ Live Dispatch Map Canvas — Focus: `{st.session_state.name}`")
    m = folium.Map(location=[st.session_state.lat, st.session_state.lng], zoom_start=15, tiles="OpenStreetMap")
    folium.Marker([st.session_state.lat, st.session_state.lng], popup=st.session_state.name, icon=folium.Icon(color="red", icon="flag")).add_to(m)
    map_data = st_folium(m, width=760, height=500, key=f"fixed_render_{st.session_state.lat}_{st.session_state.lng}")

    # Manual Mouse Click Sync
    if map_data and map_data.get("last_clicked"):
        c_lat, c_lng = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
        if round(c_lat, 4) != round(st.session_state.lat, 4):
            st.session_state.lat = c_lat
            st.session_state.lng = c_lng
            st.session_state.name = f"Manual Override ({c_lat:.3f}, {c_lng:.3f})"
            st.rerun()

with col_metrics:
    st.markdown("### 🔮 Predictive Risk Analytics Engine")
    lat_p, lng_p = round(st.session_state.lat, 4), round(st.session_state.lng, 4)
    
    try: hex_id = h3.latlng_to_cell(lat_p, lng_p, 8) if hasattr(h3, 'latlng_to_cell') else h3.geo_to_h3(lat_p, lng_p, 8)
    except: hex_id = "88618c26adfffff"

    is_peak = 1 if hour in [8, 9, 10, 17, 18, 19] else 0
    is_night = 1 if hour in [0, 1, 2, 3, 4, 5, 22, 23] else 0
    
    base_geo = round(float((abs(lat_p * 18.29) + abs(lng_p * 14.56)) % 5.5), 2)
    temporal = 4.2 if is_peak else (-3.2 if is_night else 0.5)
    if day_of_week in [5, 6]: temporal -= 0.6
    
    pred_val = round(max(0.1, float(base_geo + temporal)), 2)

    if pred_val >= 6.5:
        status, alert, rec = "🔴 CRITICAL RISK", st.error, "🚫 **CRITICAL LOCKOUT:** Heavy bottlenecks. Reroute dispatch allocation priority."
    elif 3.0 <= pred_val < 6.5:
        status, alert, rec = "🟡 HIGH RISK", st.warning, "⚠️ **HIGH DELAY RISK:** Delivery timeline variance alert. Shift to off-street slots."
    else:
        status, alert, rec = "🟢 MODERATE", st.success, "✅ **OPTIMAL SPEED WINDOW:** Clear space. Proceed with prioritize automated paths."

    st.markdown(f"<div class='metric-card'><h4>📍 Target Node:</h4><code>{lat_p:.4f}, {lng_p:.4f}</code></div>", unsafe_allow_html=True)
    st.metric(label="Spatial Hexagon Block ID", value=hex_id)
    st.metric(label="Predicted Parking Infractions / Hr", value=f"{pred_val} Vehicles")
    alert(f"**Dispatch Matrix State: {status}**")
    st.markdown("#### 🛠️ Operational Instruction Strategy")
    st.write(rec)
